import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from repositories.user_repository import UserRepository


user_repository = UserRepository()


_PBKDF2_ITERATIONS = 100_000
_TOKEN_TTL_SECONDS = 24 * 60 * 60
_TOKEN_SECRET = os.environ.get("QUIZ_PLATFORM_TOKEN_SECRET", "quiz-platform-dev-secret")


def _b64encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def _b64decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def _create_token(user):
    payload = {
        "user_id": user.user_id,
        "role": user.role,
        "exp": int(time.time()) + _TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _b64encode(payload_bytes)
    signature = hmac.new(_TOKEN_SECRET.encode("utf-8"), payload_part.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_part}.{_b64encode(signature)}"


def hash_password(password):
    if not password:
        raise ValueError("password is required")

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password, stored_hash):
    if not password or not stored_hash:
        return False

    try:
        algorithm, iterations, salt, expected_hash = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _b64decode(salt),
            int(iterations),
        )
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(_b64encode(calculated_hash), expected_hash)


def login_user(email, password):
    user = user_repository.get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        return {"ok": False, "error": "invalid-credentials"}

    return {
        "ok": True,
        "token": _create_token(user),
        "user": user.to_dict(),
    }


def register_user(name, email, password, role):
    normalized_name = (name or "").strip()
    normalized_email = (email or "").strip().lower()
    normalized_role = (role or "").strip().lower()

    if not normalized_name:
        return {"ok": False, "error": "name-required"}
    if not normalized_email:
        return {"ok": False, "error": "email-required"}
    if normalized_role not in {"admin", "student"}:
        return {"ok": False, "error": "invalid-role"}
    if user_repository.check_user_exists(normalized_email):
        return {"ok": False, "error": "email-already-registered"}

    try:
        user = user_repository.create_user(
            name=normalized_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role=normalized_role,
        )
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "token": _create_token(user),
        "user": user.to_dict(),
    }


def validate_token(token):
    if not token or "." not in token:
        return {"ok": False, "error": "invalid-token"}

    payload_part, signature_part = token.split(".", 1)
    expected_signature = hmac.new(
        _TOKEN_SECRET.encode("utf-8"),
        payload_part.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    try:
        provided_signature = _b64decode(signature_part)
    except Exception:
        return {"ok": False, "error": "invalid-token"}

    if not hmac.compare_digest(expected_signature, provided_signature):
        return {"ok": False, "error": "invalid-token"}

    try:
        payload = json.loads(_b64decode(payload_part).decode("utf-8"))
    except Exception:
        return {"ok": False, "error": "invalid-token"}

    if int(payload.get("exp", 0)) < int(time.time()):
        return {"ok": False, "error": "token-expired"}

    user = user_repository.get_user_by_id(payload.get("user_id"))
    if not user:
        return {"ok": False, "error": "user-not-found"}

    return {"ok": True, "user": user.to_dict(), "payload": payload}
