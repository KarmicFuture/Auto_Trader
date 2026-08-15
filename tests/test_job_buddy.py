from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "job-buddy"
sys.path.insert(0, str(ROOT))

from coach import coach_actions, pipeline_stats
from demo_jobs import demo_jobs
from models import Job, Profile
from score import apply_fit, parse_salary, score_fit
from sources import _parse_remotive, _parse_remoteok


def _profile(**kwargs) -> Profile:
    base = dict(
        name="Vinod",
        titles=["Software Engineer", "Backend Engineer"],
        skills=["Python", "FastAPI", "Postgres"],
        locations=["Austin", "Remote"],
        remote="remote",
        min_salary=140000,
    )
    base.update(kwargs)
    return Profile.from_dict(base)


def test_empty_profile_is_neutral():
    job = Job(
        id="1",
        source="demo",
        title="Software Engineer",
        company="Acme",
        url="https://example.com",
    )
    result = score_fit(job, Profile())
    assert result.score == 50
    assert "profile" in result.label.lower()


def test_matching_remote_python_role_scores_high():
    job = Job(
        id="1",
        source="demo",
        title="Senior Software Engineer",
        company="Harborline",
        url="https://example.com",
        location="Remote — United States",
        remote=True,
        salary_min=160000,
        salary_max=190000,
        tags=["python", "fastapi", "postgres"],
        description="Python FastAPI Postgres APIs",
    )
    result = score_fit(job, _profile())
    assert result.score >= 80
    assert result.label == "Excellent fit"


def test_onsite_low_pay_is_a_stretch():
    job = Job(
        id="2",
        source="demo",
        title="Retail Associate",
        company="Mall Co",
        url="https://example.com",
        location="Boston, MA",
        remote=False,
        salary_min=40000,
        salary_max=48000,
        tags=["retail"],
        description="Customer service on the floor.",
    )
    result = score_fit(job, _profile())
    assert result.score < 45
    assert result.label == "Stretch"


def test_parse_salary_ranges_and_k_suffix():
    low, high, text = parse_salary("$120k–$150k")
    assert low == 120000
    assert high == 150000
    assert text
    low, high, _ = parse_salary("USD 80,000")
    assert low == 80000
    assert high == 80000


def test_apply_fit_writes_fields():
    job = demo_jobs()[0]
    scored = apply_fit(job, _profile())
    assert scored.fit_score is not None
    assert scored.fit_label
    assert scored.fit_reasons


def test_demo_jobs_filter_remote_python():
    rows = demo_jobs(query="python", remote_only=True)
    assert rows
    assert all(job.remote for job in rows)
    assert any("python" in " ".join(job.tags).lower() or "python" in (job.description or "").lower() for job in rows)


def test_coach_follow_up_after_five_days():
    today = date(2026, 8, 15)
    actions = coach_actions(
        [
            {
                "id": "job-1",
                "title": "Backend Engineer",
                "company": "Kiln",
                "status": "applied",
                "applied_at": "2026-08-01",
            }
        ],
        _profile(),
        today=today,
    )
    kinds = [action.kind for action in actions]
    assert "follow_up" in kinds
    follow = next(action for action in actions if action.kind == "follow_up")
    assert follow.urgency == "now"
    assert follow.job_id == "job-1"


def test_coach_interview_today():
    today = date(2026, 8, 15)
    actions = coach_actions(
        [
            {
                "id": "job-2",
                "title": "Staff Software Engineer",
                "company": "Atlas",
                "status": "interviewing",
                "interview_at": today.isoformat(),
            }
        ],
        _profile(),
        today=today,
    )
    interview = next(action for action in actions if action.kind == "interview")
    assert "today" in interview.title.lower()
    assert interview.urgency == "now"


def test_coach_offer_and_thin_pipeline():
    actions = coach_actions(
        [{"id": "job-3", "title": "SWE", "company": "X", "status": "offer"}],
        Profile(),
        today=date(2026, 8, 15),
    )
    kinds = {action.kind for action in actions}
    assert "offer" in kinds
    assert "profile" in kinds
    assert "discover" in kinds


def test_pipeline_stats_counts_active():
    stats = pipeline_stats(
        [
            {"status": "saved"},
            {"status": "applied"},
            {"status": "closed"},
        ]
    )
    assert stats["saved"] == 1
    assert stats["applied"] == 1
    assert stats["closed"] == 1
    assert stats["active"] == 2


def test_profile_from_csv_strings():
    profile = Profile.from_dict(
        {"titles": "SWE, Backend", "skills": "Python; SQL", "remote": "hybrid"}
    )
    assert profile.titles == ["SWE", "Backend"]
    assert profile.skills == ["Python", "SQL"]
    assert profile.remote == "hybrid"


def test_parse_remotive_payload():
    jobs = _parse_remotive(
        {
            "jobs": [
                {
                    "id": 99,
                    "title": "Python Developer",
                    "company_name": "Remotive Co",
                    "url": "https://example.com/r",
                    "candidate_required_location": "USA Only",
                    "salary": "$100k",
                    "tags": ["python"],
                    "description": "<p>Hello</p>",
                    "publication_date": "2026-08-01T12:00:00",
                }
            ]
        }
    )
    assert jobs[0].id == "remotive-99"
    assert jobs[0].remote is True
    assert jobs[0].salary_min == 100000
    assert jobs[0].posted_at == "2026-08-01"
    assert jobs[0].description == "Hello"


def test_parse_remoteok_skips_legal_header():
    jobs = _parse_remoteok(
        [
            {"legal": "notice"},
            {
                "id": "abc",
                "position": "DevOps Engineer",
                "company": "RemoteOK Co",
                "url": "https://example.com/ok",
                "location": "Worldwide",
                "salary_min": 140000,
                "salary_max": 180000,
                "tags": ["devops", "remote"],
                "epoch": 1750000000,
            },
        ]
    )
    assert len(jobs) == 1
    assert jobs[0].source == "remoteok"
    assert jobs[0].title == "DevOps Engineer"


def test_coach_skips_future_follow_up():
    today = date(2026, 8, 15)
    actions = coach_actions(
        [
            {
                "id": "job-4",
                "title": "SWE",
                "company": "Y",
                "status": "applied",
                "applied_at": today.isoformat(),
                "follow_up_at": (today + timedelta(days=10)).isoformat(),
            }
        ],
        _profile(),
        today=today,
    )
    assert not any(action.kind == "follow_up" for action in actions)
