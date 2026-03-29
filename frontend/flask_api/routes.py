import os
import sys

from flask import Blueprint, Response, jsonify, request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from .tcp_bridge import send_http_request_over_tcp
except ImportError:
    from tcp_bridge import send_http_request_over_tcp

api = Blueprint("api", __name__)


def _tcp_path():
    path = request.path or "/"
    return path[4:] if path.startswith("/api") else path


def _forward_request():
    tcp_response = send_http_request_over_tcp(
        request.method,
        _tcp_path(),
        request.get_json(silent=True) or {},
        {key: value for key, value in request.headers.items() if key in {"Authorization", "Content-Type"}},
    )
    status = int(tcp_response.get("status", 500) or 500)
    headers = dict(tcp_response.get("headers") or {})
    body_bytes = tcp_response.get("body_bytes")
    if isinstance(body_bytes, (bytes, bytearray)):
        return Response(bytes(body_bytes), status=status, headers=headers)

    body = tcp_response.get("body")
    response = jsonify(body if isinstance(body, dict) else {"ok": False, "error": "tcp-invalid-body"})
    response.status_code = status
    for key, value in headers.items():
        if key.lower() != "content-type":
            response.headers[key] = value
    return response


@api.get("/health")
def health():
    return _forward_request()


@api.post("/auth/register")
def auth_register():
    return _forward_request()


@api.post("/auth/login")
def auth_login():
    return _forward_request()


@api.post("/auth/validate")
def auth_validate():
    return _forward_request()


@api.get("/quizzes/public")
def public_quizzes():
    return _forward_request()


@api.get("/quizzes/admin")
def admin_quizzes():
    return _forward_request()


@api.put("/quizzes/<int:quiz_id>")
def update_quiz(quiz_id):
    return _forward_request()


@api.delete("/quizzes/<int:quiz_id>")
def remove_quiz(quiz_id):
    return _forward_request()


@api.post("/quizzes")
def create_quiz():
    return _forward_request()


@api.post("/quizzes/join")
def join_quiz():
    return _forward_request()


@api.get("/quizzes/<int:quiz_id>")
def quiz_details(quiz_id):
    return _forward_request()


@api.post("/quizzes/<int:quiz_id>/answers")
def save_quiz_answer(quiz_id):
    return _forward_request()


@api.post("/quizzes/<int:quiz_id>/submit")
def submit_quiz(quiz_id):
    return _forward_request()


@api.get("/quizzes/<int:quiz_id>/leaderboard")
def quiz_leaderboard(quiz_id):
    return _forward_request()


@api.get("/quizzes/<int:quiz_id>/results/export")
def export_quiz_results(quiz_id):
    return _forward_request()


@api.get("/results/me")
def my_results():
    return _forward_request()
