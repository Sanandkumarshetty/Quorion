from database.session import SessionLocal
from models.user import User


def create_user(name, email, password_hash, role):
    db = SessionLocal()
    try:
        user = User(
            name=name,
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_user_by_email(email):
    db = SessionLocal()
    try:
        normalized_email = email.strip().lower()
        return db.query(User).filter(User.email == normalized_email).first()
    finally:
        db.close()


def get_user_by_id(user_id):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.user_id == user_id).first()
    finally:
        db.close()


def update_user(user_id, updated_data):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None

        for key, value in (updated_data or {}).items():
            if not hasattr(user, key):
                continue
            if key == "email" and value is not None:
                value = value.strip().lower()
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_user(user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_all_users():
    db = SessionLocal()
    try:
        return db.query(User).order_by(User.user_id.asc()).all()
    finally:
        db.close()


def check_user_exists(email):
    return get_user_by_email(email) is not None
