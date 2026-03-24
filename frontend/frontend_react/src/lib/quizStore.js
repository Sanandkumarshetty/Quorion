import { useSyncExternalStore } from "react";

const STORAGE_KEY = "quorion-live-quiz-store";
const STORE_EVENT = "quorion-live-quiz-store-change";
let cachedRaw = null;
let cachedState = null;

function canUseWindow() {
  return typeof window !== "undefined";
}

function createDefaultQuestion(index = 1) {
  return {
    id: `question-${index}`,
    text: `Question ${index}`,
    options: {
      A: "Option A",
      B: "Option B",
      C: "Option C",
      D: "Option D"
    },
    correctKey: "A"
  };
}

function createSeedQuiz() {
  const now = Date.now();
  const durationMinutes = 45;
  const startAt = new Date(now).toISOString();
  const endAt = new Date(now + durationMinutes * 60 * 1000).toISOString();

  return {
    quizId: "QUIZ-DEMO-101",
    title: "Programming Fundamentals Sprint",
    description: "Live practice quiz for dashboard previews.",
    category: "Programming",
    quizType: "private",
    password: "demo123",
    durationMinutes,
    startAt,
    endAt,
    createdAt: startAt,
    createdById: "seed-admin",
    createdByName: "Quorion Admin",
    status: "active",
    questions: [
      {
        id: "question-1",
        text: "Which keyword declares a constant in JavaScript?",
        options: { A: "let", B: "var", C: "const", D: "static" },
        correctKey: "C"
      },
      {
        id: "question-2",
        text: "What does HTML stand for?",
        options: {
          A: "HyperText Markup Language",
          B: "HighText Machine Language",
          C: "Hyper Transfer Markdown Language",
          D: "Hyperlink and Text Markup Logic"
        },
        correctKey: "A"
      }
    ]
  };
}

function createInitialState() {
  return {
    quizzes: [createSeedQuiz()],
    attempts: []
  };
}

function normalizeState(parsed) {
  return {
    quizzes: Array.isArray(parsed?.quizzes) ? parsed.quizzes : [],
    attempts: Array.isArray(parsed?.attempts) ? parsed.attempts : []
  };
}

function readStore() {
  if (!canUseWindow()) {
    return cachedState || createInitialState();
  }

  try {
    let raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const initialState = createInitialState();
      raw = JSON.stringify(initialState);
      window.localStorage.setItem(STORAGE_KEY, raw);
    }

    if (raw === cachedRaw && cachedState) {
      return cachedState;
    }

    const parsed = JSON.parse(raw);
    cachedRaw = raw;
    cachedState = normalizeState(parsed);
    return cachedState;
  } catch {
    const fallback = createInitialState();
    cachedRaw = JSON.stringify(fallback);
    cachedState = fallback;
    return fallback;
  }
}

function writeStore(nextState) {
  if (!canUseWindow()) {
    cachedState = nextState;
    cachedRaw = JSON.stringify(nextState);
    return;
  }

  const serialized = JSON.stringify(nextState);
  cachedRaw = serialized;
  cachedState = nextState;
  window.localStorage.setItem(STORAGE_KEY, serialized);
  window.dispatchEvent(new Event(STORE_EVENT));
}

function updateStore(updater) {
  const currentState = readStore();
  const nextState = updater(currentState);
  writeStore(nextState);
  return nextState;
}

function subscribe(listener) {
  if (!canUseWindow()) {
    return () => {};
  }

  function handleStoreChange() {
    cachedRaw = null;
    cachedState = null;
    listener();
  }

  function handleStorage(event) {
    if (!event.key || event.key === STORAGE_KEY) {
      handleStoreChange();
    }
  }

  window.addEventListener(STORE_EVENT, handleStoreChange);
  window.addEventListener("storage", handleStorage);

  return () => {
    window.removeEventListener(STORE_EVENT, handleStoreChange);
    window.removeEventListener("storage", handleStorage);
  };
}

function createAttempt({ quizId, user }) {
  const timestamp = new Date().toISOString();
  return {
    attemptId: `attempt-${quizId}-${user.user_id}-${Date.now()}`,
    quizId,
    userId: String(user.user_id),
    userName: user.name || "Student User",
    userEmail: user.email || "",
    role: user.role || "student",
    startedAt: timestamp,
    submittedAt: null,
    lastAnsweredAt: null,
    status: "in_progress",
    answers: {},
    score: 0,
    progressCount: 0
  };
}

