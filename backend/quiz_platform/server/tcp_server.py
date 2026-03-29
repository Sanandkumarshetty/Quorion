import os
import ssl
import threading
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket, timeout

from server.client_handler import handle_client


_server_socket = None
_is_running = False
_accept_thread = None
_lock = threading.RLock()
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CERT_PATH = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "certs", "tcp_server_cert.pem"))
_DEFAULT_KEY_PATH = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "certs", "tcp_server_key.pem"))


def _create_tls_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=os.environ.get("QUIZ_TCP_TLS_CERT", _DEFAULT_CERT_PATH),
        keyfile=os.environ.get("QUIZ_TCP_TLS_KEY", _DEFAULT_KEY_PATH),
    )
    return context


def start_server(host, port):
    global _server_socket, _is_running, _accept_thread

    with _lock:
        if _is_running:
            return

        _server_socket = socket(AF_INET, SOCK_STREAM)
        _server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        _server_socket.bind((host, port))
        _server_socket.listen(100)
        _server_socket.settimeout(1.0)
        _is_running = True
        tls_context = _create_tls_context()

        _accept_thread = threading.Thread(
            target=accept_connections,
            args=(_server_socket, tls_context),
            daemon=True,
        )
        _accept_thread.start()


def accept_connections(server_socket, tls_context):
    while _is_running:
        try:
            client_socket, _client_address = server_socket.accept()
        except timeout:
            continue
        except OSError:
            break

        try:
            secure_socket = tls_context.wrap_socket(client_socket, server_side=True)
        except ssl.SSLError:
            client_socket.close()
            continue

        worker = threading.Thread(target=handle_client, args=(secure_socket,), daemon=True)
        worker.start()


def stop_server():
    global _is_running, _server_socket, _accept_thread

    with _lock:
        _is_running = False
        if _server_socket is not None:
            try:
                _server_socket.close()
            except OSError:
                pass
            _server_socket = None

        accept_thread = _accept_thread
        _accept_thread = None

    if accept_thread is not None and accept_thread.is_alive():
        accept_thread.join(timeout=2)
