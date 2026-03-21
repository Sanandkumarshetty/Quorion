import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { categories, publicQuizzes } from "../data/mockData";

function getInitials(name) {
  return (name || "Student User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "SU";
}

export default function StudentDashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [joinForm, setJoinForm] = useState({ quizId: "", password: "" });

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="canvas">
      <TopNav
        brand="QuizPortal"
        homeTo="/student/dashboard"
        links={[
          { label: "Dashboard", to: "/student/dashboard" },
          { label: "Leaderboard", to: "/student/leaderboard" }
        ]}
        actions={
          <button className="secondary-btn" onClick={handleLogout} type="button">
            Logout
          </button>
        }
        profile={{ initials: getInitials(user?.name), name: user?.name || "Student User", subtitle: user?.email || "student@example.com" }}
      />

      <section className="page-header">
        <div>
          <h1>Welcome back, {user?.name?.split(" ")[0] || "Student"}!</h1>
          <p>Your account is active. You can now access quizzes and results.</p>
        </div>
        <div className="hero-actions">
          <button className="primary-btn small" onClick={() => navigate("/student/waiting-room?type=private")} type="button">
            Resume Last Quiz
          </button>
          <Link className="secondary-btn small button-link" to="/student/results?type=public">
            My Results
          </Link>
        </div>
      </section>

      <section className="student-grid student-grid-full">
        <article className="join-card">
          <h3>Join Private Quiz</h3>
          <label className="field">
            <span>Quiz ID</span>
            <input
              onChange={(event) => setJoinForm((current) => ({ ...current, quizId: event.target.value }))}
              placeholder="Enter quiz ID"
              value={joinForm.quizId}
            />
          </label>
          <label className="field">
            <span>Quiz Password</span>
            <input
              onChange={(event) => setJoinForm((current) => ({ ...current, password: event.target.value }))}
              placeholder="Enter quiz password"
              type="password"
              value={joinForm.password}
            />
          </label>
          <button className="primary-btn" onClick={() => navigate("/student/waiting-room?type=private")} type="button">
            Join Quiz Session
          </button>
          <small className="helper-copy">Login is required and already enforced for this page.</small>
        </article>

        <div className="student-content">
          <div className="section-heading inline">
            <h2>Quiz Categories</h2>
            <Link to="/student/results?type=public">View my scores</Link>
          </div>
          <div className="category-grid">
            {categories.map((category) => (
              <article key={category.title} className="category-card">
                <div className="feature-icon">{category.title.slice(0, 1)}</div>
                <h3>{category.title}</h3>
                <p>{category.count} quizzes</p>
              </article>
            ))}
          </div>

          <div className="section-heading inline">
            <h2>Public Quizzes</h2>
            <div className="table-actions">
              <button className="icon-btn" type="button">Filter</button>
              <button className="icon-btn" type="button">Sort</button>
            </div>
          </div>
          <div className="quiz-list">
            {publicQuizzes.map((quiz) => (
              <article key={quiz.title} className="quiz-row">
                <div>
                  <h3>{quiz.title}</h3>
                  <p>
                    {quiz.owner} - {quiz.plays} plays - {quiz.category}
                  </p>
                </div>
                <button
                  className="secondary-btn"
                  onClick={() => navigate(`/student/quiz-session?type=${quiz.quizType}`)}
                  type="button"
                >
                  Start
                </button>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
