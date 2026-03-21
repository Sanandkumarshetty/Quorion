from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db_manager import Base


class Answer(Base):
    __tablename__ = "answers"

    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.submission_id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False)
    selected_option = Column(String(1), nullable=False)  # 'A', 'B', 'C', or 'D'

    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def to_dict(self):
        return {
            "answer_id": self.answer_id,
            "submission_id": self.submission_id,
            "question_id": self.question_id,
            "selected_option": self.selected_option,
        }

    def __repr__(self):
        return f"<Answer(answer_id={self.answer_id}, question_id={self.question_id}, selected={self.selected_option!r})>"
