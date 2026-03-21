const API_BASE = "/api";

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.ok === false) {
    const message = data.error || data.message || "Request failed";
    throw new Error(message);
  }

  return data;
}

export async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse(response);
}

export async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  return parseResponse(response);
}
