// js/auth.js
function setUser(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

function getUser() {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}

function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
  window.location.href = "login.html";
}

async function login(email, password) {
  const res = await fetch(`${ACCOUNTS_API}/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: (email || "").trim().toLowerCase(),
      password: password || "",
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Invalid credentials");

  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  setUser(data.user);
  return data.user;
}

function requireAuth() {
  const user = getUser();
  if (!user) {
    window.location.href = "login.html";
    return null;
  }
  return user;
}

function requireRole(roles = []) {
  const user = requireAuth();
  if (!user) return null;

  if (roles.length && !roles.includes(user.role)) {
    // ✅ redirect to correct page instead of just failing with 403
    goToDashboardByRole(user);
    return null;
  }
  return user;
}

function goToDashboardByRole(user) {
  if (!user) return logout();

  if (user.role === "admin") window.location.href = "admin.html";
  else if (user.role === "supervisor") window.location.href = "supervisor.html";
  else window.location.href = "intern.html";
}
