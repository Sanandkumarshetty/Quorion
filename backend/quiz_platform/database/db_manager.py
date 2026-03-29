import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
DATABASE_PATH = os.path.join(PROJECT_ROOT, "quiz_platform.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()


def create_database():
    """Create database and tables"""
    # Import models so Base registers them before create_all
    from models.user import User
    from models.quiz import Quiz
    from models.question import Question
    from models.submission import Submission
    from models.answer import Answer
    Base.metadata.create_all(bind=engine)
