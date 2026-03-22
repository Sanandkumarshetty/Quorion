from database.quiz_repository import create_quiz, get_all_quizzes


def generate_quiz_id():
    quizzes = get_all_quizzes()
    if not quizzes:
        return 1
    return max(quiz.quiz_id for quiz in quizzes) + 1


def create_public_quiz(title, duration, category, created_by):
    validate_quiz_data(
        {
            "title": title,
            "duration": duration,
            "category": category,
            "created_by": created_by,
            "is_private": False,
        }
    )
    return create_quiz(
        {
            "title": str(title).strip(),
            "duration": int(duration),
            "category": str(category or "").strip() or None,
            "created_by": created_by,
            "is_private": False,
            "password": None,
        }
    )


def create_private_quiz(title, duration, category, password, created_by):
    validate_quiz_data(
        {
            "title": title,
            "duration": duration,
            "category": category,
            "password": password,
            "created_by": created_by,
            "is_private": True,
        }
    )
    return create_quiz(
        {
            "title": str(title).strip(),
            "duration": int(duration),
            "category": str(category or "").strip() or None,
            "created_by": created_by,
            "is_private": True,
            "password": str(password).strip(),
        }
    )


def validate_quiz_data(quiz_data):
    payload = dict(quiz_data or {})
    title = str(payload.get("title") or "").strip()
    category = str(payload.get("category") or "").strip()
    created_by = payload.get("created_by")
    is_private = bool(payload.get("is_private"))

    if not title:
        raise ValueError("title-required")
    if created_by is None:
        raise ValueError("created-by-required")
    if not category:
        raise ValueError("category-required")

    try:
        duration = int(payload.get("duration"))
    except (TypeError, ValueError):
        raise ValueError("duration-must-be-an-integer")

    if duration <= 0:
        raise ValueError("duration-must-be-positive")

    if is_private and not str(payload.get("password") or "").strip():
        raise ValueError("password-required-for-private-quiz")

    return True