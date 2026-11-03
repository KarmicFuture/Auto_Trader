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

  const sourceLabel = (source, status) => {
    const label = source || "Unknown";
    return status === "active" ? label : `${label} (inactive)`;
  };
