import os
import sys

from flask import Blueprint, jsonify, request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from auth.admin_auth import login_admin, register_admin
from auth.auth_service import validate_token
from auth.student_auth import login_student, register_student

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.post("/auth/register")
def auth_register():
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()
    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if role == "admin":
        result = register_admin(name, email, password)
    elif role == "student":
        result = register_student(name, email, password)
    else:
        result = {"ok": False, "error": "invalid-role"}

    return jsonify(result), 200 if result.get("ok") else 400


@api.post("/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    role = (payload.get("role") or "").strip().lower()
    email = payload.get("email")
    password = payload.get("password")

    if role == "admin":
        result = login_admin(email, password)
    elif role == "student":
        result = login_student(email, password)
    else:
        result = {"ok": False, "error": "invalid-role"}

    return jsonify(result), 200 if result.get("ok") else 400


@api.post("/auth/validate")
def auth_validate():
    payload = request.get_json(silent=True) or {}
    result = validate_token(payload.get("token"))
    return jsonify(result), 200 if result.get("ok") else 401


@api.get("/dashboard")
def dashboard():
    return jsonify(
        {
            "adminStats": [
                {"label": "Total Quizzes", "value": "24", "trend": "+12% from last month"},
                {"label": "Active Users", "value": "1,247", "trend": "+8% from last week"},
                {"label": "Completion Rate", "value": "87.5%", "trend": "-2% from last month"}
            ],
            "recentQuizzes": [
                {"name": "JavaScript Fundamentals", "type": "Public", "participants": 156, "status": "Active"},
                {"name": "React Components Quiz", "type": "Private", "participants": 23, "status": "Draft"},
                {"name": "Python Basics", "type": "Public", "participants": 89, "status": "Ended"}
            ]
        }
    )


@api.get("/public-quizzes")
def public_quizzes():
    return jsonify(
        [
            {"title": "Advanced JavaScript Patterns", "owner": "Admin", "plays": "20k", "category": "Programming"},
            {"title": "Network Security Fundamentals", "owner": "System Owner", "plays": "15k", "category": "Networking"},
            {"title": "World Geography Masterclass", "owner": "Admin", "plays": "10k", "category": "General Knowledge"}
        ]
    )


@api.post("/join-quiz")
def join_quiz():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "message": "Stub response for future Python integration",
            "received": payload,
            "nextRoute": "/student/waiting-room"
        }
    )


@api.post("/create-quiz")
def create_quiz():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "message": "Quiz payload accepted by Flask stub",
            "quizId": payload.get("quizId", "QUIZ-2025-001"),
            "payload": payload
        }
    )
