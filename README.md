# Quorion
# 🚀 Quarion – Real-Time Multi-Client Quiz Platform

## 📌 Overview

**Quarion** is a real-time multi-client online quiz platform that enables multiple users to participate in quizzes simultaneously with dynamic scoring and leaderboard updates. The system is designed using a hybrid architecture combining **Flask (API layer)**, **TCP socket server (real-time engine)**, and **React (frontend UI)**.

The platform supports both **Admin** and **Student** roles, allowing quiz creation, participation, evaluation, and ranking in a competitive environment.

---

## 🧠 Key Features

### 👨‍🏫 Admin Features

* Create public and private quizzes
* Add multiple-choice questions
* Schedule quizzes
* Monitor quiz progress in real-time
* View live leaderboard during quiz

### 👨‍🎓 Student Features

* Register and login securely
* Join public or private quizzes
* Attempt quizzes in real-time
* Submit answers dynamically
* View final leaderboard after quiz completion

### ⚡ Real-Time System

* TCP socket-based communication
* Instant answer evaluation
* Live leaderboard updates for admin
* Final leaderboard broadcast to students

---

## 🏗️ Tech Stack

### Frontend

* **React.js**
* Axios (API communication)

### Backend

* **Flask** (REST API layer)
* **Python TCP Sockets** (real-time engine)
* **SQLAlchemy** (ORM)

### Database

* SQLite (development)
* Easily extendable to PostgreSQL/MySQL

---

## 📂 Project Structure

```
quiz_platform/
│
├── frontend/ (React App)
│
├── backend/
│   ├── main.py
│
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── auth/
│   ├── quiz_management/
│   ├── quiz_runtime/
│   ├── server/
│   └── utils/
```

---

## ⚙️ System Architecture

```
React Frontend
       │
       ▼
Flask API Server
       │
       ▼
TCP Socket Server (Real-Time Engine)
       │
       ▼
SQLAlchemy ORM
       │
       ▼
Database (SQLite)
```

---

## 🗄️ Database Design

Entities:

* Users
* Quizzes
* Questions
* Submissions
* Answers

Relationships:

* User → Quiz (Admin creates quizzes)
* Quiz → Questions
* User → Submission (Student attempts)
* Submission → Answers

---

## 🔄 Workflow

### Student Flow

1. Register/Login
2. Join quiz (public/private)
3. Enter waiting room
4. Answer questions
5. Submit quiz
6. Receive final leaderboard

### Admin Flow

1. Login
2. Create quiz
3. Add questions
4. Start quiz
5. Monitor live leaderboard

---

## 🔌 TCP Communication Protocol

### Client → Server

* LOGIN
* JOIN_QUIZ
* ANSWER
* SUBMIT

### Server → Client

* QUIZ_STARTED
* QUESTION
* LEADERBOARD_UPDATE (Admin only)
* FINAL_LEADERBOARD

---

## ⚡ Real-Time Leaderboard Logic

* Scores updated after each answer
* Admin sees leaderboard instantly
* Students see leaderboard only after quiz ends
* Ranking based on:

  * Score (descending)
  * Completion time (ascending)

---

## 🔐 Security Features

* Password hashing
* Role-based access (Admin / Student)
* Private quiz password protection

---

## 🚀 Installation & Setup

### 1. Clone Repository

```
git clone https://github.com/your-username/quarion.git
cd quarion
```

---

### 2. Backend Setup

```
cd backend
pip install -r requirements.txt
python main.py
```

---

### 3. Frontend Setup

```
cd frontend
npm install
npm start
```

---

## 🧪 Future Enhancements

* WebSocket integration for scalability
* Mobile application
* Analytics dashboard
* AI-based quiz generation
* Multi-language support

---

## 👥 Team Contribution

| Module            | Responsibility   |
| ----------------- | ---------------- |
| Models & Database | Data Layer       |
| Authentication    | User Management  |
| Quiz Management   | Admin Features   |
| Runtime + Server  | Real-Time Engine |

---

## 📜 License

This project is developed for academic and educational purposes.

---

## ⭐ Conclusion

Quarion provides a scalable and efficient platform for conducting real-time quizzes with dynamic leaderboard tracking. It combines networking, database design, and modern web technologies to create an interactive and competitive learning environment.

---

**Made with ❤️ using Python, Flask, and React**
