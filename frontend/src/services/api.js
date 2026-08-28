// EchoScape backend REST client.
// Uses relative URLs so the Vite dev/preview proxy forwards /api -> Flask.

const BASE = "/api";

async function request(path, options = {}) {
  const resp = await fetch(`${BASE}${path}`, options);
  let body = null;
  try {
    body = await resp.json();
  } catch {
    body = null;
  }
  if (!resp.ok) {
    const message = body?.error || `Request failed (${resp.status})`;
    throw new Error(message);
  }
  return body;
}

export function getHealth() {
  return request("/health");
}

export function getRoom() {
  return request("/room");
}

export function getStatus() {
  return request("/sensor/status");
}

export function getDevices() {
  return request("/devices");
}

export function analyzeRoomImage(file) {
  const form = new FormData();
  form.append("image", file);
  return request("/analyze-room", { method: "POST", body: form });
}

export function resetRoom() {
  return request("/room/reset", { method: "POST" });
}

export function startSensor(mode = "real") {
  return request("/sensor/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
}

export function stopSensor() {
  return request("/sensor/stop", { method: "POST" });
}

export function calibrateSensor(seconds = 3) {
  return request("/sensor/calibrate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seconds }),
  });
}
