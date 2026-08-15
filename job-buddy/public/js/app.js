const STORAGE_PROFILE = "jobbuddy.profile";
const STORAGE_APPS = "jobbuddy.apps";
const STATUSES = ["saved", "applied", "interviewing", "offer", "closed"];
const STATUS_LABEL = {
  saved: "Saved",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  closed: "Closed",
};

const state = {
  view: "today",
  jobs: [],
  applications: loadApplications(),
  profile: loadProfile(),
  activeJob: null,
};

const $ = (id) => document.getElementById(id);

function loadProfile() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_PROFILE) || "{}") || {};
  } catch {
    return {};
  }
}

function loadApplications() {
  try {
    const rows = JSON.parse(localStorage.getItem(STORAGE_APPS) || "[]");
    return Array.isArray(rows) ? rows : [];
  } catch {
    return [];
  }
}

function saveProfile(profile) {
  state.profile = profile;
  localStorage.setItem(STORAGE_PROFILE, JSON.stringify(profile));
}

function saveApplications() {
  localStorage.setItem(STORAGE_APPS, JSON.stringify(state.applications));
}

function csv(value) {
  return String(value || "")
    .split(/[,;]/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function profilePayload() {
  return {
    name: state.profile.name || "",
    titles: csv(state.profile.titles),
    skills: csv(state.profile.skills),
    locations: csv(state.profile.locations),
    remote: state.profile.remote || "any",
    min_salary: state.profile.min_salary || null,
  };
}

function greet() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function money(job) {
  if (job.salary_text) return job.salary_text;
  if (job.salary_min && job.salary_max) {
    return `$${Number(job.salary_min).toLocaleString()}–$${Number(job.salary_max).toLocaleString()}`;
  }
  return "Salary n/a";
}

function fitClass(label) {
  if (!label) return "neutral";
  if (label.startsWith("Excellent")) return "excellent";
  if (label.startsWith("Strong")) return "strong";
  if (label.startsWith("Possible")) return "possible";
  if (label.startsWith("Stretch")) return "stretch";
  return "neutral";
}

function showView(name) {
  state.view = name;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.view === name);
  });
  document.querySelectorAll(".view").forEach((view) => {
    const active = view.id === `view-${name}`;
    view.classList.toggle("is-active", active);
    view.hidden = !active;
  });
  if (name === "today") renderToday();
  if (name === "pipeline") renderPipeline();
  if (name === "profile") fillProfileForm();
}

function fillProfileForm() {
  $("profile-name").value = state.profile.name || "";
  $("profile-titles").value = state.profile.titles || "";
  $("profile-skills").value = state.profile.skills || "";
  $("profile-locations").value = state.profile.locations || "";
  $("profile-remote").value = state.profile.remote || "any";
  $("profile-salary").value = state.profile.min_salary || "";
}

async function renderToday() {
  const name = (state.profile.name || "").trim();
  $("today-kicker").textContent = name ? `${greet()}, ${name}` : greet();
  $("today-title").textContent = "Here’s what needs you.";

  const res = await fetch("/api/coach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      profile: profilePayload(),
      applications: state.applications,
    }),
  });
  const data = await res.json();
  const stats = data.stats || {};
  $("today-stats").innerHTML = [
    ["saved", "Saved"],
    ["applied", "Applied"],
    ["interviewing", "Interviews"],
    ["offer", "Offers"],
  ]
    .map(
      ([key, label]) =>
        `<article class="stat"><strong>${stats[key] || 0}</strong><span>${label}</span></article>`
    )
    .join("");

  const actions = data.actions || [];
  const box = $("today-actions");
  if (!actions.length) {
    box.innerHTML =
      '<article class="card"><h3>You’re clear</h3><p>No follow-ups or interviews are waiting. Search Discover when you want another thread.</p></article>';
    return;
  }
  box.innerHTML = actions
    .map((action) => {
      const job = state.applications.find((row) => row.id === action.job_id);
      return `<article class="card action" data-job='${escapeAttr(JSON.stringify(job || null))}'>
        <span class="urgency ${action.urgency}">${action.urgency}</span>
        <h3>${escapeHtml(action.title)}</h3>
        <p>${escapeHtml(action.detail)}</p>
      </article>`;
    })
    .join("");
  box.querySelectorAll(".action").forEach((card) => {
    card.addEventListener("click", () => {
      const job = JSON.parse(card.dataset.job || "null");
      if (job) openDrawer(job);
      else if (card.textContent.toLowerCase().includes("profile")) showView("profile");
      else showView("discover");
    });
  });
}

