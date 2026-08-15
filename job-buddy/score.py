"""Score how well a job matches a searcher's profile."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from models import Job, Profile

_TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")
_STOP = {
    "and",
    "the",
    "for",
    "with",
    "job",
    "role",
    "senior",
    "junior",
    "staff",
    "lead",
    "principal",
}


@dataclass(frozen=True)
class FitResult:
    score: float
    label: str
    reasons: list[str]


def score_fit(job: Job, profile: Profile) -> FitResult:
    if profile.is_empty():
        return FitResult(50.0, "Add a profile to score fit", ["No target titles or skills yet."])

    reasons: list[str] = []
    title_pts, title_reason = _title_points(job.title, profile.titles)
    skill_pts, skill_reason = _skill_points(job, profile.skills)
    loc_pts, loc_reason = _location_points(job, profile)
    pay_pts, pay_reason = _salary_points(job, profile.min_salary)

    if title_reason:
        reasons.append(title_reason)
    if skill_reason:
        reasons.append(skill_reason)
    if loc_reason:
        reasons.append(loc_reason)
    if pay_reason:
        reasons.append(pay_reason)

    score = _clamp(title_pts + skill_pts + loc_pts + pay_pts, 0.0, 100.0)
    return FitResult(round(score, 1), fit_label(score), reasons)


def apply_fit(job: Job, profile: Profile) -> Job:
    result = score_fit(job, profile)
    job.fit_score = result.score
    job.fit_label = result.label
    job.fit_reasons = result.reasons
    return job


def fit_label(score: float) -> str:
    if score >= 80:
        return "Excellent fit"
    if score >= 65:
        return "Strong fit"
    if score >= 45:
        return "Possible"
    return "Stretch"


def _title_points(job_title: str, targets: Iterable[str]) -> tuple[float, str]:
    targets = [t for t in targets if t.strip()]
    if not targets:
        return 12.0, "No target titles — scoring from skills and location."

    job_norm = _norm(job_title)
    best = 0.0
    matched = ""
    for target in targets:
        target_norm = _norm(target)
        if not target_norm:
            continue
        if target_norm in job_norm or job_norm in target_norm:
            best = 30.0
            matched = target
            break
        overlap = _token_overlap(job_title, target)
        pts = 30.0 * overlap
        if pts > best:
            best = pts
            matched = target
    if best >= 22:
        return best, f"Title lines up with “{matched}”."
    if best >= 10:
        return best, f"Partial title match with “{matched}”."
    return best, "Title is a stretch versus your targets."


def _skill_points(job: Job, skills: Iterable[str]) -> tuple[float, str]:
    skills = [s for s in skills if s.strip()]
    if not skills:
        return 10.0, "Add skills to sharpen the fit score."

    haystack = " ".join(
        [
            job.title,
            " ".join(job.tags),
            (job.description or "")[:2000],
        ]
    ).lower()
    hits = [skill for skill in skills if _skill_in(skill, haystack)]
    ratio = len(hits) / len(skills)
    pts = 35.0 * ratio
    if hits:
        shown = ", ".join(hits[:4])
        extra = f" (+{len(hits) - 4} more)" if len(hits) > 4 else ""
        return pts, f"Skills in the listing: {shown}{extra}."
    return pts, "None of your skills showed up in the listing."


def _location_points(job: Job, profile: Profile) -> tuple[float, str]:
    pref = profile.remote
    job_loc = (job.location or "").lower()
    remote_job = job.remote or "remote" in job_loc or "anywhere" in job_loc

    if pref == "remote":
        if remote_job:
            return 20.0, "Remote role — matches your preference."
        return 4.0, "On-site / hybrid listing while you want remote."
    if pref == "onsite":
        if remote_job and not profile.locations:
            return 6.0, "Remote listing while you want on-site."
        if _location_hit(job_loc, profile.locations):
            return 20.0, "Location matches one of your cities."
        if profile.locations:
            return 6.0, "Different city than your on-site targets."
        return 12.0, "On-site / hybrid — close to your preference."
    if pref == "hybrid":
        if remote_job or "hybrid" in job_loc:
            return 16.0, "Remote or hybrid — workable for you."
        if _location_hit(job_loc, profile.locations):
            return 18.0, "In one of your cities."
        return 8.0, "Location is a maybe."

    # any
    if _location_hit(job_loc, profile.locations):
        return 20.0, "Location matches one of your cities."
    if remote_job:
        return 16.0, "Remote — open to anywhere."
    if profile.locations:
        return 8.0, "Location is not one of your saved cities."
    return 12.0, "No location preference set."


def _salary_points(job: Job, min_salary: int | None) -> tuple[float, str]:
    if min_salary is None:
        return 8.0, "No salary floor set."
    high = job.salary_max or job.salary_min
    low = job.salary_min or job.salary_max
    if high is None:
        return 8.0, "Salary not listed."
    if high >= min_salary:
        if low is not None and low >= min_salary:
            return 15.0, "Pay range clears your floor."
        return 12.0, "Top of the range meets your floor."
    if high >= min_salary * 0.85:
        return 7.0, "Pay is a bit under your floor."
    return 2.0, "Pay is below your floor."


def parse_salary(text: str | None) -> tuple[int | None, int | None, str | None]:
    if not text:
        return None, None, None
    raw = str(text).strip()
    if not raw or raw.lower() in {"n/a", "na", "none", "undisclosed"}:
        return None, None, None

    amounts = [_to_annual(match) for match in _SALARY_NUM.finditer(raw)]
    amounts = [n for n in amounts if n is not None and 15_000 <= n <= 1_000_000]
    if not amounts:
        return None, None, raw
    return min(amounts), max(amounts), raw


_SALARY_NUM = re.compile(
    r"(?<![a-z])(?:usd|us\$|\$|€|£)?\s*(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(k|m)?",
    re.I,
)


def _to_annual(match: re.Match[str]) -> int | None:
    number = match.group(1).replace(",", "")
    suffix = (match.group(2) or "").lower()
    try:
        value = float(number)
    except ValueError:
        return None
    if suffix == "k":
        value *= 1_000
    elif suffix == "m":
        value *= 1_000_000
    # Hourly-looking leftovers (e.g. 45) are ignored by the 15k floor.
    return int(round(value))


def _location_hit(job_loc: str, cities: Iterable[str]) -> bool:
    for city in cities:
        needle = _norm(city)
        if needle and needle in _norm(job_loc):
            return True
    return False


def _skill_in(skill: str, haystack: str) -> bool:
    skill = skill.strip().lower()
    if not skill:
        return False
    if len(skill) <= 2 or skill in {"c++", "c#", "go", "r"}:
        return re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", haystack) is not None
    return skill in haystack


def _token_overlap(left: str, right: str) -> float:
    a = _tokens(left)
    b = _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _tokens(text: str) -> set[str]:
    return {tok for tok in _TOKEN_RE.findall(_norm(text)) if tok not in _STOP}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9+#.\s]+", " ", (text or "").lower()).strip()


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
