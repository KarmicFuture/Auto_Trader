const authForm = document.getElementById("auth-form");
const resumeForm = document.getElementById("resume-form");
const contactForm = document.getElementById("contact-form");
const authError = document.getElementById("auth-error");
const resumeError = document.getElementById("resume-error");
const contactError = document.getElementById("contact-error");
const nameField = document.getElementById("name-field");
const authSubmit = document.getElementById("auth-submit");
const authHint = document.getElementById("auth-hint");
const fileInput = document.getElementById("resume-file");
const fileName = document.getElementById("file-name");
const logoutBtn = document.getElementById("btn-logout");
const deskNav = document.getElementById("desk-nav");
const deckEl = document.getElementById("deck");

let mode = "register";
let tips = [];
let category = "all";
let currentUser = null;
let contacts = [];
let deck = [];
let liked = [];
let dragging = null;

function show(id) {
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.hidden = screen.id !== id;
  });
  const signedIn = id !== "screen-welcome";
  logoutBtn.hidden = !signedIn;
  const appViews = ["screen-swipe", "screen-network", "screen-desk"];
  deskNav.hidden = !appViews.includes(id);
  deskNav.querySelectorAll("[data-view]").forEach((btn) => {
    btn.classList.toggle("is-active", `screen-${btn.dataset.view}` === id);
  });
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
    : "Welcome back. We’ll pick up at your resume or your swipe deck.";
  showError(authError, "");
}

function routeUser(user, preferred) {
  currentUser = user;
  if (!user) {
    show("screen-welcome");
    return;
  }
  if (!user.has_resume) {
    const kicker = document.getElementById("resume-kicker");
    const via = user.linkedin ? "LinkedIn" : "email";
    kicker.textContent = `Account saved · ${user.name} · ${via}`;
    show("screen-resume");
    return;
  }
  const view = preferred || ((user.contact_count || 0) > 0 ? "swipe" : "network");
  if (view === "desk") {
    renderDesk(user);
    show("screen-desk");
    return;
  }
  if (view === "network") {
    show("screen-network");
    loadContacts();
    return;
  }
  show("screen-swipe");
  loadDeck();
}

function renderDesk(user) {
  document.getElementById("desk-kicker").textContent = user.linkedin
    ? `Hi, ${user.name} · LinkedIn`
    : `Hi, ${user.name}`;
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

function renderPeople() {
  const list = document.getElementById("people-list");
  const empty = document.getElementById("people-empty");
  const go = document.getElementById("btn-to-swipe");
  empty.hidden = contacts.length > 0;
  go.hidden = contacts.length === 0;
  list.innerHTML = contacts
    .map(
      (person) => `<li>
        <div>
          <strong>${escapeHtml(person.name)}</strong>
          <p>${escapeHtml(person.company)} · ${escapeHtml(person.relation)}</p>
        </div>
        <button type="button" class="btn ghost" data-del="${person.id}">Remove</button>
      </li>`
    )
    .join("");
  list.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", () => removeContact(Number(btn.dataset.del)));
  });
}

function renderDeck() {
  const empty = document.getElementById("deck-empty");
  const actions = document.getElementById("swipe-actions");
  empty.hidden = deck.length > 0;
  actions.hidden = deck.length === 0;
  deckEl.innerHTML = "";
  deck.slice(0, 3).reverse().forEach((job, index, arr) => {
    const depth = arr.length - 1 - index;
    const card = document.createElement("article");
    card.className = "swipe-card";
    card.dataset.id = job.id;
    card.style.zIndex = String(10 - depth);
    card.style.transform = depth ? `scale(${1 - depth * 0.04}) translateY(${depth * 10}px)` : "";
    const through = job.through || {};
    card.innerHTML = `
      <span class="stamp yes">INTRO</span>
      <span class="stamp nope">PASS</span>
      <span class="through">${escapeHtml(through.name || "Someone you know")} · ${escapeHtml(through.relation || "knows")}</span>
      <h3>${escapeHtml(job.title)}</h3>
      <p class="company">${escapeHtml(job.company)}</p>
      <p>${escapeHtml(job.location || "")}</p>
      <p>${escapeHtml(job.blurb || "")}</p>
    `;
    if (depth === 0) bindSwipe(card, job);
    deckEl.appendChild(card);
  });
  document.getElementById("swipe-status").textContent = deck.length
    ? `${deck.length} role${deck.length === 1 ? "" : "s"} through people you know`
    : "";
}

function renderLiked() {
  const list = document.getElementById("liked-list");
  if (!liked.length) {
    list.innerHTML = "";
    return;
  }
  list.innerHTML = liked
    .map(
      (row) => `<li>
        <div>
          <strong>${escapeHtml(row.title || "Intro")}</strong>
          <p>${escapeHtml(row.company || "")}</p>
        </div>
        <span class="through">Intro</span>
      </li>`
    )
    .join("");
}

