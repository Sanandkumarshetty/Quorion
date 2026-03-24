from database import quiz_repository as quiz_db


class QuestionRepository:
    def add_question(self, quiz_id, text, a, b, c, d, correct):
        return quiz_db.add_question(
            quiz_id,
            {
                "question_text": text,
                "options": {"A": a, "B": b, "C": c, "D": d},
                "correct_answer": correct,
            },
        )

    def get_questions_by_quiz(self, quiz_id):
        return quiz_db.get_questions_by_quiz(quiz_id)
