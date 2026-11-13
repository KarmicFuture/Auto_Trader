const els = {
  locDot: document.getElementById("loc-dot"),
  locLabel: document.getElementById("loc-label"),
  locMeta: document.getElementById("loc-meta"),
  btnLocate: document.getElementById("btn-locate"),
  btnWatch: document.getElementById("btn-watch"),
  btnRefresh: document.getElementById("btn-refresh"),
  radius: document.getElementById("radius"),
  classification: document.getElementById("classification"),
  keyword: document.getElementById("keyword"),
  banner: document.getElementById("banner"),
  listTitle: document.getElementById("list-title"),
  listCount: document.getElementById("list-count"),
  eventList: document.getElementById("event-list"),
  empty: document.getElementById("empty"),
  manualDialog: document.getElementById("manual-dialog"),
  manualForm: document.getElementById("manual-form"),
};

const state = {
  lat: null,
  lon: null,
  accuracy: null,
  watching: false,
  watchId: null,
  events: [],
  mode: null,
  place: null,
  activeEventId: null,
  config: { hasTicketmasterKey: false },
};

let map;
let userLayer;
let eventsLayer;
let fetchTimer;

function setBanner(message) {
  if (!message) {
    els.banner.hidden = true;
    els.banner.textContent = "";
    return;
  }
  els.banner.hidden = false;
  els.banner.textContent = message;
}

function formatWhen(event) {
  if (event.start) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(event.start));
    } catch {
      /* fall through */
    }
  }
  if (event.localDate) {
    return `${event.localDate}${event.localTime ? ` · ${event.localTime.slice(0, 5)}` : ""}`;
  }
  return "Date TBA";
}

function formatPlaceLabel() {
  const p = state.place;
  if (!p) return null;
  return (
    [p.neighborhood, p.city, p.state].filter(Boolean).join(", ") ||
    p.displayName ||
    null
  );
}

function updateLocationCard(status) {
  els.locDot.classList.remove("live", "error");
  if (status === "live") els.locDot.classList.add("live");
  if (status === "error") els.locDot.classList.add("error");

  if (state.lat != null && state.lon != null) {
    const place = formatPlaceLabel();
    els.locLabel.textContent = place || "Location locked";
    const accuracy =
      state.accuracy != null ? `±${Math.round(state.accuracy)} m` : "manual pin";
    els.locMeta.textContent = `${state.lat.toFixed(4)}, ${state.lon.toFixed(4)} · ${accuracy}${
      state.watching ? " · tracking on" : ""
    }`;
  }
}

function initMap() {
  map = L.map("map", {
    zoomControl: true,
    attributionControl: true,
  }).setView([39.8283, -98.5795], 4);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(map);

  userLayer = L.layerGroup().addTo(map);
  eventsLayer = L.layerGroup().addTo(map);
}

