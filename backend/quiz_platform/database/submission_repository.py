from database.session import SessionLocal
from models.answer import Answer
from models.submission import Submission


def create_submission(student_id, quiz_id):
    db = SessionLocal()
    try:
        submission = Submission(student_id=student_id, quiz_id=quiz_id)
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_answer(submission_id, question_id, selected_option):
    db = SessionLocal()
    try:
        answer = (
            db.query(Answer)
            .filter(Answer.submission_id == submission_id, Answer.question_id == question_id)
            .first()
        )
        if answer:
            answer.selected_option = selected_option
        else:
            answer = Answer(
                submission_id=submission_id,
                question_id=question_id,
                selected_option=selected_option,
            )
            db.add(answer)

        db.commit()
        db.refresh(answer)
        return answer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_submission_by_id(submission_id):
    db = SessionLocal()
    try:
        return db.query(Submission).filter(Submission.submission_id == submission_id).first()
    finally:
        db.close()


def get_student_submission(student_id, quiz_id):
    db = SessionLocal()
    try:
        return (
            db.query(Submission)
            .filter(Submission.student_id == student_id, Submission.quiz_id == quiz_id)
            .order_by(Submission.submission_id.desc())
            .first()
        )
    finally:
        db.close()


def update_submission_score(submission_id, score):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.submission_id == submission_id).first()
        if not submission:
            return None

        submission.score = score
        db.commit()
        db.refresh(submission)
        return submission
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_submissions_by_quiz(quiz_id):
    db = SessionLocal()
    try:
        return (
            db.query(Submission)
            .filter(Submission.quiz_id == quiz_id)
            .order_by(Submission.score.desc(), Submission.completion_time.asc())
            .all()
        )
    finally:
        db.close()


def delete_submission(submission_id):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.submission_id == submission_id).first()
        if not submission:
            return False

        db.delete(submission)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
