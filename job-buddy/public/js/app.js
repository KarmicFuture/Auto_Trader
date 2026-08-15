const authForm = document.getElementById("auth-form");
const resumeForm = document.getElementById("resume-form");
const authError = document.getElementById("auth-error");
const resumeError = document.getElementById("resume-error");
const nameField = document.getElementById("name-field");
const authSubmit = document.getElementById("auth-submit");
const authHint = document.getElementById("auth-hint");
const fileInput = document.getElementById("resume-file");
const fileName = document.getElementById("file-name");
const logoutBtn = document.getElementById("btn-logout");

let mode = "register";
let tips = [];
let category = "all";
let currentUser = null;

function show(id) {
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.hidden = screen.id !== id;
  });
  logoutBtn.hidden = id === "screen-welcome";
}

function showError(node, message) {
  if (!message) {
    node.hidden = true;
    node.textContent = "";
    return;
  }
  node.hidden = false;
  node.textContent = message;
}

function setMode(next) {
  mode = next;
  document.querySelectorAll("[data-mode]").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.mode === next);
  });
  const registering = next === "register";
  nameField.hidden = !registering;
  document.getElementById("name").required = registering;
  document.getElementById("password").autocomplete = registering
    ? "new-password"
    : "current-password";
  authSubmit.textContent = registering ? "Create account" : "Sign in";
  authHint.textContent = registering
    ? "We’ll save your account, then ask for your resume."
    : "Welcome back. We’ll pick up at your resume or your tip desk.";
  showError(authError, "");
}

function routeUser(user) {
  currentUser = user;
  if (!user) {
    show("screen-welcome");
    return;
  }
  if (!user.has_resume) {
    const kicker = document.getElementById("resume-kicker");
    kicker.textContent = `Account saved · ${user.name}`;
    show("screen-resume");
    return;
  }
  renderDesk(user);
  show("screen-desk");
}

function renderDesk(user) {
  document.getElementById("desk-kicker").textContent = `Hi, ${user.name}`;
  document.getElementById("desk-title").textContent = "Tips and tricks to find the job.";
  const resume = user.resume;
  document.getElementById("resume-card").innerHTML = `
    <div>
      <p class="kicker">Resume on file</p>
      <strong>${escapeHtml(resume.filename)}</strong>
      <p>${formatBytes(resume.size_bytes)} · uploaded ${escapeHtml(resume.uploaded_at.slice(0, 10))}</p>
    </div>
    <button type="button" class="btn ghost" id="btn-replace">Replace resume</button>
  `;
  document.getElementById("btn-replace").addEventListener("click", () => {
    document.getElementById("resume-kicker").textContent = "Update resume";
    show("screen-resume");
  });
  renderTips();
}

function renderTips() {
  const rows = category === "all" ? tips : tips.filter((tip) => tip.category === category);
  document.getElementById("tip-grid").innerHTML = rows
    .map(
      (tip) => `<article class="tip">
        <p class="cat">${escapeHtml(tip.category)}</p>
        <h3>${escapeHtml(tip.title)}</h3>
        <p>${escapeHtml(tip.body)}</p>
      </article>`
    )
    .join("");
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function readJson(res) {
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || "Something went wrong.");
  }
  return data;
}

async function loadMe() {
  const res = await fetch("/api/me");
  const data = await res.json();
  routeUser(data.user);
  if (data.user) await loadTips();
}

async function loadTips() {
  const res = await fetch("/api/tips");
  if (!res.ok) return;
  const data = await res.json();
  tips = data.tips || [];
  renderTips();
}

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError(authError, "");
  const body = new FormData(authForm);
  if (mode === "login") body.delete("name");
  try {
    const data = await readJson(
      await fetch(mode === "register" ? "/api/register" : "/api/login", {
        method: "POST",
        body,
      })
    );
    routeUser(data.user);
    if (data.user) await loadTips();
  } catch (err) {
    showError(authError, err.message);
  }
});

resumeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError(resumeError, "");
  const body = new FormData(resumeForm);
  try {
    const data = await readJson(await fetch("/api/resume", { method: "POST", body }));
    routeUser(data.user);
    await loadTips();
  } catch (err) {
    showError(resumeError, err.message);
  }
});

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "No file selected";
});

document.querySelectorAll("[data-mode]").forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

document.querySelectorAll(".tip-toolbar .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    category = btn.dataset.cat;
    document.querySelectorAll(".tip-toolbar .chip").forEach((chip) => {
      chip.classList.toggle("is-active", chip === btn);
    });
    renderTips();
  });
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  currentUser = null;
  tips = [];
  authForm.reset();
  resumeForm.reset();
  fileName.textContent = "No file selected";
  setMode("register");
  show("screen-welcome");
});

setMode("register");
loadMe();
