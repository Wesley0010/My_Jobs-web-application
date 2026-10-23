const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'myjobs.token';
const USER_KEY = 'myjobs.user';

// ---------- Token + user storage ----------
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function setUser(user) {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
  return !!getToken();
}

// ---------- Core fetch helper ----------
async function request(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Token ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!res.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      (data && Object.values(data)[0]) ||
      `Request failed (${res.status})`;
    throw new Error(Array.isArray(message) ? message[0] : String(message));
  }

  return data;
}

// ---------- Public API ----------
export async function apiRegister({ name, email, password }) {
  const data = await request('/api/auth/register/', {
    method: 'POST',
    body: { name, email, password },
  });
  // Do NOT store token — user must sign in afterwards.
  return data.user;
}

export async function apiLogin({ email, password }) {
  const data = await request('/api/auth/login/', {
    method: 'POST',
    body: { email, password },
  });
  setToken(data.token);
  setUser(data.user);
  return data.user;
}

export async function apiLogout() {
  try {
    await request('/api/auth/logout/', { method: 'POST', auth: true });
  } catch {
    // ignore
  } finally {
    clearAuth();
  }
}

export async function apiMe() {
  return request('/api/auth/me/', { method: 'GET', auth: true });
}