import os
import sys

from flask import Flask
from flask_cors import CORS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend", "quiz_platform"))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.db_manager import create_database

try:
    from .routes import api
except ImportError:
    from routes import api


def create_app():
    app = Flask(__name__)
    CORS(app)
    create_database()
    app.register_blueprint(api, url_prefix="/api")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
