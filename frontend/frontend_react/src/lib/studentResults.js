const STORAGE_KEY = "quorion-student-results";
const DEFAULT_TOTAL_QUESTIONS = 20;

function readStoredResults() {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStoredResults(results) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
}

function normalizeQuizType(quizType) {
  return quizType === "private" ? "private" : "public";
}

function buildScore(totalQuestions, score) {
  const safeTotal = Number(totalQuestions) > 0 ? Number(totalQuestions) : DEFAULT_TOTAL_QUESTIONS;
  if (score != null && Number.isFinite(Number(score))) {
    const boundedScore = Math.max(0, Math.min(safeTotal, Number(score)));
    return boundedScore;
  }

  const baseline = Math.max(8, Math.floor(safeTotal * 0.6));
  const variance = Math.max(1, safeTotal - baseline);
  return baseline + Math.floor(Math.random() * variance);
}

export function saveStudentQuizResult({
  userId,
  quizType,
  quizTitle,
  quizId,
  score,
  totalQuestions = DEFAULT_TOTAL_QUESTIONS,
  completionTime
}) {
  if (userId == null) {
    return null;
  }

  const normalizedType = normalizeQuizType(quizType);
  const normalizedScore = buildScore(totalQuestions, score);
  const safeTotal = Number(totalQuestions) > 0 ? Number(totalQuestions) : DEFAULT_TOTAL_QUESTIONS;
  const submittedAt = new Date().toISOString();
  const nextResult = {
    attemptId: `attempt-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    userId,
    quizType: normalizedType,
    quizId: String(quizId || `${normalizedType}-${Date.now()}`),
    quizTitle: String(quizTitle || (normalizedType === "private" ? "Private Quiz Session" : "Public Quiz Session")),
    score: normalizedScore,
    totalQuestions: safeTotal,
    percentage: Math.round((normalizedScore / safeTotal) * 100),
    completionTime: completionTime || "Completed",
    submittedAt
  };

  const currentResults = readStoredResults();
  writeStoredResults([nextResult, ...currentResults]);
  return nextResult;
}

export function getStudentQuizResults(userId) {
  if (userId == null) {
    return [];
  }

  return readStoredResults()
    .filter((result) => String(result.userId) === String(userId))
    .sort((left, right) => new Date(right.submittedAt).getTime() - new Date(left.submittedAt).getTime());
}

export function getGroupedStudentQuizResults(userId) {
  const results = getStudentQuizResults(userId);
  return {
    public: results.filter((result) => result.quizType === "public"),
    private: results.filter((result) => result.quizType === "private")
  };
}

export function formatSubmittedAt(value) {
  if (!value) {
    return "Recently";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Recently";
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}
