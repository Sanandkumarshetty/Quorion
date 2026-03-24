import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { fetchMyResults, fetchPublicQuizzes, joinQuiz } from "../lib/quizApi";

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
  const [joinError, setJoinError] = useState("");
  const [publicQuizzes, setPublicQuizzes] = useState([]);
  const [results, setResults] = useState([]);

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        const [publicResponse, resultsResponse] = await Promise.all([fetchPublicQuizzes(), fetchMyResults()]);
        if (!active) {
          return;
        }
        setPublicQuizzes(publicResponse.quizzes || []);
        setResults(resultsResponse.results || []);
      } catch {
        if (active) {
          setPublicQuizzes([]);
          setResults([]);
        }
      }
    }

    loadData();
    return () => {
      active = false;
    };
  }, []);

  const groupedResults = useMemo(() => ({
    public: results.filter((result) => result.quizType === "public"),
    private: results.filter((result) => result.quizType === "private")
  }), [results]);
  const categories = useMemo(() => {
    const counts = new Map();
    publicQuizzes.forEach((quiz) => counts.set(quiz.category, (counts.get(quiz.category) || 0) + 1));
    return Array.from(counts.entries()).map(([title, count]) => ({ title, count }));
  }, [publicQuizzes]);
  const totalAttempts = results.length;
  const latestPrivateQuiz = groupedResults.private[0];
  const fallbackQuiz = publicQuizzes[0];

  function handleLogout() {
    logout();
    navigate("/");
  }

  async function handleJoinPrivateQuiz() {
    try {
      const response = await joinQuiz(joinForm);
      setJoinError("");
      if (response.submission?.completed || response.canAttempt === false) {
        navigate(`/student/leaderboard?quizId=${encodeURIComponent(response.quiz.quizId)}`);
        return;
      }

      const startAt = response.quiz?.startAt ? new Date(response.quiz.startAt).getTime() : null;
      const shouldWait = response.quiz?.quizType === "private" && Number.isFinite(startAt) && startAt > Date.now();
      if (shouldWait) {
        navigate(`/student/waiting-room?quizId=${encodeURIComponent(response.quiz.quizId)}`, { state: { quiz: response.quiz, submission: response.submission } });
        return;
      }

      navigate(`/student/quiz-session?quizId=${encodeURIComponent(response.quiz.quizId)}`);
    } catch (error) {
      setJoinError(error.message || "Enter a valid private quiz ID and password.");
    }
  }

  function handleResume() {
    if (latestPrivateQuiz) {
      navigate(`/student/leaderboard?quizId=${encodeURIComponent(latestPrivateQuiz.quizId)}`);
      return;
    }

    if (fallbackQuiz) {
      navigate(`/student/quiz-session?quizId=${encodeURIComponent(fallbackQuiz.quizId)}`);
      return;
    }

    navigate("/student/results");
  }

  return (
    <div className="canvas">
      <TopNav brand="QuizPortal" homeTo="/student/dashboard" links={[{ label: "Dashboard", to: "/student/dashboard" }]} actions={<button className="secondary-btn" onClick={handleLogout} type="button">Logout</button>} profile={{ initials: getInitials(user?.name), name: user?.name || "Student User", subtitle: user?.email || "student@example.com" }} />

      <section className="page-header">
        <div><h1>Welcome back, {user?.name?.split(" ")[0] || "Student"}!</h1><p>Your account is active. You can now access quizzes and results.</p></div>
        <div className="hero-actions"><button className="primary-btn small" onClick={handleResume} type="button">Resume Last Quiz</button><Link className="secondary-btn small button-link" to="/student/results">My Results</Link></div>
      </section>

      <section className="student-grid student-grid-full">
        <article className="join-card">
          <h3>Join Private Quiz</h3>
          <label className="field"><span>Quiz ID</span><input onChange={(event) => setJoinForm((current) => ({ ...current, quizId: event.target.value }))} placeholder="Enter quiz ID" value={joinForm.quizId} /></label>
          <label className="field"><span>Quiz Password</span><input onChange={(event) => setJoinForm((current) => ({ ...current, password: event.target.value }))} placeholder="Enter quiz password" type="password" value={joinForm.password} /></label>
          <button className="primary-btn" onClick={handleJoinPrivateQuiz} type="button">Join Quiz Session</button>
          <small className="helper-copy">After submitting a private quiz, joining again will open the leaderboard instead of creating a new attempt.</small>
          {joinError ? <div className="form-alert error">{joinError}</div> : null}
        </article>

        <div className="student-content">
          <div className="section-heading inline"><h2>Quiz Categories</h2><Link to="/student/results">View my scores</Link></div>
          <div className="stats-grid">
            <article className="mini-stat"><span>Total Results</span><strong>{totalAttempts}</strong><p>Only quizzes you attended are shown</p></article>
            <article className="mini-stat"><span>Public Quizzes</span><strong>{publicQuizzes.length}</strong><p>Loaded from the backend quiz list</p></article>
            <article className="mini-stat"><span>Private Results</span><strong>{groupedResults.private.length}</strong><p>Private quiz history from your submissions</p></article>
          </div>
          <div className="category-grid">
            {categories.length ? categories.map((category) => (
              <article key={category.title} className="category-card"><div className="feature-icon">{category.title.slice(0, 1)}</div><h3>{category.title}</h3><p>{category.count} quizzes</p></article>
            )) : <article className="result-card empty-results-state"><h3>No categories yet</h3><p>Once public quizzes are available, they will appear here.</p></article>}
          </div>

          <div className="section-heading inline"><h2>Public Quizzes</h2></div>
          <div className="quiz-list">
            {publicQuizzes.length ? publicQuizzes.map((quiz) => (
              <article key={quiz.quizId} className="quiz-row"><div><h3>{quiz.title}</h3><p>{quiz.createdByName} - {quiz.category} - {quiz.questionCount} questions</p></div><button className="secondary-btn" onClick={() => navigate(`/student/quiz-session?quizId=${encodeURIComponent(quiz.quizId)}`)} type="button">Start</button></article>
            )) : <article className="result-card empty-results-state"><h3>No public quizzes available</h3><p>Ask the admin to publish a quiz and it will appear here.</p></article>}
          </div>
        </div>
      </section>
    </div>
  );
}
