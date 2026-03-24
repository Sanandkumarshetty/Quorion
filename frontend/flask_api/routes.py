import csv
import io
import os
import sys
from datetime import datetime, timedelta

from flask import Blueprint, Response, jsonify, request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from auth.admin_auth import login_admin, register_admin
from auth.auth_service import validate_token
from auth.student_auth import login_student, register_student
from quiz_management.question_manager import add_question as add_managed_question
from quiz_management.quiz_creator import create_private_quiz, create_public_quiz
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository
from repositories.submission_repository import SubmissionRepository


quiz_repository = QuizRepository()
submission_repository = SubmissionRepository()
question_repository = QuestionRepository()
from database.session import SessionLocal
from quiz_runtime.evaluation import evaluate_answer

try:
    from .tcp_bridge import send_tcp_request
except ImportError:
    from tcp_bridge import send_tcp_request

api = Blueprint("api", __name__)


ERROR_MESSAGES = {
    "invalid-credentials": "Invalid email or password.",
    "admin-access-required": "This account does not have admin access.",
    "student-access-required": "This account does not have student access.",
    "invalid-role": "Please choose a valid role.",
    "name-required": "Name is required.",
    "email-required": "Email is required.",
    "email-already-registered": "This email is already registered.",
    "password is required": "Password is required.",
    "invalid-token": "Your session is invalid. Please log in again.",
    "token-expired": "Your session expired. Please log in again.",
    "user-not-found": "User account not found.",
    "quiz-not-found": "Quiz not found.",
    "invalid-quiz-password": "Incorrect quiz password.",
    "private-quiz-password-required": "This private quiz requires a password.",
    "quiz-is-public": "This quiz is public and does not need a password.",
    "forbidden": "You do not have permission for this action.",
    "question-not-found": "Question not found.",
    "submission-not-found": "Submission not found. Join the quiz first.",
    "quiz-already-submitted": "You have already submitted this quiz and cannot attempt it again.",
    "quiz-not-started": "This private quiz has not started yet. Please wait for the scheduled start time.",
    "quiz-ended": "This quiz has ended. You can no longer attempt it.",
    "leaderboard-not-available": "Leaderboard is available only for private quizzes.",
}


def _message_for(error_code):
    return ERROR_MESSAGES.get(error_code, error_code or "Request failed")


def _response_from_auth(result, success_status=200, failure_status=400):
    if result.get("ok"):
        return jsonify(result), success_status
    return jsonify({"ok": False, "error": result.get("error"), "message": _message_for(result.get("error"))}), failure_status


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    payload = request.get_json(silent=True) or {}
    return payload.get("token")


def _require_user(role=None):
    result = validate_token(_extract_token())
    if not result.get("ok"):
        return None, (jsonify({"ok": False, "error": result.get("error"), "message": _message_for(result.get("error"))}), 401)

    user = result.get("user")
    if role and user.get("role") != role:
        return None, (jsonify({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}), 403)

    return user, None


def _current_time():
    return datetime.now()


def _parse_start_time(value):
    if not value:
        return _current_time()
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def _quiz_end_time(quiz):
    start_time = quiz.start_time or _current_time()
    return start_time + timedelta(seconds=int(quiz.duration or 0))


def _quiz_status(quiz):
    now = _current_time()
    start_time = quiz.start_time or now
    end_time = _quiz_end_time(quiz)
    if end_time <= now:
        return "ended"
    if start_time > now:
        return "scheduled"
    return "active"


def _quiz_has_started(quiz):
    start_time = quiz.start_time or _current_time()
    return start_time <= _current_time()


def _quiz_has_ended(quiz):
    return _quiz_end_time(quiz) <= _current_time()


def _submission_end_time(submission, quiz):
    started_at = submission.submitted_at or _current_time()
    return started_at + timedelta(seconds=int(quiz.duration or 0))


def _submission_has_ended(submission, quiz):
    return _submission_end_time(submission, quiz) <= _current_time()


