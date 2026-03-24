from database.quiz_repository import (
    add_question as repository_add_question,
)
from database.session import SessionLocal
from models.question import Question


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


def update_question(question_id, updated_data):
    db = SessionLocal()
    try:
        question = db.query(Question).filter(Question.question_id == question_id).first()
        if not question:
            return None

        payload = dict(updated_data or {})
        if "question_text" in payload:
            normalized_text = str(payload["question_text"] or "").strip()
            if not normalized_text:
                raise ValueError("question-text-required")
            question.question_text = normalized_text

        if "options" in payload:
            normalized_options = _normalize_options(payload["options"])
            question.option_a = normalized_options["A"]
            question.option_b = normalized_options["B"]
            question.option_c = normalized_options["C"]
            question.option_d = normalized_options["D"]

        if "correct_answer" in payload:
            normalized_answer = str(payload["correct_answer"] or "").strip().upper()
            if normalized_answer not in {"A", "B", "C", "D"}:
                raise ValueError("correct-answer-must-be-A-B-C-or-D")
            question.correct_answer = normalized_answer

        db.commit()
        db.refresh(question)
        return question
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
