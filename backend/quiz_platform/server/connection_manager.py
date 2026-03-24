import threading
from socket import SHUT_RDWR


_lock = threading.RLock()
_student_connections = {}
_admin_connections = {}
_socket_to_identity = {}


def _send_message(client_socket, message):
    data = message.encode("utf-8")
    total_sent = 0

    while total_sent < len(data):
        sent = client_socket.send(data[total_sent:])
        if sent == 0:
            raise OSError("socket connection broken")
        total_sent += sent


def _safe_send(client_socket, message):
    if not isinstance(message, str):
        message = str(message)
    try:
        _send_message(client_socket, message)
        return True
    except OSError:
        return False


def add_student_connection(student_id, client_socket):
    with _lock:
        _student_connections[student_id] = client_socket
        _socket_to_identity[client_socket] = ("student", student_id)


def add_admin_connection(admin_id, client_socket):
    with _lock:
        _admin_connections[admin_id] = client_socket
        _socket_to_identity[client_socket] = ("admin", admin_id)


def remove_connection(client_socket):
    with _lock:
        identity = _socket_to_identity.pop(client_socket, None)
        if identity:
            role, user_id = identity
            if role == "student":
                _student_connections.pop(user_id, None)
            elif role == "admin":
                _admin_connections.pop(user_id, None)

    try:
        client_socket.shutdown(SHUT_RDWR)
    except OSError:
        pass
    try:
        client_socket.close()
    except OSError:
        pass


def broadcast_to_students(message):
    with _lock:
        sockets = list(_student_connections.values())

    dead_sockets = []
    for student_socket in sockets:
        if not _safe_send(student_socket, message):
            dead_sockets.append(student_socket)

    for dead_socket in dead_sockets:
        remove_connection(dead_socket)


def broadcast_to_admins(message):
    with _lock:
        sockets = list(_admin_connections.values())

    dead_sockets = []
    for admin_socket in sockets:
        if not _safe_send(admin_socket, message):
            dead_sockets.append(admin_socket)

    for dead_socket in dead_sockets:
        remove_connection(dead_socket)
