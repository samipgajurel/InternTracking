function getParam(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name);
}

function toggleNew() {
  const p = document.getElementById("new_password");
  p.type = p.type === "password" ? "text" : "password";
}

// strength
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
  if (s < 35) { bar.style.background = "#ff6384"; text.textContent = "Weak"; }
  else if (s < 70) { bar.style.background = "#ffcd56"; text.textContent = "Medium"; }
  else { bar.style.background = "#4bc0c0"; text.textContent = "Strong"; }
}
document.getElementById("new_password").addEventListener("input", renderStrength);
renderStrength();

async function resetPassword() {
  const msg = document.getElementById("msg");
  msg.textContent = "Resetting...";

  const uid = getParam("uid");
  const token = getParam("token");
  const new_password = document.getElementById("new_password").value;

  if (!uid || !token) {
    msg.textContent = "Invalid link.";
    return;
  }

  const res = await fetch(`${ACCOUNTS_API}/reset-password/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uid, token, new_password })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    msg.textContent = data.detail || "Reset failed";
    return;
  }

  msg.textContent = data.detail || "Password reset successful. Redirecting to login...";
  setTimeout(() => window.location.href = "login.html", 1200);
}
