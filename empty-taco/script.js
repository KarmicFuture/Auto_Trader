const BOOKING_EMAIL = "book@emptytaco.com";
const RED_CROSS_DONATE = "https://www.redcross.org/donate/donation.html";

function donationFrom(form) {
  const on = form.querySelector('[name="donate_redcross"]')?.checked;
  const amount = Number(form.querySelector('[name="donate_amount"]')?.value || 0);
  return on ? amount : 0;
}

function openRedCrossIfNeeded(amount) {
  if (!amount) return;
  window.open(RED_CROSS_DONATE, "_blank", "noopener");
}

const prices = {
  classic: 3,
  combo: 5,
  mix: 4,
};

const mixLabels = {
  classic: "$3 dogs",
  combo: "$5 combos",
  mix: "a mix",
};

function ticketId() {
  const n = Math.floor(1000 + Math.random() * 9000);
  return `ET-${n}`;
}

function formValues(form) {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

function estimate(values) {
  const people = Math.max(0, Number(values.headcount) || 0);
  const unit = prices[values.mix] || prices.mix;
  return {
    people,
    unit,
    total: Math.round(people * unit),
    label: mixLabels[values.mix] || "a mix",
  };
}

function bookingText(values, id) {
  const quote = estimate(values);
  return [
    `Empty Taco booking ${id}`,
    "",
    `Name: ${values.name || ""}`,
    `Email: ${values.email || ""}`,
    `Phone: ${values.phone || ""}`,
    `Event: ${values.event_type || ""}`,
    `Address: ${values.address || ""}`,
    `Date: ${values.date || ""}`,
    `Start: ${values.time || ""}`,
    `Hours: ${values.hours || ""}`,
    `Headcount: ${quote.people}`,
    `Mostly: ${quote.label}`,
    `Rough ticket: ~$${quote.total}`,
    "",
    `Notes: ${values.notes || "(none)"}`,
  ].join("\n");
}

function updateQuote(form) {
  const values = formValues(form);
  const quote = estimate(values);
  const math = document.getElementById("quote-math");
  if (!math) return;
  math.textContent = `${quote.people} people × ${quote.label} ≈ $${quote.total}`;
}

function setMinDate() {
  const input = document.querySelector('input[name="date"]');
  if (!input) return;
  const start = new Date();
  start.setDate(start.getDate() + 2);
  input.min = start.toISOString().slice(0, 10);
}

function showStatus(message, ok) {
  const el = document.getElementById("form-status");
  if (!el) return;
  el.textContent = message;
  el.style.color = ok ? "#2f5e32" : "#8e1c12";
}

function validate(form) {
  if (form.reportValidity()) return true;
  showStatus("We need a name, a place, a time, and a way to write you back.", false);
  return false;
}

function bindForm() {
  const form = document.getElementById("booking-form");
  const idEl = document.getElementById("ticket-id");
  const copyBtn = document.getElementById("copy-btn");
  if (!form || !idEl) return;

  const id = ticketId();
  idEl.textContent = id;
  setMinDate();
  updateQuote(form);

  form.addEventListener("input", () => updateQuote(form));
  form.addEventListener("change", () => updateQuote(form));

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!validate(form)) return;
    const values = formValues(form);
    const body = bookingText(values, id);
    const subject = `Empty Taco booking — ${values.date} — ${values.address}`;
    const href = `mailto:${BOOKING_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = href;
    showStatus("Opening your email with the booking filled in. If nothing opens, tap Copy the request.", true);
  });

  copyBtn?.addEventListener("click", async () => {
    if (!validate(form)) return;
    const values = formValues(form);
    const body = bookingText(values, id);
    try {
      await navigator.clipboard.writeText(body);
      showStatus(`Copied. Send it to ${BOOKING_EMAIL} whenever you’re ready.`, true);
    } catch {
      showStatus("Could not copy. Select and copy the email draft instead.", false);
    }
  });
}

const termLines = [
  { cmd: true, text: "$ whoami" },
  { cmd: false, text: "people-who-believe-in-lunch" },
  { cmd: true, text: "$ cat mission.txt" },
  { cmd: false, text: "A hot dog can fix a bad day." },
  { cmd: false, text: "Make life easier. Put fun back in." },
  { cmd: false, text: "$3 dog. $5 combo. $20 to a friend." },
  { cmd: true, text: "$ serve --with kindness" },
  { cmd: false, text: "steamer hot · mustard ready · come as you are" },
];

function updateSendTotal(form) {
  const math = document.getElementById("send-math");
  if (!math) return;
  const gift = donationFrom(form);
  math.textContent = gift
    ? `$20 dog + $${gift} Red Cross = $${20 + gift}`
    : "$20 — one hot dog, delivered to someone you care about";
}

function bindSend() {
  const form = document.getElementById("send-form");
  const status = document.getElementById("send-status");
  if (!form) return;

  form.addEventListener("input", () => updateSendTotal(form));
  form.addEventListener("change", () => updateSendTotal(form));
  updateSendTotal(form);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.reportValidity()) {
      if (status) {
        status.textContent = "We need your name, theirs, and a place to bring the dog.";
        status.style.color = "#8e1c12";
      }
      return;
    }
    const values = formValues(form);
    const gift = donationFrom(form);
    const body = [
      "Empty Taco — $20 send a hot dog to a friend",
      "",
      `From: ${values.from_name || ""} <${values.from_email || ""}>`,
      `To: ${values.to_name || ""}`,
      `Phone: ${values.to_phone || ""}`,
      `Address: ${values.to_address || ""}`,
      `Note: ${values.note || "(none)"}`,
      "",
      "Dog: $20",
      gift
        ? `Red Cross donation: $${gift} (via redcross.org/donate)`
        : "Red Cross donation: none",
      `Total noted: $${20 + gift}`,
    ].join("\n");
    openRedCrossIfNeeded(gift);
    window.location.href = `mailto:${BOOKING_EMAIL}?subject=${encodeURIComponent("Empty Taco $20 friend dog")}&body=${encodeURIComponent(body)}`;
    if (status) {
      status.textContent = gift
        ? "Opening the Red Cross donate page and your email. Thank you."
        : "Opening email. We’ll confirm, then you can send the $20.";
      status.style.color = "#2f5e32";
    }
  });
}

function bindMerch() {
  const form = document.getElementById("merch-form");
  const status = document.getElementById("merch-status");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = formValues(form);
    const items = [...form.querySelectorAll('input[name="item"]:checked')].map((el) => el.value);
    if (!form.reportValidity() || !items.length) {
      if (status) {
        status.textContent = "Pick at least one item and leave your name and email.";
        status.style.color = "#8e1c12";
      }
      return;
    }
    const gift = donationFrom(form);
    const body = [
      "Empty Taco merch pile",
      "",
      `Name: ${values.name || ""}`,
      `Email: ${values.email || ""}`,
      `Items: ${items.join(", ")}`,
      `Notes: ${values.notes || "(none)"}`,
      gift
        ? `Red Cross donation: $${gift} (via redcross.org/donate)`
        : "Red Cross donation: none",
    ].join("\n");
    openRedCrossIfNeeded(gift);
    window.location.href = `mailto:${BOOKING_EMAIL}?subject=${encodeURIComponent("Empty Taco merch")}&body=${encodeURIComponent(body)}`;
    if (status) {
      status.textContent = gift
        ? "Opening the Red Cross donate page and your email."
        : "Opening email. If nothing happens, write book@emptytaco.com.";
      status.style.color = "#2f5e32";
    }
  });
}

function playTerminal() {
  const log = document.getElementById("term-log");
  if (!log) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) {
    log.textContent = termLines.map((line) => line.text).join("\n");
    return;
  }

  let i = 0;
  log.textContent = "";

  const writeLine = () => {
    if (i >= termLines.length) return;
    const line = termLines[i];
    const prefix = log.textContent ? "\n" : "";
    if (!line.cmd) {
      log.textContent += `${prefix}${line.text}`;
      i += 1;
      window.setTimeout(writeLine, 220);
      return;
    }

    let char = 0;
    log.textContent += prefix;
    const tick = () => {
      log.textContent += line.text.charAt(char);
      char += 1;
      if (char < line.text.length) {
        window.setTimeout(tick, 28);
      } else {
        i += 1;
        window.setTimeout(writeLine, 260);
      }
    };
    tick();
  };

  writeLine();
}

function sprinkle(event) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const colors = ["#ff3d2e", "#ffc107", "#2f9e44", "#4cc9f0", "#ff6bb5"];
  const x = event.clientX;
  const y = event.clientY;
  for (let i = 0; i < 10; i += 1) {
    const dot = document.createElement("span");
    dot.className = "pop";
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    dot.style.background = colors[i % colors.length];
    const angle = (Math.PI * 2 * i) / 10;
    dot.style.setProperty("--x", `${Math.cos(angle) * 70}px`);
    dot.style.setProperty("--y", `${Math.sin(angle) * 70}px`);
    document.body.appendChild(dot);
    window.setTimeout(() => dot.remove(), 720);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bindForm();
  bindSend();
  bindMerch();
  playTerminal();
  document.querySelectorAll(".btn, .top__cta").forEach((el) => {
    el.addEventListener("click", sprinkle);
  });
});
