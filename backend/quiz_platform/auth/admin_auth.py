from auth.auth_service import login_user, register_user


def register_admin(name, email, password):
    return register_user(name, email, password, "admin")


def login_admin(email, password):
    result = login_user(email, password)
    if not result.get("ok"):
        return result
    if result["user"].get("role") != "admin":
        return {"ok": False, "error": "admin-access-required"}
    return result
