from database import submission_repository as submission_db
from repositories.answer_repository import AnswerRepository


class SubmissionRepository:
    def __init__(self):
        self.answer_repository = AnswerRepository()

    def create_submission(self, quiz_id, student_id, submitted_at=None):
        from database.session import SessionLocal

        db = SessionLocal()
        try:
            return submission_db.create_submission_record(db, quiz_id, student_id, submitted_at=submitted_at)
        finally:
            db.close()

    def get_active_submission(self, db, quiz_id, student_id):
        return submission_db.get_active_submission(db, quiz_id, student_id)

    def get_latest_submission(self, db, quiz_id, student_id):
        return submission_db.get_latest_submission(db, quiz_id, student_id)

    def get_completed_submission(self, db, quiz_id, student_id):
        return submission_db.get_completed_submission(db, quiz_id, student_id)

    def get_existing_submission(self, db, quiz_id, student_id):
        return submission_db.get_existing_submission(db, quiz_id, student_id)

    def save_answer(self, db, submission, question_id, selected_option):
        return self.answer_repository.save_answer(db, submission.submission_id, question_id, selected_option)

    def get_results_for_student(self, db, student_id):
        return submission_db.get_results_for_student(db, student_id)
