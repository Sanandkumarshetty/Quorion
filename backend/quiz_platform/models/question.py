from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.db_manager import Base


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"), nullable=False)
    question_text = Column(String(500), nullable=False)
    option_a = Column(String(200), nullable=False)
    option_b = Column(String(200), nullable=False)
    option_c = Column(String(200), nullable=False)
    option_d = Column(String(200), nullable=False)
    correct_answer = Column(String(1), nullable=False)  # 'A', 'B', 'C', or 'D'

    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "options": {
                "A": self.option_a,
                "B": self.option_b,
                "C": self.option_c,
                "D": self.option_d,
            },
            "correct_answer": self.correct_answer,
        }

    def __repr__(self):
        return f"<Question(question_id={self.question_id}, quiz_id={self.quiz_id})>"
