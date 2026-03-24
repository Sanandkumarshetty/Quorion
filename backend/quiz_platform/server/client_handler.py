import json
import threading

from quiz_runtime.leaderboard import get_leaderboard
from quiz_runtime.quiz_session import add_student_to_session, create_session, end_session, record_answer
from server.connection_manager import (
    add_admin_connection,
    add_student_connection,
    broadcast_to_admins,
    broadcast_to_students,
    remove_connection,
)
from utils.helpers import create_response_message, parse_message
from utils.timer import get_remaining_time, start_timer


_sessions_lock = threading.RLock()
_sessions = {}


def _parse_message(raw_data):
    return parse_message(raw_data)


def _build_response(message_type, payload):
    return create_response_message(message_type, payload)


def _send_message(client_socket, message):
    data = message.encode("utf-8")
    total_sent = 0

    while total_sent < len(data):
        sent = client_socket.send(data[total_sent:])
        if sent == 0:
            raise OSError("socket connection broken")
        total_sent += sent


def _send(client_socket, message_type, payload):
    response = _build_response(message_type, payload)
    _send_message(client_socket, response)


def _get_or_create_session(quiz_id):
    with _sessions_lock:
        if quiz_id not in _sessions:
            session = create_session(quiz_id)
            session.update(
                {
                    "student_names": {},
                    "attempted_count": {},
                    "total_questions": {},
                    "submitted": set(),
                    "started_at": start_timer(session.get("quiz", {}).get("duration", 0) or 0),
                }
            )
            _sessions[quiz_id] = session
        return _sessions[quiz_id]


def _decorate_leaderboard_rows(session, rows):
    decorated_rows = []
    total_questions_map = session.get("total_questions", {})
    attempted_count_map = session.get("attempted_count", {})
    student_names = session.get("student_names", {})
    submitted = session.get("submitted", set())

    for row in rows:
        student_id = row.get("student_id")
        total_questions = int(total_questions_map.get(student_id, 0) or 0)
        attempted_count = int(attempted_count_map.get(student_id, 0) or 0)
        is_submitted = student_id in submitted
        decorated = dict(row)
        decorated["name"] = student_names.get(student_id, f"Student {student_id}")
        decorated["total_questions"] = total_questions
        decorated["attempted_count"] = attempted_count
        decorated["completion"] = "Completed" if is_submitted else f"{attempted_count}/{total_questions} answered"
        decorated["status"] = "Submitted" if is_submitted else "Live"
        decorated_rows.append(decorated)

    decorated_rows.sort(
        key=lambda row: (
            -float(row.get("score", 0)),
            -int(row.get("attempted_count", 0)),
            float(row.get("completion_time", float("inf"))),
            str(row.get("name", "")).lower(),
        )
    )
    for index, row in enumerate(decorated_rows, start=1):
        row["rank"] = index
    return decorated_rows


def _calculate_leaderboard(quiz_id):
    with _sessions_lock:
        session = _sessions.get(quiz_id)
    if not session:
        return []

    rows = get_leaderboard(session)
    return _decorate_leaderboard_rows(session, rows)


def handle_client(client_socket):
    buffer = ""
    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = _parse_message(line)
                if not message:
                    continue

                action = message.get("action")
                message["_client_socket"] = client_socket

                if action == "login":
                    payload = process_login(message)
                elif action == "join_quiz":
                    payload = process_join_quiz(message)
                elif action == "answer":
                    payload = process_answer(message)
                elif action == "submit":
                    payload = process_submit(message)
                elif action == "leaderboard":
                    quiz_id = message.get("payload", {}).get("quiz_id")
                    payload = {"ok": True, "leaderboard": _calculate_leaderboard(quiz_id)}
                else:
                    payload = {"ok": False, "error": f"unknown-action:{action}"}

                _send(client_socket, "response", payload)
    except OSError:
        pass
    finally:
        disconnect_client(client_socket)


