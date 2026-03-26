from utils.helpers import format_leaderboard


def update_leaderboard(session):
    with session["lock"]:
        rows = [
            {
                "student_id": student_id,
                "score": score,
                "completion_time": session.get("completion_time", {}).get(student_id, float("inf")),
            }
            for student_id, score in session.get("scores", {}).items()
        ]
        session["leaderboard"] = format_leaderboard(rows)
        return list(session["leaderboard"])


def get_leaderboard(session):
    with session["lock"]:
        leaderboard = session.get("leaderboard")
        if leaderboard:
            return list(leaderboard)
    return update_leaderboard(session)
