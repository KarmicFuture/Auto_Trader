"use strict";

const express = require("express");

const TM_BASE = "https://app.ticketmaster.com/discovery/v2/events.json";
const NOMINATIM = "https://nominatim.openstreetmap.org/reverse";

function toNumber(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function haversineMiles(lat1, lon1, lat2, lon2) {
  const toRad = (d) => (d * Math.PI) / 180;
  const R = 3958.8;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function offsetLatLon(lat, lon, milesNorth, milesEast) {
  const lat2 = lat + milesNorth / 69.0;
  const lon2 = lon + milesEast / (69.0 * Math.cos((lat * Math.PI) / 180));
  return { lat: lat2, lon: lon2 };
}

function buildDemoEvents(lat, lon, radius, keyword, classification) {
  const templates = [
    {
      name: "Sunset Jazz in the Park",
      classification: "Music",
      genre: "Jazz",
      venue: "Riverside Amphitheater",
      offset: [1.2, -0.8],
      hours: 6,
      price: "$25–$45",
    },
    {
      name: "Neighborhood Food Night Market",
      classification: "Miscellaneous",
      genre: "Food & Drink",
      venue: "Market Square",
      offset: [-0.6, 1.4],
      hours: 28,
      price: "Free entry",
    },
    {
      name: "Indie Film Outdoor Screening",
      classification: "Film",
      genre: "Independent",
      venue: "Community Lawn",
      offset: [2.1, 0.5],
      hours: 52,
      price: "$12",
    },
    {
      name: "Local FC Home Match",
      classification: "Sports",
      genre: "Soccer",
      venue: "City Stadium",
      offset: [-3.0, 2.2],
      hours: 74,
      price: "$30–$90",
    },
    {
      name: "Comedy Club Late Show",
      classification: "Arts & Theatre",
      genre: "Comedy",
      venue: "The Copper Room",
      offset: [0.4, -1.1],
      hours: 10,
      price: "$18",
    },
    {
      name: "Weekend Maker Fair",
      classification: "Miscellaneous",
      genre: "Festival",
      venue: "Expo Hall",
      offset: [4.5, -2.0],
      hours: 96,
      price: "$8",
    },
    {
      name: "Chamber Orchestra Evening",
      classification: "Music",
      genre: "Classical",
      venue: "Civic Concert Hall",
      offset: [-1.8, -2.4],
      hours: 120,
      price: "$40–$75",
    },
    {
      name: "Tech Meetup: Build Night",
      classification: "Miscellaneous",
      genre: "Networking",
      venue: "Innovation Hub",
      offset: [0.9, 0.3],
      hours: 34,
      price: "Free",
    },
  ];

  const now = Date.now();
  let events = templates.map((t, i) => {
    const loc = offsetLatLon(lat, lon, t.offset[0], t.offset[1]);
    const start = new Date(now + t.hours * 3600 * 1000);
    const distance = haversineMiles(lat, lon, loc.lat, loc.lon);
    return {
      id: `demo-${i + 1}`,
      name: t.name,
      url: null,
      image: null,
      classification: t.classification,
      genre: t.genre,
      start: start.toISOString(),
      localDate: start.toISOString().slice(0, 10),
      localTime: start.toTimeString().slice(0, 5),
      venue: t.venue,
      city: "Near you",
      state: "",
      address: "",
      lat: loc.lat,
      lon: loc.lon,
      distanceMiles: Number(distance.toFixed(1)),
      priceRange: t.price,
      source: "demo",
    };
  });

  events = events.filter((e) => e.distanceMiles <= radius);
  if (keyword) {
    const q = keyword.toLowerCase();
    events = events.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.venue.toLowerCase().includes(q) ||
        e.genre.toLowerCase().includes(q)
    );
  }
  if (classification) {
    const c = classification.toLowerCase();
    events = events.filter((e) => e.classification.toLowerCase().includes(c));
  }
  events.sort((a, b) => a.distanceMiles - b.distanceMiles);
  return events;
}

function normalizeTicketmasterEvent(raw, userLat, userLon) {
  const venue = raw._embedded?.venues?.[0] || {};
  const loc = venue.location || {};
  const evLat = Number(loc.latitude);
  const evLon = Number(loc.longitude);
  const dates = raw.dates?.start || {};
  const classif = raw.classifications?.[0] || {};
  const images = Array.isArray(raw.images) ? raw.images : [];
  const image =
    images.find((img) => img.ratio === "16_9" && img.width >= 600)?.url ||
    images[0]?.url ||
    null;
  const price = raw.priceRanges?.[0];
  let priceRange = null;
  if (price) {
    const min = price.min != null ? `$${price.min}` : "";
    const max = price.max != null ? `$${price.max}` : "";
    priceRange = min && max && min !== max ? `${min}–${max}` : min || max;
  }

  const distance =
    Number.isFinite(evLat) && Number.isFinite(evLon)
      ? Number(haversineMiles(userLat, userLon, evLat, evLon).toFixed(1))
      : null;

  return {
    id: raw.id,
    name: raw.name,
    url: raw.url || null,
    image,
    classification: classif.segment?.name || "Event",
    genre: classif.genre?.name || "",
    start: dates.dateTime || null,
    localDate: dates.localDate || null,
    localTime: dates.localTime || null,
    venue: venue.name || "Venue TBA",
    city: venue.city?.name || "",
    state: venue.state?.stateCode || "",
    address: venue.address?.line1 || "",
    lat: Number.isFinite(evLat) ? evLat : null,
    lon: Number.isFinite(evLon) ? evLon : null,
    distanceMiles: distance,
    priceRange,
    source: "ticketmaster",
  };
}

async function fetchTicketmasterEvents({ lat, lon, radius, keyword, classification, size }) {
  const key = process.env.TICKETMASTER_API_KEY;
  if (!key) return null;

  const params = new URLSearchParams({
    apikey: key,
    latlong: `${lat},${lon}`,
    radius: String(radius),
    unit: "miles",
    size: String(size),
    sort: "distance,asc",
  });
  if (keyword) params.set("keyword", keyword);
  if (classification) params.set("classificationName", classification);

  const res = await fetch(`${TM_BASE}?${params.toString()}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    const err = new Error(`Ticketmaster error ${res.status}`);
    err.status = res.status;
    err.detail = text.slice(0, 300);
    throw err;
  }
  const data = await res.json();
  const rawEvents = data._embedded?.events || [];
  return rawEvents.map((e) => normalizeTicketmasterEvent(e, lat, lon));
}

async function reverseGeocode(lat, lon) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    format: "json",
    zoom: "12",
  });
  const res = await fetch(`${NOMINATIM}?${params.toString()}`, {
    headers: {
      Accept: "application/json",
      "User-Agent": "NearbyEventsDashboard/1.0 (local demo)",
    },
  });
  if (!res.ok) return null;
  const data = await res.json();
  const addr = data.address || {};
  return {
    displayName: data.display_name || null,
    neighborhood: addr.neighbourhood || addr.suburb || addr.quarter || null,
    city: addr.city || addr.town || addr.village || addr.municipality || null,
    state: addr.state || null,
    country: addr.country || null,
  };
}

function createApiRouter() {
  const router = express.Router();

  router.get("/config", (_req, res) => {
    res.json({
      hasTicketmasterKey: Boolean(process.env.TICKETMASTER_API_KEY),
      defaultRadiusMiles: 25,
      maxRadiusMiles: 100,
    });
  });

  router.get("/place", async (req, res) => {
    const lat = toNumber(req.query.lat, NaN);
    const lon = toNumber(req.query.lon, NaN);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return res.status(400).json({ error: "lat and lon are required" });
    }
    try {
      const place = await reverseGeocode(lat, lon);
      return res.json({ lat, lon, place });
    } catch (err) {
      return res.status(502).json({ error: "Reverse geocoding failed", detail: String(err.message) });
    }
  });

  router.get("/events", async (req, res) => {
    const lat = toNumber(req.query.lat, NaN);
    const lon = toNumber(req.query.lon, NaN);
    const radius = Math.min(Math.max(toNumber(req.query.radius, 25), 1), 100);
    const keyword = String(req.query.keyword || "").trim();
    const classification = String(req.query.classification || "").trim();
    const size = Math.min(Math.max(toNumber(req.query.size, 40), 1), 100);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return res.status(400).json({ error: "lat and lon are required" });
    }

    try {
      const live = await fetchTicketmasterEvents({
        lat,
        lon,
        radius,
        keyword,
        classification,
        size,
      });

      if (live) {
        return res.json({
          mode: "live",
          provider: "ticketmaster",
          lat,
          lon,
          radius,
          count: live.length,
          events: live,
        });
      }

      const demo = buildDemoEvents(lat, lon, radius, keyword, classification);
      return res.json({
        mode: "demo",
        provider: "demo",
        lat,
        lon,
        radius,
        count: demo.length,
        events: demo,
        notice:
          "Showing demo events around your location. Add TICKETMASTER_API_KEY for live Ticketmaster listings.",
      });
    } catch (err) {
      const demo = buildDemoEvents(lat, lon, radius, keyword, classification);
      return res.status(200).json({
        mode: "demo",
        provider: "demo",
        lat,
        lon,
        radius,
        count: demo.length,
        events: demo,
        notice: `Live events unavailable (${err.message}). Showing demo events instead.`,
      });
    }
  });

  return router;
}

module.exports = {
  createApiRouter,
  buildDemoEvents,
  haversineMiles,
};
