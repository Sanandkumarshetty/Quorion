from auth.auth_service import login_user, register_user
from database.user_repository import get_user_by_id


def register_admin(name, email, password):
    return register_user(name, email, password, "admin")


def login_admin(email, password):
    result = login_user(email, password)
    if not result.get("ok"):
        return result
    if result["user"].get("role") != "admin":
        return {"ok": False, "error": "admin-access-required"}
    return result


def verify_admin(user_id):
    user = get_user_by_id(user_id)
    return bool(user and user.role == "admin")


def get_admin_profile(admin_id):
    user = get_user_by_id(admin_id)
    if not user or user.role != "admin":
        return {"ok": False, "error": "admin-not-found"}
    return {"ok": True, "admin": user.to_dict()}
