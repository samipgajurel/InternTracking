// frontend/js/api.js

async function apiFetch(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // If you use JWT token, attach it automatically
  const access = localStorage.getItem("access");
  if (access) headers["Authorization"] = `Bearer ${access}`;

  try {
    const res = await fetch(url, {
      mode: "cors",
      credentials: "omit", // IMPORTANT: you're using JWT, not cookies
      ...options,
      headers,
    });

    // Try to parse JSON safely
    const text = await res.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }

    if (!res.ok) {
      // Make backend errors readable
      const msg =
        data.detail ||
        data.message ||
        (typeof data === "string" ? data : null) ||
        `HTTP ${res.status}`;
      throw new Error(msg);
    }

    return data;
  } catch (err) {
    // This is the exact place where "Failed to fetch" happens
    console.error("apiFetch error:", err);

    // Friendly message
    if (String(err).includes("Failed to fetch")) {
      throw new Error(
        "Failed to fetch. Check: (1) API URL correct, (2) Render backend is live, (3) CORS allows Netlify."
      );
    }
    throw err;
  }
}