async function searchJobs(event) {
  event?.preventDefault();
  const params = new URLSearchParams({
    q: $("q").value.trim(),
    location: $("location").value.trim(),
    remote: $("remote-only").checked ? "true" : "false",
    name: state.profile.name || "",
    titles: state.profile.titles || "",
    skills: state.profile.skills || "",
    locations: state.profile.locations || "",
    work: state.profile.remote || "any",
  });
  if (state.profile.min_salary) params.set("min_salary", String(state.profile.min_salary));

  $("discover-banner").hidden = true;
  $("job-grid").innerHTML = '<article class="card"><p>Searching boards…</p></article>';
  const res = await fetch(`/api/jobs?${params.toString()}`);
  const data = await res.json();
  state.jobs = data.jobs || [];
  renderJobs(data);
}

function renderJobs(data) {
  const mode = $("discover-mode");
  mode.hidden = false;
  mode.textContent =
    data.mode === "demo"
      ? "Demo listings"
      : data.mode === "mixed"
        ? "Live + warnings"
        : `${data.count} live roles`;

  const banner = $("discover-banner");
  if (data.errors?.length) {
    banner.hidden = false;
    banner.textContent = data.errors.join(" · ");
  } else {
    banner.hidden = true;
  }

  const empty = $("discover-empty");
  const grid = $("job-grid");
  if (!state.jobs.length) {
    grid.innerHTML = "";
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  grid.innerHTML = state.jobs.map(jobCard).join("");
  grid.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => {
      const job = state.jobs.find((row) => row.id === card.dataset.id);
      if (job) openDrawer(mergeTracked(job));
    });
  });
}

function jobCard(job) {
  const tags = (job.tags || [])
    .slice(0, 4)
    .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join("");
  const tracked = state.applications.find((row) => row.id === job.id);
  return `<button type="button" class="card job-card" data-id="${escapeAttr(job.id)}">
    <header>
      <div>
        <h3>${escapeHtml(job.title)}</h3>
        <p>${escapeHtml(job.company)}</p>
      </div>
      <span class="fit ${fitClass(job.fit_label)}">${escapeHtml(job.fit_label || "Fit n/a")}${
        job.fit_score != null ? ` · ${Math.round(job.fit_score)}` : ""
      }</span>
    </header>
    <div class="meta">
      <span>${escapeHtml(job.location || "Location n/a")}</span>
      <span>${escapeHtml(money(job))}</span>
      <span>${escapeHtml(job.source)}</span>
      ${tracked ? `<span>${STATUS_LABEL[tracked.status] || tracked.status}</span>` : ""}
    </div>
    <div class="tags">${tags}</div>
  </button>`;
}

function renderPipeline() {
  const board = $("pipeline-board");
  board.innerHTML = STATUSES.map((status) => {
    const cards = state.applications
      .filter((job) => (job.status || "saved") === status)
      .map(
        (job) => `<article class="card" draggable="true" data-id="${escapeAttr(job.id)}">
          <h3>${escapeHtml(job.title)}</h3>
          <p>${escapeHtml(job.company)}</p>
        </article>`
      )
      .join("");
    return `<section class="column" data-status="${status}">
      <h3>${STATUS_LABEL[status]} · ${
        state.applications.filter((job) => (job.status || "saved") === status).length
      }</h3>
      ${cards || '<p class="empty">Drop a role here.</p>'}
    </section>`;
  }).join("");

  board.querySelectorAll(".card[data-id]").forEach((card) => {
    card.addEventListener("click", () => {
      const job = state.applications.find((row) => row.id === card.dataset.id);
      if (job) openDrawer(job);
    });
    card.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", card.dataset.id);
    });
  });
  board.querySelectorAll(".column").forEach((column) => {
    column.addEventListener("dragover", (event) => {
      event.preventDefault();
      column.classList.add("drop");
    });
    column.addEventListener("dragleave", () => column.classList.remove("drop"));
    column.addEventListener("drop", (event) => {
      event.preventDefault();
      column.classList.remove("drop");
      const id = event.dataTransfer.getData("text/plain");
      const job = state.applications.find((row) => row.id === id);
      if (!job) return;
      job.status = column.dataset.status;
      if (job.status === "applied" && !job.applied_at) {
        job.applied_at = todayISO();
      }
      saveApplications();
      renderPipeline();
      if (state.view === "today") renderToday();
    });
  });
}

