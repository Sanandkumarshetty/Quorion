from database import user_repository as user_db


class UserRepository:
    def create_user(self, name, email, password_hash, role):
        return user_db.create_user(name, email, password_hash, role)

    def get_user_by_email(self, email):
        return user_db.get_user_by_email(email)

    def get_user_by_id(self, user_id):
        return user_db.get_user_by_id(user_id)

    def check_user_exists(self, email):
        return user_db.check_user_exists(email)
