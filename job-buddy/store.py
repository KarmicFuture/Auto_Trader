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
    password_hash TEXT NOT NULL,
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


def create_user(name: str, email: str, password_hash: str) -> dict[str, Any]:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, now_iso()),
        )
        return get_user_by_id(int(cur.lastrowid), conn)


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
    }
    if resume:
        payload["resume"] = {
            "filename": resume["filename"],
            "content_type": resume["content_type"],
            "size_bytes": resume["size_bytes"],
            "uploaded_at": resume["uploaded_at"],
        }
    return payload
