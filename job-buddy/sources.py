"""Normalize public job boards. Failures fall back to demo listings."""

from __future__ import annotations

import re
import time
from typing import Any, Callable
from urllib.parse import urlencode

import requests

from demo_jobs import demo_jobs
from models import Job
from score import parse_salary

USER_AGENT = "JobBuddy/1.0 (+https://github.com/KarmicFuture/Auto_Trader)"
TIMEOUT = 12
CACHE_TTL = 8 * 60

_cache: dict[str, tuple[float, list[Job]]] = {}


def search_jobs(
    *,
    query: str = "",
    location: str = "",
    remote_only: bool = False,
    live: bool = True,
) -> tuple[list[Job], list[str], str]:
    """Return (jobs, errors, mode) where mode is live|mixed|demo."""
    errors: list[str] = []
    fetched: list[Job] = []

    if live:
        fetchers: list[tuple[str, Callable[[], list[Job]]]] = [
            ("remotive", lambda: _fetch_remotive(query)),
            ("arbeitnow", lambda: _fetch_arbeitnow(query, location, remote_only)),
            ("remoteok", lambda: _fetch_remoteok(query)),
        ]
        for name, fetcher in fetchers:
            try:
                fetched.extend(fetcher())
            except Exception as exc:  # network / parse — keep going
                errors.append(f"{name}: {exc}")

    jobs = _dedupe(fetched)
    jobs = _filter_jobs(jobs, query=query, location=location, remote_only=remote_only)

    mode = "live"
    if not jobs:
        jobs = demo_jobs(query=query, location=location, remote_only=remote_only)
        mode = "demo"
        if live and fetched == []:
            errors.append("Live boards were empty or unreachable — showing demo roles.")
    elif errors:
        mode = "mixed"

    jobs.sort(key=lambda job: job.posted_at or "", reverse=True)
    return jobs, errors, mode


def _filter_jobs(
    jobs: list[Job],
    *,
    query: str,
    location: str,
    remote_only: bool,
) -> list[Job]:
    q = query.strip().lower()
    loc = location.strip().lower()
    rows = jobs
    if q:
        rows = [
            job
            for job in rows
            if q in job.title.lower()
            or q in job.company.lower()
            or q in " ".join(job.tags).lower()
            or q in (job.location or "").lower()
        ]
    if loc:
        rows = [
            job
            for job in rows
            if loc in (job.location or "").lower()
            or (job.remote and loc in {"remote", "anywhere", "us", "united states"})
        ]
    if remote_only:
        rows = [job for job in rows if job.remote]
    return rows


def _dedupe(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        key = f"{job.company.lower()}|{job.title.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def _cached(key: str, loader: Callable[[], list[Job]]) -> list[Job]:
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return [Job(**job.to_dict()) for job in hit[1]]
    rows = loader()
    _cache[key] = (now, rows)
    return [Job(**job.to_dict()) for job in rows]


def _get(url: str, **kwargs: Any) -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    headers.update(kwargs.pop("headers", {}))
    response = requests.get(url, timeout=TIMEOUT, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()


def _fetch_remotive(query: str) -> list[Job]:
    params = {}
    if query:
        params["search"] = query
    qs = f"?{urlencode(params)}" if params else ""
    key = f"remotive:{query.lower()}"
    return _cached(key, lambda: _parse_remotive(_get(f"https://remotive.com/api/remote-jobs{qs}")))


def _parse_remotive(payload: Any) -> list[Job]:
    jobs = []
    for row in payload.get("jobs") or []:
        salary_min, salary_max, salary_text = parse_salary(row.get("salary"))
        location = row.get("candidate_required_location") or "Remote"
        jobs.append(
            Job(
                id=f"remotive-{row.get('id')}",
                source="remotive",
                title=str(row.get("title") or "Untitled"),
                company=str(row.get("company_name") or "Unknown"),
                url=str(row.get("url") or row.get("short_url") or ""),
                location=str(location),
                remote=True,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_text=salary_text or (str(row.get("salary")).strip() or None),
                tags=[str(tag) for tag in (row.get("tags") or []) if tag][:12],
                description=_plain(row.get("description")),
                posted_at=_date_prefix(row.get("publication_date")),
            )
        )
    return jobs[:80]


def _fetch_arbeitnow(query: str, location: str, remote_only: bool) -> list[Job]:
    key = f"arbeitnow:{query.lower()}:{location.lower()}:{remote_only}"
    return _cached(key, lambda: _parse_arbeitnow(_get("https://www.arbeitnow.com/api/job-board-api")))


def _parse_arbeitnow(payload: Any) -> list[Job]:
    jobs = []
    for row in payload.get("data") or []:
        remote = bool(row.get("remote"))
        tags = [str(tag) for tag in (row.get("tags") or []) if tag]
        job_types = [str(item) for item in (row.get("job_types") or []) if item]
        jobs.append(
            Job(
                id=f"arbeitnow-{row.get('slug') or row.get('url')}",
                source="arbeitnow",
                title=str(row.get("title") or "Untitled"),
                company=str(row.get("company_name") or "Unknown"),
                url=str(row.get("url") or ""),
                location=str(row.get("location") or ("Remote" if remote else "")),
                remote=remote,
                tags=(tags + job_types)[:12],
                description=_plain(row.get("description")),
                posted_at=_from_epoch(row.get("created_at")),
            )
        )
    return jobs[:80]


def _fetch_remoteok(query: str) -> list[Job]:
    key = f"remoteok:{query.lower()}"
    return _cached(
        key,
        lambda: _parse_remoteok(
            _get("https://remoteok.com/api", headers={"User-Agent": USER_AGENT})
        ),
    )


def _parse_remoteok(payload: Any) -> list[Job]:
    jobs = []
    rows = payload if isinstance(payload, list) else []
    for row in rows:
        if not isinstance(row, dict) or not row.get("id") or not row.get("position"):
            continue
        salary_min = _int_or_none(row.get("salary_min"))
        salary_max = _int_or_none(row.get("salary_max"))
        tags = [str(tag) for tag in (row.get("tags") or []) if tag and tag != "remote"]
        jobs.append(
            Job(
                id=f"remoteok-{row.get('id')}",
                source="remoteok",
                title=str(row.get("position") or "Untitled"),
                company=str(row.get("company") or "Unknown"),
                url=str(row.get("url") or row.get("apply_url") or ""),
                location=str(row.get("location") or "Remote"),
                remote=True,
                salary_min=salary_min if salary_min and salary_min > 1000 else None,
                salary_max=salary_max if salary_max and salary_max > 1000 else None,
                salary_text=_salary_text(salary_min, salary_max),
                tags=tags[:12],
                description=_plain(row.get("description")),
                posted_at=_from_epoch(row.get("epoch") or row.get("date")),
            )
        )
    return jobs[:80]


def _plain(html: Any) -> str | None:
    if not html:
        return None
    text = str(html)
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1500] or None


def _date_prefix(value: Any) -> str | None:
    if not value:
        return None
    return str(value)[:10]


def _from_epoch(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        ts = float(value)
        if ts > 1e12:
            ts /= 1000
        return time.strftime("%Y-%m-%d", time.gmtime(ts))
    except (TypeError, ValueError, OSError):
        return _date_prefix(value)


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _salary_text(low: int | None, high: int | None) -> str | None:
    if low and high:
        return f"${low:,}–${high:,}"
    if high:
        return f"Up to ${high:,}"
    if low:
        return f"From ${low:,}"
    return None
