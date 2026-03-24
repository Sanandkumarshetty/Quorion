# Quorion

## Overview

Quorion is a multi-client quiz platform with a React frontend, a Flask API layer, and a Python quiz engine/data layer. It supports both admin and student workflows for creating quizzes, joining quizzes, attempting questions, submitting responses, and viewing results.

The project currently uses:
- React + Vite for the frontend UI
- Flask for API endpoints
- SQLAlchemy with SQLite for persistence
- Additional backend modules for quiz management and server/runtime logic

## Core Features

### Admin
- Create public and private quizzes
- Add multiple-choice questions
- Schedule private quizzes with a start time
- Join the same private quiz as admin to monitor it live
- View live leaderboard updates during private quiz attempts
- See student score and attempted-question count before final submission
- Modify and delete public quizzes
- Download quiz results
- Auto-delete a private quiz after downloading its results

### Student
- Register and log in
- Join private quizzes using quiz ID and password
- Enter public quizzes directly from the dashboard
- Wait in a waiting room before a scheduled private quiz starts
- Attempt quizzes with auto-save on answer selection
- View public quiz answer review after submission
- View private leaderboard only after full submission
- Reattempt public quizzes later
- Cannot reattempt a private quiz after submission

## Public vs Private Quiz Rules

### Private quiz
- Requires quiz ID and password
- If a student joins before the scheduled start time, they stay in the waiting room
- The waiting room countdown shows time left until the quiz start time
- Admin sees a live leaderboard during the quiz
- Students can open the leaderboard only after submitting
- After submission, the student cannot reattempt the same private quiz
- When admin downloads private quiz results, that private quiz is deleted

### Public quiz
- No waiting room
- Students can enter directly
- No live leaderboard for students
- After submission, students can review correct answers for all questions
- Public quizzes can be attempted again in the future
- Admin can modify and delete public quizzes

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
|   `-- main.py
|-- frontend\flask_api\
|   |-- app.py
|   `-- routes.py
|-- frontend\frontend_react\
|   |-- src\
|   |-- package.json
|   `-- vite.config.js
`-- README.md
```

## API Notes

- Flask registers API routes under `/api`
- Opening `http://127.0.0.1:5000/` or `http://<ip>:5000/` directly will show `Not Found` unless you add a root route
- The frontend talks to the backend through the Vite dev proxy during development

## Setup

### Clone The Repository

```powershell
git clone https://github.com/your-username/quorion.git
cd quorion
pip install -r requirements.txt
```

### Install Requirements

### Python dependencies

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you are not using the existing virtual environment, create one first and then run the same install command.

### Frontend dependencies

```powershell
cd frontend\frontend_react
npm install
cd ..\..
```

### 1. Backend

From the repo root:

```powershell
.venv\Scripts\python frontend\flask_api\app.py
```

This starts the Flask API on:

```text
http://127.0.0.1:5000
```

If you want network access for multiple devices on the same Wi-Fi, the app binds to `0.0.0.0`, so you can use your machine IP such as:

```text
http://10.14.142.254:5000
```

### 2. Frontend

```powershell
cd frontend\frontend_react
npm install
npm run dev -- --host 10.14.142.254
```

Local frontend URL:

```text
http://localhost:5173
```

Network frontend URL example:

```text
http://10.14.142.254:5173
```

### 3. Production Build Check

```powershell
cd frontend\frontend_react
npm run build
```

## Multi-Client Testing

To test with multiple laptops or phones on the same network:
- Start the backend first
- Start the frontend with `npm run dev -- --host <your-ip>`
- Open the frontend URL on each device
- Make sure all devices are on the same Wi-Fi
- If devices cannot connect, check Windows Firewall permissions for Python and Node

## Important Implementation Notes

- Answer saving happens when a student selects an option
- Clicking the same already-selected option does not send another save request
- Public quiz sessions do not poll the server continuously while the student is idle
- Admin leaderboard refreshes periodically for live monitoring
- Student leaderboard only shows submitted participants, not students still attempting
- After submitting a private quiz, using browser back should return the student to the dashboard flow instead of re-entering the quiz attempt

## Database

Current development database:
- SQLite

Key entities:
- Users
- Quizzes
- Questions
- Submissions
- Answers

## Current Tech Stack

### Frontend
- React
- React Router
- Vite

### Backend
- Flask
- SQLAlchemy
- Python

### Database
- SQLite

## Suggested Future Improvements

- Replace polling-based live updates with WebSockets
- Add environment-based config for host, port, and proxy target
- Add automated tests for quiz flow and leaderboard rules
- Add export formats beyond CSV
- Add deployment-ready WSGI/ASGI configuration

## License

This project is for academic and educational use.
