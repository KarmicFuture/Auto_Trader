const BOOKING_EMAIL = "book@emptytaco.com";

const prices = {
  classic: 5,
  loaded: 7,
  combo: 8,
  mix: 6.5,
};

const mixLabels = {
  classic: "classic dogs",
  loaded: "loaded dogs",
  combo: "combos",
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
  showStatus("Fill the required fields — we need a place, a time, and a way to write back.", false);
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
    showStatus("Opening your email app with the ticket filled in. If nothing opens, use Copy the request.", true);
  });

  copyBtn?.addEventListener("click", async () => {
    if (!validate(form)) return;
    const values = formValues(form);
    const body = bookingText(values, id);
    try {
      await navigator.clipboard.writeText(body);
      showStatus(`Copied. Paste it to ${BOOKING_EMAIL} or text it to us.`, true);
    } catch {
      showStatus("Could not copy. Select and copy the email draft instead.", false);
    }
  });
}

const termLines = [
  { cmd: true, text: "$ whoami" },
  { cmd: false, text: "tech-people-who-love-a-hot-dog" },
  { cmd: true, text: "$ cat mission.txt" },
  { cmd: false, text: "Stand up a licensed Tampa food business" },
  { cmd: false, text: "in ~3 weeks, under $2,000." },
  { cmd: false, text: "AI on the back office. Humans on the cart." },
  { cmd: true, text: "$ serve --to your-place" },
  { cmd: false, text: "hitch ok · steamer hot · mustard loaded" },
  { cmd: false, text: "ready. send the address." },
];

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

document.addEventListener("DOMContentLoaded", () => {
  bindForm();
  playTerminal();
});