def _finalize_submission(submission, questions):
    if submission.completion_time is not None:
        return submission

    submitted_at = submission.submitted_at or _current_time()
    submission.score = _compute_submission_score(submission, questions)
    submission.completion_time = max((_current_time() - submitted_at).total_seconds(), 0.0)
    submission.submitted_at = _current_time()
    return submission


def _student_can_enter_quiz(quiz, user):
    return user.get("role") == "admin" or not quiz.is_private or _quiz_has_started(quiz)


def _serialize_question(question, include_correct=False):
    payload = {
        "questionId": question.question_id,
        "text": question.question_text,
        "options": {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d,
        },
    }
    if include_correct:
        payload["correctAnswer"] = question.correct_answer
    return payload


def _serialize_quiz(quiz, include_questions=False, include_correct=False, submission=None):
    quiz_type = "private" if quiz.is_private else "public"
    start_at = quiz.start_time.isoformat() if quiz.start_time else None
    end_at = _quiz_end_time(quiz).isoformat()
    status = _quiz_status(quiz)
    participant_count = len(getattr(quiz, "submissions", []))

    if not quiz.is_private:
        status = "active"
        start_at = None
        if submission and submission.completion_time is None:
            end_at = _submission_end_time(submission, quiz).isoformat()
        else:
            end_at = None

    payload = {
        "quizId": quiz.quiz_id,
        "title": quiz.title,
        "category": quiz.category,
        "createdBy": quiz.created_by,
        "createdByName": quiz.creator.name if getattr(quiz, "creator", None) else "Admin",
        "quizType": quiz_type,
        "password": quiz.password if quiz.is_private else "",
        "durationMinutes": max(1, int((quiz.duration or 0) / 60)),
        "startAt": start_at,
        "endAt": end_at,
        "status": status,
        "submissionCount": len([submission for submission in getattr(quiz, "submissions", []) if submission.completion_time is not None]),
        "participantCount": participant_count,
        "questionCount": len(getattr(quiz, "questions", [])),
    }
    if include_questions:
        payload["questions"] = [_serialize_question(question, include_correct=include_correct) for question in quiz.questions]
    return payload


def _compute_submission_score(submission, questions):
    answer_map = {answer.question_id: answer.selected_option for answer in submission.answers}
    score = 0.0
    for question in questions:
        selected = answer_map.get(question.question_id)
        score += evaluate_answer(question, selected).get("score", 0.0) if selected else 0.0
    return score


def _serialize_submission(submission):
    quiz = submission.quiz
    total_questions = len(quiz.questions)
    score = int(round(float(submission.score or 0.0)))
    percentage = int(round((score / total_questions) * 100)) if total_questions else 0
    answered = {str(answer.question_id): answer.selected_option for answer in submission.answers}
    payload = {
        "attemptId": submission.submission_id,
        "quizId": quiz.quiz_id,
        "quizTitle": quiz.title,
        "quizType": "private" if quiz.is_private else "public",
        "score": score,
        "totalQuestions": total_questions,
        "percentage": percentage,
        "completionTimeSeconds": submission.completion_time,
        "submittedAt": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "answers": answered,
        "completed": submission.completion_time is not None,
    }
    if not quiz.is_private and submission.completion_time is not None:
        payload["review"] = [
            {
                "questionId": question.question_id,
                "question": question.question_text,
                "options": {
                    "A": question.option_a,
                    "B": question.option_b,
                    "C": question.option_c,
                    "D": question.option_d,
                },
                "selectedOption": answered.get(str(question.question_id)),
                "correctAnswer": question.correct_answer,
            }
            for question in quiz.questions
        ]
    return payload


def _get_or_create_active_submission(db, quiz_id, student_id):
    active_submission = submission_repository.get_active_submission(db, quiz_id, student_id)
    if active_submission:
        return active_submission

    latest_submission = submission_repository.get_latest_submission(db, quiz_id, student_id)
    if latest_submission and latest_submission.completion_time is not None and latest_submission.quiz.is_private:
        return latest_submission

    return submission_repository.create_submission(quiz_id, student_id, submitted_at=_current_time())


