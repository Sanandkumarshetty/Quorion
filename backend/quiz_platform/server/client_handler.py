import json
import threading
import time

from server.connection_manager import (
    add_admin_connection,
    add_student_connection,
    broadcast_to_admins,
    broadcast_to_students,
    remove_connection,
)


_sessions_lock = threading.RLock()
_sessions = {}


def _parse_message(raw_data):
    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode("utf-8", errors="ignore")
    raw_data = raw_data.strip()
    if not raw_data:
        return {}

    try:
        message = json.loads(raw_data)
    except json.JSONDecodeError:
        return {"action": "invalid", "payload": {"reason": "invalid-json"}}

    if not isinstance(message, dict):
        return {"action": "invalid", "payload": {"reason": "object-required"}}
    return message


def _build_response(message_type, payload):
    return json.dumps({"type": message_type, "payload": payload}) + "\n"


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
            _sessions[quiz_id] = {
                "quiz_id": quiz_id,
                "students": set(),
                "answers": {},
                "scores": {},
                "completion_time": {},
                "started_at": time.time(),
                "ended": False,
                "lock": threading.RLock(),
            }
        return _sessions[quiz_id]


def _calculate_leaderboard(quiz_id):
    with _sessions_lock:
        session = _sessions.get(quiz_id)
    if not session:
        return []

    with session["lock"]:
        rows = []
        for student_id, score in session["scores"].items():
            rows.append(
                {
                    "student_id": student_id,
                    "score": score,
                    "completion_time": session["completion_time"].get(student_id, float("inf")),
                }
            )

    rows.sort(key=lambda row: (-float(row.get("score", 0)), float(row.get("completion_time", float("inf")))))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


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

    if student_id is None or quiz_id is None:
        return {"ok": False, "error": "student_id-and-quiz_id-required"}

    session = _get_or_create_session(quiz_id)
    with session["lock"]:
        session["students"].add(student_id)
        session["answers"].setdefault(student_id, {})
        session["scores"].setdefault(student_id, 0)

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

    if None in (student_id, quiz_id, question_id) or not selected_option:
        return {"ok": False, "error": "missing-answer-fields"}

    session = _get_or_create_session(quiz_id)
    with session["lock"]:
        session["answers"].setdefault(student_id, {})
        session["answers"][student_id][question_id] = selected_option

    return {"ok": True, "saved": True}


def process_submit(message):
    payload = message.get("payload", {})
    student_id = payload.get("student_id")
    quiz_id = payload.get("quiz_id")

    if student_id is None or quiz_id is None:
        return {"ok": False, "error": "student_id-and-quiz_id-required"}

    score = float(payload.get("score", 0))
    completion_time = payload.get("completion_time")

    session = _get_or_create_session(quiz_id)
    with session["lock"]:
        session["scores"][student_id] = score
        if completion_time is None:
            completion_time = max(time.time() - session["started_at"], 0)
        session["completion_time"][student_id] = float(completion_time)

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
