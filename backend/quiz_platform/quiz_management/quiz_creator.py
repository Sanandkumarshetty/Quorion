from database.quiz_repository import create_quiz


def create_public_quiz(title, duration, category, created_by, start_time=None):
    normalized = validate_quiz_data(
        {
            "title": title,
            "duration": duration,
            "category": category,
            "created_by": created_by,
            "is_private": False,
            "start_time": start_time,
        }
    )
    return create_quiz(normalized)


def create_private_quiz(title, duration, category, password, created_by, start_time=None):
    normalized = validate_quiz_data(
        {
            "title": title,
            "duration": duration,
            "category": category,
            "password": password,
            "created_by": created_by,
            "is_private": True,
            "start_time": start_time,
        }
    )
    return create_quiz(normalized)


def validate_quiz_data(quiz_data):
    payload = dict(quiz_data or {})

    title = str(payload.get("title") or "").strip()
    if not title:
        raise ValueError("title-required")

    created_by = payload.get("created_by")
    if created_by is None:
        raise ValueError("created-by-required")

    try:
        duration = int(payload.get("duration"))
    except (TypeError, ValueError):
        raise ValueError("duration-must-be-an-integer") from None

    if duration <= 0:
        raise ValueError("duration-must-be-greater-than-zero")

    is_private = bool(payload.get("is_private"))
    password = str(payload.get("password") or "").strip()
    if is_private and not password:
        raise ValueError("password-required-for-private-quiz")

    category = payload.get("category")
    if category is not None and not str(category).strip():
        raise ValueError("category-cannot-be-empty")

    return {
        "title": title,
        "duration": duration,
        "category": str(category).strip() if category is not None else None,
        "created_by": created_by,
        "is_private": is_private,
        "password": password or None,
        "start_time": payload.get("start_time"),
    }
