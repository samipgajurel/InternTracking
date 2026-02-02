// js/signup.js
// Requires config.js to define: ACCOUNTS_API (ex: `${API_BASE}/accounts`)

const fullNameEl = document.getElementById("full_name");
const emailEl = document.getElementById("email");
const pwEl = document.getElementById("password");
const pw2El = document.getElementById("password2");
const roleEl = document.getElementById("role");

const msgEl = document.getElementById("msg");
const btnEl = document.getElementById("signupBtn");

const pwBar = document.getElementById("pwBar");
const pwText = document.getElementById("pwText");
const matchText = document.getElementById("matchText");

const afterSignup = document.getElementById("afterSignup");
const migaduBtn = document.getElementById("migaduBtn");

function togglePw(id) {
  const el = document.getElementById(id);
  el.type = el.type === "password" ? "text" : "password";
}

// ✅ rules: 8+ chars, number, special
function validatePassword(pw) {
  if (!pw || pw.length < 8) return "Password must be at least 8 characters.";
  if (!/[0-9]/.test(pw)) return "Password must include at least one number.";
  if (!/[^A-Za-z0-9]/.test(pw)) return "Password must include at least one special character.";
  return "";
}

function scorePassword(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8) score += 30;
  if (/[0-9]/.test(pw)) score += 30;
  if (/[^A-Za-z0-9]/.test(pw)) score += 40;
  return Math.min(100, score);
}

function strengthLabel(score) {
  if (score >= 80) return "Strong ✅";
  if (score >= 50) return "Almost there ⚠️";
  return "Weak ❌ (needs number + special)";
}

function updateStrength() {
  const pw = pwEl.value || "";
  const score = scorePassword(pw);

  pwBar.style.width = score + "%";
  if (score >= 80) pwBar.style.background = "#4BC0C0";
  else if (score >= 50) pwBar.style.background = "#FF9F40";
  else pwBar.style.background = "#ff4d4d";

  pwText.textContent = pw ? strengthLabel(score) : "";
  updateMatch();
}

function updateMatch() {
  const pw = pwEl.value || "";
  const pw2 = pw2El.value || "";
  if (!pw2) {
    matchText.textContent = "";
    return;
  }
  matchText.textContent = (pw === pw2) ? "Passwords match ✅" : "Passwords do not match ❌";
}

pwEl.addEventListener("input", updateStrength);
pw2El.addEventListener("input", updateMatch);

// Initial
updateStrength();
updateMatch();

async function doSignup() {
  const full_name = (fullNameEl.value || "").trim();
  const email = (emailEl.value || "").trim().toLowerCase();
  const password = pwEl.value || "";
  const password2 = pw2El.value || "";
  const role = roleEl.value;

  msgEl.textContent = "";
  afterSignup.style.display = "none";

  if (!full_name || !email || !password || !password2) {
    msgEl.textContent = "Please fill all fields.";
    return;
  }

  const pwErr = validatePassword(password);
  if (pwErr) {
    msgEl.textContent = pwErr;
    return;
  }

  if (password !== password2) {
    msgEl.textContent = "Passwords do not match.";
    return;
  }

  btnEl.disabled = true;
  msgEl.textContent = "Creating account...";

  try {
    const res = await fetch(`${ACCOUNTS_API}/signup/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name, email, password, role })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Signup failed");

    const redirectUrl = data.redirect_url || "https://webmail.migadu.com/";

    msgEl.textContent = "✅ Signup success. Redirecting to Migadu for email verification...";
    afterSignup.style.display = "block";

    migaduBtn.onclick = () => window.location.href = redirectUrl;

    setTimeout(() => {
      window.location.href = redirectUrl;
    }, 1200);

  } catch (e) {
    msgEl.textContent = e.message;
  } finally {
    btnEl.disabled = false;
  }
}
