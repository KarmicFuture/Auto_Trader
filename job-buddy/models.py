from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Profile:
    name: str = ""
    titles: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    remote: str = "any"  # any | remote | hybrid | onsite
    min_salary: Optional[int] = None

    def is_empty(self) -> bool:
        return not (
            self.name
            or self.titles
            or self.skills
            or self.locations
            or self.min_salary
            or self.remote not in ("", "any")
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Profile":
        raw = data or {}
        titles = _as_str_list(raw.get("titles") or raw.get("title"))
        skills = _as_str_list(raw.get("skills"))
        locations = _as_str_list(raw.get("locations") or raw.get("location"))
        min_salary = raw.get("min_salary")
        try:
            min_salary_int = int(min_salary) if min_salary not in (None, "") else None
        except (TypeError, ValueError):
            min_salary_int = None
        remote = str(raw.get("remote") or "any").strip().lower()
        if remote not in {"any", "remote", "hybrid", "onsite"}:
            remote = "any"
        return cls(
            name=str(raw.get("name") or "").strip(),
            titles=titles,
            skills=skills,
            locations=locations,
            remote=remote,
            min_salary=min_salary_int,
        )


@dataclass
class Job:
    id: str
    source: str
    title: str
    company: str
    url: str
    location: Optional[str] = None
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_text: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    description: Optional[str] = None
    posted_at: Optional[str] = None
    fit_score: Optional[float] = None
    fit_label: Optional[str] = None
    fit_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoachAction:
    id: str
    kind: str  # follow_up | interview | offer | discover | profile
    title: str
    detail: str
    urgency: str  # now | soon | later
    job_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",")]
        return [part for part in parts if part]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []
