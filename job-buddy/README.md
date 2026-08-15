# Job Buddy

A job-finding website: create an account, save it, upload a resume, then use practical tips for the search.

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

## Flow

1. **Landing** — create an account (or sign in)
2. **Account is saved** in a local SQLite database (`data/jobbuddy.sqlite`)
3. **Resume upload** — PDF, Word, RTF, or text (max 8 MB)
4. **Desk** — tips and tricks for finding jobs

Passwords are hashed with PBKDF2. Sessions use an HTTP-only cookie. Resume files stay on disk under `data/resumes/`.
