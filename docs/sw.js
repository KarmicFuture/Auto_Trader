/* Auto Board service worker — cache app shell + last listings snapshot. */
const CACHE = "auto-board-v1";
const SHELL = [
  "./",
  "./index.html",
  "./static/styles.css",
  "./static/app.js",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
  "./static/icons/apple-touch-icon.png",
  "./manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  const isListingData =
    url.pathname.endsWith("/api/listings") || url.pathname.endsWith("/listings.json");

  if (isListingData) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request));
  }
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE);
  try {
    const fresh = await fetch(request);
    if (fresh.ok) {
      cache.put(request, fresh.clone());
    }
    return fresh;
  } catch {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw new Error("offline");
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const fresh = await fetch(request);
    const cache = await caches.open(CACHE);
    if (fresh.ok && request.url.startsWith(self.location.origin)) {
      cache.put(request, fresh.clone());
    }
    return fresh;
  } catch {
    if (request.mode === "navigate") {
      const fallback = await caches.match("./index.html");
      if (fallback) return fallback;
    }
    throw new Error("offline");
  }
}
