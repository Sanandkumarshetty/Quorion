import json
import uuid


def generate_unique_id():
    return str(uuid.uuid4())


def parse_message(data):
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="ignore")

    if data is None:
        return {}

    data = str(data).strip()
    if not data:
        return {}

    try:
        message = json.loads(data)
    except json.JSONDecodeError:
        return {"action": "invalid", "payload": {"reason": "invalid-json"}}

    if not isinstance(message, dict):
        return {"action": "invalid", "payload": {"reason": "object-required"}}

    return message


def format_leaderboard(leaderboard_data):
    rows = []
    for index, entry in enumerate(leaderboard_data or [], start=1):
        if isinstance(entry, dict):
            row = dict(entry)
        else:
            student_id = getattr(entry, "student_id", None)
            score = getattr(entry, "score", 0)
            completion_time = getattr(entry, "completion_time", float("inf"))
            row = {
                "student_id": student_id,
                "score": score,
                "completion_time": completion_time,
            }

        row["score"] = float(row.get("score", 0))
        row["completion_time"] = float(row.get("completion_time", float("inf")))
        rows.append(row)

    rows.sort(key=lambda row: (-row["score"], row["completion_time"]))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    return rows


def create_response_message(type, payload):
    return json.dumps({"type": type, "payload": payload}) + "\n"
