import os
import socket

from utils.binary_protocol import recv_framed_message, send_framed_message


TCP_HOST = os.environ.get("QUIZ_TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.environ.get("QUIZ_TCP_PORT", "12000"))
SOCKET_TIMEOUT_SECONDS = float(os.environ.get("QUIZ_TCP_TIMEOUT", "2.0"))


def send_tcp_request(action, payload):
    with socket.create_connection((TCP_HOST, TCP_PORT), timeout=SOCKET_TIMEOUT_SECONDS) as client_socket:
        client_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        try:
            send_framed_message(client_socket, {"action": action, "payload": payload})
            response = recv_framed_message(client_socket)
        except (OSError, ValueError, TypeError):
            response = None

    if not isinstance(response, dict):
        return {"ok": False, "error": "tcp-invalid-response"}

    if response.get("type") != "response":
        return {"ok": False, "error": "tcp-unexpected-message"}

    payload = response.get("payload")
    return payload if isinstance(payload, dict) else {"ok": False, "error": "tcp-invalid-payload"}
