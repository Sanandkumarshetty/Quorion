import os
import sys

from flask import Flask
from flask_cors import CORS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.db_manager import create_database
from quiz_management.quiz_scheduler import get_upcoming_quizzes
from server.tcp_server import start_server as start_tcp_server

try:
    from .routes import api
except ImportError:
    from routes import api


def create_app():
    app = Flask(__name__)
    CORS(app)
    create_database()
    get_upcoming_quizzes()
    start_tcp_server("0.0.0.0", 12000)
    app.register_blueprint(api, url_prefix="/api")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
