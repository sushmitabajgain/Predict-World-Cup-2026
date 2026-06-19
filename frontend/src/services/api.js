const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return response.json();
}

export function getTeams() {
  return request('/teams');
}

export function predictMatch(payload) {
  return request('/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getPredictions() {
  return request('/predictions');
}