def _build_leaderboard(quiz, viewer_user_id=None, include_live_attempts=False):
    questions = list(quiz.questions)
    rows = []
    total_questions = len(questions)

    for submission in quiz.submissions:
        progress_count = len(submission.answers)
        is_completed = submission.completion_time is not None
        if not include_live_attempts and not is_completed:
            continue

        live_score = int(round(_compute_submission_score(submission, questions)))
        rows.append({
            "rank": 0,
            "userId": submission.student_id,
            "name": submission.student.name if submission.student else f"Student {submission.student_id}",
            "score": live_score,
            "totalQuestions": total_questions,
            "attemptedCount": progress_count,
            "completion": "Completed" if is_completed else f"{progress_count}/{total_questions} answered",
            "status": "Current User" if str(submission.student_id) == str(viewer_user_id) else ("Submitted" if is_completed else "Live"),
            "sortCompletion": float(submission.completion_time) if is_completed else float("inf"),
            "sortProgress": progress_count,
        })

    rows.sort(key=lambda row: (-row["score"], -row["sortProgress"], row["sortCompletion"], str(row["name"]).lower()))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
        row.pop("sortCompletion", None)
        row.pop("sortProgress", None)

    viewer_rank = next((row["rank"] for row in rows if str(row["userId"]) == str(viewer_user_id)), None)
    return {
        "quiz": _serialize_quiz(quiz, include_questions=False),
        "leaderboard": rows,
        "participantCount": len(rows),
        "submissionCount": len([submission for submission in quiz.submissions if submission.completion_time is not None]),
        "viewerRank": viewer_rank,
        "liveParticipantCount": len([submission for submission in quiz.submissions if submission.completion_time is None]),
        "includesLiveAttempts": include_live_attempts,
    }


def _sync_tcp_join(user, quiz, submission=None):
    tcp_payload = {
        "student_id": user.get("user_id"),
        "quiz_id": quiz.quiz_id,
        "student_name": user.get("name") or f"User {user.get('user_id')}",
        "total_questions": len(getattr(quiz, "questions", []) or []),
    }
    if user.get("role") == "admin":
        tcp_payload["student_id"] = f"admin-{user.get('user_id')}"
    try:
        return send_tcp_request("join_quiz", tcp_payload)
    except OSError:
        return {"ok": False, "error": "tcp-unavailable"}


def _sync_tcp_answer(user, quiz, submission, question_id, selected_option):
    try:
        return send_tcp_request(
            "answer",
            {
                "student_id": user.get("user_id"),
                "student_name": user.get("name") or f"Student {user.get('user_id')}",
                "quiz_id": quiz.quiz_id,
                "question_id": question_id,
                "selected_option": selected_option,
                "score": int(round(float(submission.score or 0.0))),
                "attempted_count": len(submission.answers),
                "total_questions": len(quiz.questions),
            },
        )
    except OSError:
        return {"ok": False, "error": "tcp-unavailable"}


def _sync_tcp_submit(user, quiz, submission):
    try:
        return send_tcp_request(
            "submit",
            {
                "student_id": user.get("user_id"),
                "student_name": user.get("name") or f"Student {user.get('user_id')}",
                "quiz_id": quiz.quiz_id,
                "score": int(round(float(submission.score or 0.0))),
                "completion_time": float(submission.completion_time or 0.0),
                "attempted_count": len(submission.answers),
                "total_questions": len(quiz.questions),
            },
        )
    except OSError:
        return {"ok": False, "error": "tcp-unavailable"}


def _tcp_leaderboard_rows(quiz_id):
    try:
        response = send_tcp_request("leaderboard", {"quiz_id": quiz_id})
    except OSError:
        return []

    rows = response.get("leaderboard") if isinstance(response, dict) else []
    return rows if isinstance(rows, list) else []


