# Quorion

## Overview

Quorion is a quiz platform with a React frontend, a thin Flask HTTP gateway, a TLS-secured TCP application server, and SQLite persistence.

The current application flow is:
- React + Vite for the UI
- Flask as a browser-facing HTTP gateway under `/api`
- TLS-secured TCP socket server as the main backend processing layer
- SQLAlchemy + SQLite for persistence
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
- Flask gateway for browser HTTP requests
- TLS-secured TCP socket server for auth, quiz, submission, and leaderboard processing
- Python repository and management layers behind the TCP server

### Database
- SQLite
- Active database file: `D:\Quorion\quiz_platform.db`

## Project Structure

```text
D:\Quorion
|-- backend\quiz_platform\
|   |-- auth\
|   |-- certs\
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
- Flask gateway on `http://127.0.0.1:5000`
- TLS-secured TCP application server on port `12000`

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

- Flask registers routes under `/api` and forwards them to the TCP server
- Opening `http://127.0.0.1:5000/` directly will show `Not Found` unless you add a root route
- The React frontend talks to Flask through the Vite dev proxy during development
- Flask forwards browser requests to the TCP server as framed binary messages over TLS
- The TCP server performs the business logic and database work, then sends the result back to Flask

## Important Implementation Notes

- Answer saving happens when a student selects an option
- Clicking the same selected option does not send another save request
- Public quiz sessions do not continuously poll while a student is idle
- Admin leaderboard refreshes periodically for live monitoring
- Student private leaderboard shows submitted participants only
- Browser requests still use HTTP, but backend processing now happens through a TLS-secured TCP server
- Internal TCP communication uses a custom framed binary protocol with explicit payload lengths

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
- `server/*` for the TLS TCP server, live session handling, and HTTP request dispatching
- `utils/*` for binary framing, TLS-adjacent socket helpers, and timer utilities

## Request Flow

- Browser sends an HTTP request to Flask under `/api`
- Flask forwards method, path, headers, and body to the TCP server
- The TCP server receives a framed binary message over TLS
- The TCP server executes auth, quiz, submission, or leaderboard logic
- SQLAlchemy reads or updates SQLite as needed
- The TCP server sends a response back to Flask
- Flask returns the final HTTP response to the browser

## Security

- Internal Flask-to-TCP communication is protected with SSL/TLS using Python's `ssl` module
- Development certificate files are stored in `backend\quiz_platform\certs\`
- The TCP server loads the certificate and private key before accepting secure connections

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
