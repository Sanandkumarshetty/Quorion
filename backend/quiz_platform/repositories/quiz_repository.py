from models.quiz import Quiz
from database.db_manager import SessionLocal

class QuizRepository:

    def create_quiz(self, title, category, created_by, is_private, password, duration):
        db = SessionLocal()
        quiz = Quiz(
            title=title,
            category=category,
            created_by=created_by,
            is_private=is_private,
            password=password,
            duration=duration
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        db.close()
        return quiz

    def get_quiz_by_id(self, quiz_id):
        db = SessionLocal()
        quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
        db.close()
        return quiz

    def get_all_quizzes(self):
        db = SessionLocal()
        quizzes = db.query(Quiz).all()
        db.close()
        return quizzes