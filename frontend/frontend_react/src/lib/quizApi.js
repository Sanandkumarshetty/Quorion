import { getJson, postJson } from "./api";

export function fetchAdminQuizDashboard() {
  return getJson("/quizzes/admin");
}

export function createQuiz(payload) {
  return postJson("/quizzes", payload);
}

export function fetchPublicQuizzes() {
  return getJson("/quizzes/public");
}

export function joinQuiz(payload) {
  return postJson("/quizzes/join", payload);
}

export function fetchQuizDetails(quizId) {
  return getJson(`/quizzes/${quizId}`);
}

export function saveQuizAnswer(quizId, payload) {
  return postJson(`/quizzes/${quizId}/answers`, payload);
}

export function submitQuiz(quizId) {
  return postJson(`/quizzes/${quizId}/submit`, {});
}

export function fetchLeaderboard(quizId) {
  return getJson(`/quizzes/${quizId}/leaderboard`);
}

export function fetchMyResults() {
  return getJson("/results/me");
}

export async function downloadQuizResults(quizId) {
  const raw = typeof window !== "undefined" ? window.localStorage.getItem("quorion-auth-session") : null;
  const session = raw ? JSON.parse(raw) : null;
  const token = session?.token;
  const response = await fetch(`/api/quizzes/${quizId}/results/export`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || data.error || "Unable to download quiz results.");
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const fileNameMatch = disposition.match(/filename="?([^";]+)"?/i);
  const fileName = fileNameMatch?.[1] || `quiz_${quizId}_results.csv`;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}


export function updateQuiz(quizId, payload) {
  return fetch(`/api/quizzes/${quizId}`, {
    method: "PUT",
    headers: (() => {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem("quorion-auth-session") : null;
      const session = raw ? JSON.parse(raw) : null;
      const token = session?.token;
      return {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "Content-Type": "application/json"
      };
    })(),
    body: JSON.stringify(payload)
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.message || data.error || "Unable to update quiz.");
    }
    return data;
  });
}

export function deletePublicQuiz(quizId) {
  return fetch(`/api/quizzes/${quizId}`, {
    method: "DELETE",
    headers: (() => {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem("quorion-auth-session") : null;
      const session = raw ? JSON.parse(raw) : null;
      const token = session?.token;
      return token ? { Authorization: `Bearer ${token}` } : {};
    })()
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.message || data.error || "Unable to delete quiz.");
    }
    return data;
  });
}