function normalizeQuizStatus(quiz) {
  const now = Date.now();
  const start = new Date(quiz.startAt).getTime();
  const end = new Date(quiz.endAt).getTime();

  if (Number.isFinite(end) && end <= now) {
    return "ended";
  }

  if (Number.isFinite(start) && start > now) {
    return "scheduled";
  }

  return "active";
}

function calculateScore(quiz, answers) {
  return quiz.questions.reduce((score, question) => {
    return score + (answers?.[question.id] === question.correctKey ? 1 : 0);
  }, 0);
}

function sanitizeQuestions(questions) {
  const prepared = Array.isArray(questions) && questions.length ? questions : [createDefaultQuestion(1)];
  return prepared.map((question, index) => ({
    id: question.id || `question-${index + 1}`,
    text: question.text?.trim() || `Question ${index + 1}`,
    options: {
      A: question.options?.A?.trim() || "Option A",
      B: question.options?.B?.trim() || "Option B",
      C: question.options?.C?.trim() || "Option C",
      D: question.options?.D?.trim() || "Option D"
    },
    correctKey: ["A", "B", "C", "D"].includes(question.correctKey) ? question.correctKey : "A"
  }));
}

export function useQuizStoreSnapshot() {
  return useSyncExternalStore(subscribe, readStore, readStore);
}

export function getQuizStoreSnapshot() {
  return readStore();
}

export function createQuiz({ form, user }) {
  const createdAt = new Date().toISOString();
  const durationMinutes = Math.max(1, Number(form.durationMinutes) || 30);
  const startAt = form.startAt || createdAt;
  const endAt = new Date(new Date(startAt).getTime() + durationMinutes * 60 * 1000).toISOString();
  const quizType = form.quizType === "public" ? "public" : "private";
  const generatedId = form.quizId?.trim() || `QUIZ-${Date.now().toString().slice(-6)}`;
  const nextQuiz = {
    quizId: generatedId,
    title: form.title?.trim() || "Untitled Quiz",
    description: form.description?.trim() || "",
    category: form.category?.trim() || "General Knowledge",
    quizType,
    password: quizType === "private" ? form.password?.trim() || "quiz123" : "",
    durationMinutes,
    startAt,
    endAt,
    createdAt,
    createdById: String(user?.user_id || "admin"),
    createdByName: user?.name || "Admin User",
    status: "active",
    questions: sanitizeQuestions(form.questions)
  };

  updateStore((currentState) => ({
    ...currentState,
    quizzes: [nextQuiz, ...currentState.quizzes.filter((quiz) => quiz.quizId !== nextQuiz.quizId)]
  }));

  return nextQuiz;
}

export function getQuizById(quizId) {
  if (!quizId) {
    return null;
  }

  const store = readStore();
  return store.quizzes.find((quiz) => quiz.quizId === quizId) || null;
}

export function getQuizByCredentials({ quizId, password }) {
  if (!quizId) {
    return null;
  }

  const quiz = getQuizById(String(quizId).trim());
  if (!quiz) {
    return null;
  }

  if (quiz.quizType === "private" && quiz.password !== String(password || "").trim()) {
    return null;
  }

  return quiz;
}

export function ensureQuizAttempt({ quizId, user }) {
  if (!quizId || !user?.user_id || user?.role === "admin") {
    return null;
  }

  const store = updateStore((currentState) => {
    const existingAttempt = currentState.attempts.find(
      (attempt) => attempt.quizId === quizId && String(attempt.userId) === String(user.user_id)
    );

    if (existingAttempt) {
      return currentState;
    }

    return {
      ...currentState,
      attempts: [...currentState.attempts, createAttempt({ quizId, user })]
    };
  });

  return store.attempts.find(
    (attempt) => attempt.quizId === quizId && String(attempt.userId) === String(user.user_id)
  ) || null;
}

export function saveQuizAnswer({ quizId, user, questionId, selectedKey }) {
  if (!quizId || !user?.user_id || !questionId || !selectedKey || user?.role === "admin") {
    return null;
  }

  const quiz = getQuizById(quizId);
  if (!quiz) {
    return null;
  }

  const timestamp = new Date().toISOString();
  const nextState = updateStore((currentState) => {
    let foundAttempt = false;
    const nextAttempts = currentState.attempts.map((attempt) => {
      if (attempt.quizId !== quizId || String(attempt.userId) !== String(user.user_id)) {
        return attempt;
      }

      foundAttempt = true;
      const nextAnswers = { ...(attempt.answers || {}), [questionId]: selectedKey };
      return {
        ...attempt,
        answers: nextAnswers,
        score: calculateScore(quiz, nextAnswers),
        progressCount: Object.keys(nextAnswers).length,
        lastAnsweredAt: timestamp,
        status: "in_progress"
      };
    });

    if (foundAttempt) {
      return { ...currentState, attempts: nextAttempts };
    }

    const createdAttempt = createAttempt({ quizId, user });
    const nextAnswers = { [questionId]: selectedKey };

    return {
      ...currentState,
      attempts: [
        ...currentState.attempts,
        {
          ...createdAttempt,
          answers: nextAnswers,
          score: calculateScore(quiz, nextAnswers),
          progressCount: 1,
          lastAnsweredAt: timestamp
        }
      ]
    };
  });

  return nextState.attempts.find(
    (attempt) => attempt.quizId === quizId && String(attempt.userId) === String(user.user_id)
  ) || null;
}

