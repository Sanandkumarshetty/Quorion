from database.quiz_repository import (
    add_question as repository_add_question,
)


def _normalize_options(options):
    normalized_options = dict(options or {})
    expected_keys = {"A", "B", "C", "D"}
    if set(normalized_options.keys()) != expected_keys:
        raise ValueError("options-must-include-A-B-C-D")

    for key, value in normalized_options.items():
        if not str(value or "").strip():
            raise ValueError(f"option-{key.lower()}-required")
    return {key: str(value).strip() for key, value in normalized_options.items()}


def add_question(quiz_id, question_text, options, correct_answer):
    normalized_text = str(question_text or "").strip()
    normalized_answer = str(correct_answer or "").strip().upper()
    normalized_options = _normalize_options(options)

    if not normalized_text:
        raise ValueError("question-text-required")
    if normalized_answer not in {"A", "B", "C", "D"}:
        raise ValueError("correct-answer-must-be-A-B-C-or-D")

    question = repository_add_question(
        quiz_id,
        {
            "question_text": normalized_text,
            "options": normalized_options,
            "correct_answer": normalized_answer,
        },
    )
    if question is None:
        raise ValueError("quiz-not-found")
    return question
