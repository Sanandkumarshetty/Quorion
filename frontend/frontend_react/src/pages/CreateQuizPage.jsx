import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";

function getInitials(name) {
  return (name || "Admin User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "AD";
}

export default function CreateQuizPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [quizType, setQuizType] = useState("private");
  const [questionCount, setQuestionCount] = useState(1);

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="canvas">
      <TopNav
        brand="QuizBuilder"
        homeTo="/admin/dashboard"
        links={[
          { label: "Dashboard", to: "/admin/dashboard" },
          { label: "Create Quiz", to: "/admin/create-quiz" },
          { label: "Leaderboard", to: "/student/leaderboard" }
        ]}
        actions={
          <button className="secondary-btn" onClick={handleLogout} type="button">
            Logout
          </button>
        }
        profile={{ initials: getInitials(user?.name), name: user?.name || "Admin User", subtitle: user?.email || "Quiz Manager" }}
      />

      <section className="page-header left">
        <div>
          <h1>Configure New Quiz</h1>
          <p>Your admin account is active. Set up your quiz details and add questions for your students.</p>
        </div>
      </section>

      <section className="create-layout">
        <article className="panel">
          <h3>Quiz Type</h3>
          <button
            className={quizType === "private" ? "radio-card selected radio-card-button" : "radio-card radio-card-button"}
            onClick={() => setQuizType("private")}
            type="button"
          >
            <input type="radio" checked={quizType === "private"} readOnly />
            <div>
              <strong>Private Quiz</strong>
              <span>Requires ID and password</span>
            </div>
          </button>
          <button
            className={quizType === "public" ? "radio-card selected radio-card-button" : "radio-card radio-card-button"}
            onClick={() => setQuizType("public")}
            type="button"
          >
            <input type="radio" checked={quizType === "public"} readOnly />
            <div>
              <strong>Public Quiz</strong>
              <span>Accessible via link only</span>
            </div>
          </button>
        </article>

        <article className="panel wide">
          <h3>Configuration</h3>
          <div className="form-grid">
            {quizType === "private" ? (
              <>
                <label className="field">
                  <span>Quiz ID</span>
                  <input defaultValue="QUIZ-2025-001" />
                </label>
                <label className="field">
                  <span>Quiz Password</span>
                  <input defaultValue="secure-room" />
                </label>
              </>
            ) : null}
            <label className="field">
              <span>Duration (Minutes)</span>
              <input defaultValue="60" />
            </label>
            <label className="field">
              <span>Date and Time</span>
              <input defaultValue="15-10-2025 10:00" />
            </label>
          </div>
        </article>
      </section>

      <section className="question-builder">
        <div className="section-heading inline">
          <h2>Questions</h2>
          <button className="primary-btn small" onClick={() => setQuestionCount((value) => value + 1)} type="button">
            Add Question
          </button>
        </div>

        <article className="question-editor">
          <label className="field">
            <span>Question {questionCount}</span>
            <textarea rows="4" placeholder="Enter question text here..." />
          </label>
          <div className="form-grid">
            <label className="field"><span>Option A</span><input placeholder="Option A" /></label>
            <label className="field"><span>Option B</span><input placeholder="Option B" /></label>
            <label className="field"><span>Option C</span><input placeholder="Option C" /></label>
            <label className="field"><span>Option D</span><input placeholder="Option D" /></label>
          </div>
          <div className="section-heading inline">
            <label className="field compact-field">
              <span>Correct Answer Key</span>
              <select defaultValue="Select Answer">
                <option>Select Answer</option>
                <option>A</option>
                <option>B</option>
                <option>C</option>
                <option>D</option>
              </select>
            </label>
            <span className="muted-label">Hidden from students</span>
          </div>
        </article>

        <div className="add-more-card">{questionCount > 1 ? `${questionCount} questions prepared` : "Click Add Question to prepare more items"}</div>

        <div className="builder-actions">
          <Link className="secondary-btn button-link" to="/admin/dashboard">Save as Draft</Link>
          <button className="primary-btn" onClick={() => navigate("/admin/dashboard")} type="button">Publish Quiz</button>
        </div>
      </section>
    </div>
  );
}
