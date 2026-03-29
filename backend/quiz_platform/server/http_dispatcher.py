import csv
import io
import re
from datetime import datetime, timedelta

from auth.admin_auth import login_admin, register_admin
from auth.auth_service import validate_token
from auth.student_auth import login_student, register_student
from database.session import SessionLocal
from quiz_management.question_manager import add_question as add_managed_question
from quiz_management.quiz_creator import create_private_quiz, create_public_quiz
from quiz_runtime.evaluation import evaluate_answer
from repositories.question_repository import QuestionRepository
from repositories.quiz_repository import QuizRepository
from repositories.submission_repository import SubmissionRepository
from server import live_actions


quiz_repository = QuizRepository()
submission_repository = SubmissionRepository()
question_repository = QuestionRepository()


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

_QUIZ_ID_ROUTE = re.compile(r"^/quizzes/(?P<quiz_id>\d+)$")
_ANSWER_ROUTE = re.compile(r"^/quizzes/(?P<quiz_id>\d+)/answers$")
_SUBMIT_ROUTE = re.compile(r"^/quizzes/(?P<quiz_id>\d+)/submit$")
_LEADERBOARD_ROUTE = re.compile(r"^/quizzes/(?P<quiz_id>\d+)/leaderboard$")
_EXPORT_ROUTE = re.compile(r"^/quizzes/(?P<quiz_id>\d+)/results/export$")


def _message_for(error_code):
    return ERROR_MESSAGES.get(error_code, error_code or "Request failed")


def _json_response(body, status=200, headers=None):
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    return {"status": status, "body": body, "headers": response_headers}


def _binary_response(body, status=200, headers=None):
    return {"status": status, "body_bytes": body, "headers": headers or {}}


def _auth_response(result, success_status=200, failure_status=400):
    if result.get("ok"):
        return _json_response(result, status=success_status)
    return _json_response(
        {"ok": False, "error": result.get("error"), "message": _message_for(result.get("error"))},
        status=failure_status,
    )


def _extract_token(headers, payload):
    auth_header = (headers or {}).get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return (payload or {}).get("token")


def _require_user(headers, payload, role=None):
    result = validate_token(_extract_token(headers, payload))
    if not result.get("ok"):
        return None, _json_response(
            {"ok": False, "error": result.get("error"), "message": _message_for(result.get("error"))},
            status=401,
        )

    user = result.get("user")
    if role and user.get("role") != role:
        return None, _json_response({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}, status=403)
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
    return (quiz.start_time or _current_time()) <= _current_time()


def _submission_end_time(submission, quiz):
    started_at = submission.submitted_at or _current_time()
    return started_at + timedelta(seconds=int(quiz.duration or 0))


def _submission_has_ended(submission, quiz):
    return _submission_end_time(submission, quiz) <= _current_time()


def _compute_submission_score(submission, questions):
    answer_map = {answer.question_id: answer.selected_option for answer in submission.answers}
    score = 0.0
    for question in questions:
        selected = answer_map.get(question.question_id)
        score += evaluate_answer(question, selected).get("score", 0.0) if selected else 0.0
    return score


def _finalize_submission(submission, questions):
    if submission.completion_time is not None:
        return submission
    submitted_at = submission.submitted_at or _current_time()
    submission.score = _compute_submission_score(submission, questions)
    submission.completion_time = max((_current_time() - submitted_at).total_seconds(), 0.0)
    submission.submitted_at = _current_time()
    return submission


def _serialize_question(question, include_correct=False):
    payload = {
        "questionId": question.question_id,
        "text": question.question_text,
        "options": {"A": question.option_a, "B": question.option_b, "C": question.option_c, "D": question.option_d},
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
        end_at = _submission_end_time(submission, quiz).isoformat() if submission and submission.completion_time is None else None

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
        "submissionCount": len([item for item in getattr(quiz, "submissions", []) if item.completion_time is not None]),
        "participantCount": participant_count,
        "questionCount": len(getattr(quiz, "questions", [])),
    }
    if include_questions:
        payload["questions"] = [_serialize_question(question, include_correct=include_correct) for question in quiz.questions]
    return payload


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
                "options": {"A": question.option_a, "B": question.option_b, "C": question.option_c, "D": question.option_d},
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
        rows.append(
            {
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
            }
        )

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


