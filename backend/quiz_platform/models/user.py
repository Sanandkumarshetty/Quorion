from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db_manager import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' or 'student'
    created_at = Column(DateTime, server_default=func.now())

    quizzes_created = relationship("Quiz", back_populates="creator")
    submissions = relationship("Submission", back_populates="student")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": str(self.created_at),
        }

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email!r}, role={self.role!r})>"
