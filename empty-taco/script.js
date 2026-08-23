const BOOKING_EMAIL = "book@emptytaco.com";

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
  { cmd: false, text: "gen-x-still-here-still-hungry" },
  { cmd: true, text: "$ cat mission.txt" },
  { cmd: false, text: "Make life easier. Have fun." },
  { cmd: false, text: "Implement fun in a ridiculous world." },
  { cmd: false, text: "$3 dog. $5 with chips and a drink." },
  { cmd: true, text: "$ serve --to your-place" },
  { cmd: false, text: "hitch ok · steamer hot · merch in the tub" },
  { cmd: false, text: "ready. send the address." },
];

function bindSend() {
  const form = document.getElementById("send-form");
  const status = document.getElementById("send-status");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.reportValidity()) {
      if (status) {
        status.textContent = "Need you, them, and a place to park the dog.";
        status.style.color = "#fff6e4";
      }
      return;
    }
    const values = formValues(form);
    const body = [
      "Empty Taco — $20 send a hot dog to a friend",
      "",
      `From: ${values.from_name || ""} <${values.from_email || ""}>`,
      `To: ${values.to_name || ""}`,
      `Phone: ${values.to_phone || ""}`,
      `Address: ${values.to_address || ""}`,
      `Note: ${values.note || "(none)"}`,
      "",
      "Amount: $20",
    ].join("\n");
    window.location.href = `mailto:${BOOKING_EMAIL}?subject=${encodeURIComponent("Empty Taco $20 friend dog")}&body=${encodeURIComponent(body)}`;
    if (status) {
      status.textContent = "Opening email. We’ll confirm, then you shoot us $20.";
      status.style.color = "#fff6e4";
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
        status.textContent = "Pick at least one thing and tell us who you are.";
        status.style.color = "#8e1c12";
      }
      return;
    }
    const body = [
      "Empty Taco merch pile",
      "",
      `Name: ${values.name || ""}`,
      `Email: ${values.email || ""}`,
      `Items: ${items.join(", ")}`,
      `Notes: ${values.notes || "(none)"}`,
    ].join("\n");
    window.location.href = `mailto:${BOOKING_EMAIL}?subject=${encodeURIComponent("Empty Taco merch")}&body=${encodeURIComponent(body)}`;
    if (status) {
      status.textContent = "Opening email. If nothing happens, copy that and yell at book@emptytaco.com.";
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

document.addEventListener("DOMContentLoaded", () => {
  bindForm();
  bindSend();
  bindMerch();
  playTerminal();
});
