"""Turn a pipeline into the next useful actions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable

from models import CoachAction, Profile


ACTIVE = {"saved", "applied", "interviewing", "offer"}


def coach_actions(
    applications: Iterable[dict[str, Any]],
    profile: Profile | None = None,
    *,
    today: date | None = None,
) -> list[CoachAction]:
    today = today or date.today()
    profile = profile or Profile()
    apps = [row for row in applications if isinstance(row, dict)]
    actions: list[CoachAction] = []

    if profile.is_empty():
        actions.append(
            CoachAction(
                id="profile-empty",
                kind="profile",
                title="Set up your profile",
                detail="Add target titles, skills, and a salary floor so Job Buddy can score listings.",
                urgency="now",
            )
        )

    interviews = []
    for app in apps:
        if str(app.get("status") or "").lower() != "interviewing":
            continue
        when = _parse_date(app.get("interview_at") or app.get("interview_date"))
        interviews.append((app, when))

    for app, when in interviews:
        title = _job_label(app)
        if when is None:
            actions.append(
                CoachAction(
                    id=f"interview-date-{app.get('id')}",
                    kind="interview",
                    title=f"Add an interview date — {title}",
                    detail="You’re in Interviewing. Put a date on the calendar so prep shows up here.",
                    urgency="soon",
                    job_id=str(app.get("id") or "") or None,
                )
            )
            continue
        days = (when - today).days
        if days < 0:
            continue
        if days == 0:
            actions.append(
                CoachAction(
                    id=f"interview-today-{app.get('id')}",
                    kind="interview",
                    title=f"Interview today — {title}",
                    detail="Review your notes and the job post once more before you walk in.",
                    urgency="now",
                    job_id=str(app.get("id") or "") or None,
                )
            )
        elif days <= 3:
            actions.append(
                CoachAction(
                    id=f"interview-soon-{app.get('id')}",
                    kind="interview",
                    title=f"Prep for {title}",
                    detail=f"Interview in {days} day{'s' if days != 1 else ''}. Sketch stories and questions tonight.",
                    urgency="now" if days <= 1 else "soon",
                    job_id=str(app.get("id") or "") or None,
                )
            )

    for app in apps:
        if str(app.get("status") or "").lower() != "applied":
            continue
        applied = _parse_date(app.get("applied_at") or app.get("applied_date"))
        follow = _parse_date(app.get("follow_up_at") or app.get("follow_up_date"))
        title = _job_label(app)
        due = follow or (applied + timedelta(days=5) if applied else None)
        if due is None:
            actions.append(
                CoachAction(
                    id=f"applied-date-{app.get('id')}",
                    kind="follow_up",
                    title=f"Mark when you applied — {title}",
                    detail="A date lets Job Buddy remind you to follow up.",
                    urgency="later",
                    job_id=str(app.get("id") or "") or None,
                )
            )
            continue
        if due <= today:
            wait = (today - (applied or due)).days
            actions.append(
                CoachAction(
                    id=f"follow-{app.get('id')}",
                    kind="follow_up",
                    title=f"Follow up — {title}",
                    detail=(
                        f"It’s been {wait} day{'s' if wait != 1 else ''} since you applied. "
                        "A short check-in keeps you in the pile."
                    ),
                    urgency="now" if wait >= 7 else "soon",
                    job_id=str(app.get("id") or "") or None,
                )
            )

    for app in apps:
        if str(app.get("status") or "").lower() != "offer":
            continue
        title = _job_label(app)
        actions.append(
            CoachAction(
                id=f"offer-{app.get('id')}",
                kind="offer",
                title=f"Offer in hand — {title}",
                detail="Write down comp, deadline, and what you’d still want to know before deciding.",
                urgency="now",
                job_id=str(app.get("id") or "") or None,
            )
        )

    active = [app for app in apps if str(app.get("status") or "").lower() in ACTIVE]
    if len(active) < 3:
        actions.append(
            CoachAction(
                id="discover-thin",
                kind="discover",
                title="Find a few more roles",
                detail="A healthy pipeline has several live threads. Search Discover and save three that fit.",
                urgency="soon" if active else "now",
            )
        )

    return _prioritize(actions)[:8]


def pipeline_stats(applications: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "saved": 0,
        "applied": 0,
        "interviewing": 0,
        "offer": 0,
        "closed": 0,
        "active": 0,
    }
    for app in applications:
        status = str((app or {}).get("status") or "saved").lower()
        if status not in counts:
            status = "saved"
        counts[status] += 1
        if status in ACTIVE:
            counts["active"] += 1
    return counts


def _prioritize(actions: list[CoachAction]) -> list[CoachAction]:
    rank = {"now": 0, "soon": 1, "later": 2}
    kind_rank = {"offer": 0, "interview": 1, "follow_up": 2, "profile": 3, "discover": 4}
    return sorted(
        actions,
        key=lambda action: (rank.get(action.urgency, 9), kind_rank.get(action.kind, 9), action.title),
    )


def _job_label(app: dict[str, Any]) -> str:
    title = str(app.get("title") or "Untitled role").strip()
    company = str(app.get("company") or "").strip()
    return f"{title} at {company}" if company else title


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return date(value.year, value.month, value.day)
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None
