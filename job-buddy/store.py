"""SQLite persistence for accounts, sessions, and resumes."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    linkedin_sub TEXT UNIQUE,
    picture TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    company TEXT NOT NULL,
    relation TEXT NOT NULL DEFAULT 'knows',
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS swipes (
    user_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    contact_id INTEGER,
    title TEXT,
    company TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, job_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def data_dir() -> Path:
    override = os.environ.get("JOB_BUDDY_HOME")
    root = Path(override) if override else Path(__file__).resolve().parent / "data"
    root.mkdir(parents=True, exist_ok=True)
    (root / "resumes").mkdir(parents=True, exist_ok=True)
    return root


def db_path() -> Path:
    return data_dir() / "jobbuddy.sqlite"


def resume_dir() -> Path:
    return data_dir() / "resumes"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    if "linkedin_sub" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN linkedin_sub TEXT")
    if "picture" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN picture TEXT")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_linkedin_sub ON users(linkedin_sub)"
    )


def create_user(
    name: str,
    email: str,
    password_hash: str | None = None,
    *,
    linkedin_sub: str | None = None,
    picture: str | None = None,
) -> dict[str, Any]:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, linkedin_sub, picture, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, password_hash, linkedin_sub, picture, now_iso()),
        )
        return get_user_by_id(int(cur.lastrowid), conn)


def get_user_by_linkedin(sub: str) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE linkedin_sub = ?",
            (sub,),
        ).fetchone()
        return dict(row) if row else None


def upsert_linkedin_user(
    *,
    sub: str,
    name: str,
    email: str,
    picture: str | None = None,
) -> dict[str, Any]:
    existing = get_user_by_linkedin(sub)
    if existing:
        with connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET name = COALESCE(NULLIF(?, ''), name),
                    picture = COALESCE(?, picture)
                WHERE id = ?
                """,
                (name, picture, existing["id"]),
            )
        return get_user_by_id(existing["id"])

    by_email = get_user_by_email(email)
    if by_email:
        with connect() as conn:
            conn.execute(
                """
                UPDATE users
                SET linkedin_sub = ?,
                    picture = COALESCE(?, picture)
                WHERE id = ?
                """,
                (sub, picture, by_email["id"]),
            )
        return get_user_by_id(by_email["id"])

    display = name.strip() or email.split("@")[0]
    return create_user(
        display,
        email,
        password_hash=None,
        linkedin_sub=sub,
        picture=picture,
    )


def save_oauth_state(state: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO oauth_states (state, created_at) VALUES (?, ?)",
            (state, now_iso()),
        )


def pop_oauth_state(state: str | None) -> bool:
    if not state:
        return False
    with connect() as conn:
        row = conn.execute(
            "SELECT created_at FROM oauth_states WHERE state = ?",
            (state,),
        ).fetchone()
        conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        return row is not None


def get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    if conn is None:
        with connect() as owned:
            row = owned.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise KeyError(f"user {user_id} not found")
    return dict(row)


def create_session(user_id: int, token: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, now_iso()),
        )


def user_for_session(token: str | None) -> Optional[dict[str, Any]]:
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
        return dict(row) if row else None


def delete_session(token: str | None) -> None:
    if not token:
        return
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def save_resume(
    user_id: int,
    *,
    filename: str,
    stored_name: str,
    content_type: str,
    size_bytes: int,
) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO resumes (user_id, filename, stored_name, content_type, size_bytes, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                filename = excluded.filename,
                stored_name = excluded.stored_name,
                content_type = excluded.content_type,
                size_bytes = excluded.size_bytes,
                uploaded_at = excluded.uploaded_at
            """,
            (user_id, filename, stored_name, content_type, size_bytes, now_iso()),
        )
        row = conn.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def get_resume(user_id: int) -> Optional[dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def public_user(user: dict[str, Any], resume: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "has_resume": bool(resume),
        "linkedin": bool(user.get("linkedin_sub")),
        "picture": user.get("picture"),
    }
    if resume:
        payload["resume"] = {
            "filename": resume["filename"],
            "content_type": resume["content_type"],
            "size_bytes": resume["size_bytes"],
            "uploaded_at": resume["uploaded_at"],
        }
    payload["contact_count"] = count_contacts(user["id"])
    return payload


def count_contacts(user_id: int) -> int:
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM contacts WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return int(row["n"] if row else 0)


def list_contacts(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def add_contact(user_id: int, name: str, company: str, relation: str) -> dict[str, Any]:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO contacts (user_id, name, company, relation, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, company, relation, now_iso()),
        )
        row = conn.execute("SELECT * FROM contacts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def delete_contact(user_id: int, contact_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, user_id),
        )
        return cur.rowcount > 0


def swiped_ids(user_id: int) -> set[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT job_id FROM swipes WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return {str(row["job_id"]) for row in rows}


def record_swipe(
    user_id: int,
    *,
    job_id: str,
    decision: str,
    contact_id: int | None,
    title: str,
    company: str,
) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO swipes (user_id, job_id, decision, contact_id, title, company, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, job_id) DO UPDATE SET
                decision = excluded.decision,
                contact_id = excluded.contact_id,
                title = excluded.title,
                company = excluded.company,
                created_at = excluded.created_at
            """,
            (user_id, job_id, decision, contact_id, title, company, now_iso()),
        )
        row = conn.execute(
            "SELECT * FROM swipes WHERE user_id = ? AND job_id = ?",
            (user_id, job_id),
        ).fetchone()
        return dict(row)


def liked_swipes(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM swipes
            WHERE user_id = ? AND decision = 'intro'
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