def _csv_bytes_for_quiz(quiz):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Rank", "Student Name", "Student Email", "Score", "Total Questions", "Progress", "Status", "Submitted At"])
    leaderboard = _build_leaderboard(quiz, include_live_attempts=True).get("leaderboard", [])
    by_user = {submission.student_id: submission for submission in quiz.submissions}
    for row in leaderboard:
        submission = by_user.get(row["userId"])
        writer.writerow(
            [
                row["rank"],
                row["name"],
                submission.student.email if submission and submission.student else "",
                row["score"],
                row["totalQuestions"],
                row["completion"],
                row["status"],
                submission.submitted_at.isoformat() if submission and submission.submitted_at else "",
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _route_request(method, path):
    if method == "GET" and path == "/health":
        return ("health", {})
    if method == "POST" and path == "/auth/register":
        return ("auth_register", {})
    if method == "POST" and path == "/auth/login":
        return ("auth_login", {})
    if method == "POST" and path == "/auth/validate":
        return ("auth_validate", {})
    if method == "GET" and path == "/quizzes/public":
        return ("public_quizzes", {})
    if method == "GET" and path == "/quizzes/admin":
        return ("admin_quizzes", {})
    if method == "POST" and path == "/quizzes":
        return ("create_quiz", {})
    if method == "POST" and path == "/quizzes/join":
        return ("join_quiz", {})
    if method == "GET" and path == "/results/me":
        return ("my_results", {})

    for regex, route_name in (
        (_QUIZ_ID_ROUTE, "quiz_details"),
        (_ANSWER_ROUTE, "save_answer"),
        (_SUBMIT_ROUTE, "submit_quiz"),
        (_LEADERBOARD_ROUTE, "quiz_leaderboard"),
        (_EXPORT_ROUTE, "export_results"),
    ):
        match = regex.match(path)
        if match:
            params = {"quiz_id": int(match.group("quiz_id"))}
            if route_name == "quiz_details" and method == "PUT":
                return ("update_quiz", params)
            if route_name == "quiz_details" and method == "DELETE":
                return ("remove_quiz", params)
            if route_name == "quiz_details" and method == "GET":
                return ("quiz_details", params)
            if route_name == "save_answer" and method == "POST":
                return ("save_answer", params)
            if route_name == "submit_quiz" and method == "POST":
                return ("submit_quiz", params)
            if route_name == "quiz_leaderboard" and method == "GET":
                return ("quiz_leaderboard", params)
            if route_name == "export_results" and method == "GET":
                return ("export_results", params)

    return (None, {})


def dispatch_http_request(payload):
    method = (payload.get("method") or "GET").upper()
    path = payload.get("path") or "/"
    headers = payload.get("headers") or {}
    body = payload.get("body") or {}
    route_name, params = _route_request(method, path)
    if not route_name:
        return _json_response({"ok": False, "error": "not-found", "message": "Not Found"}, status=404)

    if route_name == "health":
        return _json_response({"status": "ok"})

    if route_name == "auth_register":
        role = (body.get("role") or "").strip().lower()
        if role == "admin":
            result = register_admin(body.get("name"), body.get("email"), body.get("password"))
        elif role == "student":
            result = register_student(body.get("name"), body.get("email"), body.get("password"))
        else:
            result = {"ok": False, "error": "invalid-role"}
        return _auth_response(result)

    if route_name == "auth_login":
        role = (body.get("role") or "").strip().lower()
        if role == "admin":
            result = login_admin(body.get("email"), body.get("password"))
        elif role == "student":
            result = login_student(body.get("email"), body.get("password"))
        else:
            result = {"ok": False, "error": "invalid-role"}
        return _auth_response(result)

    if route_name == "auth_validate":
        return _auth_response(validate_token(body.get("token")), failure_status=401)

    if route_name == "public_quizzes":
        db = SessionLocal()
        try:
            quizzes = quiz_repository.get_public_quizzes_with_relations(db)
            return _json_response({"ok": True, "quizzes": [_serialize_quiz(quiz, include_questions=False) for quiz in quizzes]})
        finally:
            db.close()

    if route_name == "admin_quizzes":
        user, error = _require_user(headers, body, role="admin")
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
            return _json_response({"ok": True, "stats": stats, "quizzes": [_serialize_quiz(quiz, include_questions=True, include_correct=True) for quiz in quizzes]})
        finally:
            db.close()

    if route_name == "create_quiz":
        user, error = _require_user(headers, body, role="admin")
        if error:
            return error
        questions = body.get("questions") or []
        quiz_type = body.get("quizType") or "private"
        duration_seconds = max(60, int(body.get("durationMinutes") or 30) * 60)
        start_time = _parse_start_time(body.get("startAt"))
        if quiz_type == "public":
            quiz = create_public_quiz(
                title=(body.get("title") or "Untitled Quiz").strip(),
                duration=duration_seconds,
                category=(body.get("category") or "General Knowledge").strip(),
                created_by=user["user_id"],
                start_time=start_time,
            )
        else:
            quiz = create_private_quiz(
                title=(body.get("title") or "Untitled Quiz").strip(),
                duration=duration_seconds,
                category=(body.get("category") or "General Knowledge").strip(),
                password=(body.get("password") or "").strip() or None,
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
            return _json_response({"ok": True, "quiz": _serialize_quiz(created_quiz, include_questions=True, include_correct=True)})
        finally:
            db.close()

    if route_name == "join_quiz":
        user, error = _require_user(headers, body)
        if error:
            return error
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, body.get("quizId"))
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            password = (body.get("password") or "").strip()
            if quiz.is_private and quiz.password != password:
                return _json_response({"ok": False, "error": "invalid-quiz-password", "message": _message_for("invalid-quiz-password")}, status=400)

            response = {
                "ok": True,
                "quiz": _serialize_quiz(quiz, include_questions=True, include_correct=user["role"] == "admin"),
                "requiresWaitingRoom": user["role"] == "student" and quiz.is_private and not _quiz_has_started(quiz),
            }
            live_actions.process_join_quiz(
                {
                    "student_id": f"admin-{user['user_id']}" if user.get("role") == "admin" else user["user_id"],
                    "quiz_id": quiz.quiz_id,
                    "student_name": user.get("name") or f"User {user['user_id']}",
                    "total_questions": len(getattr(quiz, "questions", []) or []),
                }
            )
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
                    return _json_response(response)
                response["submission"] = _serialize_submission(submission)
                response["canAttempt"] = submission.completion_time is None
            return _json_response(response)
        finally:
            db.close()

    if route_name == "quiz_details":
        user, error = _require_user(headers, body)
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if quiz.is_private and user["role"] != "admin":
                existing_submission = submission_repository.get_existing_submission(db, quiz_id, user["user_id"])
                if not existing_submission:
                    return _json_response({"ok": False, "error": "forbidden", "message": _message_for("private-quiz-password-required")}, status=403)

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
                    return _json_response(response)
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
            return _json_response(response)
        finally:
            db.close()

    if route_name == "update_quiz":
        user, error = _require_user(headers, body, role="admin")
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if quiz.created_by != user["user_id"]:
                return _json_response({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}, status=403)
            if quiz.is_private:
                return _json_response({"ok": False, "error": "forbidden", "message": "Only public quizzes can be modified from the dashboard."}, status=403)
            quiz.title = (body.get("title") or quiz.title).strip()
            quiz.category = (body.get("category") or quiz.category or "General Knowledge").strip()
            quiz.duration = max(60, int(body.get("durationMinutes") or int((quiz.duration or 1800) / 60)) * 60)
            quiz.start_time = _parse_start_time(body.get("startAt") or quiz.start_time)
            for question in list(quiz.questions):
                db.delete(question)
            db.flush()
            db.commit()
            for question in body.get("questions") or []:
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
            return _json_response({"ok": True, "quiz": _serialize_quiz(updated_quiz, include_questions=True, include_correct=True)})
        finally:
            db.close()

    if route_name == "remove_quiz":
        user, error = _require_user(headers, body, role="admin")
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if quiz.created_by != user["user_id"]:
                return _json_response({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}, status=403)
            if quiz.is_private:
                return _json_response({"ok": False, "error": "forbidden", "message": "Only public quizzes can be deleted from the dashboard."}, status=403)
        finally:
            db.close()
        quiz_repository.delete_quiz(quiz_id)
        return _json_response({"ok": True, "deleted": True, "quizId": quiz_id})

    if route_name == "save_answer":
        user, error = _require_user(headers, body, role="student")
        if error:
            return error
        quiz_id = params["quiz_id"]
        question_id = body.get("questionId")
        selected_option = str(body.get("selectedOption") or "").strip().upper()
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            question = next((item for item in quiz.questions if item.question_id == question_id), None)
            if not question:
                return _json_response({"ok": False, "error": "question-not-found", "message": _message_for("question-not-found")}, status=404)
            if quiz.is_private and not _quiz_has_started(quiz):
                return _json_response({"ok": False, "error": "quiz-not-started", "message": _message_for("quiz-not-started")}, status=409)
            submission = _get_or_create_active_submission(db, quiz.quiz_id, user["user_id"])
            if not quiz.is_private and _submission_has_ended(submission, quiz):
                _finalize_submission(submission, quiz.questions)
                db.commit()
                return _json_response({"ok": False, "error": "quiz-ended", "message": _message_for("quiz-ended")}, status=409)
            if submission.completion_time is not None:
                return _json_response({"ok": False, "error": "quiz-already-submitted", "message": _message_for("quiz-already-submitted")}, status=409)
            submission_repository.save_answer(db, submission, question_id, selected_option)
            db.commit()
            db.refresh(submission)
            submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
            submission.score = _compute_submission_score(submission, quiz.questions)
            db.commit()
            db.refresh(submission)
            live_response = live_actions.process_answer(
                {
                    "student_id": user["user_id"],
                    "student_name": user.get("name") or f"Student {user['user_id']}",
                    "quiz_id": quiz.quiz_id,
                    "question_id": question_id,
                    "selected_option": selected_option,
                    "score": int(round(float(submission.score or 0.0))),
                    "attempted_count": len(submission.answers),
                    "total_questions": len(quiz.questions),
                }
            )
            return _json_response({"ok": True, "submission": _serialize_submission(submission), "liveScore": int(round(float(submission.score or 0.0))), "answeredCount": len(submission.answers), "tcpSynced": bool(live_response.get("ok"))})
        finally:
            db.close()

    if route_name == "submit_quiz":
        user, error = _require_user(headers, body, role="student")
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if quiz.is_private and not _quiz_has_started(quiz):
                return _json_response({"ok": False, "error": "quiz-not-started", "message": _message_for("quiz-not-started")}, status=409)
            submission = submission_repository.get_active_submission(db, quiz_id, user["user_id"])
            if not submission:
                latest_submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
                if latest_submission and latest_submission.completion_time is not None:
                    return _json_response({"ok": False, "error": "quiz-already-submitted", "message": _message_for("quiz-already-submitted")}, status=409)
                return _json_response({"ok": False, "error": "submission-not-found", "message": _message_for("submission-not-found")}, status=404)
            if not quiz.is_private and _submission_has_ended(submission, quiz):
                _finalize_submission(submission, quiz.questions)
            else:
                submission.score = _compute_submission_score(submission, quiz.questions)
                submission.completion_time = max((_current_time() - submission.submitted_at).total_seconds(), 0.0) if submission.submitted_at else 0.0
                submission.submitted_at = _current_time()
            db.commit()
            db.refresh(submission)
            submission = submission_repository.get_latest_submission(db, quiz_id, user["user_id"])
            live_response = live_actions.process_submit(
                {
                    "student_id": user["user_id"],
                    "student_name": user.get("name") or f"Student {user['user_id']}",
                    "quiz_id": quiz.quiz_id,
                    "score": int(round(float(submission.score or 0.0))),
                    "completion_time": float(submission.completion_time or 0.0),
                    "attempted_count": len(submission.answers),
                    "total_questions": len(quiz.questions),
                }
            )
            return _json_response({"ok": True, "result": _serialize_submission(submission), "tcpSynced": bool(live_response.get("ok"))})
        finally:
            db.close()

    if route_name == "quiz_leaderboard":
        user, error = _require_user(headers, body)
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if not quiz.is_private:
                return _json_response({"ok": False, "error": "forbidden", "message": _message_for("leaderboard-not-available")}, status=403)
            if user["role"] == "student":
                completed_submission = submission_repository.get_completed_submission(db, quiz_id, user["user_id"])
                if not completed_submission:
                    return _json_response({"ok": False, "error": "forbidden", "message": "Students can open the leaderboard only after submitting the full quiz."}, status=403)
            include_live_attempts = user["role"] == "admin"
            response_payload = _build_leaderboard(quiz, viewer_user_id=user["user_id"], include_live_attempts=include_live_attempts)
            tcp_rows = live_actions.calculate_leaderboard(quiz_id)
            if include_live_attempts and tcp_rows:
                merged_rows = []
                database_rows = {str(row["userId"]): row for row in response_payload.get("leaderboard", [])}
                for row in tcp_rows:
                    row_user_id = str(row.get("student_id"))
                    if row_user_id.startswith("admin-"):
                        continue
                    merged_rows.append(
                        {
                            "rank": row.get("rank", 0),
                            "userId": row.get("student_id"),
                            "name": row.get("name") or database_rows.get(row_user_id, {}).get("name", f"Student {row_user_id}"),
                            "score": int(round(float(row.get("score", 0) or 0))),
                            "totalQuestions": int(row.get("total_questions", database_rows.get(row_user_id, {}).get("totalQuestions", len(quiz.questions))) or len(quiz.questions)),
                            "attemptedCount": int(row.get("attempted_count", database_rows.get(row_user_id, {}).get("attemptedCount", 0)) or 0),
                            "completion": row.get("completion") or database_rows.get(row_user_id, {}).get("completion", "Live"),
                            "status": "Current User" if str(row.get("student_id")) == str(user["user_id"]) else (row.get("status") or "Live"),
                        }
                    )
                if merged_rows:
                    response_payload["leaderboard"] = merged_rows
                    response_payload["participantCount"] = len(merged_rows)
                    response_payload["liveParticipantCount"] = len([row for row in merged_rows if row.get("status") != "Submitted"])
                    response_payload["viewerRank"] = next((row["rank"] for row in merged_rows if str(row["userId"]) == str(user["user_id"])), response_payload.get("viewerRank"))
                    response_payload["tcpEnabled"] = True
            return _json_response({"ok": True, **response_payload})
        finally:
            db.close()

    if route_name == "export_results":
        user, error = _require_user(headers, body, role="admin")
        if error:
            return error
        quiz_id = params["quiz_id"]
        db = SessionLocal()
        try:
            quiz = quiz_repository.get_quiz_with_relations(db, quiz_id)
            if not quiz:
                return _json_response({"ok": False, "error": "quiz-not-found", "message": _message_for("quiz-not-found")}, status=404)
            if quiz.created_by != user["user_id"]:
                return _json_response({"ok": False, "error": "forbidden", "message": _message_for("forbidden")}, status=403)
            csv_bytes = _csv_bytes_for_quiz(quiz)
            is_private = quiz.is_private
        finally:
            db.close()
        if is_private:
            quiz_repository.delete_quiz(quiz_id)
        return _binary_response(csv_bytes, headers={"Content-Type": "text/csv", "Content-Disposition": f'attachment; filename="quiz_{quiz_id}_results.csv"'})

    if route_name == "my_results":
        user, error = _require_user(headers, body, role="student")
        if error:
            return error
        db = SessionLocal()
        try:
            submissions = submission_repository.get_results_for_student(db, user["user_id"])
            return _json_response({"ok": True, "results": [_serialize_submission(submission) for submission in submissions]})
        finally:
            db.close()

    return _json_response({"ok": False, "error": "not-implemented"}, status=500)
