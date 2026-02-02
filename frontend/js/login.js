const emailEl = document.getElementById("email");
const passwordEl = document.getElementById("password");

/* ---------------- SHOW / HIDE PASSWORD ---------------- */
function togglePw() {
  passwordEl.type = passwordEl.type === "password" ? "text" : "password";
}

/* ---------------- LOGIN ---------------- */
async function doLogin() {
  const msg = document.getElementById("msg");
  msg.textContent = "Logging in...";

  try {
    const user = await login(emailEl.value, passwordEl.value);
    goToDashboardByRole(user);
  } catch (err) {
    msg.textContent = err.message || "Login failed";
  }
}

/* ---------------- FORGOT PASSWORD UI ---------------- */
function showForgot() {
  document.getElementById("loginBox").style.display = "none";
  document.getElementById("forgotBox").style.display = "block";
}

function showLogin() {
  document.getElementById("forgotBox").style.display = "none";
  document.getElementById("loginBox").style.display = "block";
}

/* ---------------- SEND RESET ---------------- */
async function sendReset() {
  const email = document.getElementById("forgot_email").value.trim();
  const box = document.getElementById("forgot_msg");

  if (!email) {
    box.textContent = "Email required";
    return;
  }

  box.textContent = "Sending reset link...";

  try {
    const res = await fetch(`${ACCOUNTS_API}/forgot-password/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Failed");

    box.textContent = "✅ Reset link sent. Check your email.";
  } catch (e) {
    box.textContent = e.message;
  }
}
