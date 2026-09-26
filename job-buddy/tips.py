"""Job-search tips shown after a user has an account (and ideally a resume)."""

from __future__ import annotations

TIPS = [
    {
        "id": "resume-one-page",
        "category": "Resume",
        "title": "Lead with proof, not duties",
        "body": "Rewrite each bullet as what changed because you were there: a number, a before/after, or a decision you owned. Hiring managers skim for evidence.",
    },
    {
        "id": "resume-ats",
        "category": "Resume",
        "title": "Mirror the language in the posting",
        "body": "If the role says “Python” and “stakeholder updates,” those exact phrases should appear where they are true. Applicant-tracking filters are literal.",
    },
    {
        "id": "search-target",
        "category": "Search",
        "title": "Pick a lane for two weeks",
        "body": "Choose one title and two industries. A narrower search makes your resume, outreach, and stories consistent — and you will hear back faster.",
    },
    {
        "id": "search-people",
        "category": "Search",
        "title": "Find the person, not only the portal",
        "body": "For every posting, look up the hiring manager or a teammate. A short, specific note beats another silent Apply click.",
    },
    {
        "id": "network-warm",
        "category": "Outreach",
        "title": "Start with people who already know your work",
        "body": "Former teammates and managers are the highest-yield path. Ask for a conversation and a referral only after they understand what you want next.",
    },
    {
        "id": "network-note",
        "category": "Outreach",
        "title": "Keep the first note under 80 words",
        "body": "Who you are, why them, and one clear ask (15 minutes or a referral). Attach nothing on the first touch unless they asked.",
    },
    {
        "id": "interview-stories",
        "category": "Interviews",
        "title": "Prepare six stories, not fifty answers",
        "body": "Cover a win, a miss, a conflict, a tight deadline, a time you taught someone, and a time you changed your mind. Most questions map onto those.",
    },
    {
        "id": "interview-ask",
        "category": "Interviews",
        "title": "Ask how success is measured at 90 days",
        "body": "That question shows you intend to deliver. Write down the answer — it becomes your scorecard if you get the offer.",
    },
    {
        "id": "follow-up",
        "category": "Process",
        "title": "Follow up once, then put a date on it",
        "body": "Five business days after applying or interviewing, send a short check-in. Then wait. Chasing daily reads as anxiety, not interest.",
    },
    {
        "id": "energy",
        "category": "Process",
        "title": "Protect the job you already have",
        "body": "Search in defined blocks. Sleep and a current paycheck are part of leverage. Burnout shows up in interviews before it shows up on a calendar.",
    },
]


def all_tips() -> list[dict[str, str]]:
    return list(TIPS)
