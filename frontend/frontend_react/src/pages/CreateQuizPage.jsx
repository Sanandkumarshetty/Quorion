import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import TopNav from "../components/TopNav";
import { createQuiz, fetchAdminQuizDashboard, updateQuiz } from "../lib/quizApi";

function getInitials(name) {
  return (name || "Admin User")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "AD";
}

function formatDateTimeLocal(value = new Date()) {
  const date = value instanceof Date ? value : new Date(value);
  const offset = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function createQuestion(index) {
  return {
    id: `question-${index + 1}`,
    text: "",
    options: { A: "", B: "", C: "", D: "" },
    correctAnswer: "A"
  };
}

export default function CreateQuizPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const editQuizId = searchParams.get("quizId");
  const isEditMode = searchParams.get("mode") === "edit" && Boolean(editQuizId);
  const [form, setForm] = useState({
    title: "",
    category: "Programming",
    quizType: "private",
    password: "",
    durationMinutes: 30,
    startAt: formatDateTimeLocal(),
    questions: [createQuestion(0)]
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadQuizForEdit() {
      if (!isEditMode) {
        return;
      }
      try {
        const response = await fetchAdminQuizDashboard();
        const quiz = (response.quizzes || []).find((item) => String(item.quizId) === String(editQuizId));
        if (!active || !quiz) {
          return;
        }
        setForm({
          title: quiz.title,
          category: quiz.category,
          quizType: quiz.quizType,
          password: quiz.password || "",
          durationMinutes: quiz.durationMinutes,
          startAt: quiz.startAt ? formatDateTimeLocal(quiz.startAt) : formatDateTimeLocal(),
          questions: (quiz.questions || []).map((question, index) => ({
            id: question.questionId || `question-${index + 1}`,
            text: question.text,
            options: question.options,
            correctAnswer: question.correctAnswer || "A"
          }))
        });
      } catch (requestError) {
        if (active) {
          setError(requestError.message || "Unable to load quiz for editing.");
        }
      }
    }

    loadQuizForEdit();
    return () => {
      active = false;
    };
  }, [editQuizId, isEditMode]);

  function handleLogout() {
    logout();
    navigate("/");
  }

  function updateQuestion(index, updater) {
    setForm((current) => ({
      ...current,
      questions: current.questions.map((question, questionIndex) => (questionIndex === index ? updater(question) : question))
    }));
  }

  async function handlePublishQuiz() {
    setLoading(true);
    setError("");
    try {
      const response = isEditMode ? await updateQuiz(editQuizId, form) : await createQuiz(form);
      navigate(`/admin/dashboard?quizId=${encodeURIComponent(response.quiz.quizId)}`);
    } catch (requestError) {
      setError(requestError.message || `Unable to ${isEditMode ? "update" : "create"} quiz.`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="canvas">
      <TopNav
        brand="QuizBuilder"
        homeTo="/admin/dashboard"
        links={[
          { label: "Dashboard", to: "/admin/dashboard" },
          { label: isEditMode ? "Modify Quiz" : "Create Quiz", to: isEditMode ? `/admin/create-quiz?quizId=${encodeURIComponent(editQuizId)}&mode=edit` : "/admin/create-quiz" }
        ]}
        actions={<button className="secondary-btn" onClick={handleLogout} type="button">Logout</button>}
        profile={{ initials: getInitials(user?.name), name: user?.name || "Admin User", subtitle: user?.email || "Quiz Manager" }}
      />

      <section className="page-header left">
        <div>
          <h1>{isEditMode ? "Modify Public Quiz" : "Configure New Quiz"}</h1>
          <p>{isEditMode ? "Update this public quiz without changing the rest of your current admin workflow." : "Create a real quiz room with timing, questions, and access control backed by the database."}</p>
        </div>
      </section>

      <section className="create-layout">
        <article className="panel">
          <h3>Quiz Type</h3>
          <button className={form.quizType === "private" ? "radio-card selected radio-card-button" : "radio-card radio-card-button"} disabled={isEditMode} onClick={() => setForm((current) => ({ ...current, quizType: "private" }))} type="button">
            <input type="radio" checked={form.quizType === "private"} readOnly />
            <div><strong>Private Quiz</strong><span>Requires ID and password</span></div>
          </button>
          <button className={form.quizType === "public" ? "radio-card selected radio-card-button" : "radio-card radio-card-button"} disabled={isEditMode} onClick={() => setForm((current) => ({ ...current, quizType: "public" }))} type="button">
            <input type="radio" checked={form.quizType === "public"} readOnly />
            <div><strong>Public Quiz</strong><span>Visible on the student dashboard</span></div>
          </button>
          {isEditMode ? <small className="helper-copy">Only public quizzes can be modified here from the dashboard.</small> : null}
        </article>

        <article className="panel wide">
          <h3>Configuration</h3>
          <div className="form-grid">
            <label className="field">
              <span>Quiz Title</span>
              <input onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} value={form.title} />
            </label>
            <label className="field">
              <span>Category</span>
              <input onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))} value={form.category} />
            </label>
            {form.quizType === "private" ? (
              <label className="field">
                <span>Quiz Password</span>
                <input onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} value={form.password} />
              </label>
            ) : null}
            <label className="field">
              <span>Duration (Minutes)</span>
              <input min="1" onChange={(event) => setForm((current) => ({ ...current, durationMinutes: event.target.value }))} type="number" value={form.durationMinutes} />
            </label>
            <label className="field">
              <span>Date and Time</span>
              <input onChange={(event) => setForm((current) => ({ ...current, startAt: event.target.value }))} type="datetime-local" value={form.startAt} />
            </label>
          </div>
        </article>
      </section>

      <section className="question-builder">
        <div className="section-heading inline">
          <h2>Questions</h2>
          <button className="primary-btn small" onClick={() => setForm((current) => ({ ...current, questions: [...current.questions, createQuestion(current.questions.length)] }))} type="button">
            Add Question
          </button>
        </div>

        {form.questions.map((question, index) => (
          <article key={question.id} className="question-editor">
            <label className="field">
              <span>Question {index + 1}</span>
              <textarea onChange={(event) => updateQuestion(index, (current) => ({ ...current, text: event.target.value }))} rows="4" value={question.text} />
            </label>
            <div className="form-grid">
              {Object.keys(question.options).map((key) => (
                <label key={key} className="field">
                  <span>{`Option ${key}`}</span>
                  <input onChange={(event) => updateQuestion(index, (current) => ({ ...current, options: { ...current.options, [key]: event.target.value } }))} value={question.options[key]} />
                </label>
              ))}
            </div>
            <div className="section-heading inline">
              <label className="field compact-field">
                <span>Correct Answer</span>
                <select onChange={(event) => updateQuestion(index, (current) => ({ ...current, correctAnswer: event.target.value }))} value={question.correctAnswer}>
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                  <option value="D">D</option>
                </select>
              </label>
              {form.questions.length > 1 ? <button className="secondary-btn small" onClick={() => setForm((current) => ({ ...current, questions: current.questions.filter((_, questionIndex) => questionIndex !== index) }))} type="button">Remove</button> : <span className="muted-label">Hidden from students</span>}
            </div>
          </article>
        ))}

        {error ? <div className="form-alert error">{error}</div> : null}
        <div className="builder-actions">
          <Link className="secondary-btn button-link" to="/admin/dashboard">Back to Dashboard</Link>
          <button className="primary-btn" disabled={loading} onClick={handlePublishQuiz} type="button">{loading ? (isEditMode ? "Saving..." : "Publishing...") : (isEditMode ? "Save Changes" : "Publish Quiz")}</button>
        </div>
      </section>
    </div>
  );
}
