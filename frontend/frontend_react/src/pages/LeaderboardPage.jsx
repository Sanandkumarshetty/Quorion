import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { downloadQuizResults, fetchLeaderboard } from "../lib/quizApi";

function getInitials(name) {
  return (name || "User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "US";
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

export default function LeaderboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const quizId = searchParams.get("quizId") || "";
  const mode = searchParams.get("mode") === "admin" ? "admin" : "student";
  const isAdminViewer = user?.role === "admin" || mode === "admin";
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [error, setError] = useState("");
  const [downloadError, setDownloadError] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadLeaderboard() {
      try {
        const response = await fetchLeaderboard(quizId);
        if (active) {
          setLeaderboardData(response);
          setError("");
        }
      } catch (requestError) {
        if (active) {
          setLeaderboardData(null);
          setError(requestError.message || "Unable to load leaderboard.");
        }
      }
    }

    if (quizId) {
      loadLeaderboard();
      const poller = window.setInterval(loadLeaderboard, 2000);
      return () => {
        active = false;
        window.clearInterval(poller);
      };
    }

    return () => {
      active = false;
    };
  }, [quizId]);

  if (!quizId) {
    return <div className="canvas"><section className="leaderboard-locked-state"><h1>No quiz selected</h1><p>Open the leaderboard from a quiz join flow or from the admin dashboard.</p></section></div>;
  }

  if (!leaderboardData) {
    return (
      <div className="canvas">
        <section className="leaderboard-locked-state">
          <h1>{error ? "Leaderboard unavailable" : "Loading leaderboard..."}</h1>
          <p>{error || "Please wait while the live rankings load."}</p>
          <div className="hero-actions centered"><button className="primary-btn" onClick={() => navigate(isAdminViewer ? "/admin/dashboard" : "/student/dashboard")} type="button">Back</button></div>
        </section>
      </div>
    );
  }

  const topThree = leaderboardData.leaderboard.slice(0, 3);
  const remainingTime = getTimeLeft(leaderboardData.quiz.endAt);

  async function handleDownloadResults() {
    try {
      setIsDownloading(true);
      setDownloadError("");
      await downloadQuizResults(quizId);
      if (leaderboardData.quiz.quizType === "private") {
        navigate("/admin/dashboard", { replace: true });
        return;
      }
    } catch (requestError) {
      setDownloadError(requestError.message || "Unable to download quiz results.");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="canvas">
      <TopNav
        brand="EduRank"
        homeTo={isAdminViewer ? "/admin/dashboard" : "/student/dashboard"}
        links={[
          { label: "Dashboard", to: isAdminViewer ? "/admin/dashboard" : "/student/dashboard" },
          ...(isAdminViewer ? [{ label: "Create Quiz", to: "/admin/create-quiz" }] : [{ label: "Results", to: "/student/results" }])
        ]}
        profile={{ initials: getInitials(user?.name), name: user?.name || "User", subtitle: isAdminViewer ? "Live monitor" : user?.email || "student@example.com" }}
      />

      <section className="page-header leaderboard-head">
        <div>
          <h1>{isAdminViewer ? "Live Quiz Leaderboard" : "Private Quiz Leaderboard"}</h1>
          <p>{isAdminViewer ? "This board refreshes from the backend every few seconds so you can monitor live score, progress, and attempt counts." : "This board shows only finalized submitted rankings after your full quiz submission."}</p>
        </div>
        <div className="stat-box-row">
          <div className="mini-stat"><span>{isAdminViewer ? "Time Left" : "Your Rank"}</span><strong>{isAdminViewer ? remainingTime : leaderboardData.viewerRank ? `#${leaderboardData.viewerRank}` : "-"}</strong></div>
          <div className="mini-stat"><span>Student Submissions</span><strong>{leaderboardData.submissionCount}</strong></div>
          <div className="mini-stat"><span>{isAdminViewer ? "Live Attempts" : "Ranked Students"}</span><strong>{isAdminViewer ? leaderboardData.liveParticipantCount : leaderboardData.participantCount}</strong></div>
        </div>
      </section>

      <section className="podium-grid">
        {topThree.length ? topThree.map((entry) => (
          <article key={entry.rank} className={entry.rank === 1 ? "podium-card winner" : "podium-card"}>
            <div className="profile-avatar large">{entry.name[0]}</div>
            <span className="badge">#{entry.rank}</span>
            <h3>{entry.name}</h3>
            <p>Score: {entry.score}/{entry.totalQuestions}</p>
            <small>{isAdminViewer ? entry.completion : "Submitted"}</small>
          </article>
        )) : <article className="result-card empty-results-state leaderboard-empty-state"><h3>No submissions yet</h3><p>{isAdminViewer ? "Leaderboard rows will appear here as students start answering." : "Submitted ranks will appear here after participants finish the quiz."}</p></article>}
      </section>

      <section className="leaderboard-table-card">
        <div className="table-toolbar">
          <input readOnly value={leaderboardData.quiz.title} />
          <div className="table-actions">
            <button className="secondary-btn" type="button">Time Left: {remainingTime}</button>
            <button className="primary-btn small" type="button">Quiz ID: {leaderboardData.quiz.quizId}</button>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Student Name</th>
              <th>Score</th>
              {isAdminViewer ? <th>Attempts</th> : null}
              <th>{isAdminViewer ? "Progress" : "Status"}</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leaderboardData.leaderboard.map((row) => (
              <tr key={`${row.rank}-${row.userId}`} className={row.status === "Current User" ? "highlight-row" : ""}>
                <td>{row.rank}</td>
                <td>{row.name}</td>
                <td>{row.score}/{row.totalQuestions}</td>
                {isAdminViewer ? <td>{row.attemptedCount}/{row.totalQuestions}</td> : null}
                <td>{isAdminViewer ? row.completion : "Submitted"}</td>
                <td>{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {downloadError ? <div className="form-alert error">{downloadError}</div> : null}
        <div className="table-footer-actions">
          {isAdminViewer ? (
            <>
              <button className="secondary-btn" disabled={isDownloading} onClick={handleDownloadResults} type="button">
                {isDownloading ? "Downloading..." : leaderboardData.quiz.quizType === "private" ? "Download And Delete" : "Download Results"}
              </button>
              <Link className="secondary-btn button-link" to="/admin/create-quiz">Create Another Quiz</Link>
            </>
          ) : <Link className="secondary-btn button-link" to="/student/results">Open Results</Link>}
          <Link className="primary-btn button-link" to={isAdminViewer ? "/admin/dashboard" : "/student/dashboard"}>Back to Dashboard</Link>
        </div>
      </section>
    </div>
  );
}
