(() => {
  const grid = document.getElementById("listing-grid");
  const statusLine = document.getElementById("status-line");
  const emptyState = document.getElementById("empty-state");
  const errorBanner = document.getElementById("error-banner");
  const watchFilter = document.getElementById("filter-watch");
  const sourceFilter = document.getElementById("filter-source");
  const sortFilter = document.getElementById("filter-sort");
  const refreshBtn = document.getElementById("refresh-btn");

  let listings = [];

  const money = (value) =>
    value == null ? "Price n/a" : `$${Number(value).toLocaleString("en-US")}`;

  const miles = (value) =>
    value == null ? "Mileage n/a" : `${Number(value).toLocaleString("en-US")} mi`;

  const sourceLabel = (source) => {
    const labels = {
      "cars.com": "Cars.com",
      bringatrailer: "Bring a Trailer",
      autotrader: "Autotrader",
      ebay: "eBay",
      hemmings: "Hemmings",
      cargurus: "CarGurus",
      truecar: "TrueCar",
      carsandbids: "Cars & Bids",
      carvana: "Carvana",
      facebook: "Facebook Marketplace",
      marketcheck: "MarketCheck",
    };
    return labels[source] || source;
  };

  const modelLabel = (item) => {
    if (item.watch_id === "porsche-cayman") return "Cayman";
    if (item.watch_id === "honda-s2000") return "S2000";
    return item.model || "Car";
  };

  const scoreTone = (score) => {
    if (score == null) return "muted";
    if (score >= 80) return "great";
    if (score >= 65) return "good";
    if (score >= 45) return "fair";
    if (score >= 30) return "soft";
    return "stretched";
  };

  function sortedFiltered() {
    let rows = [...listings];
    const watch = watchFilter.value;
    if (watch !== "all") {
      rows = rows.filter((row) => row.watch_id === watch);
    }
    const source = sourceFilter.value;
    if (source !== "all") {
      rows = rows.filter((row) => row.source === source);
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

  function render() {
    const rows = sortedFiltered();
    grid.innerHTML = "";
    emptyState.hidden = rows.length > 0;

    rows.forEach((item, index) => {
      const card = document.createElement("a");
      card.className = "listing";
      card.href = item.url;
      card.target = "_blank";
      card.rel = "noopener noreferrer";
      card.style.animationDelay = `${Math.min(index, 12) * 45}ms`;

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

      card.append(media, body, price);
      grid.appendChild(card);
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  async function load(force = false) {
    const baseUrl = window.S2K_API_URL || "/api/listings";
    const isStaticJson = /\.json(\?|$)/i.test(baseUrl);
    statusLine.textContent = force ? "Refreshing live inventory…" : "Loading live inventory…";
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
      statusLine.textContent = `${data.count} cars · ${s2k} S2000 · ${cayman} Cayman · updated ${when}`;

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

  watchFilter.addEventListener("change", render);
  sourceFilter.addEventListener("change", render);
  sortFilter.addEventListener("change", render);
  refreshBtn.addEventListener("click", () => load(true));

  load(false);
})();
