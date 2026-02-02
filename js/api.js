// js/api.js
function getTokens() {
  return {
    access: localStorage.getItem("access"),
    refresh: localStorage.getItem("refresh"),
  };
}

function setTokens({ access, refresh }) {
  if (access) localStorage.setItem("access", access);
  if (refresh) localStorage.setItem("refresh", refresh);
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return null;

  const res = await fetch(`${API_BASE}/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.access) return null;

  setTokens({ access: data.access }); // refresh token usually unchanged
  return data.access;
}

async function apiFetch(url, options = {}) {
  const { access } = getTokens();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(access ? { Authorization: `Bearer ${access}` } : {}),
  };

  let res = await fetch(url, { ...options, headers });

  // ✅ if expired, refresh once and retry once
  if (res.status === 401) {
    const newAccess = await refreshAccessToken();
    if (!newAccess) return res;

    const headers2 = {
      ...headers,
      Authorization: `Bearer ${newAccess}`,
    };
    res = await fetch(url, { ...options, headers: headers2 });
  }

  return res;
}