function bindSwipe(card, job) {
  const yes = card.querySelector(".stamp.yes");
  const nope = card.querySelector(".stamp.nope");
  let startX = 0;
  let dx = 0;
  let active = false;

  const onMove = (event) => {
    if (!active) return;
    const point = event.touches ? event.touches[0] : event;
    dx = point.clientX - startX;
    const rot = dx / 18;
    card.style.transform = `translateX(${dx}px) rotate(${rot}deg)`;
    yes.style.opacity = dx > 20 ? Math.min(dx / 120, 1) : 0;
    nope.style.opacity = dx < -20 ? Math.min(-dx / 120, 1) : 0;
  };

  const onUp = () => {
    if (!active) return;
    active = false;
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    window.removeEventListener("touchmove", onMove);
    window.removeEventListener("touchend", onUp);
    if (dx > 110) decide(job, "intro");
    else if (dx < -110) decide(job, "pass");
    else {
      card.style.transform = "";
      yes.style.opacity = 0;
      nope.style.opacity = 0;
    }
  };

  const onDown = (event) => {
    dragging = job.id;
    active = true;
    dx = 0;
    const point = event.touches ? event.touches[0] : event;
    startX = point.clientX;
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("touchmove", onMove, { passive: true });
    window.addEventListener("touchend", onUp);
  };

  card.addEventListener("pointerdown", onDown);
  card.addEventListener("touchstart", onDown, { passive: true });
}

async function decide(job, decision) {
  const top = deckEl.querySelector(".swipe-card:last-child");
  if (top) {
    const fly = decision === "intro" ? 640 : -640;
    top.style.transition = "transform 280ms ease";
    top.style.transform = `translateX(${fly}px) rotate(${decision === "intro" ? 18 : -18}deg)`;
  }
  deck = deck.filter((card) => card.id !== job.id);
  await fetch("/api/swipe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_id: job.id,
      decision,
      contact_id: job.through?.id || null,
      title: job.title,
      company: job.company,
    }),
  })
    .then(readJson)
    .then((data) => {
      liked = data.liked || liked;
    })
    .catch(() => {});
  setTimeout(() => {
    renderDeck();
    renderLiked();
  }, 220);
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
  const params = new URLSearchParams(window.location.search);
  const authErrorText = params.get("auth_error");
  if (authErrorText) {
    showError(authError, authErrorText);
    window.history.replaceState({}, "", "/");
  }
  const res = await fetch("/api/me");
  const data = await res.json();
  routeUser(data.user);
  if (data.user) await loadTips();
}

async function loadConfig() {
  try {
    const data = await (await fetch("/api/config")).json();
    const btn = document.getElementById("btn-linkedin");
    if (btn && data.linkedin === false) {
      btn.title = "Add LinkedIn app credentials to enable this.";
    }
  } catch {
    /* keep the button */
  }
}

async function loadTips() {
  const res = await fetch("/api/tips");
  if (!res.ok) return;
  const data = await res.json();
  tips = data.tips || [];
  renderTips();
}

async function loadContacts() {
  const data = await readJson(await fetch("/api/contacts"));
  contacts = data.contacts || [];
  if (currentUser) currentUser.contact_count = contacts.length;
  renderPeople();
}

async function loadDeck() {
  const [deckData, likedData] = await Promise.all([
    readJson(await fetch("/api/swipe/deck")),
    readJson(await fetch("/api/swipe/liked")),
  ]);
  deck = deckData.jobs || [];
  liked = likedData.liked || [];
  renderDeck();
  renderLiked();
}

async function removeContact(id) {
  const data = await readJson(await fetch(`/api/contacts/${id}`, { method: "DELETE" }));
  contacts = data.contacts || [];
  renderPeople();
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

contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError(contactError, "");
  try {
    const data = await readJson(
      await fetch("/api/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("contact-name").value.trim(),
          company: document.getElementById("contact-company").value.trim(),
          relation: document.getElementById("contact-relation").value.trim() || "knows",
        }),
      })
    );
    contacts = data.contacts || [];
    contactForm.reset();
    renderPeople();
  } catch (err) {
    showError(contactError, err.message);
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

deskNav.querySelectorAll("[data-view]").forEach((btn) => {
  btn.addEventListener("click", () => routeUser(currentUser, btn.dataset.view));
});

document.getElementById("btn-to-swipe").addEventListener("click", () => {
  routeUser(currentUser, "swipe");
});

document.getElementById("btn-pass").addEventListener("click", () => {
  if (deck[0]) decide(deck[0], "pass");
});
document.getElementById("btn-intro").addEventListener("click", () => {
  if (deck[0]) decide(deck[0], "intro");
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  currentUser = null;
  tips = [];
  contacts = [];
  deck = [];
  liked = [];
  authForm.reset();
  resumeForm.reset();
  contactForm.reset();
  fileName.textContent = "No file selected";
  setMode("register");
  show("screen-welcome");
});

setMode("register");
loadConfig();
loadMe();
