import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { fetchMyResults } from "../lib/quizApi";

function getInitials(name) {
  return (name || "Student User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "SU";
}

function formatSubmittedAt(value) {
  if (!value) {
    return "Recently";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Recently" : date.toLocaleString();
}


function PublicReviewSection({ result }) {
  if (!result?.review?.length) {
    return null;
  }

  return (
    <section className="results-group-card">
      <div className="section-heading inline">
        <div>
          <h2>Public Quiz Answer Review</h2>
          <p>Correct answers and your selected options are shown here after the quiz is completed.</p>
        </div>
        <span className="badge">{result.review.length} questions</span>
      </div>
      <div className="results-history-grid">
        {result.review.map((item, index) => (
          <article key={item.questionId} className="result-card">
            <div className="section-heading inline">
              <div>
                <h3>{`Question ${index + 1}`}</h3>
                <p className="result-question">{item.question}</p>
              </div>
              <span className={item.selectedOption === item.correctAnswer ? "result-status correct" : "result-status incorrect"}>
                {item.selectedOption === item.correctAnswer ? "Correct" : "Review"}
              </span>
            </div>
            <div className="results-history-grid">
              {Object.entries(item.options).map(([key, value]) => (
                <div key={key} className="quiz-row">
                  <div>
                    <h3>{`${key}. ${value}`}</h3>
                    <p>
                      {item.selectedOption === key ? "Your answer" : ""}
                      {item.selectedOption === key && item.correctAnswer === key ? " - Correct answer" : ""}
                      {item.selectedOption !== key && item.correctAnswer === key ? "Correct answer" : ""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ResultSection({ title, description, results, emptyMessage, latestAttemptId }) {
  return (
    <section className="results-group-card">
      <div className="section-heading inline"><div><h2>{title}</h2><p>{description}</p></div><span className="badge">{results.length} attended</span></div>
      {results.length ? (
        <div className="results-history-grid">
          {results.map((result) => (
            <article key={result.attemptId} className="result-card">
              <div className="section-heading inline">
                <div><h3>{result.quizTitle}</h3><p className="result-question">Quiz ID: {result.quizId}</p></div>
                <div className="result-card-side"><span className="result-type-pill">{result.quizType}</span>{result.attemptId === latestAttemptId ? <span className="badge">Latest</span> : null}</div>
              </div>
              <div className="result-meta-grid">
                <div><span className="muted-label">Score</span><strong>{result.score}/{result.totalQuestions}</strong></div>
                <div><span className="muted-label">Accuracy</span><strong>{result.percentage}%</strong></div>
                <div><span className="muted-label">Submitted</span><strong>{formatSubmittedAt(result.submittedAt)}</strong></div>
              </div>
            </article>
          ))}
        </div>
      ) : <article className="result-card empty-results-state"><h3>No quizzes attended yet</h3><p>{emptyMessage}</p></article>}
    </section>
  );
}

export default function QuizResultPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const latestAttemptId = searchParams.get("attempt");
  const [results, setResults] = useState([]);

  useEffect(() => {
    let active = true;
    fetchMyResults().then((response) => {
      if (active) {
        setResults(response.results || []);
      }
    }).catch(() => {
      if (active) {
        setResults([]);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!latestAttemptId) {
      return undefined;
    }

    window.history.pushState(null, "", window.location.href);
    const handlePopState = () => {
      navigate("/student/dashboard", { replace: true });
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, [latestAttemptId, navigate]);

  const groupedResults = useMemo(() => ({
    public: results.filter((result) => result.quizType === "public"),
    private: results.filter((result) => result.quizType === "private")
  }), [results]);
  const latestResult = latestAttemptId ? results.find((result) => String(result.attemptId) === String(latestAttemptId)) || results[0] : results[0];

  return (
    <div className="canvas">
      <TopNav
        brand="QuizResults"
        homeTo="/student/dashboard"
        links={[{ label: "Dashboard", to: "/student/dashboard" }]}
        profile={{ initials: getInitials(user?.name), name: user?.name || "Student User", subtitle: user?.email || "Student Review" }}
      />

      <section className="results-summary">
        <div>
          <span className="badge">My Results</span>
          <h1>Attended Quiz Scores</h1>
          <p>Only the quizzes you attended are shown here. These results are now loaded from the backend submissions table.</p>
        </div>
        <div className="results-score-card">
          <span>{latestResult ? "Latest Score" : "Results"}</span>
          <strong>{latestResult ? `${latestResult.score}/${latestResult.totalQuestions}` : "0/0"}</strong>
          <p>{latestResult ? `${latestResult.percentage}% in ${latestResult.quizTitle}` : "Attend a quiz to see your score here."}</p>
        </div>
      </section>

      <section className="results-summary results-secondary-grid">
        <article className="mini-stat"><span>Total Attended</span><strong>{results.length}</strong><p>Only your own submissions are visible</p></article>
        <article className="mini-stat"><span>Public / Private</span><strong>{groupedResults.public.length} / {groupedResults.private.length}</strong><p>Scores are divided by quiz type</p></article>
      </section>

      <div className="results-collection">
        <ResultSection title="Public Quiz Results" description="Scores from the public quizzes you have attended." results={groupedResults.public} emptyMessage="Your public quiz scores will appear here after you complete a public quiz." latestAttemptId={latestAttemptId} />
        <ResultSection title="Private Quiz Results" description="Scores from the private quizzes you have attended." results={groupedResults.private} emptyMessage="Your private quiz scores will appear here after you complete a private quiz." latestAttemptId={latestAttemptId} />
        <PublicReviewSection result={latestResult?.quizType === "public" ? latestResult : null} />
      </div>

      <section className="results-actions">
        <Link className="secondary-btn button-link" to="/student/dashboard">Browse Quizzes</Link>
        <Link className="primary-btn button-link" to="/student/dashboard">Back to Dashboard</Link>
      </section>
    </div>
  );
}
