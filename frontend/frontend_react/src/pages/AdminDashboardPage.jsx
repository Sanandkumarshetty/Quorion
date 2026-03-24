import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import TopNav from "../components/TopNav";
import { useAuth } from "../auth/AuthProvider";
import { deletePublicQuiz, fetchAdminQuizDashboard, fetchLeaderboard, joinQuiz } from "../lib/quizApi";

function getInitials(name) {
  return (name || "Admin User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "AD";
}

function getTimeLeft(endAt) {
  if (!endAt) {
    return "00:00";
  }
  const remainingMs = Math.max(0, new Date(endAt).getTime() - Date.now());
  const totalSeconds = Math.floor(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const [joinForm, setJoinForm] = useState({ quizId: "", password: "" });
  const [selectedQuizId, setSelectedQuizId] = useState(searchParams.get("quizId") || "");
  const [showAllQuizzes, setShowAllQuizzes] = useState(false);
  const [showQuizCatalog, setShowQuizCatalog] = useState(false);
  const [dashboard, setDashboard] = useState({ stats: { totalQuizzes: 0, activeQuizzes: 0, submissionCount: 0 }, quizzes: [] });
  const [liveData, setLiveData] = useState(null);
  const [joinError, setJoinError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [, setTick] = useState(0);

  useEffect(() => {
    let active = true;
    async function loadDashboard() {
      try {
        const response = await fetchAdminQuizDashboard();
        if (!active) {
          return;
        }
        setDashboard(response);
        setLoadError("");
      } catch (error) {
        if (active) {
          setLoadError(error.message || "Unable to load dashboard.");
        }
      }
    }

    loadDashboard();
    const poller = window.setInterval(loadDashboard, 3000);
    const timer = window.setInterval(() => setTick((value) => value + 1), 1000);

    return () => {
      active = false;
      window.clearInterval(poller);
      window.clearInterval(timer);
    };
  }, []);

  const runningPublicQuizzes = useMemo(
    () => dashboard.quizzes.filter((quiz) => quiz.quizType === "public" && quiz.status === "active"),
    [dashboard.quizzes]
  );
  const visibleQuizzes = showQuizCatalog ? (showAllQuizzes ? dashboard.quizzes : runningPublicQuizzes) : [];
  const selectedQuiz = dashboard.quizzes.find((quiz) => String(quiz.quizId) === String(selectedQuizId)) || null;
  const isSelectedPrivateQuiz = selectedQuiz?.quizType === "private";

  useEffect(() => {
    if (!visibleQuizzes.length) {
      setSelectedQuizId("");
      return;
    }

    if (!selectedQuizId || !visibleQuizzes.some((quiz) => String(quiz.quizId) === String(selectedQuizId))) {
      setSelectedQuizId(searchParams.get("quizId") || visibleQuizzes[0].quizId);
    }
  }, [searchParams, selectedQuizId, visibleQuizzes]);

  useEffect(() => {
    let active = true;

    async function loadLiveData() {
      if (!selectedQuizId || !isSelectedPrivateQuiz) {
        setLiveData(null);
        return;
      }
      try {
        const response = await fetchLeaderboard(selectedQuizId);
        if (active) {
          setLiveData(response);
        }
      } catch {
        if (active) {
          setLiveData(null);
        }
      }
    }

    loadLiveData();
    if (!isSelectedPrivateQuiz) {
      return () => {
        active = false;
      };
    }

    const poller = window.setInterval(loadLiveData, 2000);
    return () => {
      active = false;
      window.clearInterval(poller);
    };
  }, [isSelectedPrivateQuiz, selectedQuizId]);

  function handleLogout() {
    logout();
    navigate("/");
  }

  async function handleJoinQuiz() {
    try {
      const response = await joinQuiz(joinForm);
      setJoinError("");
      if (response.quiz?.quizType === "private") {
        navigate(`/student/leaderboard?quizId=${encodeURIComponent(response.quiz.quizId)}&mode=admin`);
        return;
      }
      navigate(`/student/quiz-session?quizId=${encodeURIComponent(response.quiz.quizId)}`);
    } catch (error) {
      setJoinError(error.message || "Unable to join this quiz.");
    }
  }

  async function handleDeleteQuiz(quizId) {
    try {
      setActionError("");
      await deletePublicQuiz(quizId);
      setDashboard((current) => ({
        ...current,
        quizzes: current.quizzes.filter((quiz) => String(quiz.quizId) !== String(quizId))
      }));
      if (String(selectedQuizId) === String(quizId)) {
        setSelectedQuizId("");
      }
    } catch (error) {
      setActionError(error.message || "Unable to delete quiz.");
    }
  }

  return (
    <div className="canvas admin-dashboard-shell">
      <TopNav brand="QuizPortal" homeTo="/admin/dashboard" links={[{ label: "Dashboard", to: "/admin/dashboard" }]} actions={<button className="secondary-btn" onClick={handleLogout} type="button">Logout</button>} profile={{ initials: getInitials(user?.name), name: user?.name || "Admin User", subtitle: user?.email || "Quiz Manager" }} />

      <section className="page-header admin-hero-header">
        <div><h1>Welcome back, {user?.name?.split(" ")[0] || "Admin"}!</h1><p>Private quizzes support live leaderboard monitoring. Public quizzes are simple self-serve attempts with answer review after submission.</p></div>
        <div className="hero-actions"><Link className="primary-btn small button-link" to="/admin/create-quiz">Create Quiz</Link><button className="secondary-btn small" onClick={handleJoinQuiz} type="button">Join Quiz</button></div>
      </section>

      <section className="student-grid student-grid-full admin-dashboard-grid">
        <article className="join-card admin-join-card">
          <h3>Join Created Quiz</h3>
          <label className="field"><span>Quiz ID</span><input onChange={(event) => setJoinForm((current) => ({ ...current, quizId: event.target.value }))} placeholder="Enter quiz ID" value={joinForm.quizId} /></label>
          <label className="field"><span>Quiz Password</span><input onChange={(event) => setJoinForm((current) => ({ ...current, password: event.target.value }))} placeholder="Enter quiz password" type="password" value={joinForm.password} /></label>
          <button className="primary-btn" onClick={handleJoinQuiz} type="button">Open Quiz</button>
          <small className="helper-copy">Private quizzes can be monitored live. Public quizzes open as normal student attempts without waiting room or leaderboard.</small>
          {joinError ? <div className="form-alert error">{joinError}</div> : null}
          {loadError ? <div className="form-alert error">{loadError}</div> : null}
          {actionError ? <div className="form-alert error">{actionError}</div> : null}
        </article>

        <div className="student-content admin-content-panel">
          <div className="section-heading inline">
            <div>
              <h2>{showQuizCatalog ? (showAllQuizzes ? "All Created Quizzes" : "Running Public Quizzes") : "Quiz List Hidden"}</h2>
              <p>{showQuizCatalog ? (showAllQuizzes ? "Private and public quizzes created by this admin are listed here." : "Only currently running public quizzes are shown here.") : "Press the button to show your created quizzes."}</p>
            </div>
            <div className="hero-actions">
              <button className="secondary-btn small" onClick={() => setShowQuizCatalog((value) => !value)} type="button">
                {showQuizCatalog ? "Hide Quiz List" : "Show Quiz List"}
              </button>
              {showQuizCatalog ? (
                <button className="secondary-btn small" onClick={() => setShowAllQuizzes((value) => !value)} type="button">
                  {showAllQuizzes ? "Show Running Public Only" : "View All Created Quizzes"}
                </button>
              ) : null}
              <Link to="/admin/create-quiz">Create another quiz</Link>
            </div>
          </div>
          <div className="stats-grid admin-stats-grid">
            <article className="mini-stat"><span>Total Quizzes</span><strong>{dashboard.stats.totalQuizzes}</strong><p>Private and public rooms created from this admin account</p></article>
            <article className="mini-stat"><span>Active Quizzes</span><strong>{dashboard.stats.activeQuizzes}</strong><p>Rooms still accepting answers before the timer ends</p></article>
            <article className="mini-stat"><span>Student Submissions</span><strong>{dashboard.stats.submissionCount}</strong><p>Completed quiz submissions across your created quizzes</p></article>
          </div>

          <div className="admin-quiz-card-grid">
            {showQuizCatalog && visibleQuizzes.length ? visibleQuizzes.map((quiz) => (
              <button key={quiz.quizId} className={quiz.quizId === selectedQuizId ? "admin-quiz-card selected" : "admin-quiz-card"} onClick={() => setSelectedQuizId(quiz.quizId)} type="button">
                <div className="section-heading inline"><div><h3>{quiz.title}</h3><p>{quiz.quizId} • {quiz.quizType}</p></div><span className="badge">{quiz.status}</span></div>
                <div className="admin-quiz-meta"><span>{quiz.startAt ? new Date(quiz.startAt).toLocaleString() : "Not scheduled"}</span><span>{quiz.submissionCount} submissions</span></div>
                {quiz.quizType === "public" ? (
                  <div className="hero-actions top-gap">
                    <Link className="secondary-btn small button-link" to={`/admin/create-quiz?quizId=${encodeURIComponent(quiz.quizId)}&mode=edit`}>Modify Quiz</Link>
                    <button className="secondary-btn small" onClick={(event) => { event.stopPropagation(); handleDeleteQuiz(quiz.quizId); }} type="button">Delete Quiz</button>
                  </div>
                ) : null}
              </button>
            )) : (
              <article className="result-card empty-results-state">
                <h3>{showQuizCatalog ? (showAllQuizzes ? "No quizzes created yet" : "No running public quizzes right now") : "Quiz list is hidden"}</h3>
                <p>{showQuizCatalog ? (showAllQuizzes ? "Create your first quiz to unlock the join flow." : "Switch to all quizzes if you want to browse every created quiz.") : "Press Show Quiz List when you want to browse quizzes."}</p>
                {!showQuizCatalog ? <button className="primary-btn small" onClick={() => setShowQuizCatalog(true)} type="button">Show Quiz List</button> : null}
                {showQuizCatalog && !showAllQuizzes ? <button className="primary-btn small" onClick={() => setShowAllQuizzes(true)} type="button">View All Created Quizzes</button> : null}
              </article>
            )}
          </div>

          {showQuizCatalog && selectedQuiz ? (
            isSelectedPrivateQuiz ? (
              <section className="table-card admin-live-panel">
                <div className="section-heading inline">
                  <div><h2>{selectedQuiz.title}</h2><p>{selectedQuiz.quizId} • {selectedQuiz.questionCount} questions • Password: {selectedQuiz.password || "Not required"}</p></div>
                  <div className="hero-actions">
                    <Link className="secondary-btn button-link" to={`/student/leaderboard?quizId=${encodeURIComponent(selectedQuiz.quizId)}&mode=admin`}>Open Full View</Link>
                  </div>
                </div>

                <div className="admin-live-stats">
                  <article className="mini-stat compact-stat"><span>Time Left</span><strong>{getTimeLeft(selectedQuiz.endAt)}</strong></article>
                  <article className="mini-stat compact-stat"><span>Participants</span><strong>{liveData?.participantCount || selectedQuiz.participantCount}</strong></article>
                  <article className="mini-stat compact-stat"><span>Completed</span><strong>{liveData?.submissionCount || selectedQuiz.submissionCount}</strong></article>
                </div>

                <table className="data-table">
                  <thead><tr><th>Rank</th><th>Student Name</th><th>Score</th><th>Progress</th><th>Status</th></tr></thead>
                  <tbody>
                    {liveData?.leaderboard?.length ? liveData.leaderboard.map((row) => (
                      <tr key={`${row.rank}-${row.userId}`}><td>{row.rank}</td><td>{row.name}</td><td>{row.score}/{row.totalQuestions}</td><td>{row.completion}</td><td>{row.status}</td></tr>
                    )) : <tr><td colSpan="5">No live submissions yet. Student answers will appear here as soon as they select an option.</td></tr>}
                  </tbody>
                </table>
              </section>
            ) : (
              <section className="table-card admin-live-panel">
                <div className="section-heading inline">
                  <div><h2>{selectedQuiz.title}</h2><p>{selectedQuiz.quizId} • {selectedQuiz.questionCount} questions • Public quiz</p></div>
                  <div className="hero-actions">
                    <Link className="secondary-btn button-link" to={`/admin/create-quiz?quizId=${encodeURIComponent(selectedQuiz.quizId)}&mode=edit`}>Modify Quiz</Link>
                  </div>
                </div>

                <div className="admin-live-stats">
                  <article className="mini-stat compact-stat"><span>Submissions</span><strong>{selectedQuiz.submissionCount}</strong></article>
                </div>

                <article className="result-card empty-results-state leaderboard-empty-state">
                  <h3>No public leaderboard or live monitor</h3>
                </article>
              </section>
            )
          ) : null}
        </div>
      </section>
    </div>
  );
}
