from server import live_actions
from server.http_dispatcher import dispatch_http_request
from utils.binary_protocol import recv_framed_message, send_framed_message

def _send(client_socket, message_type, payload):
    send_framed_message(client_socket, {"type": message_type, "payload": payload})


def handle_client(client_socket):
    try:
        while True:
            message = recv_framed_message(client_socket)
            if message is None:
                break

            action = message.get("action")
            message["_client_socket"] = client_socket

            if action == "login":
                payload = live_actions.process_live_login(message.get("payload", {}), client_socket)
            elif action == "join_quiz":
                payload = live_actions.process_join_quiz(message.get("payload", {}))
            elif action == "answer":
                payload = live_actions.process_answer(message.get("payload", {}))
            elif action == "submit":
                payload = live_actions.process_submit(message.get("payload", {}))
            elif action == "leaderboard":
                quiz_id = message.get("payload", {}).get("quiz_id")
                payload = {"ok": True, "leaderboard": live_actions.calculate_leaderboard(quiz_id)}
            elif action == "http_request":
                payload = dispatch_http_request(message.get("payload", {}))
            else:
                payload = {"ok": False, "error": f"unknown-action:{action}"}

            _send(client_socket, "response", payload)
    except (OSError, ValueError, TypeError):
        pass
    finally:
        disconnect_client(client_socket)


def disconnect_client(client_socket):
    live_actions.disconnect_client(client_socket)
