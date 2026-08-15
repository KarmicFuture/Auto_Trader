#!/usr/bin/env python3
"""Job Buddy — local career desk."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coach import coach_actions, pipeline_stats  # noqa: E402
from models import Profile  # noqa: E402
from score import apply_fit  # noqa: E402
from sources import search_jobs  # noqa: E402

PUBLIC = ROOT / "public"

app = FastAPI(title="Job Buddy", description="Search, score, and track job applications.")


class CoachRequest(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    applications: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "job-buddy"}


@app.get("/api/jobs")
def api_jobs(
    q: str = Query("", description="Keyword, title, or skill"),
    location: str = Query(""),
    remote: bool = Query(False),
    live: bool = Query(True),
    name: str = Query(""),
    titles: str = Query(""),
    skills: str = Query(""),
    locations: str = Query(""),
    work: str = Query("any"),
    min_salary: int | None = Query(None, ge=0, le=1_000_000),
) -> dict[str, Any]:
    jobs, errors, mode = search_jobs(
        query=q,
        location=location,
        remote_only=remote,
        live=live,
    )
    profile = Profile.from_dict(
        {
            "name": name,
            "titles": titles,
            "skills": skills,
            "locations": locations or location,
            "remote": work,
            "min_salary": min_salary,
        }
    )
    scored = [apply_fit(job, profile).to_dict() for job in jobs]
    scored.sort(key=lambda row: (row.get("fit_score") is None, -(row.get("fit_score") or 0)))
    return {
        "jobs": scored[:60],
        "count": min(len(scored), 60),
        "mode": mode,
        "errors": errors,
        "profile_empty": profile.is_empty(),
    }


@app.post("/api/coach")
def api_coach(body: CoachRequest) -> dict[str, Any]:
    profile = Profile.from_dict(body.profile)
    actions = [action.to_dict() for action in coach_actions(body.applications, profile)]
    return {
        "actions": actions,
        "stats": pipeline_stats(body.applications),
        "profile_empty": profile.is_empty(),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


app.mount("/css", StaticFiles(directory=PUBLIC / "css"), name="css")
app.mount("/js", StaticFiles(directory=PUBLIC / "js"), name="js")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3030)


if __name__ == "__main__":
    main()