def process_login(message):
    payload = message.get("payload", {})
    client_socket = message.get("_client_socket")

    role = payload.get("role")
    user_id = payload.get("user_id")

    if role not in {"student", "admin"}:
        return {"ok": False, "error": "invalid-role"}
    if user_id is None:
        return {"ok": False, "error": "user_id-required"}

    if role == "student":
        add_student_connection(user_id, client_socket)
    else:
        add_admin_connection(user_id, client_socket)

    return {"ok": True, "role": role, "user_id": user_id}


def process_join_quiz(message):
    payload = message.get("payload", {})
    student_id = payload.get("student_id")
    quiz_id = payload.get("quiz_id")
    student_name = payload.get("student_name")
    total_questions = payload.get("total_questions")

    if student_id is None or quiz_id is None:
        return {"ok": False, "error": "student_id-and-quiz_id-required"}

    session = _get_or_create_session(quiz_id)
    add_student_to_session(session, student_id)
    with session["lock"]:
        session["attempted_count"].setdefault(student_id, 0)
        if student_name:
            session["student_names"][student_id] = student_name
        if total_questions is not None:
            session["total_questions"][student_id] = int(total_questions)

    broadcast_to_admins(
        _build_response(
            "event",
            {
                "event": "student_joined",
                "quiz_id": quiz_id,
                "student_id": student_id,
            },
        )
    )
    return {"ok": True, "quiz_id": quiz_id, "student_id": student_id}


def process_answer(message):
    payload = message.get("payload", {})
    student_id = payload.get("student_id")
    quiz_id = payload.get("quiz_id")
    question_id = payload.get("question_id")
    selected_option = payload.get("selected_option")
    score = payload.get("score")
    attempted_count = payload.get("attempted_count")
    total_questions = payload.get("total_questions")
    student_name = payload.get("student_name")

    if None in (student_id, quiz_id, question_id) or not selected_option:
        return {"ok": False, "error": "missing-answer-fields"}

    session = _get_or_create_session(quiz_id)
    record_answer(session, student_id, question_id, selected_option)
    with session["lock"]:
        if score is not None:
            session["scores"][student_id] = float(score)
        if attempted_count is not None:
            session["attempted_count"][student_id] = int(attempted_count)
        if total_questions is not None:
            session["total_questions"][student_id] = int(total_questions)
        if student_name:
            session["student_names"][student_id] = student_name

    leaderboard = _calculate_leaderboard(quiz_id)
    broadcast_to_admins(
        _build_response(
            "event",
            {"event": "leaderboard_update", "quiz_id": quiz_id, "rows": leaderboard},
        )
    )

    return {"ok": True, "saved": True, "leaderboard": leaderboard}


def process_submit(message):
    payload = message.get("payload", {})
    student_id = payload.get("student_id")
    quiz_id = payload.get("quiz_id")
    student_name = payload.get("student_name")
    total_questions = payload.get("total_questions")
    attempted_count = payload.get("attempted_count")

    if student_id is None or quiz_id is None:
        return {"ok": False, "error": "student_id-and-quiz_id-required"}

    score = float(payload.get("score", 0))
    completion_time = payload.get("completion_time")

    session = _get_or_create_session(quiz_id)
    with session["lock"]:
        session["scores"][student_id] = score
        if student_name:
            session["student_names"][student_id] = student_name
        if total_questions is not None:
            session["total_questions"][student_id] = int(total_questions)
        if attempted_count is not None:
            session["attempted_count"][student_id] = int(attempted_count)
        if completion_time is None:
            duration = session.get("quiz", {}).get("duration", 0) or 0
            completion_time = max(float(duration) - get_remaining_time(session.get("started_at"), duration), 0.0)
        session["completion_time"][student_id] = float(completion_time)
        session["submitted"].add(student_id)
    end_session(session)

    leaderboard = _calculate_leaderboard(quiz_id)
    leaderboard_message = _build_response(
        "event",
        {"event": "leaderboard_update", "quiz_id": quiz_id, "rows": leaderboard},
    )
    broadcast_to_students(leaderboard_message)
    broadcast_to_admins(leaderboard_message)

    return {"ok": True, "submitted": True, "leaderboard": leaderboard}


def disconnect_client(client_socket):
    remove_connection(client_socket)
