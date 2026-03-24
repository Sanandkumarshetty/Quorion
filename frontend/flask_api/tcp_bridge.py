import json
import os
import socket


TCP_HOST = os.environ.get("QUIZ_TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.environ.get("QUIZ_TCP_PORT", "12000"))
SOCKET_TIMEOUT_SECONDS = float(os.environ.get("QUIZ_TCP_TIMEOUT", "2.0"))


def send_tcp_request(action, payload):
    message = json.dumps({"action": action, "payload": payload}) + "\n"

    with socket.create_connection((TCP_HOST, TCP_PORT), timeout=SOCKET_TIMEOUT_SECONDS) as client_socket:
        client_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        client_socket.sendall(message.encode("utf-8"))

        buffer = ""
        while "\n" not in buffer:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="ignore")

    if not buffer.strip():
        return {"ok": False, "error": "tcp-no-response"}

    line = buffer.split("\n", 1)[0].strip()
    try:
        response = json.loads(line)
    except json.JSONDecodeError:
        return {"ok": False, "error": "tcp-invalid-response"}

    if response.get("type") != "response":
        return {"ok": False, "error": "tcp-unexpected-message"}

    payload = response.get("payload")
    return payload if isinstance(payload, dict) else {"ok": False, "error": "tcp-invalid-payload"}
