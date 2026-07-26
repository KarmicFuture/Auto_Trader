(() => {
  const grid = document.getElementById("listing-grid");
  const statusLine = document.getElementById("status-line");
  const emptyState = document.getElementById("empty-state");
  const errorBanner = document.getElementById("error-banner");
  const sourceFilter = document.getElementById("filter-source");
  const sortFilter = document.getElementById("filter-sort");
  const refreshBtn = document.getElementById("refresh-btn");

  let listings = [];

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

  function sortedFiltered() {
    let rows = [...listings];
    const source = sourceFilter.value;
    if (source !== "all") {
      rows = rows.filter((row) => row.source === source);
    }

    const sort = sortFilter.value;
    rows.sort((a, b) => {
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
          fallback.textContent = "S2000";
          media.appendChild(fallback);
        });
        media.appendChild(img);
      } else {
        const fallback = document.createElement("div");
        fallback.className = "listing__fallback";
        fallback.textContent = "S2000";
        media.appendChild(fallback);
      }

      const body = document.createElement("div");
      body.className = "listing__body";
      body.innerHTML = `
        <p class="listing__source">${sourceLabel(item.source)}</p>
        <h3 class="listing__title">${escapeHtml(item.title)}</h3>
        <p class="listing__meta">${escapeHtml(
          [miles(item.mileage), item.location || "United States"].filter(Boolean).join(" · ")
        )}</p>
      `;

      const price = document.createElement("div");
      price.className = "listing__price";
      price.innerHTML = `
        <strong>${money(item.price)}</strong>
        <span>${item.year ?? "S2000"}</span>
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
    statusLine.textContent = force ? "Refreshing live inventory…" : "Loading live S2000s…";
    refreshBtn.disabled = true;
    try {
      const response = await fetch(`/api/listings${force ? "?refresh=true" : ""}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      listings = data.listings || [];
      const when = data.refreshed_at
        ? new Date(data.refreshed_at).toLocaleString()
        : "just now";
      statusLine.textContent = `${data.count} S2000s across the US · updated ${when}`;

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

  sourceFilter.addEventListener("change", render);
  sortFilter.addEventListener("change", render);
  refreshBtn.addEventListener("click", () => load(true));

  load(false);
})();
