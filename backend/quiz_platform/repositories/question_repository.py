from models.question import Question
from database.session import SessionLocal

class QuestionRepository:

    def add_question(self, quiz_id, text, a, b, c, d, correct):
        db = SessionLocal()
        question = Question(
            quiz_id=quiz_id,
            question_text=text,
            option_a=a,
            option_b=b,
            option_c=c,
            option_d=d,
            correct_answer=correct
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        db.close()
        return question

    def get_questions_by_quiz(self, quiz_id):
        db = SessionLocal()
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        db.close()
        return questions
