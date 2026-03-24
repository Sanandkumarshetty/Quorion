# Quorion

## Overview

Quorion is a quiz platform with a React frontend, a Flask API, a Python backend, SQLite persistence, and an internal TCP socket layer for quiz-session events.

The current application flow is:
- React + Vite for the UI
- Flask for browser-facing HTTP APIs under `/api`
- SQLAlchemy + SQLite for persistence
- TCP socket server for backend quiz session communication started together with the Flask app
- Backend repository and management layers for auth, quiz creation, question handling, submissions, and leaderboard/session logic

## Core Features

### Admin
- Create public and private quizzes
- Add multiple-choice questions
- Schedule private quizzes with a start time
- Join private quizzes as admin and monitor live progress
- View live leaderboard updates for private quizzes
- Modify and delete public quizzes
- Download quiz results
- Auto-delete a private quiz after exporting its results

### Student
- Register and log in
- Join private quizzes with quiz ID and password
- Enter public quizzes from the dashboard
- Wait in a waiting room before a scheduled private quiz starts
- Attempt quizzes with auto-save on answer selection
- View public quiz answer review after submission
- View private leaderboard only after full submission
- Reattempt public quizzes later
- Cannot reattempt a private quiz after submitting it

## Public vs Private Quiz Rules

### Private quiz
- Requires quiz ID and password
- If a student joins before the scheduled start time, they stay in the waiting room
- Admin sees live private-quiz rankings during the session
- Students can open the leaderboard only after full submission
- Students cannot reattempt a submitted private quiz
- Exporting private quiz results deletes that private quiz

### Public quiz
- No waiting room
- Students can enter directly
- No live leaderboard for students
- Students can review correct answers after submission
- Public quizzes can be attempted again later
- Admin can modify and delete public quizzes

## Architecture

### Frontend
- React
- React Router
- Vite

### Backend
- Flask API for browser requests
- Python repository and management layers
- Internal TCP socket server for quiz join, answer, submit, and leaderboard event syncing

### Database
- SQLite
- Active database file: `D:\Quorion\quiz_platform.db`

## Project Structure

```text
D:\Quorion
|-- backend\quiz_platform\
|   |-- auth\
|   |-- database\
|   |-- models\
|   |-- quiz_management\
|   |-- quiz_runtime\
|   |-- repositories\
|   |-- server\
|   `-- utils\
|-- frontend\flask_api\
|   |-- app.py
|   |-- routes.py
|   `-- tcp_bridge.py
|-- frontend\frontend_react\
|   |-- src\
|   |-- package.json
|   `-- vite.config.js
|-- quiz_platform.db
`-- README.md
```

## Run Commands

### 1. Backend

Run from the project root:

```powershell
.venv\Scripts\python frontend\flask_api\app.py
```

This starts:
- Flask API on `http://127.0.0.1:5000`
- TCP socket server on port `12000`

### 2. Frontend

Run from the project root:

```powershell
cd frontend\frontend_react
npm run dev
```

Typical local frontend URL:
- `http://localhost:5173`

For LAN access:

```powershell
cd frontend\frontend_react
npm run dev -- --host 0.0.0.0
```

## Setup

### Python dependencies

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend dependencies

```powershell
cd frontend\frontend_react
npm install
cd ..\..
```

## API Notes

- Flask registers routes under `/api`
- Opening `http://127.0.0.1:5000/` directly will show `Not Found` unless you add a root route
- The React frontend talks to Flask through the Vite dev proxy during development
- The backend then syncs quiz-session events through the TCP layer internally

## Important Implementation Notes

- Answer saving happens when a student selects an option
- Clicking the same selected option does not send another save request
- Public quiz sessions do not continuously poll while a student is idle
- Admin leaderboard refreshes periodically for live monitoring
- Student private leaderboard shows submitted participants only
- The app keeps browser behavior the same while internally using TCP for backend quiz-event communication

## Multi-Client Testing

To test with multiple devices on the same network:
- Start the backend first
- Start the frontend with `npm run dev -- --host 0.0.0.0`
- Open the frontend URL from each device
- Make sure all devices are on the same Wi-Fi
- If devices cannot connect, check Windows Firewall permissions for Python and Node

## Current Backend Layers In Use

- `auth/*` for registration, login, token validation
- `database/*` for SQLAlchemy-backed data access
- `repositories/*` as the active repository abstraction layer
- `quiz_management/*` for quiz and question management
- `quiz_runtime/*` for evaluation, session, and leaderboard support
- `server/*` for TCP socket handling
- `utils/*` for message formatting and timer utilities

## Database Entities

- Users
- Quizzes
- Questions
- Submissions
- Answers

## Suggested Future Improvements

- Replace polling-based live updates with WebSockets or SSE for the browser
- Add automated tests for quiz flow, TCP bridge behavior, and leaderboard rules
- Add environment-based config for host, port, and proxy target
- Add deployment-ready WSGI/ASGI configuration
- Add richer result export options beyond CSV

## License

This project is for academic and educational use.
