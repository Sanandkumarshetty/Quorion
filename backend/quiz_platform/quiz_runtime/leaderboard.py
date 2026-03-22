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


def generate_leaderboard(session):
    return update_leaderboard(session)


def get_leaderboard(session):
    with session["lock"]:
        leaderboard = session.get("leaderboard")
        if leaderboard:
            return list(leaderboard)
    return update_leaderboard(session)


def send_admin_leaderboard(session):
    return {
        "event": "leaderboard_update",
        "quiz_id": session.get("quiz_id"),
        "rows": get_leaderboard(session),
        "target": "admin",
    }


def broadcast_final_leaderboard(session):
    with session["lock"]:
        session["is_active"] = False
    return {
        "event": "final_leaderboard",
        "quiz_id": session.get("quiz_id"),
        "rows": update_leaderboard(session),
        "target": "all",
    }
