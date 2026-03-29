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
