import time

def evaluate_answer(question, selected_option):
    if not question:
        raise ValueError("question-required")

    normalized_option = str(selected_option or "").strip().upper()
    if normalized_option not in {"A", "B", "C", "D"}:
        raise ValueError("selected-option-must-be-A-B-C-or-D")

    if isinstance(question, dict):
        correct_answer = question.get("correct_answer")
        question_id = question.get("question_id")
    else:
        correct_answer = getattr(question, "correct_answer", None)
        question_id = getattr(question, "question_id", None)

    normalized_answer = str(correct_answer or "").strip().upper()
    is_correct = normalized_option == normalized_answer

    return {
        "question_id": question_id,
        "selected_option": normalized_option,
        "correct_answer": normalized_answer,
        "is_correct": is_correct,
        "score": 1.0 if is_correct else 0.0,
    }


def update_score(session, student_id, result):
    if result is None:
        raise ValueError("result-required")

    with session["lock"]:
        score_delta = result.get("score", result) if isinstance(result, dict) else result
        session["scores"].setdefault(student_id, 0.0)
        session["scores"][student_id] = float(session["scores"][student_id]) + float(score_delta)
        return session["scores"][student_id]


def calculate_final_score(session, student_id):
    with session["lock"]:
        answers = dict(session.get("answers", {}).get(student_id, {}))
        questions = list(session.get("questions", []))

    total_score = 0.0
    question_map = {
        question.get("question_id"): question
        for question in questions
        if isinstance(question, dict) and question.get("question_id") is not None
    }

    for question_id, selected_option in answers.items():
        question = question_map.get(question_id)
        if question is None:
            continue
        total_score += evaluate_answer(question, selected_option)["score"]

    with session["lock"]:
        session["scores"][student_id] = float(total_score)
        session.setdefault("completion_time", {})
        session["completion_time"].setdefault(
            student_id,
            max(time.time() - float(session.get("created_at", time.time())), 0.0),
        )
        return session["scores"][student_id]


def finalize_quiz_results(session):
    with session["lock"]:
        student_ids = list(session.get("students", set()) | set(session.get("answers", {}).keys()))

    results = []
    for student_id in student_ids:
        final_score = calculate_final_score(session, student_id)
        with session["lock"]:
            results.append(
                {
                    "student_id": student_id,
                    "score": final_score,
                    "completion_time": session.get("completion_time", {}).get(student_id, float("inf")),
                }
            )

    with session["lock"]:
        session["is_active"] = False
        session["ended_at"] = time.time()

    return sorted(
        results,
        key=lambda row: (-float(row.get("score", 0.0)), float(row.get("completion_time", float("inf")))),
    )
