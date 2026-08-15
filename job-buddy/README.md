# Job Buddy

A job-finding website: create an account, upload a resume, add people you know, then swipe jobs only at their companies.

This project is self-contained. This agent can only open pull requests on `KarmicFuture/Auto_Trader`, so the app currently lives in that repo under `job-buddy/`. To put it in its own GitHub repository:

```bash
gh repo create Job_Buddy --private --source=job-buddy --remote=job-buddy --push
```

Or from the `job-buddy/` folder:

```bash
git init
git add .
git commit -m "Initial Job Buddy site"
gh repo create Job_Buddy --private --source=. --remote=origin --push
```

## Run

```bash
cd job-buddy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 server.py
```

Open http://localhost:3040

## LinkedIn sign-on

The landing page offers **Continue with LinkedIn** (OpenID Connect: `openid profile email`).

1. Create an app at [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Add the product **Sign In with LinkedIn using OpenID Connect**
3. Under Auth, set the redirect URL to `http://localhost:3040/api/auth/linkedin/callback`
4. Copy `.env.example` to `.env` and fill in the client id and secret

```bash
cp .env.example .env
```

Without those values, the LinkedIn button still appears and explains that sign-on is not configured yet. Email signup keeps working.

A LinkedIn login creates (or links) a Job Buddy account, then continues to **resume upload** if none is on file.

## Warm swipe

Job Buddy never shows a cold job board. After a resume is on file:

1. Add people you know (name, company, how you know them)
2. The deck is **only** roles at those companies
3. Swipe right to save an intro, left to pass

LinkedIn’s sign-in product does not share your connection list, so you add the people yourself. If a company isn’t in the catalog, you still get an intro card for that person.

## Flow

1. **Landing** — create an account (or sign in with LinkedIn)
2. **Account is saved** in a local SQLite database (`data/jobbuddy.sqlite`)
3. **Resume upload** — PDF, Word, RTF, or text (max 8 MB)
4. **People you know** — name + company
5. **Swipe** — Tinder-style cards, only jobs linked to those people
6. **Tips** — still on the desk

Passwords are hashed with PBKDF2. Sessions use an HTTP-only cookie. Resume files stay on disk under `data/resumes/`.
