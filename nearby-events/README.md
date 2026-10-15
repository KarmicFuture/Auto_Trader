# Nearby Events

Location-aware dashboard that finds **events happening near you**.

Uses the browser **Geolocation API** (with optional continuous tracking), plots you and nearby events on a map, and lists what’s coming up within your chosen radius.

## Preview

```bash
cd nearby-events
npm install
npm run dev
```

Open [http://localhost:3020](http://localhost:3020) and allow location access when prompted.

- **Use my location** — one-shot GPS fix  
- **Keep tracking** — `watchPosition` updates as you move  
- Right-click **Use my location** — enter lat/lon manually if GPS is blocked  

Health: [http://localhost:3020/health](http://localhost:3020/health)

## Live events (optional)

Without a key, the app shows **demo events** centered on your coordinates so the UI still works.

1. Get a free Consumer Key at [developer.ticketmaster.com](https://developer.ticketmaster.com/)
2. Copy `.env.example` → `.env` and set `TICKETMASTER_API_KEY=...`
3. Restart `npm run dev`

The server proxies Ticketmaster so your key never ships to the browser.

## Stack

- Node 18+ / Express
- Leaflet + CARTO dark basemap
- OpenStreetMap Nominatim for reverse geocoding (place label)

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/config` | Whether a Ticketmaster key is configured |
| GET | `/api/place?lat=&lon=` | Reverse-geocode a friendly place name |
| GET | `/api/events?lat=&lon=&radius=&keyword=&classification=` | Nearby events (live or demo) |
