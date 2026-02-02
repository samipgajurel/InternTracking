const me = requireAuth();
document.getElementById("who").textContent = `${me.email} | ${me.staff_id || ""}`;

function safe(s){
  return (s ?? "").toString().replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
}

function showTab(name){
  document.getElementById("tab_interns").style.display = (name==="interns") ? "" : "none";
  document.getElementById("tab_assign").style.display = (name==="assign") ? "" : "none";
  document.getElementById("tab_tasks").style.display = (name==="tasks") ? "" : "none";
  document.getElementById("tab_complaints").style.display = (name==="complaints") ? "" : "none";

  if(name==="interns") loadInterns();
  if(name==="assign") loadInternDropdown();
  if(name==="tasks") loadTasks();
  if(name==="complaints") loadComplaints();
}

async function loadInternDropdown(){
  const sel = document.getElementById("task_intern");
  sel.innerHTML = `<option>Loading...</option>`;

  const res = await apiFetch(`${API_BASE}/supervisor/interns/`);
  const data = await res.json().catch(()=>[]);
  if(!res.ok){
    sel.innerHTML = `<option value="">Error</option>`;
    return;
  }

  sel.innerHTML = data.length
    ? data.map(i => `<option value="${i.id}">${safe(i.full_name)} (${safe(i.staff_id||"")})</option>`).join("")
    : `<option value="">No interns assigned</option>`;
}

async function loadInterns(){
  const q = document.getElementById("intern_q").value.trim();
  const box = document.getElementById("intern_list");
  box.textContent = "Loading...";

  const res = await apiFetch(`${API_BASE}/supervisor/interns/?q=${encodeURIComponent(q)}`);
  const data = await res.json().catch(()=>[]);
  if(!res.ok){
    box.textContent = "Failed to load interns.";
    return;
  }
  if(!data.length){
    box.textContent = "No interns assigned to you yet.";
    return;
  }

  box.innerHTML = data.map(i => {
    const p = i.performance || {};
    return `
      <div class="card" style="margin:10px 0;">
        <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
          <div>
            <b>${safe(i.full_name)}</b>
            <div class="muted small">${safe(i.email)} • ${safe(i.staff_id||"")}</div>
          </div>
          <div class="small">
            Score: <b>${p.score ?? 0}</b> |
            Tasks: <b>${p.done_tasks ?? 0}/${p.total_tasks ?? 0}</b> |
            Overdue: <b>${p.overdue ?? 0}</b>
          </div>
        </div>

        <hr/>

        <div class="row">
          <div class="field" style="flex:0.3; min-width:140px;">
            <label>Progress (0-5)</label>
            <select id="rate_${i.id}">
              ${[0,1,2,3,4,5].map(x => `<option value="${x}" ${x===(i.progress_rating||0)?"selected":""}>${x}</option>`).join("")}
            </select>
          </div>

          <div class="field" style="flex:1; min-width:240px;">
            <label>Feedback</label>
            <input id="fb_${i.id}" value="${safe(i.feedback||"")}" placeholder="Write feedback..."/>
          </div>

          <div style="display:flex; align-items:flex-end;">
            <button class="secondary" onclick="saveProgress(${i.id})">Save</button>
          </div>
        </div>
        <div class="muted small" id="msg_${i.id}"></div>
      </div>
    `;
  }).join("");
}

async function saveProgress(internId){
  const msg = document.getElementById(`msg_${internId}`);
  msg.textContent = "Saving...";

  const rating = document.getElementById(`rate_${internId}`).value;
  const feedback = document.getElementById(`fb_${internId}`).value;

  const res = await apiFetch(`${API_BASE}/supervisor/intern-progress/`, {
    method:"POST",
    body: JSON.stringify({
      intern_id: internId,
      rating: rating,
      feedback: feedback
    })
  });

  const data = await res.json().catch(()=>({}));
  msg.textContent = res.ok ? "✅ Saved" : (data.detail || "Failed");
}

async function createTask(){
  const msg = document.getElementById("task_msg");
  msg.textContent = "Assigning...";

  const intern = document.getElementById("task_intern").value;
  const title = document.getElementById("task_title").value.trim();
  const description = document.getElementById("task_desc").value.trim();
  const due_date = document.getElementById("task_due").value || null;

  if(!intern){ msg.textContent="Select an intern"; return; }
  if(!title){ msg.textContent="Title required"; return; }

  const res = await apiFetch(`${API_BASE}/tasks/create/`, {
    method:"POST",
    body: JSON.stringify({
      intern: parseInt(intern,10),
      title,
      description,
      due_date
    })
  });

  const data = await res.json().catch(()=>({}));
  msg.textContent = res.ok ? "✅ Task assigned" : (data.detail || "Failed");
}

async function loadTasks(){
  const box = document.getElementById("task_list");
  box.textContent = "Loading...";

  const res = await apiFetch(`${API_BASE}/tasks/supervisor/`);
  const data = await res.json().catch(()=>[]);
  if(!res.ok){
    box.textContent = "Failed to load tasks.";
    return;
  }
  if(!data.length){
    box.textContent = "No tasks assigned yet.";
    return;
  }

  box.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>Title</th><th>Status</th><th>Intern</th><th>Due</th><th>Created</th>
        </tr>
      </thead>
      <tbody>
        ${data.map(t=>`
          <tr>
            <td><b>${safe(t.title)}</b><div class="muted small">${safe(t.description||"")}</div></td>
            <td>${safe(t.status)}</td>
            <td>${t.intern}</td>
            <td>${t.due_date || "-"}</td>
            <td class="small">${new Date(t.created_at).toLocaleString()}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

async function loadComplaints(){
  const box = document.getElementById("complaint_list");
  box.textContent = "Loading...";

  const res = await apiFetch(`${API_BASE}/complaints/supervisor/`);
  const data = await res.json().catch(()=>[]);
  if(!res.ok){
    box.textContent = "Failed to load complaints.";
    return;
  }
  if(!data.length){
    box.textContent = "No complaints from your interns.";
    return;
  }

  box.innerHTML = data.map(c => `
    <div class="card" style="margin:10px 0;">
      <b>${safe(c.title)}</b>
      <div class="muted small">${safe(c.intern.full_name)} • ${safe(c.intern.email)}</div>
      <p class="small">${safe(c.message)}</p>

      <div class="row">
        <select id="cstat_${c.id}" style="width:160px;">
          <option value="open" ${c.status==="open"?"selected":""}>open</option>
          <option value="resolved" ${c.status==="resolved"?"selected":""}>resolved</option>
        </select>
        <button class="secondary" onclick="updateComplaint(${c.id})">Update</button>
        <span class="muted small" id="cmsg_${c.id}"></span>
      </div>
    </div>
  `).join("");
}

async function updateComplaint(id){
  const msg = document.getElementById(`cmsg_${id}`);
  msg.textContent = "Updating...";

  const status = document.getElementById(`cstat_${id}`).value;

  const res = await apiFetch(`${API_BASE}/complaints/update-status/`, {
    method:"POST",
    body: JSON.stringify({ complaint_id: id, status })
  });

  const data = await res.json().catch(()=>({}));
  msg.textContent = res.ok ? "✅ Updated" : (data.detail || "Failed");
}

// default load
showTab("interns");
