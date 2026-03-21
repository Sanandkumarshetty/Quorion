import { Link, useNavigate, useSearchParams } from "react-router-dom";
import TopNav from "../components/TopNav";

export default function WaitingRoomPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const quizType = searchParams.get("type") === "private" ? "private" : "public";
  const isPrivateQuiz = quizType === "private";

  return (
    <div className="canvas waiting-canvas">
      <TopNav
        brand="QuizFlow"
        homeTo="/student/dashboard"
        compact
        links={[
          { label: "Dashboard", to: "/student/dashboard" },
          ...(isPrivateQuiz ? [{ label: "Leaderboard", to: "/student/leaderboard?type=private" }] : [])
        ]}
        profile={{ initials: "AT", name: "Alex Thompson", subtitle: "Student ID: 103421" }}
      />

      <section className="waiting-card">
        <span className="badge">Waiting Room</span>
        <h1>{isPrivateQuiz ? "Advanced Macroeconomics Final" : "Public Practice Quiz"}</h1>
        <p>Quiz Type: {isPrivateQuiz ? "Private" : "Public"}</p>
      </section>

      <section className="waiting-card">
        <p className="muted-label">Quiz starts in</p>
        <div className="countdown-row">
          <div className="countdown-box">
            <strong>00</strong>
            <span>Hours</span>
          </div>
          <span className="colon">:</span>
          <div className="countdown-box">
            <strong>12</strong>
            <span>Minutes</span>
          </div>
          <span className="colon">:</span>
          <div className="countdown-box">
            <strong>45</strong>
            <span>Seconds</span>
          </div>
        </div>
        <p className="waiting-note">Waiting for the host to release the first question.</p>
      </section>

      <section className="waiting-card profile-row">
        <div className="profile-chip large">
          <div className="profile-avatar">AT</div>
          <div>
            <span className="muted-label">Logged in as</span>
            <strong>alex_thompson_99</strong>
          </div>
        </div>
        <div className="hero-actions">
          <button className="secondary-btn" onClick={() => navigate("/student/dashboard")} type="button">
            Edit Profile
          </button>
          <Link className="secondary-btn button-link" to="/student/dashboard">
            Leave Room
          </Link>
        </div>
      </section>

      <section className="waiting-card info-list">
        <h3>Before you begin</h3>
        <ul>
          <li>Ensure your internet connection is stable throughout the session.</li>
          <li>Once the quiz starts, you cannot pause the countdown.</li>
          <li>Refresh the page if the timer does not update automatically.</li>
        </ul>
        <div className="hero-actions centered top-gap">
          <button className="primary-btn" onClick={() => navigate(`/student/quiz-session?type=${quizType}`)} type="button">
            Enter Quiz Demo
          </button>
          {isPrivateQuiz ? (
            <Link className="secondary-btn button-link" to="/student/leaderboard?type=private">
              View Leaderboard
            </Link>
          ) : null}
        </div>
      </section>
    </div>
  );
}
