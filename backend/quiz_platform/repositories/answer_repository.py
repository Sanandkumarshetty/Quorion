from models.answer import Answer
from database.db_manager import SessionLocal

class AnswerRepository:

    def add_answer(self, submission_id, question_id, selected_option):
        db = SessionLocal()
        answer = Answer(
            submission_id=submission_id,
            question_id=question_id,
            selected_option=selected_option
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        db.close()
        return answer