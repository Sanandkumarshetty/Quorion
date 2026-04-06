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

## Setup

### Python dependencies

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
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
- Browser-to-Flask traffic is plain HTTP in local development unless you place Flask behind HTTPS separately
- Passwords are stored using PBKDF2-SHA256 hashing
- Login issues a signed token that is used as a Bearer token for protected routes

## Startup Behavior

- Starting `frontend\flask_api\app.py` also creates database tables if they do not exist yet
- The same startup path also launches the internal TCP server automatically
- Flask runs on `0.0.0.0:5000` in debug mode when started directly
- The TCP server listens on `0.0.0.0:12000`

## Environment Variables

- `QUIZ_TCP_HOST`: TCP target host used by Flask bridge, default `127.0.0.1`
- `QUIZ_TCP_PORT`: TCP target port used by Flask bridge, default `12000`
- `QUIZ_TCP_TIMEOUT`: TCP socket timeout in seconds, default `2.0`
- `QUIZ_TCP_TLS_CA_CERT`: CA/cert path used by the Flask bridge to trust the TCP server certificate
- `QUIZ_TCP_TLS_CERT`: certificate path loaded by the TCP server
- `QUIZ_TCP_TLS_KEY`: private key path loaded by the TCP server
- `QUIZ_PLATFORM_TOKEN_SECRET`: secret used to sign auth tokens
- `VITE_API_PROXY_TARGET`: Vite proxy target for `/api`, default `http://127.0.0.1:5000`

## Authentication Notes

- Supported roles are `admin` and `student`
- Auth session data is stored in browser local storage by the frontend
- Protected frontend pages require a valid role-based session
- Token validation is handled by the backend before protected quiz/admin actions
- Token TTL is currently 24 hours

## API Surface

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/validate`
- `GET /api/quizzes/public`
- `GET /api/quizzes/admin`
- `POST /api/quizzes`
- `POST /api/quizzes/join`
- `GET /api/quizzes/{quiz_id}`
- `PUT /api/quizzes/{quiz_id}`
- `DELETE /api/quizzes/{quiz_id}`
- `POST /api/quizzes/{quiz_id}/answers`
- `POST /api/quizzes/{quiz_id}/submit`
- `GET /api/quizzes/{quiz_id}/leaderboard`
- `GET /api/quizzes/{quiz_id}/results/export`
- `GET /api/results/me`

## Quiz Timing and Attempt Logic

- Private quizzes use the quiz's shared scheduled `startAt`
- Public quizzes are always exposed to students as immediately available
- Public quiz timing is per-attempt: the countdown is based on when the student's submission record is created
- Private quiz timing is shared around the quiz schedule, but submission completion time is still stored per student
- If a public attempt times out, the backend finalizes it automatically on the next relevant request
- Rejoining a public quiz after finishing starts a fresh attempt
- Rejoining a submitted private quiz does not create a new attempt

## Result and Leaderboard Logic

- Student leaderboard access is restricted to private quizzes and only after full submission
- Admin leaderboard views can include live in-progress attempts
- Leaderboard ranking is sorted by score, then progress, then faster completion time, then student name
- Exported results are returned as CSV
- Exporting a private quiz result CSV deletes that private quiz and its related records

## Data Model

- `users`: stores admin/student accounts
- `quizzes`: stores title, category, owner, privacy, password, duration, and optional start time
- `questions`: stores the text, four options, and the correct answer key
- `submissions`: stores one attempt record, score, submission timestamp, and completion time
- `answers`: stores selected options for each question within a submission

## Development Notes

- The backend uses SQLAlchemy ORM with SQLite at the project root
- There are two backend layers related to quiz persistence:
- `database/*` contains the lower-level SQLAlchemy functions
- `repositories/*` contains the active repository abstraction used by the dispatcher/services
- Flask is a thin gateway and most quiz logic lives in `backend\quiz_platform\server\http_dispatcher.py`
- The React frontend calls `/api` and relies on the Vite dev proxy during local development

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
