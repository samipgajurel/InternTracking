// frontend/js/login.js

function togglePw() {
  const p = document.getElementById("password");
  p.type = p.type === "password" ? "text" : "password";
}

async function doLogin() {
  const email = document.getElementById("email").value.trim().toLowerCase();
  const password = document.getElementById("password").value;
  const msg = document.getElementById("msg");
  msg.textContent = "";

  if (!email || !password) {
    msg.textContent = "Email and password required.";
    return;
  }

  try {
    const data = await apiFetch(`${ACCOUNTS_API}/login/`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    // Your backend might return tokens OR user. Handle both.
    if (data.access && data.refresh) {
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
    }

    // If backend returns user object, store it
    if (data.user) localStorage.setItem("user", JSON.stringify(data.user));

    // If backend doesn't return user, call /me/
    if (!data.user && localStorage.getItem("access")) {
      const me = await apiFetch(`${ACCOUNTS_API}/me/`, { method: "GET" });
      localStorage.setItem("user", JSON.stringify(me));
    }

    window.location.href = "dashboard.html";
  } catch (err) {
    msg.textContent = err.message || "Login failed";
  }
}
