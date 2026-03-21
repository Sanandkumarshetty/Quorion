import { Link, useSearchParams } from "react-router-dom";
import TopNav from "../components/TopNav";
import { leaderboardRows, leaderboardTopThree } from "../data/mockData";

export default function LeaderboardPage() {
  const [searchParams] = useSearchParams();
  const isPrivateQuiz = searchParams.get("type") === "private";

  if (!isPrivateQuiz) {
    return (
      <div className="canvas">
        <TopNav
          brand="EduRank"
          homeTo="/student/dashboard"
          links={[
            { label: "Dashboard", to: "/student/dashboard" },
            { label: "Results", to: "/student/results?type=public" }
          ]}
          profile={{ initials: "AJ", name: "Alex Johnson", subtitle: "Student ID: 99-120" }}
        />
        <section className="leaderboard-locked-state">
          <h1>Leaderboard is available only for private quizzes</h1>
          <p>For public quizzes, students see answer review, score details, and reattempt availability after one hour.</p>
          <div className="hero-actions centered">
            <Link className="secondary-btn button-link" to="/student/results?type=public">Open Results</Link>
            <Link className="primary-btn button-link" to="/student/dashboard">Back to Dashboard</Link>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="canvas">
      <TopNav
        brand="EduRank"
        homeTo="/student/dashboard"
        links={[
          { label: "Dashboard", to: "/student/dashboard" },
          { label: "Leaderboard", to: "/student/leaderboard?type=private" }
        ]}
        profile={{ initials: "AJ", name: "Alex Johnson", subtitle: "Student ID: 99-120" }}
      />

      <section className="page-header leaderboard-head">
        <div>
          <h1>Private Quiz Leaderboard</h1>
          <p>Real-time rankings are available for private quiz sessions only.</p>
        </div>
        <div className="stat-box-row">
          <div className="mini-stat">
            <span>Your Rank</span>
            <strong>#12</strong>
          </div>
          <div className="mini-stat">
            <span>Total Players</span>
            <strong>1,240</strong>
          </div>
        </div>
      </section>

      <section className="podium-grid">
        {leaderboardTopThree.map((entry) => (
          <article key={entry.rank} className={entry.rank === 1 ? "podium-card winner" : "podium-card"}>
            <div className="profile-avatar large">{entry.name[0]}</div>
            <span className="badge">#{entry.rank}</span>
            <h3>{entry.name}</h3>
            <p>Score: {entry.score}</p>
            <small>Time: {entry.time}</small>
          </article>
        ))}
      </section>

      <section className="leaderboard-table-card">
        <div className="table-toolbar">
          <input placeholder="Search student or score..." />
          <div className="table-actions">
            <button className="secondary-btn" type="button">Filter</button>
            <button className="primary-btn small" type="button">Export</button>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Student Name</th>
              <th>Score</th>
              <th>Completion Time</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leaderboardRows.map((row) => (
              <tr key={`${row.rank}-${row.name}`} className={row.status === "Current User" ? "highlight-row" : ""}>
                <td>{row.rank}</td>
                <td>{row.name}</td>
                <td>{row.score}</td>
                <td>{row.completion}</td>
                <td>{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="table-footer-actions">
          <Link className="secondary-btn button-link" to="/student/results?type=private">Open Results</Link>
          <Link className="primary-btn button-link" to="/student/dashboard">Back to Dashboard</Link>
        </div>
      </section>
    </div>
  );
}
