from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db_manager import Base


class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    score = Column(Float, default=0.0)
    completion_time = Column(Float, nullable=True)  # seconds taken to complete
    submitted_at = Column(DateTime, server_default=func.now())

    student = relationship("User", back_populates="submissions")
    quiz = relationship("Quiz", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "submission_id": self.submission_id,
            "quiz_id": self.quiz_id,
            "student_id": self.student_id,
            "score": self.score,
            "completion_time": self.completion_time,
            "submitted_at": str(self.submitted_at),
        }

    def __repr__(self):
        return f"<Submission(submission_id={self.submission_id}, student_id={self.student_id}, score={self.score})>"
