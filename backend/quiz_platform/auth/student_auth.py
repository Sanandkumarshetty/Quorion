from auth.auth_service import login_user, register_user


def register_student(name, email, password):
    return register_user(name, email, password, "student")


def login_student(email, password):
    result = login_user(email, password)
    if not result.get("ok"):
        return result
    if result["user"].get("role") != "student":
        return {"ok": False, "error": "student-access-required"}
    return result
