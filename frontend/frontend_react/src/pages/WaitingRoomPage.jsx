import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { fetchQuizDetails } from "../lib/quizApi";

function getInitials(name) {
  return (name || "Student User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "SU";
}

function getTimeUntilStart(startAt) {
  if (!startAt) {
    return "00:00";
  }
  const remainingMs = Math.max(0, new Date(startAt).getTime() - Date.now());
  const totalSeconds = Math.floor(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export default function WaitingRoomPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const quizId = searchParams.get("quizId") || "";
  const [quiz, setQuiz] = useState(location.state?.quiz || null);
  const [, setTick] = useState(0);
  const quizRef = useRef(location.state?.quiz || null);

  useEffect(() => {
    quizRef.current = quiz;
  }, [quiz]);

  useEffect(() => {
    let active = true;
    let requestInFlight = false;

    async function syncQuizStatus() {
      if (!quizId || requestInFlight) {
        return;
      }

      requestInFlight = true;
      try {
        const response = await fetchQuizDetails(quizId);
        if (!active) {
          return;
        }
        const nextQuiz = response.quiz;
        setQuiz(nextQuiz);
        if (!response.requiresWaitingRoom || (nextQuiz?.startAt && new Date(nextQuiz.startAt).getTime() <= Date.now())) {
          navigate(`/student/quiz-session?quizId=${encodeURIComponent(quizId)}`, { replace: true });
        }
      } catch {
        if (active) {
          setQuiz(null);
        }
      } finally {
        requestInFlight = false;
      }
    }

    if (quizId) {
      syncQuizStatus();
    }

    const timer = window.setInterval(() => {
      setTick((value) => value + 1);
      const currentQuiz = quizRef.current;
      if (currentQuiz?.startAt && new Date(currentQuiz.startAt).getTime() <= Date.now()) {
        syncQuizStatus();
      }
    }, 1000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [navigate, quizId]);

  if (!quiz) {
    return (
      <div className="canvas waiting-canvas">
        <section className="waiting-card">
          <h1>Quiz not found</h1>
          <p>Go back to the dashboard and join again using a valid quiz ID and password.</p>
          <div className="hero-actions centered top-gap"><Link className="primary-btn button-link" to="/student/dashboard">Back to Dashboard</Link></div>
        </section>
      </div>
    );
  }

  return (
    <div className="canvas waiting-canvas">
      <TopNav
        brand="QuizFlow"
        homeTo="/student/dashboard"
        compact
        links={[{ label: "Dashboard", to: "/student/dashboard" }]}
        profile={{ initials: getInitials(user?.name), name: user?.name || "Student User", subtitle: user?.email || "student@example.com" }}
      />

      <section className="waiting-card">
        <span className="badge">Waiting Room</span>
        <h1>{quiz.title}</h1>
        <p>Quiz Type: {quiz.quizType === "private" ? "Private" : "Public"}</p>
      </section>

      <section className="waiting-card">
        <p className="muted-label">Time until quiz starts</p>
        <div className="countdown-row"><div className="countdown-box wide-countdown-box"><strong>{getTimeUntilStart(quiz.startAt)}</strong><span>Until Start</span></div></div>
        <p className="waiting-note">Please stay on this page. The quiz will open automatically at the scheduled time.</p>
      </section>

      <section className="waiting-card profile-row">
        <div className="profile-chip large">
          <div className="profile-avatar">{getInitials(user?.name)}</div>
          <div><span className="muted-label">Logged in as</span><strong>{user?.email || "student@example.com"}</strong></div>
        </div>
        <div><span className="muted-label">Quiz ID</span><strong>{quiz.quizId}</strong></div>
      </section>

      <section className="waiting-card info-list">
        <h3>Before you begin</h3>
        <ul>
          <li>Each answer selection updates your saved progress in the backend.</li>
          <li>This waiting room is only for scheduled private quizzes joined before the start time.</li>
          <li>The countdown follows the scheduled quiz start time configured by the admin.</li>
        </ul>
        <div className="hero-actions centered top-gap">
          <Link className="secondary-btn button-link" to="/student/dashboard">Leave Room</Link>
        </div>
      </section>
    </div>
  );
}
