import os
import socket
import ssl

from utils.binary_protocol import recv_framed_message, send_framed_message


TCP_HOST = os.environ.get("QUIZ_TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.environ.get("QUIZ_TCP_PORT", "12000"))
SOCKET_TIMEOUT_SECONDS = float(os.environ.get("QUIZ_TCP_TIMEOUT", "2.0"))
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))
DEFAULT_CA_CERT_PATH = os.path.join(BACKEND_DIR, "certs", "tcp_server_cert.pem")


def _create_tls_context():
    context = ssl.create_default_context(cafile=os.environ.get("QUIZ_TCP_TLS_CA_CERT", DEFAULT_CA_CERT_PATH))
    context.check_hostname = False
    return context


def send_tcp_request(action, payload):
    tls_context = _create_tls_context()

    with socket.create_connection((TCP_HOST, TCP_PORT), timeout=SOCKET_TIMEOUT_SECONDS) as raw_socket:
        raw_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        try:
            with tls_context.wrap_socket(raw_socket, server_hostname=TCP_HOST) as client_socket:
                client_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
                send_framed_message(client_socket, {"action": action, "payload": payload})
                response = recv_framed_message(client_socket)
        except (OSError, ssl.SSLError, ValueError, TypeError):
            response = None

    if not isinstance(response, dict):
        return {"ok": False, "error": "tcp-invalid-response"}

    if response.get("type") != "response":
        return {"ok": False, "error": "tcp-unexpected-message"}

    payload = response.get("payload")
    return payload if isinstance(payload, dict) else {"ok": False, "error": "tcp-invalid-payload"}


def send_http_request_over_tcp(method, path, body=None, headers=None):
    response = send_tcp_request(
        "http_request",
        {
            "method": method,
            "path": path,
            "body": body or {},
            "headers": headers or {},
        },
    )
    if not isinstance(response, dict):
        return {"status": 500, "body": {"ok": False, "error": "tcp-invalid-response"}}
    return response
