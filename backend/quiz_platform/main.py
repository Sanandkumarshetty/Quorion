import time

from database.db_manager import create_database
from server.tcp_server import start_server as tcp_start_server
from quiz_management.quiz_scheduler import get_upcoming_quizzes


def initialize_system():
    """Initialize database and required services"""
    create_database()


def start_server():
    """Start TCP quiz server"""
    tcp_start_server("0.0.0.0", 12000)


def load_scheduled_quizzes():
    """Load quizzes scheduled for execution"""
    return get_upcoming_quizzes()


def main():
    """Main application runner"""
    initialize_system()
    load_scheduled_quizzes()
    start_server()

    print("Quiz TCP server is ready to receive on port 12000")

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Server stopped")
            break


if __name__ == "__main__":
    main()
