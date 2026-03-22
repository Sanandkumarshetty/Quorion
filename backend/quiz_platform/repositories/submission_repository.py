from models.submission import Submission
from database.db_manager import SessionLocal

class SubmissionRepository:

    def create_submission(self, quiz_id, student_id):
        db = SessionLocal()
        submission = Submission(quiz_id=quiz_id, student_id=student_id)
        db.add(submission)
        db.commit()
        db.refresh(submission)
        db.close()
        return submission

    def get_submission(self, submission_id):
        db = SessionLocal()
        submission = db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()
        db.close()
        return submission