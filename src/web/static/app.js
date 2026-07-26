(() => {
  const grid = document.getElementById("listing-grid");
  const savedGrid = document.getElementById("saved-grid");
  const statusLine = document.getElementById("status-line");
  const emptyState = document.getElementById("empty-state");
  const savedEmpty = document.getElementById("saved-empty");
  const errorBanner = document.getElementById("error-banner");
  const watchFilter = document.getElementById("filter-watch");
  const sourceFilter = document.getElementById("filter-source");
  const sortFilter = document.getElementById("filter-sort");
  const priceFilter = document.getElementById("filter-price");
  const valueFilter = document.getElementById("filter-value");
  const searchFilter = document.getElementById("filter-search");
  const refreshBtn = document.getElementById("refresh-btn");
  const installBtn = document.getElementById("install-btn");
  const savedCount = document.getElementById("saved-count");
  const tabs = [...document.querySelectorAll(".tab")];
  const views = [...document.querySelectorAll(".view")];

  const STORAGE_KEY = "auto-board-saved-v1";

  let listings = [];
  let savedIds = loadSavedIds();
  let currentView = "board";
  let deferredInstall = null;

  const money = (value) =>
    value == null ? "Price n/a" : `$${Number(value).toLocaleString("en-US")}`;

  const miles = (value) =>
    value == null ? "Mileage n/a" : `${Number(value).toLocaleString("en-US")} mi`;

  const sourceLabel = (source) => {
    if (source === "cars.com") return "Cars.com";
    if (source === "bringatrailer") return "Bring a Trailer";
    if (source === "autotrader") return "Autotrader";
    return source;
  };

  const modelLabel = (item) => {
    if (item.watch_id === "porsche-cayman") return "Cayman";
    if (item.watch_id === "honda-s2000") return "S2000";
    return item.model || "Car";
  };

  const listingKey = (item) => `${item.source}:${item.id}`;

  const scoreTone = (score) => {
    if (score == null) return "muted";
    if (score >= 80) return "great";
    if (score >= 65) return "good";
    if (score >= 45) return "fair";
    if (score >= 30) return "soft";
    return "stretched";
  };

  function loadSavedIds() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return new Set(Array.isArray(parsed) ? parsed : []);
    } catch {
      return new Set();
    }
  }

  function persistSaved() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...savedIds]));
    const count = savedIds.size;
    savedCount.hidden = count === 0;
    savedCount.textContent = String(count);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function matchesSearch(item, query) {
    if (!query) return true;
    const hay = [
      item.title,
      item.make,
      item.model,
      item.location,
      item.source,
      item.year,
      item.value_label,
    ]
      .filter((part) => part != null)
      .join(" ")
      .toLowerCase();
    return hay.includes(query);
  }

  function sortedFiltered(pool) {
    let rows = [...pool];
    const watch = watchFilter.value;
    if (watch !== "all") {
      rows = rows.filter((row) => row.watch_id === watch);
    }
    const source = sourceFilter.value;
    if (source !== "all") {
      rows = rows.filter((row) => row.source === source);
    }
    const maxPrice = priceFilter.value;
    if (maxPrice !== "all") {
      const cap = Number(maxPrice);
      rows = rows.filter((row) => row.price != null && row.price <= cap);
    }
    const minValue = valueFilter.value;
    if (minValue !== "all") {
      const floor = Number(minValue);
      rows = rows.filter((row) => (row.value_score ?? -1) >= floor);
    }
    const query = searchFilter.value.trim().toLowerCase();
    if (query) {
      rows = rows.filter((row) => matchesSearch(row, query));
    }

    const sort = sortFilter.value;
    rows.sort((a, b) => {
      if (sort === "value-desc") return (b.value_score ?? -1) - (a.value_score ?? -1);
      if (sort === "price-asc") return (a.price ?? 1e12) - (b.price ?? 1e12);
      if (sort === "price-desc") return (b.price ?? -1) - (a.price ?? -1);
      if (sort === "year-desc") return (b.year ?? 0) - (a.year ?? 0);
      if (sort === "mileage-asc") return (a.mileage ?? 1e12) - (b.mileage ?? 1e12);
      return 0;
    });
    return rows;
  }

  function createListingCard(item, index) {
    const card = document.createElement("a");
    card.className = "listing";
    card.href = item.url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";
    card.style.animationDelay = `${Math.min(index, 12) * 40}ms`;

    const key = listingKey(item);
    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "listing__save";
    saveBtn.setAttribute("aria-label", savedIds.has(key) ? "Unsave listing" : "Save listing");
    saveBtn.setAttribute("aria-pressed", savedIds.has(key) ? "true" : "false");
    saveBtn.textContent = savedIds.has(key) ? "★" : "☆";
    saveBtn.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (savedIds.has(key)) savedIds.delete(key);
      else savedIds.add(key);
      persistSaved();
      render();
    });

    const media = document.createElement("div");
    media.className = "listing__media";
    const fallbackText = modelLabel(item);
    if (item.thumbnail) {
      const img = document.createElement("img");
      img.className = "listing__img";
      img.src = item.thumbnail;
      img.alt = item.title;
      img.loading = "lazy";
      img.referrerPolicy = "no-referrer";
      img.addEventListener("error", () => {
        img.remove();
        const fallback = document.createElement("div");
        fallback.className = "listing__fallback";
        fallback.textContent = fallbackText;
        media.appendChild(fallback);
      });
      media.appendChild(img);
    } else {
      const fallback = document.createElement("div");
      fallback.className = "listing__fallback";
      fallback.textContent = fallbackText;
      media.appendChild(fallback);
    }

    const delta =
      item.value_delta == null
        ? ""
        : item.value_delta <= 0
          ? `${money(Math.abs(item.value_delta))} under fair`
          : `${money(item.value_delta)} over fair`;

    const body = document.createElement("div");
    body.className = "listing__body";
    body.innerHTML = `
      <p class="listing__source">${sourceLabel(item.source)} · ${escapeHtml(
        item.make && item.model ? `${item.make} ${item.model}` : modelLabel(item)
      )}</p>
      <h3 class="listing__title">${escapeHtml(item.title)}</h3>
      <p class="listing__meta">${escapeHtml(
        [miles(item.mileage), item.location || "United States"].filter(Boolean).join(" · ")
      )}</p>
      <p class="listing__value-note">${escapeHtml(
        item.fair_value != null
          ? `Fair value ${money(item.fair_value)}${delta ? ` · ${delta}` : ""}`
          : "Fair value unavailable"
      )}</p>
    `;

    const price = document.createElement("div");
    price.className = "listing__price";
    const tone = scoreTone(item.value_score);
    price.innerHTML = `
      <strong>${money(item.price)}</strong>
      <span class="value-pill value-pill--${tone}">
        ${item.value_score == null ? "No score" : `Value ${item.value_score}`}
      </span>
      <span>${escapeHtml(item.value_label || item.year || modelLabel(item))}</span>
    `;

    card.append(saveBtn, media, body, price);
    return card;
  }

  function renderGrid(target, rows, emptyEl) {
    target.innerHTML = "";
    emptyEl.hidden = rows.length > 0;
    rows.forEach((item, index) => {
      target.appendChild(createListingCard(item, index));
    });
  }

  function render() {
    if (currentView === "board") {
      renderGrid(grid, sortedFiltered(listings), emptyState);
    } else if (currentView === "saved") {
      const saved = listings.filter((item) => savedIds.has(listingKey(item)));
      renderGrid(savedGrid, sortedFiltered(saved), savedEmpty);
      if (!saved.length) {
        savedEmpty.hidden = false;
        savedEmpty.textContent = "No saved cars yet. Star a listing from the board.";
      } else if (!sortedFiltered(saved).length) {
        savedEmpty.hidden = false;
        savedEmpty.textContent = "No saved cars matched those filters.";
      }
    }
    persistSaved();
  }

  function setView(name) {
    currentView = name;
    views.forEach((view) => {
      const active = view.dataset.view === name;
      view.hidden = !active;
      view.classList.toggle("view--active", active);
    });
    tabs.forEach((tab) => {
      const active = tab.dataset.nav === name;
      tab.classList.toggle("tab--active", active);
      if (active) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    });
    render();
  }

  async function load(force = false) {
    const baseUrl = window.S2K_API_URL || "/api/listings";
    const isStaticJson = /\.json(\?|$)/i.test(baseUrl);
    statusLine.textContent = force ? "Refreshing…" : "Loading inventory…";
    refreshBtn.disabled = true;
    if (isStaticJson) {
      refreshBtn.hidden = true;
    }
    try {
      const url =
        force && !isStaticJson
          ? `${baseUrl}${baseUrl.includes("?") ? "&" : "?"}refresh=true`
          : baseUrl;
      const response = await fetch(url, { cache: force ? "no-store" : "default" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      listings = data.listings || [];
      const when = data.refreshed_at
        ? new Date(data.refreshed_at).toLocaleString()
        : "just now";
      const s2k = listings.filter((x) => x.watch_id === "honda-s2000").length;
      const cayman = listings.filter((x) => x.watch_id === "porsche-cayman").length;
      statusLine.textContent = `${data.count} cars · ${s2k} S2000 · ${cayman} Cayman · ${when}`;

      if (data.errors && data.errors.length) {
        errorBanner.hidden = false;
        errorBanner.textContent = `Some sources were unavailable: ${data.errors.join(" · ")}`;
      } else {
        errorBanner.hidden = true;
      }
      render();
    } catch (err) {
      statusLine.textContent = "Could not load listings.";
      errorBanner.hidden = false;
      errorBanner.textContent = String(err.message || err);
    } finally {
      refreshBtn.disabled = false;
    }
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    const swUrl = window.S2K_SW_URL || "./sw.js";
    window.addEventListener("load", () => {
      navigator.serviceWorker.register(swUrl).catch(() => {
        /* ignore SW failures on file:// or restricted hosts */
      });
    });
  }

  watchFilter.addEventListener("change", render);
  sourceFilter.addEventListener("change", render);
  sortFilter.addEventListener("change", render);
  priceFilter.addEventListener("change", render);
  valueFilter.addEventListener("change", render);
  searchFilter.addEventListener("input", render);
  refreshBtn.addEventListener("click", () => load(true));
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => setView(tab.dataset.nav));
  });

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstall = event;
    installBtn.hidden = false;
  });

  installBtn.addEventListener("click", async () => {
    if (!deferredInstall) return;
    deferredInstall.prompt();
    await deferredInstall.userChoice;
    deferredInstall = null;
    installBtn.hidden = true;
  });

  window.addEventListener("appinstalled", () => {
    installBtn.hidden = true;
    deferredInstall = null;
  });

  persistSaved();
  registerServiceWorker();
  load(false);
})();
