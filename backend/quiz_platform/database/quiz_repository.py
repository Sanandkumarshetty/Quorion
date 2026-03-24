from datetime import datetime

from sqlalchemy.orm import joinedload

from database.session import SessionLocal
from models.question import Question
from models.quiz import Quiz
from models.submission import Submission


def _normalize_start_time(start_time):
    if start_time is None or isinstance(start_time, datetime):
        return start_time
    if isinstance(start_time, str):
        return datetime.fromisoformat(start_time)
    raise ValueError("invalid-start-time")


def create_quiz(quiz_data):
    db = SessionLocal()
    try:
        payload = dict(quiz_data or {})
        if "start_time" in payload:
            payload["start_time"] = _normalize_start_time(payload.get("start_time"))

        quiz = Quiz(**payload)
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_quiz_by_id(quiz_id):
    db = SessionLocal()
    try:
        return db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    finally:
        db.close()


def get_all_quizzes():
    db = SessionLocal()
    try:
        return db.query(Quiz).order_by(Quiz.start_time.asc(), Quiz.quiz_id.asc()).all()
    finally:
        db.close()


def get_public_quizzes():
    db = SessionLocal()
    try:
        return (
            db.query(Quiz)
            .filter(Quiz.is_private.is_(False))
            .order_by(Quiz.start_time.asc(), Quiz.quiz_id.asc())
            .all()
        )
    finally:
        db.close()


def get_private_quiz(quiz_id):
    db = SessionLocal()
    try:
        return db.query(Quiz).filter(Quiz.quiz_id == quiz_id, Quiz.is_private.is_(True)).first()
    finally:
        db.close()


def update_quiz(quiz_id, updated_data):
    db = SessionLocal()
    try:
        quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            return None

        for key, value in (updated_data or {}).items():
            if not hasattr(quiz, key):
                continue
            if key == "start_time":
                value = _normalize_start_time(value)
            setattr(quiz, key, value)

        db.commit()
        db.refresh(quiz)
        return quiz
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_quiz(quiz_id):
    db = SessionLocal()
    try:
        quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            return False

        db.delete(quiz)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def add_question(quiz_id, question_data):
    db = SessionLocal()
    try:
        quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            return None

        options = dict((question_data or {}).get("options") or {})
        question = Question(
            quiz_id=quiz_id,
            question_text=(question_data or {}).get("question_text"),
            option_a=options.get("A"),
            option_b=options.get("B"),
            option_c=options.get("C"),
            option_d=options.get("D"),
            correct_answer=(question_data or {}).get("correct_answer"),
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_questions_by_quiz(quiz_id):
    db = SessionLocal()
    try:
        return (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.question_id.asc())
            .all()
        )
    finally:
        db.close()


def get_quiz_with_relations(db, quiz_id):
    return (
        db.query(Quiz)
        .options(
            joinedload(Quiz.creator),
            joinedload(Quiz.questions),
            joinedload(Quiz.submissions).joinedload(Submission.student),
            joinedload(Quiz.submissions).joinedload(Submission.answers),
        )
        .filter(Quiz.quiz_id == quiz_id)
        .first()
    )


def get_public_quizzes_with_relations(db):
    return (
        db.query(Quiz)
        .options(joinedload(Quiz.creator), joinedload(Quiz.questions), joinedload(Quiz.submissions))
        .filter(Quiz.is_private.is_(False))
        .order_by(Quiz.start_time.asc(), Quiz.quiz_id.asc())
        .all()
    )


def get_admin_quizzes_with_relations(db, admin_user_id):
    return (
        db.query(Quiz)
        .options(joinedload(Quiz.creator), joinedload(Quiz.questions), joinedload(Quiz.submissions))
        .filter(Quiz.created_by == admin_user_id)
        .order_by(Quiz.start_time.desc(), Quiz.quiz_id.desc())
        .all()
    )


def delete_question(question_id):
    db = SessionLocal()
    try:
        question = db.query(Question).filter(Question.question_id == question_id).first()
        if not question:
            return False

        db.delete(question)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
