from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db_manager import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    category = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    is_private = Column(Boolean, default=False)
    password = Column(String(100), nullable=True)
    duration = Column(Integer, nullable=False)  # seconds
    start_time = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="quizzes_created")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="quiz", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "quiz_id": self.quiz_id,
            "title": self.title,
            "category": self.category,
            "created_by": self.created_by,
            "is_private": self.is_private,
            "duration": self.duration,
            "start_time": str(self.start_time),
        }

    def __repr__(self):
        return f"<Quiz(quiz_id={self.quiz_id}, title={self.title!r}, is_private={self.is_private})>"
