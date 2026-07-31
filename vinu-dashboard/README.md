> **Repo note:** This app is intended to live in its own GitHub repository (`KarmicFuture/vinu-dashboard`). It is checked into Auto_Trader temporarily so the scaffold is on GitHub until that repo exists and Cursor is granted access to it.

# Vinu Dashboard

Operations console for **[Vinu.us](https://vinu.us)** — track launch readiness, pages, related projects, and day-to-day tasks for Vinod Kumar’s personal brand site.

## Preview

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

Health check: [http://localhost:3000/health](http://localhost:3000/health)

## What’s inside

- **Overview** — site status, launch progress, activity, open tasks
- **Pages** — Vinu.us surfaces (home, about, work, contact)
- **Projects** — linked Karmic Futures / Vinu builds
- **Launch** — checklist from brand lock to full-site go-live
- **Tasks** — lightweight to-dos persisted in `data/dashboard-state.json`

## Stack

- Node.js 18+
- Express (CommonJS entry `app.js` for simple Hostinger-style deploys)
- Static UI in `public/` (Fraunces + DM Sans)

## Deploy notes (Hostinger / Node web app)

1. Connect GitHub repo `KarmicFuture/vinu-dashboard`
2. Framework: **Express.js**
3. Node: **20**
4. Build: `npm run build` (optional; copies into `dist/`)
5. Start: `npm start`
6. Entry file: `app.js`
7. Output directory: leave empty (prefer root `app.js`)

Do not set `PORT` yourself on Hostinger.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/overview` | Summary metrics |
| GET | `/api/pages` | Page inventory |
| GET | `/api/projects` | Related projects |
| GET/PATCH | `/api/checklist`, `/api/checklist/:id` | Launch checklist |
| GET/POST/PATCH/DELETE | `/api/tasks` | Task CRUD |
| GET | `/api/activity` | Recent activity |

## License

Private project for Vinu.us / KarmicFuture.
