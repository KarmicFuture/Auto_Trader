#!/usr/bin/env python3
"""Job Buddy — accounts, resume upload, and job-search tips."""

from __future__ import annotations

import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, FastAPI, File, Form, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth import (  # noqa: E402
    hash_password,
    new_session_token,
    normalize_email,
    validate_signup,
    verify_password,
)
from store import (  # noqa: E402
    create_session,
    create_user,
    delete_session,
    get_resume,
    get_user_by_email,
    init_db,
    public_user,
    resume_dir,
    save_resume,
    user_for_session,
)
from tips import all_tips  # noqa: E402

PUBLIC = ROOT / "public"
COOKIE = "jobbuddy_session"
MAX_RESUME_BYTES = 8 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".doc", ".docx", ".txt", ".rtf"}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Job Buddy",
    description="Find work with a clearer process.",
    lifespan=lifespan,
)


def _error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"ok": False, "error": message}, status_code=status)


def _set_session(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "job-buddy"}


@app.get("/api/me")
def me(jobbuddy_session: str | None = Cookie(default=None)) -> dict:
    user = user_for_session(jobbuddy_session)
    if not user:
        return {"user": None}
    return {"user": public_user(user, get_resume(user["id"]))}


@app.post("/api/register", response_model=None)
def register(
    response: Response,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    problem = validate_signup(name, email, password)
    if problem:
        return _error(problem)
    email_norm = normalize_email(email)
    if get_user_by_email(email_norm):
        return _error("An account with that email already exists. Sign in instead.")
    user = create_user(name.strip(), email_norm, hash_password(password))
    token = new_session_token()
    create_session(user["id"], token)
    _set_session(response, token)
    return {"ok": True, "user": public_user(user), "next": "resume"}


@app.post("/api/login", response_model=None)
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
):
    user = get_user_by_email(normalize_email(email))
    if not user or not verify_password(password, user["password_hash"]):
        return _error("Email or password is incorrect.", 401)
    token = new_session_token()
    create_session(user["id"], token)
    _set_session(response, token)
    resume = get_resume(user["id"])
    return {
        "ok": True,
        "user": public_user(user, resume),
        "next": "desk" if resume else "resume",
    }


@app.post("/api/logout")
def logout(
    response: Response,
    jobbuddy_session: str | None = Cookie(default=None),
) -> dict[str, bool]:
    delete_session(jobbuddy_session)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.post("/api/resume", response_model=None)
async def upload_resume(
    file: UploadFile = File(...),
    jobbuddy_session: str | None = Cookie(default=None),
):
    user = user_for_session(jobbuddy_session)
    if not user:
        return _error("Create an account first.", 401)

    filename = Path(file.filename or "resume").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return _error("Upload a PDF, Word, RTF, or text resume.")

    data = await file.read()
    if not data:
        return _error("That file looks empty.")
    if len(data) > MAX_RESUME_BYTES:
        return _error("Resume must be 8 MB or smaller.")

    stored = f"{user['id']}-{SAFE_NAME.sub('_', filename)}"
    dest = resume_dir() / stored
    old = get_resume(user["id"])
    dest.write_bytes(data)
    if old and old["stored_name"] != stored:
        previous = resume_dir() / old["stored_name"]
        if previous.exists():
            previous.unlink()

    record = save_resume(
        user["id"],
        filename=filename,
        stored_name=stored,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
    )
    return {"ok": True, "user": public_user(user, record), "next": "desk"}


@app.get("/api/tips", response_model=None)
def tips(jobbuddy_session: str | None = Cookie(default=None)):
    if not user_for_session(jobbuddy_session):
        return _error("Create an account to read the full tip library.", 401)
    return {"tips": all_tips()}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PUBLIC / "index.html")


app.mount("/css", StaticFiles(directory=PUBLIC / "css"), name="css")
app.mount("/js", StaticFiles(directory=PUBLIC / "js"), name="js")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3040)


if __name__ == "__main__":
    main()
