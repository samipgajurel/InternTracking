// Show logged-in user
const me = requireAuth();
if (me) {
  document.getElementById("who").textContent = `${me.email} | ${me.staff_id || ""}`;
}

function goBack() {
  const u = getUser();
  if (!u) return logout();
  if (u.role === "admin") window.location.href = "admin.html";
  else if (u.role === "supervisor") window.location.href = "supervisor.html";
  else window.location.href = "intern.html";
}

function togglePw(id) {
  const el = document.getElementById(id);
  el.type = el.type === "password" ? "text" : "password";
}

// -------- Strength meter (same logic you use in login/reset) --------
function scorePassword(pw) {
  if (!pw) return 0;
  let score = 0;

  const hasLower = /[a-z]/.test(pw);
  const hasUpper = /[A-Z]/.test(pw);
  const hasNum = /[0-9]/.test(pw);
  const hasSym = /[^A-Za-z0-9]/.test(pw);

  score += Math.min(40, pw.length * 4);
  score += hasLower ? 10 : 0;
  score += hasUpper ? 10 : 0;
  score += hasNum ? 10 : 0;
  score += hasSym ? 10 : 0;

  if (pw.length < 8) score -= 15;

  score = Math.max(0, Math.min(100, score));
  return score;
}

function renderStrength() {
  const pw = document.getElementById("new_password").value || "";
  const bar = document.getElementById("pwBar");
  const text = document.getElementById("pwText");

  const s = scorePassword(pw);
  bar.style.width = `${s}%`;

  if (s < 35) {
    bar.style.background = "#ff6384";
    text.textContent = "Weak";
  } else if (s < 70) {
    bar.style.background = "#ffcd56";
    text.textContent = "Medium";
  } else {
    bar.style.background = "#4bc0c0";
    text.textContent = "Strong";
  }
}

document.getElementById("new_password").addEventListener("input", renderStrength);
renderStrength();

// -------- Submit change password --------
async function changePassword() {
  const msg = document.getElementById("msg");
  msg.textContent = "Updating password...";

  const current_password = document.getElementById("current_password").value;
  const new_password = document.getElementById("new_password").value;
  const confirm_password = document.getElementById("confirm_password").value;

  if (!current_password || !new_password || !confirm_password) {
    msg.textContent = "Please fill all fields.";
    return;
  }

  if (new_password !== confirm_password) {
    msg.textContent = "New password and confirm password do not match.";
    return;
  }

  // send refresh token so backend can blacklist and force logout
  const refresh = localStorage.getItem("refresh") || "";

  const res = await apiFetch(`${ACCOUNTS_API}/change-password/`, {
    method: "POST",
    body: JSON.stringify({
      current_password,
      new_password,
      refresh,
    }),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    msg.textContent = data.detail || "Password change failed.";
    return;
  }

  msg.textContent = data.detail || "Password changed. Logging out...";
  // force logout (required)
  setTimeout(() => logout(), 900);
}
