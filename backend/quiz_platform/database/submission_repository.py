from datetime import datetime

from sqlalchemy.orm import joinedload

from models.answer import Answer
from models.submission import Submission
from models.quiz import Quiz


def get_latest_submission(db, quiz_id, student_id):
    return (
        db.query(Submission)
        .options(joinedload(Submission.answers), joinedload(Submission.quiz).joinedload(Quiz.questions))
        .filter(Submission.quiz_id == quiz_id, Submission.student_id == student_id)
        .order_by(Submission.submission_id.desc())
        .first()
    )


def get_active_submission(db, quiz_id, student_id):
    return (
        db.query(Submission)
        .options(joinedload(Submission.answers), joinedload(Submission.quiz).joinedload(Quiz.questions))
        .filter(Submission.quiz_id == quiz_id, Submission.student_id == student_id, Submission.completion_time.is_(None))
        .order_by(Submission.submission_id.desc())
        .first()
    )


def get_completed_submission(db, quiz_id, student_id):
    return (
        db.query(Submission)
        .filter(Submission.quiz_id == quiz_id, Submission.student_id == student_id, Submission.completion_time.is_not(None))
        .first()
    )


def get_existing_submission(db, quiz_id, student_id):
    return (
        db.query(Submission)
        .filter(Submission.quiz_id == quiz_id, Submission.student_id == student_id)
        .first()
    )


def create_submission_record(db, quiz_id, student_id, submitted_at=None):
    submission = Submission(
        quiz_id=quiz_id,
        student_id=student_id,
        submitted_at=submitted_at or datetime.now(),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return get_latest_submission(db, quiz_id, student_id)


def save_submission_answer(db, submission, question_id, selected_option):
    existing_answer = next((answer for answer in submission.answers if answer.question_id == question_id), None)
    if existing_answer:
        existing_answer.selected_option = selected_option
        return existing_answer

    answer = Answer(submission_id=submission.submission_id, question_id=question_id, selected_option=selected_option)
    db.add(answer)
    return answer


def get_results_for_student(db, student_id):
    return (
        db.query(Submission)
        .options(joinedload(Submission.quiz).joinedload(Quiz.questions), joinedload(Submission.answers))
        .filter(Submission.student_id == student_id, Submission.completion_time.is_not(None))
        .order_by(Submission.submitted_at.desc(), Submission.submission_id.desc())
        .all()
    )
