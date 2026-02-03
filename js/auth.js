// frontend/js/auth.js

function saveTokens(access, refresh) {
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
}

function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
  window.location.href = "login.html";
}

// Optional: refresh token function (not required just to login)
async function refreshToken() {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return null;

  try {
    const data = await apiFetch(JWT_REFRESH_API, {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });
    if (data.access) localStorage.setItem("access", data.access);
    return data.access || null;
  } catch (e) {
    logout();
    return null;
  }
}