export function submitQuizAttempt({ quizId, user }) {
  if (!quizId || !user?.user_id || user?.role === "admin") {
    return null;
  }

  const quiz = getQuizById(quizId);
  if (!quiz) {
    return null;
  }

  const timestamp = new Date().toISOString();
  const nextState = updateStore((currentState) => ({
    ...currentState,
    attempts: currentState.attempts.map((attempt) => {
      if (attempt.quizId !== quizId || String(attempt.userId) !== String(user.user_id)) {
        return attempt;
      }

      return {
        ...attempt,
        submittedAt: timestamp,
        lastAnsweredAt: attempt.lastAnsweredAt || timestamp,
        score: calculateScore(quiz, attempt.answers || {}),
        progressCount: Object.keys(attempt.answers || {}).length,
        status: "submitted"
      };
    })
  }));

  return nextState.attempts.find(
    (attempt) => attempt.quizId === quizId && String(attempt.userId) === String(user.user_id)
  ) || null;
}

export function getQuizTimeLeft(quiz) {
  if (!quiz?.endAt) {
    return "00:00";
  }

  const end = new Date(quiz.endAt).getTime();
  const remainingMs = Math.max(0, end - Date.now());
  const totalSeconds = Math.floor(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function getQuizLiveSummary(quizId, viewerUserId) {
  const quiz = getQuizById(quizId);
  const store = readStore();

  if (!quiz) {
    return {
      quiz: null,
      leaderboard: [],
      submissionCount: 0,
      participantCount: 0,
      viewerRank: null
    };
  }

  const attempts = store.attempts
    .filter((attempt) => attempt.quizId === quizId && attempt.role !== "admin")
    .map((attempt) => ({
      ...attempt,
      score: Number(attempt.score) || 0,
      progressCount: Number(attempt.progressCount) || 0
    }))
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      if (right.progressCount !== left.progressCount) {
        return right.progressCount - left.progressCount;
      }

      const leftTime = new Date(left.lastAnsweredAt || left.submittedAt || left.startedAt).getTime();
      const rightTime = new Date(right.lastAnsweredAt || right.submittedAt || right.startedAt).getTime();
      return leftTime - rightTime;
    });

  const leaderboard = attempts.map((attempt, index) => ({
    rank: index + 1,
    name: attempt.userName,
    userId: attempt.userId,
    score: attempt.score,
    totalQuestions: quiz.questions.length,
    completion: attempt.submittedAt ? "Completed" : `${attempt.progressCount}/${quiz.questions.length} answered`,
    status: String(attempt.userId) === String(viewerUserId) ? "Current User" : attempt.submittedAt ? "Submitted" : "Live"
  }));

  const viewerRow = leaderboard.find((row) => String(row.userId) === String(viewerUserId));

  return {
    quiz: { ...quiz, status: normalizeQuizStatus(quiz) },
    leaderboard,
    submissionCount: attempts.filter((attempt) => attempt.status === "submitted").length,
    participantCount: attempts.length,
    viewerRank: viewerRow?.rank || null
  };
}

export function canStudentOpenLeaderboard({ quizId, userId }) {
  if (!quizId || !userId) {
    return false;
  }

  const store = readStore();
  return store.attempts.some(
    (attempt) =>
      attempt.quizId === quizId &&
      String(attempt.userId) === String(userId) &&
      attempt.status === "submitted"
  );
}

export function getCreatedQuizzesForAdmin(adminUserId) {
  const store = readStore();
  return store.quizzes
    .filter((quiz) => String(quiz.createdById) === String(adminUserId) || adminUserId == null)
    .map((quiz) => {
      const summary = getQuizLiveSummary(quiz.quizId);
      return {
        ...quiz,
        status: normalizeQuizStatus(quiz),
        participantCount: summary.participantCount,
        submissionCount: summary.submissionCount
      };
    })
    .sort((left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime());
}

export function formatQuizDate(value) {
  if (!value) {
    return "Not scheduled";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not scheduled";
  }

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}
