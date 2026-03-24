const API_BASE = "/api";
const AUTH_STORAGE_KEY = "quorion-auth-session";

function getAuthToken() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    const session = raw ? JSON.parse(raw) : null;
    return session?.token || null;
  } catch {
    return null;
  }
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.ok === false) {
    const message = data.message || data.error || "Request failed";
    throw new Error(message);
  }

  return data;
}

function buildHeaders(extraHeaders = {}) {
  const token = getAuthToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders
  };
}

export async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: buildHeaders({
      "Content-Type": "application/json"
    }),
    body: JSON.stringify(payload)
  });

  return parseResponse(response);
}

export async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: buildHeaders()
  });
  return parseResponse(response);
}