def _csv_response_for_quiz(quiz):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Rank", "Student Name", "Student Email", "Score", "Total Questions", "Progress", "Status", "Submitted At"])
    leaderboard = _build_leaderboard(quiz, include_live_attempts=True).get("leaderboard", [])
    by_user = {submission.student_id: submission for submission in quiz.submissions}
    for row in leaderboard:
        submission = by_user.get(row["userId"])
        writer.writerow([
            row["rank"],
            row["name"],
            submission.student.email if submission and submission.student else "",
            row["score"],
            row["totalQuestions"],
            row["completion"],
            row["status"],
            submission.submitted_at.isoformat() if submission and submission.submitted_at else "",
        ])
    payload = buffer.getvalue()
    filename = f"quiz_{quiz.quiz_id}_results.csv"
    return Response(
        payload,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/auth/register")
def auth_register():
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if role == "admin":
        result = register_admin(name, email, password)
    elif role == "student":
        result = register_student(name, email, password)
    else:
        result = {"ok": False, "error": "invalid-role"}

    return _response_from_auth(result)


@api.post("/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()
    email = payload.get("email")
    password = payload.get("password")

    if role == "admin":
        result = login_admin(email, password)
    elif role == "student":
        result = login_student(email, password)
    else:
        result = {"ok": False, "error": "invalid-role"}

    return _response_from_auth(result)


@api.post("/auth/validate")
def auth_validate():
    result = validate_token((request.get_json(silent=True) or {}).get("token"))
    return _response_from_auth(result, failure_status=401)


@api.get("/quizzes/public")
def public_quizzes():
    db = SessionLocal()
    try:
        quizzes = quiz_repository.get_public_quizzes_with_relations(db)
        return jsonify({"ok": True, "quizzes": [_serialize_quiz(quiz, include_questions=False) for quiz in quizzes]})
    finally:
        db.close()


@api.get("/quizzes/admin")
def admin_quizzes():
    user, error = _require_user(role="admin")
    if error:
        return error

    db = SessionLocal()
    try:
        quizzes = quiz_repository.get_admin_quizzes_with_relations(db, user["user_id"])
        stats = {
            "totalQuizzes": len(quizzes),
            "activeQuizzes": len([quiz for quiz in quizzes if _quiz_status(quiz) == "active"]),
            "submissionCount": sum(len([submission for submission in quiz.submissions if submission.completion_time is not None]) for quiz in quizzes),
        }
        return jsonify({"ok": True, "stats": stats, "quizzes": [_serialize_quiz(quiz, include_questions=True, include_correct=True) for quiz in quizzes]})
    finally:
        db.close()


@api.put("/quizzes/<int:quiz_id>")
def update_quiz(quiz_id):
    user, error = _require_user(role="admin")
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.created_by != user["user_id"]:
            return jsonify({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}), 403
        if quiz.is_private:
            return jsonify({"ok": False, "error": "forbidden", "message": "Only public quizzes can be modified from the dashboard."}), 403

        quiz.title = (payload.get("title") or quiz.title).strip()
        quiz.category = (payload.get("category") or quiz.category or "General Knowledge").strip()
        quiz.duration = max(60, int(payload.get("durationMinutes") or int((quiz.duration or 1800) / 60)) * 60)
        quiz.start_time = _parse_start_time(payload.get("startAt") or quiz.start_time)

        incoming_questions = payload.get("questions") or []
        existing_questions = list(quiz.questions)
        for question in existing_questions:
            db.delete(question)
        db.flush()

        db.commit()

        for question in incoming_questions:
            options = question.get("options") or {}
            question_repository.add_question(
                quiz.quiz_id,
                (question.get("text") or "").strip() or "Untitled Question",
                options.get("A") or "Option A",
                options.get("B") or "Option B",
                options.get("C") or "Option C",
                options.get("D") or "Option D",
                (question.get("correctAnswer") or question.get("correctKey") or "A").strip().upper(),
            )
        updated_quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        return jsonify({"ok": True, "quiz": _serialize_quiz(updated_quiz, include_questions=True, include_correct=True)})
    finally:
        db.close()


@api.delete("/quizzes/<int:quiz_id>")
def remove_quiz(quiz_id):
    user, error = _require_user(role="admin")
    if error:
        return error

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.created_by != user["user_id"]:
            return jsonify({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}), 403
        if quiz.is_private:
            return jsonify({"ok": False, "error": "forbidden", "message": "Only public quizzes can be deleted from the dashboard."}), 403
    finally:
        db.close()

    quiz_repository.delete_quiz(quiz_id)
    return jsonify({"ok": True, "deleted": True, "quizId": quiz_id})


@api.post("/quizzes")
def create_quiz():
    user, error = _require_user(role="admin")
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    questions = payload.get("questions") or []

    quiz_type = (payload.get("quizType") or "private")
    duration_seconds = max(60, int(payload.get("durationMinutes") or 30) * 60)
    start_time = _parse_start_time(payload.get("startAt"))
    if quiz_type == "public":
        quiz = create_public_quiz(
            title=(payload.get("title") or "Untitled Quiz").strip(),
            duration=duration_seconds,
            category=(payload.get("category") or "General Knowledge").strip(),
            created_by=user["user_id"],
            start_time=start_time,
        )
    else:
        quiz = create_private_quiz(
            title=(payload.get("title") or "Untitled Quiz").strip(),
            duration=duration_seconds,
            category=(payload.get("category") or "General Knowledge").strip(),
            password=(payload.get("password") or "").strip() or None,
            created_by=user["user_id"],
            start_time=start_time,
        )

    for question in questions:
        add_managed_question(
            quiz.quiz_id,
            (question.get("text") or "").strip() or "Untitled Question",
            question.get("options") or {},
            (question.get("correctAnswer") or question.get("correctKey") or "A").strip().upper(),
        )

    db = SessionLocal()
    try:
        created_quiz = quiz_repository.get_quiz_with_relations(db, quiz.quiz_id)
        return jsonify({"ok": True, "quiz": _serialize_quiz(created_quiz, include_questions=True, include_correct=True)})
    finally:
        db.close()


@api.post("/quizzes/join")
def join_quiz():
    user, error = _require_user()
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    quiz_id = payload.get("quizId")
    password = (payload.get("password") or "").strip()

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.is_private and quiz.password != password:
            return jsonify({"ok": False, "error": "invalid-quiz-password", "message": _message_for("invalid-quiz-password")}), 400

        serialized_quiz = _serialize_quiz(quiz, include_questions=True, include_correct=user["role"] == "admin")
        response = {
            "ok": True,
            "quiz": serialized_quiz,
            "requiresWaitingRoom": user["role"] == "student" and quiz.is_private and not _quiz_has_started(quiz),
        }
        _sync_tcp_join(user, quiz)

        if user["role"] == "student":
            submission = _get_or_create_active_submission(db, quiz.quiz_id, user["user_id"])
            if not quiz.is_private:
                if submission.completion_time is None and _submission_has_ended(submission, quiz):
                    _finalize_submission(submission, quiz.questions)
                    db.commit()
                    submission = submission_repository.get_latest_submission(db, quiz.quiz_id, user["user_id"])
                if submission.completion_time is not None:
                    submission = _get_or_create_active_submission(db, quiz.quiz_id, user["user_id"])
                response["quiz"] = _serialize_quiz(quiz, include_questions=True, include_correct=user["role"] == "admin", submission=submission)
                response["submission"] = _serialize_submission(submission) if submission.completion_time is None else None
                response["canAttempt"] = True
                return jsonify(response)

            response["submission"] = _serialize_submission(submission)
            response["canAttempt"] = submission.completion_time is None
        return jsonify(response)
    finally:
        db.close()


@api.get("/quizzes/<int:quiz_id>")
def quiz_details(quiz_id):
    user, error = _require_user()
    if error:
        return error

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.is_private and user["role"] != "admin":
            existing_submission = submission_repository.get_existing_submission(db, quiz_id, user["user_id"])
            if not existing_submission:
                return jsonify({"ok": False, "error": "forbidden", "message": _message_for("private-quiz-password-required")}), 403

        response = {
            "ok": True,
            "quiz": _serialize_quiz(quiz, include_questions=True, include_correct=user["role"] == "admin"),
            "requiresWaitingRoom": user["role"] == "student" and quiz.is_private and not _quiz_has_started(quiz),
        }
        if user["role"] == "student":
            if quiz.is_private:
                submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
                response["submission"] = _serialize_submission(submission) if submission else None
                response["canAttempt"] = bool(submission is None or submission.completion_time is None)
                return jsonify(response)

            submission = _get_or_create_active_submission(db, quiz_id, user["user_id"])
            if submission.completion_time is None and _submission_has_ended(submission, quiz):
                _finalize_submission(submission, quiz.questions)
                db.commit()
                submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
            if submission.completion_time is not None:
                submission = _get_or_create_active_submission(db, quiz_id, user["user_id"])
            response["quiz"] = _serialize_quiz(quiz, include_questions=True, include_correct=user["role"] == "admin", submission=submission)
            response["submission"] = _serialize_submission(submission) if submission.completion_time is None else None
            response["canAttempt"] = True
        return jsonify(response)
    finally:
        db.close()


@api.post("/quizzes/<int:quiz_id>/answers")
def save_quiz_answer(quiz_id):
    user, error = _require_user(role="student")
    if error:
        return error

    payload = request.get_json(silent=True) or {}
    question_id = payload.get("questionId")
    selected_option = str(payload.get("selectedOption") or "").strip().upper()

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404

        question = next((item for item in quiz.questions if item.question_id == question_id), None)
        if not question:
            return jsonify({"ok": False, "error": "question-not-found", "message": _message_for("question-not-found")}), 404
        if quiz.is_private and not _quiz_has_started(quiz):
            return jsonify({"ok": False, "error": "quiz-not-started", "message": _message_for("quiz-not-started")}), 409

        submission = _get_or_create_active_submission(db, quiz.quiz_id, user["user_id"])
        if not quiz.is_private and _submission_has_ended(submission, quiz):
            _finalize_submission(submission, quiz.questions)
            db.commit()
            return jsonify({"ok": False, "error": "quiz-ended", "message": _message_for("quiz-ended")}), 409
        if submission.completion_time is not None:
            return jsonify({"ok": False, "error": "quiz-already-submitted", "message": _message_for("quiz-already-submitted")}), 409
        submission_repository.save_answer(db, submission, question_id, selected_option)

        db.commit()
        db.refresh(submission)
        submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
        submission.score = _compute_submission_score(submission, quiz.questions)
        db.commit()
        db.refresh(submission)

        tcp_response = _sync_tcp_answer(user, quiz, submission, question_id, selected_option)

        return jsonify({
            "ok": True,
            "submission": _serialize_submission(submission),
            "liveScore": int(round(float(submission.score or 0.0))),
            "answeredCount": len(submission.answers),
            "tcpSynced": bool(tcp_response.get("ok")),
        })
    finally:
        db.close()


@api.post("/quizzes/<int:quiz_id>/submit")
def submit_quiz(quiz_id):
    user, error = _require_user(role="student")
    if error:
        return error

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.is_private and not _quiz_has_started(quiz):
            return jsonify({"ok": False, "error": "quiz-not-started", "message": _message_for("quiz-not-started")}), 409

        submission = submission_repository.get_active_submission(db, quiz_id, user["user_id"])
        if not submission:
            latest_submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
            if latest_submission and latest_submission.completion_time is not None:
                return jsonify({"ok": False, "error": "quiz-already-submitted", "message": _message_for("quiz-already-submitted")}), 409
            return jsonify({"ok": False, "error": "submission-not-found", "message": _message_for("submission-not-found")}), 404

        if not quiz.is_private and _submission_has_ended(submission, quiz):
            _finalize_submission(submission, quiz.questions)
        else:
            submission.score = _compute_submission_score(submission, quiz.questions)
            submission.completion_time = max((_current_time() - submission.submitted_at).total_seconds(), 0.0) if submission.submitted_at else 0.0
            submission.submitted_at = _current_time()
        db.commit()
        db.refresh(submission)
        submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
        tcp_response = _sync_tcp_submit(user, quiz, submission)
        return jsonify({"ok": True, "result": _serialize_submission(submission), "tcpSynced": bool(tcp_response.get("ok"))})
    finally:
        db.close()


@api.get("/quizzes/<int:quiz_id>/leaderboard")
def quiz_leaderboard(quiz_id):
    user, error = _require_user()
    if error:
        return error

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if not quiz.is_private:
            return jsonify({"ok": False, "error": "forbidden", "message": _message_for("leaderboard-not-available")}), 403

        if user["role"] == "student":
            completed_submission = submission_repository.get_completed_submission(db, quiz_id, user["user_id"])
            if not completed_submission:
                return jsonify({"ok": False, "error": "forbidden", "message": "Students can open the leaderboard only after submitting the full quiz."}), 403

        include_live_attempts = user["role"] == "admin"
        payload = _build_leaderboard(quiz, viewer_user_id=user["user_id"], include_live_attempts=include_live_attempts)
        tcp_rows = _tcp_leaderboard_rows(quiz_id)
        if include_live_attempts and tcp_rows:
            merged_rows = []
            database_rows = {str(row["userId"]): row for row in payload.get("leaderboard", [])}
            for row in tcp_rows:
                row_user_id = str(row.get("student_id"))
                if row_user_id.startswith("admin-"):
                    continue
                merged_rows.append({
                    "rank": row.get("rank", 0),
                    "userId": row.get("student_id"),
                    "name": row.get("name") or database_rows.get(row_user_id, {}).get("name", f"Student {row_user_id}"),
                    "score": int(round(float(row.get("score", 0) or 0))),
                    "totalQuestions": int(row.get("total_questions", database_rows.get(row_user_id, {}).get("totalQuestions", len(quiz.questions))) or len(quiz.questions)),
                    "attemptedCount": int(row.get("attempted_count", database_rows.get(row_user_id, {}).get("attemptedCount", 0)) or 0),
                    "completion": row.get("completion") or database_rows.get(row_user_id, {}).get("completion", "Live"),
                    "status": "Current User" if str(row.get("student_id")) == str(user["user_id"]) else (row.get("status") or "Live"),
                })
            if merged_rows:
                payload["leaderboard"] = merged_rows
                payload["participantCount"] = len(merged_rows)
                payload["liveParticipantCount"] = len([row for row in merged_rows if row.get("status") != "Submitted"])
                payload["viewerRank"] = next((row["rank"] for row in merged_rows if str(row["userId"]) == str(user["user_id"])), payload.get("viewerRank"))
                payload["tcpEnabled"] = True
        return jsonify({"ok": True, **payload})
    finally:
        db.close()


@api.get("/quizzes/<int:quiz_id>/results/export")
def export_quiz_results(quiz_id):
    user, error = _require_user(role="admin")
    if error:
        return error

    db = SessionLocal()
    try:
        quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
        if not quiz:
            return jsonify({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}), 404
        if quiz.created_by != user["user_id"]:
            return jsonify({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}), 403

        response = _csv_response_for_quiz(quiz)
        is_private = quiz.is_private
    finally:
        db.close()

    if is_private:
        quiz_repository.delete_quiz(quiz_id)
    return response


@api.get("/results/me")
def my_results():
    user, error = _require_user(role="student")
    if error:
        return error

    db = SessionLocal()
    try:
        submissions = submission_repository.get_results_for_student(db, user["user_id"])
        return jsonify({"ok": True, "results": [_serialize_submission(submission) for submission in submissions]})
    finally:
        db.close()
