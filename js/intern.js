// frontend/js/intern.js
// ✅ Intern dashboard full JS
// - Works with your existing UI (no design change)
// - Uses /api/intern/tasks/ (alias) and also falls back to /api/tasks/my/
// - Attendance POST payload matches backend exactly: {date:"YYYY-MM-DD", status, note}
// - Adds Progress & Feedback tab using /api/intern/my-supervisor/
// - Auto-refresh token via apiFetch (your js/api.js) and handles 401 retry
// - Safe DOM checks (won't break if some ids are missing)

(() => {
  // ---------- AUTH / ROLE ----------
  const user = requireRole(["intern"]);
  if (!user) return;

  // Put "who" badge if present
  const who = document.getElementById("who");
  if (who) who.textContent = `${user.email} | ${user.staff_id || ""}`;

  // ---------- HELPERS ----------
  const $ = (id) => document.getElementById(id);

  function setText(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
  }

  function setHTML(id, html) {
    const el = $(id);
    if (el) el.innerHTML = html;
  }

  function todayISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function monthISO() {
    // YYYY-MM
    return new Date().toISOString().slice(0, 7);
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function stars(n) {
    const x = Math.max(0, Math.min(5, parseInt(n || 0, 10)));
    return "★★★★★☆☆☆☆☆".slice(5 - x, 10 - x);
  }

  async function readJSON(res) {
    return await res.json().catch(() => ({}));
  }

  // ---------- NAV (tabs) ----------
  // Your intern.html likely has buttons/tabs.
  // We support ids:
  //   tab_tasks, tab_attendance, tab_reports, tab_complaints, tab_progress
  // and sections:
  //   sec_tasks, sec_attendance, sec_reports, sec_complaints, sec_progress
  const tabs = [
    { tab: "tab_tasks", sec: "sec_tasks" },
    { tab: "tab_attendance", sec: "sec_attendance" },
    { tab: "tab_reports", sec: "sec_reports" },
    { tab: "tab_complaints", sec: "sec_complaints" },
    { tab: "tab_progress", sec: "sec_progress" }, // ✅ new
  ];

  function showSection(secId) {
    tabs.forEach(({ tab, sec }) => {
      const t = $(tab);
      const s = $(sec);
      if (s) s.style.display = sec === secId ? "block" : "none";
      if (t) t.classList.toggle("active", sec === secId);
    });
  }

  function wireTabs() {
    tabs.forEach(({ tab, sec }) => {
      const t = $(tab);
      if (!t) return;
      t.addEventListener("click", () => {
        showSection(sec);
        // lazy load when opened
        if (sec === "sec_tasks") loadTasks();
        if (sec === "sec_attendance") loadAttendance();
        if (sec === "sec_reports") loadReports();
        if (sec === "sec_complaints") loadComplaints();
        if (sec === "sec_progress") loadProgressFeedback();
      });
    });
  }

  // ---------- TASKS ----------
  // supports both:
  //  /api/intern/tasks/  (your frontend expected)
  //  /api/tasks/my/      (your backend original)
  async function fetchMyTasks() {
    // try alias first
    let res = await apiFetch(`${API_BASE}/intern/tasks/`);
    if (res.status === 404) res = await apiFetch(`${API_BASE}/tasks/my/`);
    return res;
  }

  async function loadTasks() {
    const boxId = "tasks_box"; // optional container
    const msgId = "tasks_msg"; // optional message
    if ($(boxId)) setText(boxId, "Loading...");
    if ($(msgId)) setText(msgId, "");

    const res = await fetchMyTasks();
    const data = await readJSON(res);

    if (!res.ok) {
      const detail = data.detail || "Failed to load tasks";
      if ($(boxId)) setText(boxId, detail);
      if ($(msgId)) setText(msgId, detail);
      return;
    }

    const tasks = Array.isArray(data) ? data : [];
    if (!$(boxId)) return;

    if (!tasks.length) {
      setText(boxId, "No tasks assigned yet.");
      return;
    }

    setHTML(
      boxId,
      `
      <table class="table">
        <thead>
          <tr>
            <th>Title</th><th>Status</th><th>Due</th><th>Update</th>
          </tr>
        </thead>
        <tbody>
          ${tasks
            .map(
              (t) => `
            <tr>
              <td>
                <b>${escapeHtml(t.title)}</b><br/>
                <span class="muted small">${escapeHtml(t.description || "")}</span>
              </td>
              <td>${escapeHtml(t.status)}</td>
              <td>${escapeHtml(t.due_date || "-")}</td>
              <td>
                <select data-task-id="${t.id}" class="taskStatus">
                  <option value="pending" ${t.status === "pending" ? "selected" : ""}>pending</option>
                  <option value="in_progress" ${t.status === "in_progress" ? "selected" : ""}>in_progress</option>
                  <option value="done" ${t.status === "done" ? "selected" : ""}>done</option>
                </select>
                <button class="secondary smallBtn" data-save-id="${t.id}">Save</button>
              </td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `
    );

    // wire save buttons
    document.querySelectorAll("[data-save-id]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-save-id");
        const sel = document.querySelector(`select.taskStatus[data-task-id="${id}"]`);
        const status = sel ? sel.value : "pending";
        await updateTaskStatus(id, status);
      });
    });
  }

  async function updateTaskStatus(taskId, status) {
    const msgId = "tasks_msg";
    if ($(msgId)) setText(msgId, "Saving...");

    // try alias first
    let res = await apiFetch(`${API_BASE}/intern/tasks/${taskId}/`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    if (res.status === 404) {
      res = await apiFetch(`${API_BASE}/tasks/my/${taskId}/`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
    }

    const data = await readJSON(res);
    if (!res.ok) {
      const detail = data.detail || "Update failed";
      if ($(msgId)) setText(msgId, detail);
      alert(detail);
      return;
    }

    if ($(msgId)) setText(msgId, "✅ Updated");
    // refresh list
    loadTasks();
  }

  // ---------- ATTENDANCE ----------
  async function loadAttendance() {
    const listId = "attendance_list";
    const msgId = "attendance_msg";
    if ($(listId)) setText(listId, "Loading...");
    if ($(msgId)) setText(msgId, "");

    const res = await apiFetch(`${API_BASE}/attendance/my/`);
    const data = await readJSON(res);

    if (!res.ok) {
      const detail = data.detail || "Failed to load attendance";
      if ($(listId)) setText(listId, detail);
      if ($(msgId)) setText(msgId, detail);
      return;
    }

    const rows = Array.isArray(data) ? data : [];
    if (!$(listId)) return;

    if (!rows.length) {
      setText(listId, "No attendance marked yet.");
      return;
    }

    setHTML(
      listId,
      `
      <table class="table">
        <thead><tr><th>Date</th><th>Status</th><th>Note</th></tr></thead>
        <tbody>
          ${rows
            .map(
              (r) => `
            <tr>
              <td>${escapeHtml(r.date)}</td>
              <td>${escapeHtml(r.status)}</td>
              <td>${escapeHtml(r.note || "-")}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `
    );
  }

  // Button handler (expects your page has a "Mark Today" button calling markAttendance)
  window.markAttendance = async function markAttendance() {
    const msgId = "attendance_msg";
    if ($(msgId)) setText(msgId, "Saving...");

    // try to read from existing UI controls:
    // <select id="attendance_status"> OR <select id="status">
    const statusEl = $("attendance_status") || $("status");
    const noteEl = $("attendance_note") || $("note");

    const status = (statusEl?.value || "present").trim();
    const note = (noteEl?.value || "").trim();

    // ✅ backend requires "date"
    const payload = { date: todayISO(), status, note };

    const res = await apiFetch(`${API_BASE}/attendance/my/`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const data = await readJSON(res);

    if (!res.ok) {
      const detail =
        data.detail ||
        (typeof data === "object" ? JSON.stringify(data) : "Attendance failed");
      if ($(msgId)) setText(msgId, detail);
      alert(detail);
      return;
    }

    if ($(msgId)) setText(msgId, "✅ Marked");
    loadAttendance();
  };

  // ---------- REPORTS ----------
  async function loadReports() {
    const listId = "reports_list";
    const msgId = "reports_msg";
    if ($(listId)) setText(listId, "Loading...");
    if ($(msgId)) setText(msgId, "");

    const res = await apiFetch(`${API_BASE}/reports/my/`);
    const data = await readJSON(res);

    if (!res.ok) {
      const detail = data.detail || "Failed to load reports";
      if ($(listId)) setText(listId, detail);
      if ($(msgId)) setText(msgId, detail);
      return;
    }

    const rows = Array.isArray(data) ? data : [];
    if (!$(listId)) return;

    if (!rows.length) {
      setText(listId, "No reports submitted yet.");
      return;
    }

    setHTML(
      listId,
      `
      <table class="table">
        <thead><tr><th>Month</th><th>Summary</th><th>Created</th></tr></thead>
        <tbody>
          ${rows
            .map(
              (r) => `
            <tr>
              <td>${escapeHtml(r.month)}</td>
              <td>${escapeHtml((r.summary || "").slice(0, 120))}${(r.summary || "").length > 120 ? "..." : ""}</td>
              <td>${escapeHtml(r.created_at || "-")}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `
    );
  }

  window.submitReport = async function submitReport() {
    const msgId = "reports_msg";
    if ($(msgId)) setText(msgId, "Saving...");

    // expected inputs:
    //  <input id="report_month"> and <textarea id="report_summary">
    const mEl = $("report_month");
    const sEl = $("report_summary");

    const month = (mEl?.value || monthISO()).trim();
    const summary = (sEl?.value || "").trim();

    if (!summary) {
      if ($(msgId)) setText(msgId, "Summary required");
      alert("Summary required");
      return;
    }

    const res = await apiFetch(`${API_BASE}/reports/my/`, {
      method: "POST",
      body: JSON.stringify({ month, summary }),
    });

    const data = await readJSON(res);
    if (!res.ok) {
      const detail = data.detail || "Report submit failed";
      if ($(msgId)) setText(msgId, detail);
      alert(detail);
      return;
    }

    if ($(msgId)) setText(msgId, "✅ Report submitted");
    if (sEl) sEl.value = "";
    loadReports();
  };

  // ---------- COMPLAINTS ----------
  async function loadComplaints() {
    const listId = "complaints_list";
    const msgId = "complaints_msg";
    if ($(listId)) setText(listId, "Loading...");
    if ($(msgId)) setText(msgId, "");

    const res = await apiFetch(`${API_BASE}/complaints/my/`);
    const data = await readJSON(res);

    if (!res.ok) {
      const detail = data.detail || "Failed to load complaints";
      if ($(listId)) setText(listId, detail);
      if ($(msgId)) setText(msgId, detail);
      return;
    }

    const rows = Array.isArray(data) ? data : [];
    if (!$(listId)) return;

    if (!rows.length) {
      setText(listId, "No complaints submitted.");
      return;
    }

    setHTML(
      listId,
      `
      <table class="table">
        <thead><tr><th>Title</th><th>Status</th><th>Created</th></tr></thead>
        <tbody>
          ${rows
            .map(
              (c) => `
            <tr>
              <td>
                <b>${escapeHtml(c.title)}</b><br/>
                <span class="muted small">${escapeHtml((c.message || "").slice(0, 120))}${(c.message || "").length > 120 ? "..." : ""}</span>
              </td>
              <td>${escapeHtml(c.status)}</td>
              <td>${escapeHtml(c.created_at || "-")}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `
    );
  }

  window.submitComplaint = async function submitComplaint() {
    const msgId = "complaints_msg";
    if ($(msgId)) setText(msgId, "Saving...");

    const tEl = $("complaint_title");
    const mEl = $("complaint_message");

    const title = (tEl?.value || "").trim();
    const message = (mEl?.value || "").trim();

    if (!title || !message) {
      const d = "Title and message required";
      if ($(msgId)) setText(msgId, d);
      alert(d);
      return;
    }

    const res = await apiFetch(`${API_BASE}/complaints/my/`, {
      method: "POST",
      body: JSON.stringify({ title, message }),
    });

    const data = await readJSON(res);
    if (!res.ok) {
      const detail = data.detail || "Complaint submit failed";
      if ($(msgId)) setText(msgId, detail);
      alert(detail);
      return;
    }

    if ($(msgId)) setText(msgId, "✅ Complaint submitted");
    if (tEl) tEl.value = "";
    if (mEl) mEl.value = "";
    loadComplaints();
  };

  // ---------- ✅ PROGRESS & FEEDBACK (NEW TAB) ----------
  async function loadProgressFeedback() {
    const boxId = "progress_box"; // container on your Progress & Feedback card
    if ($(boxId)) setText(boxId, "Loading...");

    const res = await apiFetch(`${API_BASE}/intern/my-supervisor/`);
    const data = await readJSON(res);

    if (!res.ok) {
      const detail = data.detail || "Failed to load progress & feedback";
      if ($(boxId)) setText(boxId, detail);
      return;
    }

    if (!$(boxId)) return;

    if (!data.assigned) {
      setHTML(
        boxId,
        `
        <div class="muted">${escapeHtml(data.detail || "No supervisor assigned yet.")}</div>
      `
      );
      return;
    }

    const sup = data.supervisor || {};
    const rating = data.progress_rating ?? 0;
    const feedback = data.feedback || "";

    setHTML(
      boxId,
      `
      <h3 style="margin-top:0">Progress & Feedback</h3>
      <div class="muted">Supervisor</div>
      <div><b>${escapeHtml(sup.full_name || "-")}</b> <span class="muted small">(${escapeHtml(sup.email || "-")})</span></div>
      <hr/>
      <div class="muted">Your Rating</div>
      <div style="font-size:18px"><b>${escapeHtml(String(rating))}/5</b> <span class="muted">${escapeHtml(stars(rating))}</span></div>
      <hr/>
      <div class="muted">Supervisor Feedback</div>
      <div style="white-space:pre-wrap">${escapeHtml(feedback || "No feedback yet.")}</div>
    `
    );
  }

  // ---------- INIT ----------
  function initDefaultTab() {
    // show tasks by default if available, else first section found
    if ($("sec_tasks")) showSection("sec_tasks");
    else if ($("sec_attendance")) showSection("sec_attendance");
    else if ($("sec_reports")) showSection("sec_reports");
    else if ($("sec_complaints")) showSection("sec_complaints");
    else if ($("sec_progress")) showSection("sec_progress");
  }

  wireTabs();
  initDefaultTab();

  // load initial visible section
  // (showSection already called above)
  if ($("sec_tasks") && $("sec_tasks").style.display !== "none") loadTasks();
  else if ($("sec_attendance") && $("sec_attendance").style.display !== "none") loadAttendance();
  else if ($("sec_reports") && $("sec_reports").style.display !== "none") loadReports();
  else if ($("sec_complaints") && $("sec_complaints").style.display !== "none") loadComplaints();
  else if ($("sec_progress") && $("sec_progress").style.display !== "none") loadProgressFeedback();
})();
