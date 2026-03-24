import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { fetchQuizDetails, saveQuizAnswer, submitQuiz } from "../lib/quizApi";

function getInitials(name) {
  return (name || "Student User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "SU";
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

export default function QuizSessionPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const quizId = searchParams.get("quizId") || "";
  const [quiz, setQuiz] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [, setTick] = useState(0);
  const autoSubmitStartedRef = useRef(false);

  function navigateAfterSubmit(result, quizTypeOverride) {
    const activeQuizType = quizTypeOverride || quiz?.quizType;
    if (activeQuizType === "private") {
      navigate(`/student/leaderboard?quizId=${encodeURIComponent(result.quizId || quizId)}&attempt=${encodeURIComponent(result.attemptId)}`, { replace: true });
      return;
    }
    navigate(`/student/results?attempt=${encodeURIComponent(result.attemptId)}&type=${encodeURIComponent(activeQuizType || "public")}`, { replace: true });
  }

  useEffect(() => {
    autoSubmitStartedRef.current = false;
  }, [quizId]);

  useEffect(() => {
    let active = true;

    async function loadQuiz() {
      try {
        const response = await fetchQuizDetails(quizId);
        if (!active) {
          return;
        }

        if (response.submission?.completed || response.canAttempt === false) {
          if (response.quiz?.quizType === "private") {
            navigate(`/student/leaderboard?quizId=${encodeURIComponent(quizId)}`, { replace: true });
          } else if (response.submission?.attemptId) {
            navigateAfterSubmit(response.submission, response.quiz?.quizType);
          } else {
            navigate("/student/dashboard", { replace: true });
          }
          return;
        }

        if (response.requiresWaitingRoom) {
          navigate(`/student/waiting-room?quizId=${encodeURIComponent(quizId)}`, { replace: true, state: { quiz: response.quiz, submission: response.submission } });
          return;
        }

        setQuiz(response.quiz);
        setSubmission(response.submission);
        setError("");
      } catch (requestError) {
        if (!active) {
          return;
        }
        const message = requestError.message || "Unable to load quiz.";
        if (message.includes("ended")) {
          navigate("/student/dashboard", { replace: true });
          return;
        }
        setError(message);
      }
    }

    loadQuiz();
    return () => {
      active = false;
    };
  }, [navigate, quizId]);

  useEffect(() => {
    if (!quiz?.endAt || submission?.completed) {
      return undefined;
    }

    const timer = window.setInterval(async () => {
      setTick((value) => value + 1);
      if (autoSubmitStartedRef.current) {
        return;
      }
      if (new Date(quiz.endAt).getTime() > Date.now()) {
        return;
      }

      autoSubmitStartedRef.current = true;
      try {
        const response = await submitQuiz(quiz.quizId);
        navigateAfterSubmit(response.result, quiz.quizType);
      } catch (requestError) {
        const message = requestError.message || "";
        if (message.includes("already submitted") || message.includes("ended")) {
          try {
            const latestResponse = await fetchQuizDetails(quiz.quizId);
            if (latestResponse.submission?.completed) {
              navigateAfterSubmit(latestResponse.submission, quiz.quizType);
              return;
            }
          } catch {
            // Ignore follow-up fetch errors and fall back to the dashboard.
          }
          navigate("/student/dashboard", { replace: true });
          return;
        }
        setError(message || "Unable to auto-submit this quiz.");
        autoSubmitStartedRef.current = false;
      }
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, [navigate, quiz, submission?.completed]);

  if (!quiz) {
    return <div className="canvas"><section className="leaderboard-locked-state"><h1>Loading quiz...</h1><p>{error || "Please wait while we load the quiz session."}</p></section></div>;
  }

  const questions = quiz.questions || [];
  const currentQuestion = questions[currentQuestionIndex] || questions[0];
  const selectedOption = submission?.answers?.[String(currentQuestion?.questionId)] || "";
  const canGoPrev = currentQuestionIndex > 0;
  const canGoNext = currentQuestionIndex < questions.length - 1;

  async function handleSelectOption(key) {
    if (selectedOption === key) {
      return;
    }

    try {
      const response = await saveQuizAnswer(quiz.quizId, { questionId: currentQuestion.questionId, selectedOption: key });
      setSubmission(response.submission);
      setError("");
    } catch (requestError) {
      const message = requestError.message || "";
      if (message.includes("already submitted")) {
        navigate(quiz.quizType === "private" ? `/student/leaderboard?quizId=${encodeURIComponent(quiz.quizId)}` : "/student/dashboard", { replace: true });
        return;
      }
      if (message.includes("has not started yet")) {
        navigate(`/student/waiting-room?quizId=${encodeURIComponent(quiz.quizId)}`, { replace: true, state: { quiz, submission } });
        return;
      }
      if (message.includes("ended")) {
        autoSubmitStartedRef.current = true;
        try {
          const latestResponse = await fetchQuizDetails(quiz.quizId);
          if (latestResponse.submission?.completed) {
            navigateAfterSubmit(latestResponse.submission, quiz.quizType);
            return;
          }
        } catch {
          // Ignore follow-up fetch errors and fall back to the dashboard.
        }
        navigate("/student/dashboard", { replace: true });
        return;
      }
      setError(message || "Unable to save your answer.");
    }
  }

  async function handleConfirmSubmit() {
    try {
      const response = await submitQuiz(quiz.quizId);
      navigateAfterSubmit(response.result, quiz.quizType);
    } catch (requestError) {
      const message = requestError.message || "";
      if (message.includes("already submitted")) {
        navigate(quiz.quizType === "private" ? `/student/leaderboard?quizId=${encodeURIComponent(quiz.quizId)}` : "/student/dashboard", { replace: true });
        return;
      }
      if (message.includes("has not started yet")) {
        navigate(`/student/waiting-room?quizId=${encodeURIComponent(quiz.quizId)}`, { replace: true, state: { quiz, submission } });
        return;
      }
      if (message.includes("ended")) {
        try {
          const latestResponse = await fetchQuizDetails(quiz.quizId);
          if (latestResponse.submission?.completed) {
            navigateAfterSubmit(latestResponse.submission, quiz.quizType);
            return;
          }
        } catch {
          // Ignore follow-up fetch errors and fall back to the dashboard.
        }
        navigate("/student/dashboard", { replace: true });
        return;
      }
      setError(message || "Unable to submit this quiz.");
    }
  }

  return (
    <div className="canvas quiz-canvas reverse-quiz-layout">
      <div className="quiz-content">
        <TopNav
          brand="QuizFlow"
          homeTo="/student/dashboard"
          compact
          links={[{ label: "Dashboard", to: "/student/dashboard" }]}
          profile={{ initials: getInitials(user?.name), name: user?.name || "Student User", subtitle: user?.email || "student@example.com" }}
        />
        <section className="quiz-question-card">
          <div className="section-heading inline">
            <div>
              <p className="question-index">Question {currentQuestionIndex + 1} / {questions.length}</p>
              <h2>{quiz.title}</h2>
            </div>
            <span>{quiz.category}</span>
          </div>
          <h3 className="question-text">{currentQuestion?.text}</h3>
          <div className="answer-list">
            {Object.entries(currentQuestion?.options || {}).map(([key, option]) => (
              <button key={key} className={selectedOption === key ? "answer-option selected" : "answer-option"} onClick={() => handleSelectOption(key)} type="button">
                <span className="answer-badge">{key}</span>{option}
              </button>
            ))}
          </div>
          <div className="section-heading inline">
            <button className="secondary-btn" disabled={!canGoPrev} onClick={() => setCurrentQuestionIndex((value) => Math.max(0, value - 1))} type="button">Previous</button>
            <button className="primary-btn small" disabled={!canGoNext} onClick={() => setCurrentQuestionIndex((value) => Math.min(questions.length - 1, value + 1))} type="button">Next</button>
          </div>
          <p className="helper-copy">Answers are saved live to the backend until the timer ends. Public quizzes auto-submit at timeout.</p>
          {error ? <div className="form-alert error">{error}</div> : null}
        </section>
      </div>

      <aside className="quiz-sidebar">
        <div className="timer-panel"><span>Time Remaining</span><strong>{getTimeLeft(quiz.endAt)}</strong></div>
        <div className="question-nav">
          <span>Questions</span>
          <div className="question-grid">
            {questions.map((question, index) => (
              <button key={question.questionId} className={index === currentQuestionIndex ? "question-pill active" : submission?.answers?.[String(question.questionId)] ? "question-pill answered" : "question-pill"} onClick={() => setCurrentQuestionIndex(index)} type="button">{index + 1}</button>
            ))}
          </div>
        </div>
        <div className="legend">
          <div><span className="legend-dot current"></span> Current question</div>
          <div><span className="legend-dot answered"></span> Answer saved</div>
          <div><span className="legend-dot"></span> Not answered</div>
        </div>
        <button className="primary-btn" onClick={() => setShowConfirm(true)} type="button">Submit Quiz</button>
      </aside>

      {showConfirm ? (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Submit your quiz?</h3>
            <p>This will finalize your score in the backend and unlock the leaderboard if this is a private quiz.</p>
            <div className="dual-actions">
              <button className="secondary-btn" onClick={() => setShowConfirm(false)} type="button">Cancel</button>
              <button className="primary-btn" onClick={handleConfirmSubmit} type="button">Confirm Submit</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
