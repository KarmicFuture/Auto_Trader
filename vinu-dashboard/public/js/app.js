const views = ["overview", "pages", "projects", "launch", "tasks"];
const titles = {
  overview: "Overview",
  pages: "Pages",
  projects: "Projects",
  launch: "Launch",
  tasks: "Tasks",
};

const els = {
  viewTitle: document.getElementById("view-title"),
  statusEyebrow: document.getElementById("status-eyebrow"),
  livePill: document.getElementById("live-pill"),
  updatedAt: document.getElementById("updated-at"),
  heroLede: document.getElementById("hero-lede"),
  progressRing: document.getElementById("progress-ring"),
  progressPercent: document.getElementById("progress-percent"),
  statRow: document.getElementById("stat-row"),
  activityList: document.getElementById("activity-list"),
  taskPreview: document.getElementById("task-preview"),
  pagesList: document.getElementById("pages-list"),
  projectsList: document.getElementById("projects-list"),
  checklist: document.getElementById("checklist"),
  taskForm: document.getElementById("task-form"),
  taskInput: document.getElementById("task-input"),
  taskList: document.getElementById("task-list"),
};

let cache = {
  overview: null,
  pages: [],
  projects: [],
  checklist: [],
  tasks: [],
  activity: [],
};

async function api(path, options) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function formatWhen(iso) {
  if (!iso) return "";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function setView(name) {
  if (!views.includes(name)) return;
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.view === name);
  });
  document.querySelectorAll(".view").forEach((section) => {
    const active = section.id === `view-${name}`;
    section.classList.toggle("is-active", active);
    section.hidden = !active;
  });
  els.viewTitle.textContent = titles[name];
  history.replaceState(null, "", `#${name}`);
}

function renderOverview() {
  const o = cache.overview;
  if (!o) return;

  els.heroLede.textContent = o.tagline;
  els.livePill.textContent = o.status.replace(/-/g, " ");
  els.statusEyebrow.textContent = o.siteUrl.replace(/^https?:\/\//, "");
  els.updatedAt.textContent = o.updatedAt ? `Updated ${formatWhen(o.updatedAt)}` : "";
  els.progressPercent.textContent = `${o.checklistProgress.percent}%`;

  const circumference = 2 * Math.PI * 52;
  const offset = circumference * (1 - o.checklistProgress.percent / 100);
  els.progressRing.style.strokeDasharray = `${circumference}`;
  els.progressRing.style.strokeDashoffset = `${offset}`;

  els.statRow.innerHTML = [
    ["Pages", o.pageCount],
    ["Projects", o.projectCount],
    ["Open tasks", o.openTasks],
    ["Checklist", `${o.checklistProgress.done}/${o.checklistProgress.total}`],
  ]
    .map(
      ([label, value]) => `
      <article class="stat">
        <span>${label}</span>
        <strong>${value}</strong>
      </article>`
    )
    .join("");

  els.activityList.innerHTML = cache.activity
    .slice(0, 5)
    .map(
      (item) => `
      <li>
        <strong>${escapeHtml(item.label)}</strong>
        <time datetime="${item.at}">${formatWhen(item.at)}</time>
      </li>`
    )
    .join("");

  els.taskPreview.innerHTML = cache.tasks
    .filter((task) => !task.done)
    .slice(0, 4)
    .map(
      (task) => `
      <li>
        <strong>${escapeHtml(task.title)}</strong>
        <span class="meta">${formatWhen(task.createdAt)}</span>
      </li>`
    )
    .join("") || `<li><strong>No open tasks</strong><span class="meta">You're clear</span></li>`;
}

function renderPages() {
  els.pagesList.innerHTML = cache.pages
    .map(
      (page) => `
      <li class="page-item">
        <div>
          <h3>${escapeHtml(page.title)}</h3>
          <p>${escapeHtml(page.note)}</p>
          <p><code>${escapeHtml(page.path)}</code></p>
        </div>
        <span class="badge ${escapeHtml(page.status)}">${escapeHtml(page.status)}</span>
      </li>`
    )
    .join("");
}

function renderProjects() {
  els.projectsList.innerHTML = cache.projects
    .map(
      (project) => `
      <a class="project-card" href="${escapeAttr(project.url)}" target="_blank" rel="noreferrer">
        <div style="display:flex;justify-content:space-between;gap:.75rem;align-items:start">
          <h3>${escapeHtml(project.name)}</h3>
          <span class="badge ${escapeHtml(project.status)}">${escapeHtml(project.status)}</span>
        </div>
        <p class="role">${escapeHtml(project.role)}</p>
        <p>${escapeHtml(project.url.replace(/^https?:\/\//, ""))}</p>
      </a>`
    )
    .join("");
}

function renderChecklist() {
  els.checklist.innerHTML = cache.checklist
    .map(
      (item) => `
      <li class="check-item ${item.done ? "is-done" : ""}" data-id="${escapeAttr(item.id)}">
        <button type="button" aria-label="Toggle ${escapeAttr(item.label)}">${item.done ? "✓" : ""}</button>
        <span>${escapeHtml(item.label)}</span>
      </li>`
    )
    .join("");
}

function renderTasks() {
  els.taskList.innerHTML = cache.tasks
    .map(
      (task) => `
      <li class="task-item ${task.done ? "is-done" : ""}" data-id="${escapeAttr(task.id)}">
        <button class="check" type="button" aria-label="Toggle task">${task.done ? "✓" : ""}</button>
        <p>${escapeHtml(task.title)}</p>
        <button class="remove" type="button" aria-label="Delete task">Remove</button>
      </li>`
    )
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

async function refresh() {
  const [overview, pages, projects, checklist, tasks, activity] = await Promise.all([
    api("/overview"),
    api("/pages"),
    api("/projects"),
    api("/checklist"),
    api("/tasks"),
    api("/activity"),
  ]);

  cache = { overview, pages, projects, checklist, tasks, activity };
  renderOverview();
  renderPages();
  renderProjects();
  renderChecklist();
  renderTasks();
}

function bindEvents() {
  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });

  document.querySelectorAll("[data-view-jump]").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.viewJump));
  });

  els.checklist.addEventListener("click", async (event) => {
    const item = event.target.closest(".check-item");
    if (!item) return;
    const current = cache.checklist.find((entry) => entry.id === item.dataset.id);
    if (!current) return;
    await api(`/checklist/${current.id}`, {
      method: "PATCH",
      body: JSON.stringify({ done: !current.done }),
    });
    await refresh();
  });

  els.taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = els.taskInput.value.trim();
    if (!title) return;
    await api("/tasks", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    els.taskInput.value = "";
    await refresh();
    setView("tasks");
  });

  els.taskList.addEventListener("click", async (event) => {
    const row = event.target.closest(".task-item");
    if (!row) return;
    const id = row.dataset.id;
    if (event.target.classList.contains("remove")) {
      await api(`/tasks/${id}`, { method: "DELETE" });
      await refresh();
      return;
    }
    if (event.target.classList.contains("check")) {
      const current = cache.tasks.find((entry) => entry.id === id);
      if (!current) return;
      await api(`/tasks/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ done: !current.done }),
      });
      await refresh();
    }
  });
}

async function boot() {
  bindEvents();
  const initial = location.hash.replace("#", "") || "overview";
  setView(views.includes(initial) ? initial : "overview");
  await refresh();
}

boot().catch((err) => {
  console.error(err);
  els.heroLede.textContent = "Could not load dashboard data. Is the server running?";
});
