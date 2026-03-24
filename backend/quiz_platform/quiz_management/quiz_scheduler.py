from datetime import datetime

from database.quiz_repository import get_all_quizzes


def get_upcoming_quizzes():
    now = datetime.now()
    return [quiz for quiz in get_all_quizzes() if quiz.start_time is not None and quiz.start_time > now]
