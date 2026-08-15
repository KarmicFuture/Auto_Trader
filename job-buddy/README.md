# Job Buddy

Personal career desk: search live job boards, score each listing against your profile, and keep applications moving.

This lives in `Auto_Trader` because this agent’s GitHub access is scoped to that repo. It can move to its own repository later.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 job-buddy/server.py
```

Open http://localhost:3030

## What it does

- **Today** — follow-ups, interviews, and the next useful action
- **Discover** — Remotive, Arbeitnow, and RemoteOK (no API keys). Falls back to demo roles if boards are unreachable
- **Pipeline** — Saved → Applied → Interviewing → Offer → Closed (drag cards between columns)
- **Profile** — target titles, skills, cities, remote preference, salary floor

Fit scores (0–100) compare a listing to your profile: title, skills, location/remote, and pay. Profile and pipeline are stored in the browser (`localStorage`).

## Tests

```bash
python3 -m pytest tests/test_job_buddy.py -q
```
