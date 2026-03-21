import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import TopNav from "../components/TopNav";
import { questions } from "../data/mockData";

const options = [
  "Nucleus",
  "Mitochondria",
  "Endoplasmic Reticulum",
  "Golgi Apparatus"
];

export default function QuizSessionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const quizType = searchParams.get("type") === "private" ? "private" : "public";
  const isPrivateQuiz = quizType === "private";
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [selectedOption, setSelectedOption] = useState("B");
  const [showConfirm, setShowConfirm] = useState(false);

  const canGoPrev = currentQuestion > 1;
  const canGoNext = currentQuestion < questions.length;

  return (
    <div className="canvas quiz-canvas reverse-quiz-layout">
      <div className="quiz-content">
        <TopNav
          brand="QuizFlow"
          homeTo="/student/dashboard"
          compact
          links={[
            { label: "Dashboard", to: "/student/dashboard" },
            ...(isPrivateQuiz ? [{ label: "Leaderboard", to: "/student/leaderboard?type=private" }] : [])
          ]}
          profile={{ initials: "SJ", name: "Sarah Johnson", subtitle: "Student ID: 1031-1234" }}
        />
        <section className="quiz-question-card">
          <div className="section-heading inline">
            <div>
              <p className="question-index">Question {currentQuestion} / {questions.length}</p>
              <h2>{isPrivateQuiz ? "Private Quiz Session" : "Public Quiz Session"}</h2>
            </div>
            <span>5 points</span>
          </div>
          <h3 className="question-text">
            Which of the following cellular organelles is responsible for producing ATP through cellular respiration?
          </h3>
          <div className="answer-list">
            {options.map((option, index) => {
              const key = String.fromCharCode(65 + index);
              return (
                <button
                  key={option}
                  className={selectedOption === key ? "answer-option selected" : "answer-option"}
                  onClick={() => setSelectedOption(key)}
                  type="button"
                >
                  <span className="answer-badge">{key}</span>
                  {option}
                </button>
              );
            })}
          </div>
          <div className="section-heading inline">
            <button
              className="secondary-btn"
              disabled={!canGoPrev}
              onClick={() => setCurrentQuestion((value) => Math.max(1, value - 1))}
              type="button"
            >
              Previous
            </button>
            <button
              className="primary-btn small"
              disabled={!canGoNext}
              onClick={() => setCurrentQuestion((value) => Math.min(questions.length, value + 1))}
              type="button"
            >
              Next
            </button>
          </div>
          <p className="helper-copy">Select your answer and click Next to continue.</p>
        </section>
      </div>

      <aside className="quiz-sidebar">
        <div className="timer-panel">
          <span>Time Remaining</span>
          <strong>45:30</strong>
        </div>
        <div className="question-nav">
          <span>Questions</span>
          <div className="question-grid">
            {questions.map((question) => (
              <button
                key={question}
                className={question === currentQuestion ? "question-pill active" : "question-pill"}
                onClick={() => setCurrentQuestion(question)}
                type="button"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
        <div className="legend">
          <div><span className="legend-dot current"></span> Current question</div>
          <div><span className="legend-dot"></span> Not answered</div>
        </div>
        <button className="primary-btn" onClick={() => setShowConfirm(true)} type="button">Submit Quiz</button>
        {isPrivateQuiz ? (
          <button className="secondary-btn" onClick={() => navigate("/student/leaderboard?type=private")} type="button">
            Leaderboard
          </button>
        ) : null}
      </aside>

      {showConfirm ? (
        <div className="modal-backdrop">
          <div className="modal-card">
            <h3>Submit your quiz?</h3>
            <p>
              This demo will take you to the answer review page with score details.
              {isPrivateQuiz ? " Private quizzes can also open the leaderboard from the results screen." : " Public quizzes do not show leaderboard access."}
            </p>
            <div className="dual-actions">
              <button className="secondary-btn" onClick={() => setShowConfirm(false)} type="button">Cancel</button>
              <button className="primary-btn" onClick={() => navigate(`/student/results?type=${quizType}`)} type="button">Confirm Submit</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