function mergeTracked(job) {
  const existing = state.applications.find((row) => row.id === job.id);
  return existing ? { ...job, ...existing } : { ...job, status: "saved" };
}

function openDrawer(job) {
  state.activeJob = job;
  $("drawer-company").textContent = job.company || "Company";
  $("drawer-title").textContent = job.title || "Role";
  $("drawer-meta").textContent = [job.location, money(job), job.source, job.posted_at]
    .filter(Boolean)
    .join(" · ");
  $("drawer-fit").textContent = job.fit_label
    ? `${job.fit_label}${job.fit_score != null ? ` (${Math.round(job.fit_score)})` : ""}`
    : "Save a profile to score this role.";
  $("drawer-reasons").innerHTML = (job.fit_reasons || [])
    .map((reason) => `<li>${escapeHtml(reason)}</li>`)
    .join("");
  $("drawer-status").value = job.status || "saved";
  $("drawer-applied").value = job.applied_at || "";
  $("drawer-interview").value = job.interview_at || "";
  $("drawer-follow").value = job.follow_up_at || "";
  $("drawer-contact").value = job.contact || "";
  $("drawer-notes").value = job.notes || "";
  const link = $("drawer-link");
  if (job.url) {
    link.href = job.url;
    link.hidden = false;
  } else {
    link.hidden = true;
  }
  $("job-drawer").showModal();
}

function upsertApplication(job) {
  const index = state.applications.findIndex((row) => row.id === job.id);
  if (index >= 0) state.applications[index] = job;
  else state.applications.unshift(job);
  saveApplications();
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

function bind() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => showView(tab.dataset.view));
  });
  $("search-form").addEventListener("submit", searchJobs);
  $("profile-form").addEventListener("submit", (event) => {
    event.preventDefault();
    saveProfile({
      name: $("profile-name").value.trim(),
      titles: $("profile-titles").value.trim(),
      skills: $("profile-skills").value.trim(),
      locations: $("profile-locations").value.trim(),
      remote: $("profile-remote").value,
      min_salary: $("profile-salary").value ? Number($("profile-salary").value) : null,
    });
    const note = $("profile-saved");
    note.hidden = false;
    $("rail-note").textContent = state.profile.name
      ? `Desk for ${state.profile.name}`
      : "Your search stays on this device.";
  });
  $("job-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.activeJob) return;
    const next = {
      ...state.activeJob,
      status: $("drawer-status").value,
      applied_at: $("drawer-applied").value,
      interview_at: $("drawer-interview").value,
      follow_up_at: $("drawer-follow").value,
      contact: $("drawer-contact").value.trim(),
      notes: $("drawer-notes").value.trim(),
    };
    if (next.status === "applied" && !next.applied_at) next.applied_at = todayISO();
    upsertApplication(next);
    $("job-drawer").close();
    renderPipeline();
    if (state.view === "today") renderToday();
    if (state.view === "discover") renderJobs({ mode: "live", count: state.jobs.length, errors: [] });
  });
  $("drawer-remove").addEventListener("click", () => {
    if (!state.activeJob) return;
    state.applications = state.applications.filter((row) => row.id !== state.activeJob.id);
    saveApplications();
    $("job-drawer").close();
    renderPipeline();
    if (state.view === "today") renderToday();
  });

  fillProfileForm();
  if (state.profile.name) {
    $("rail-note").textContent = `Desk for ${state.profile.name}`;
  }
  if (!$("q").value) {
    const title = csv(state.profile.titles)[0];
    if (title) $("q").value = title;
  }
  renderToday();
  searchJobs();
}

bind();