function userIcon() {
  return L.divIcon({
    className: "",
    html: '<div class="user-pin"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

function eventIcon() {
  return L.divIcon({
    className: "",
    html: '<div class="event-pin"></div>',
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

function renderMap() {
  userLayer.clearLayers();
  eventsLayer.clearLayers();

  if (state.lat != null && state.lon != null) {
    L.marker([state.lat, state.lon], { icon: userIcon(), title: "You are here" })
      .addTo(userLayer)
      .bindPopup("You are here");
    if (state.accuracy) {
      L.circle([state.lat, state.lon], {
        radius: state.accuracy,
        color: "#ef7a4e",
        weight: 1,
        fillColor: "#ef7a4e",
        fillOpacity: 0.08,
      }).addTo(userLayer);
    }
  }

  for (const event of state.events) {
    if (event.lat == null || event.lon == null) continue;
    const marker = L.marker([event.lat, event.lon], {
      icon: eventIcon(),
      title: event.name,
    }).addTo(eventsLayer);
    marker.bindPopup(
      `<strong>${escapeHtml(event.name)}</strong><br>${escapeHtml(event.venue)}<br>${escapeHtml(
        formatWhen(event)
      )}`
    );
    marker.on("click", () => selectEvent(event.id, false));
  }

  const points = [];
  if (state.lat != null && state.lon != null) points.push([state.lat, state.lon]);
  for (const event of state.events) {
    if (event.lat != null && event.lon != null) points.push([event.lat, event.lon]);
  }
  if (points.length === 1) map.setView(points[0], 12);
  else if (points.length > 1) map.fitBounds(points, { padding: [36, 36], maxZoom: 13 });
}

function renderList() {
  els.listCount.textContent = `${state.events.length} nearby`;
  els.listTitle.textContent = state.mode === "live" ? "Live events" : "Events near you";
  els.eventList.innerHTML = state.events
    .map(
      (event) => `
      <li>
        <button type="button" class="event-card ${
          event.id === state.activeEventId ? "is-active" : ""
        }" data-id="${escapeAttr(event.id)}">
          <div>
            <h3>${escapeHtml(event.name)}</h3>
            <p class="venue">${escapeHtml(event.venue)}${
              event.city ? ` · ${escapeHtml(event.city)}` : ""
            }</p>
            <p class="meta">${escapeHtml(formatWhen(event))}${
              event.distanceMiles != null ? ` · ${event.distanceMiles} mi` : ""
            }${event.priceRange ? ` · ${escapeHtml(event.priceRange)}` : ""}</p>
          </div>
          <span class="badge">${escapeHtml(event.classification || "Event")}</span>
        </button>
      </li>`
    )
    .join("");
  els.empty.hidden = state.events.length > 0;
}

function selectEvent(id, pan = true) {
  state.activeEventId = id;
  renderList();
  const event = state.events.find((e) => e.id === id);
  if (!event || event.lat == null || event.lon == null) return;
  if (pan) map.setView([event.lat, event.lon], Math.max(map.getZoom(), 13), { animate: true });
  eventsLayer.eachLayer((layer) => {
    if (layer.getLatLng && layer.getPopup) {
      const ll = layer.getLatLng();
      if (Math.abs(ll.lat - event.lat) < 1e-6 && Math.abs(ll.lng - event.lon) < 1e-6) {
        layer.openPopup();
      }
    }
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

async function api(path) {
  const res = await fetch(path);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

async function refreshPlace() {
  if (state.lat == null || state.lon == null) return;
  try {
    const data = await api(`/api/place?lat=${state.lat}&lon=${state.lon}`);
    state.place = data.place;
    updateLocationCard("live");
  } catch {
    /* non-fatal */
  }
}

async function refreshEvents() {
  if (state.lat == null || state.lon == null) {
    setBanner("Share your location to load nearby events.");
    return;
  }

  const params = new URLSearchParams({
    lat: String(state.lat),
    lon: String(state.lon),
    radius: els.radius.value,
    classification: els.classification.value,
    keyword: els.keyword.value.trim(),
  });

  els.listCount.textContent = "Loading…";
  try {
    const data = await api(`/api/events?${params.toString()}`);
    state.events = data.events || [];
    state.mode = data.mode;
    setBanner(data.notice || null);
    renderList();
    renderMap();
  } catch (err) {
    setBanner(err.message);
    state.events = [];
    renderList();
    renderMap();
  }
}

function scheduleRefresh() {
  clearTimeout(fetchTimer);
  fetchTimer = setTimeout(() => {
    refreshPlace();
    refreshEvents();
  }, 250);
}

function applyPosition(coords, { watching = false } = {}) {
  state.lat = coords.latitude;
  state.lon = coords.longitude;
  state.accuracy = coords.accuracy ?? null;
  state.watching = watching;
  updateLocationCard("live");
  els.btnWatch.hidden = false;
  els.btnWatch.textContent = watching ? "Stop tracking" : "Keep tracking";
  scheduleRefresh();
}

function geoError(err) {
  updateLocationCard("error");
  els.locLabel.textContent = "Location unavailable";
  els.locMeta.textContent =
    err?.code === 1
      ? "Permission denied. You can enter coordinates manually."
      : err?.message || "Could not read GPS. Try again or enter coordinates.";
  setBanner(els.locMeta.textContent);
  els.manualDialog.showModal();
}

function locateOnce() {
  if (!navigator.geolocation) {
    geoError({ message: "Geolocation is not supported in this browser." });
    return;
  }
  els.locLabel.textContent = "Locating…";
  els.locMeta.textContent = "Requesting precise location from your device.";
  navigator.geolocation.getCurrentPosition(
    (pos) => applyPosition(pos.coords, { watching: false }),
    geoError,
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
  );
}

function toggleWatch() {
  if (!navigator.geolocation) return;
  if (state.watching && state.watchId != null) {
    navigator.geolocation.clearWatch(state.watchId);
    state.watchId = null;
    state.watching = false;
    updateLocationCard("live");
    els.btnWatch.textContent = "Keep tracking";
    return;
  }
  state.watchId = navigator.geolocation.watchPosition(
    (pos) => applyPosition(pos.coords, { watching: true }),
    geoError,
    { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 }
  );
}

function bindEvents() {
  els.btnLocate.addEventListener("click", locateOnce);
  els.btnWatch.addEventListener("click", toggleWatch);
  els.btnRefresh.addEventListener("click", () => {
    refreshPlace();
    refreshEvents();
  });
  els.radius.addEventListener("change", refreshEvents);
  els.classification.addEventListener("change", refreshEvents);
  els.keyword.addEventListener("keydown", (e) => {
    if (e.key === "Enter") refreshEvents();
  });
  els.eventList.addEventListener("click", (e) => {
    const card = e.target.closest("[data-id]");
    if (!card) return;
    selectEvent(card.dataset.id, true);
  });

  els.manualForm.addEventListener("close", () => {
    if (els.manualDialog.returnValue !== "ok") return;
    const data = new FormData(els.manualForm);
    const lat = Number(data.get("lat"));
    const lon = Number(data.get("lon"));
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    applyPosition({ latitude: lat, longitude: lon, accuracy: null });
  });

  // Long-press / secondary path: open manual entry from locate button when held? Skip.
  els.btnLocate.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    els.manualDialog.showModal();
  });
}

function coordsFromQuery() {
  const params = new URLSearchParams(location.search);
  const lat = Number(params.get("lat"));
  const lon = Number(params.get("lon"));
  if (Number.isFinite(lat) && Number.isFinite(lon)) return { latitude: lat, longitude: lon, accuracy: null };
  return null;
}

async function boot() {
  initMap();
  bindEvents();
  try {
    state.config = await api("/api/config");
    if (!state.config.hasTicketmasterKey) {
      setBanner(
        "Demo mode: events are generated around your location. Add a free Ticketmaster API key for live listings."
      );
    }
  } catch {
    /* ignore */
  }
  const preset = coordsFromQuery();
  if (preset) applyPosition(preset);
  else locateOnce();
}

boot();
