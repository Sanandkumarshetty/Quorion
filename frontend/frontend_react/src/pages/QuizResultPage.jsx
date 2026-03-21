import { Link, useSearchParams } from "react-router-dom";
import TopNav from "../components/TopNav";
import { resultSummary } from "../data/mockData";

export default function QuizResultPage() {
  const [searchParams] = useSearchParams();
  const quizType = searchParams.get("type") === "private" ? "private" : "public";
  const isPrivateQuiz = quizType === "private";

  return (
    <div className="canvas">
      <TopNav
        brand="QuizResults"
        homeTo="/student/dashboard"
        links={[
          { label: "Dashboard", to: "/student/dashboard" },
          ...(isPrivateQuiz ? [{ label: "Leaderboard", to: "/student/leaderboard?type=private" }] : [])
        ]}
        profile={{ initials: "AJ", name: "Alex Johnson", subtitle: "Student Review" }}
      />

      <section className="results-summary">
        <div>
          <span className="badge">Quiz Completed</span>
          <h1>{isPrivateQuiz ? "Private Quiz Results" : "Public Quiz Results"}</h1>
          <p>
            Your answers are now visible along with your score.
            {isPrivateQuiz ? " Leaderboard access remains available for this private quiz." : " Leaderboard is hidden for public quizzes."}
          </p>
        </div>
        <div className="results-score-card">
          <span>Score</span>
          <strong>{resultSummary.score}/{resultSummary.total}</strong>
          <p>{resultSummary.percentage} correct</p>
        </div>
      </section>

      <section className="results-summary results-secondary-grid">
        <article className="mini-stat">
          <span>Answer Review</span>
          <strong>{resultSummary.answers.length}</strong>
          <p>Questions shown below</p>
        </article>
        <article className="mini-stat">
          <span>Reattempt</span>
          <strong>Available</strong>
          <p>You can reattempt after {resultSummary.reattemptAfter}.</p>
        </article>
      </section>

      <section className="results-list">
        {resultSummary.answers.map((answer, index) => (
          <article key={answer.question} className="result-card">
            <div className="section-heading inline">
              <h3>Question {index + 1}</h3>
              <span className={answer.status === "Correct" ? "result-status correct" : "result-status incorrect"}>
                {answer.status}
              </span>
            </div>
            <p className="result-question">{answer.question}</p>
            <p><strong>Your Answer:</strong> {answer.yourAnswer}</p>
            <p><strong>Correct Answer:</strong> {answer.correctAnswer}</p>
          </article>
        ))}
      </section>

      <section className="results-actions">
        <button className="secondary-btn" type="button" disabled>
          Reattempt in 1 hour
        </button>
        <div className="hero-actions">
          {isPrivateQuiz ? (
            <Link className="secondary-btn button-link" to="/student/leaderboard?type=private">
              Open Leaderboard
            </Link>
          ) : null}
          <Link className="primary-btn button-link" to="/student/dashboard">
            Back to Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}
