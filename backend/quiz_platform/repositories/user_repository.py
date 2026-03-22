from models.user import User
from database.db_manager import SessionLocal

class UserRepository:

    def create_user(self, name, email, password_hash, role):
        db = SessionLocal()
        user = User(name=name, email=email, password_hash=password_hash, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def get_user_by_email(self, email):
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        db.close()
        return user

    def get_user_by_id(self, user_id):
        db = SessionLocal()
        user = db.query(User).filter(User.user_id == user_id).first()
        db.close()
        return user