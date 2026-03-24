from models.answer import Answer


class AnswerRepository:
    def save_answer(self, db, submission_id, question_id, selected_option):
        answer = (
            db.query(Answer)
            .filter(Answer.submission_id == submission_id, Answer.question_id == question_id)
            .first()
        )
        if answer:
            answer.selected_option = selected_option
            return answer

        answer = Answer(
            submission_id=submission_id,
            question_id=question_id,
            selected_option=selected_option,
        )
        db.add(answer)
        return answer
