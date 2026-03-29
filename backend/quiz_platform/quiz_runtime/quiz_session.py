import threading
import time

from database.quiz_repository import get_questions_by_quiz, get_quiz_by_id


def create_session(quiz_id):
    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        raise ValueError("quiz-not-found")

    questions = get_questions_by_quiz(quiz_id)
    return {
        "quiz_id": quiz_id,
        "quiz": quiz.to_dict(),
        "questions": [question.to_dict() for question in questions],
        "students": set(),
        "answers": {},
        "scores": {},
        "completion_time": {},
        "leaderboard": [],
        "created_at": time.time(),
        "ended_at": None,
        "is_active": True,
        "lock": threading.RLock(),
    }


def add_student_to_session(session, student_id):
    with session["lock"]:
        session["students"].add(student_id)
        session["answers"].setdefault(student_id, {})
        session["scores"].setdefault(student_id, 0.0)
        session["completion_time"].setdefault(student_id, float("inf"))
    return session


def record_answer(session, student_id, question_id, answer):
    with session["lock"]:
        session["answers"].setdefault(student_id, {})
        session["answers"][student_id][question_id] = answer
    return session["answers"][student_id]


def end_session(session):
    with session["lock"]:
        session["is_active"] = False
        session["ended_at"] = time.time()
    return session
