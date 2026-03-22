from datetime import datetime
from threading import RLock

from database.quiz_repository import get_all_quizzes, get_quiz_by_id, update_quiz
from quiz_runtime.quiz_session import create_session


_active_sessions = {}
_scheduler_lock = RLock()


def _normalize_start_time(start_time):
    if isinstance(start_time, datetime):
        return start_time
    if isinstance(start_time, str):
        return datetime.fromisoformat(start_time)
    raise ValueError("invalid-start-time")


def schedule_quiz(quiz_id, start_time):
    normalized_start_time = _normalize_start_time(start_time)
    quiz = update_quiz(quiz_id, {"start_time": normalized_start_time})
    if not quiz:
        raise ValueError("quiz-not-found")
    return quiz


def check_quiz_start():
    now = datetime.now()
    started_sessions = []

    for quiz in get_all_quizzes():
        if quiz.start_time is None or quiz.start_time > now:
            continue

        with _scheduler_lock:
            if quiz.quiz_id in _active_sessions:
                continue

        started_sessions.append(start_quiz_session(quiz.quiz_id))

    return started_sessions


def get_upcoming_quizzes():
    now = datetime.now()
    return [quiz for quiz in get_all_quizzes() if quiz.start_time is not None and quiz.start_time > now]


def start_quiz_session(quiz_id):
    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        raise ValueError("quiz-not-found")

    with _scheduler_lock:
        session = _active_sessions.get(quiz_id)
        if session is not None:
            return session

        session = create_session(quiz_id)
        _active_sessions[quiz_id] = session
        return session
