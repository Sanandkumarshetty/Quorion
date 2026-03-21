from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite:///quiz_platform.db"

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


def get_connection():
    """Return a raw database connection from the engine"""
    return engine.connect()


def close_connection(connection):
    """Close database connection"""
    connection.close()


def commit_changes(connection):
    """Commit database transactions"""
    connection.commit()


def rollback_changes(connection):
    """Rollback failed transactions"""
    connection.rollback()
