from auth.auth_service import login_user, register_user
from database.session import SessionLocal
from database.user_repository import get_user_by_id
from models.quiz import Quiz


def _get_quiz(quiz_id):
    db = SessionLocal()
    try:
        return db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    finally:
        db.close()


def register_student(name, email, password):
    return register_user(name, email, password, "student")


def login_student(email, password):
    result = login_user(email, password)
    if not result.get("ok"):
        return result
    if result["user"].get("role") != "student":
        return {"ok": False, "error": "student-access-required"}
    return result


def join_public_quiz(student_id, quiz_id):
    student = get_user_by_id(student_id)
    if not student or student.role != "student":
        return {"ok": False, "error": "student-not-found"}

    quiz = _get_quiz(quiz_id)
    if not quiz:
        return {"ok": False, "error": "quiz-not-found"}
    if quiz.is_private:
        return {"ok": False, "error": "private-quiz-password-required"}

    return {"ok": True, "quiz": quiz.to_dict(), "student": student.to_dict()}


def join_private_quiz(student_id, quiz_id, password):
    student = get_user_by_id(student_id)
    if not student or student.role != "student":
        return {"ok": False, "error": "student-not-found"}

    quiz = _get_quiz(quiz_id)
    if not quiz:
        return {"ok": False, "error": "quiz-not-found"}
    if not quiz.is_private:
        return {"ok": False, "error": "quiz-is-public"}
    if quiz.password != password:
        return {"ok": False, "error": "invalid-quiz-password"}

    return {"ok": True, "quiz": quiz.to_dict(), "student": student.to_dict()}


def get_student_profile(student_id):
    user = get_user_by_id(student_id)
    if not user or user.role != "student":
        return {"ok": False, "error": "student-not-found"}
    return {"ok": True, "student": user.to_dict()}
