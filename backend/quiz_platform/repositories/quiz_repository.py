from database import quiz_repository as quiz_db


class QuizRepository:
    def create_quiz(self, title, category, created_by, is_private, password, duration, start_time=None):
        return quiz_db.create_quiz(
            {
                "title": title,
                "category": category,
                "created_by": created_by,
                "is_private": is_private,
                "password": password,
                "duration": duration,
                "start_time": start_time,
            }
        )

    def get_public_quizzes_with_relations(self, db):
        return quiz_db.get_public_quizzes_with_relations(db)

    def get_admin_quizzes_with_relations(self, db, admin_user_id):
        return quiz_db.get_admin_quizzes_with_relations(db, admin_user_id)

    def get_quiz_with_relations(self, db, quiz_id):
        return quiz_db.get_quiz_with_relations(db, quiz_id)

    def delete_quiz(self, quiz_id):
        return quiz_db.delete_quiz(quiz_id)
