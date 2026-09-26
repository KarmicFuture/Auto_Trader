#!/usr/bin/env python3
"""Job Buddy — accounts, resume upload, and job-search tips."""

from __future__ import annotations

import os
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Cookie, FastAPI, File, Form, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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
    add_contact,
    count_contacts,
    create_session,
    create_user,
    delete_contact,
    delete_session,
    get_resume,
    get_user_by_email,
    init_db,
    liked_swipes,
    list_contacts,
    pop_oauth_state,
    public_user,
    record_swipe,
    resume_dir,
    save_oauth_state,
    save_resume,
    swiped_ids,
    upsert_linkedin_user,
    user_for_session,
)
from tips import all_tips  # noqa: E402
from jobs import jobs_through_people  # noqa: E402
import linkedin as linkedin_auth  # noqa: E402

PUBLIC = ROOT / "public"
COOKIE = "jobbuddy_session"
MAX_RESUME_BYTES = 8 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".doc", ".docx", ".txt", ".rtf"}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_dotenv(ROOT / ".env")
    init_db()
    yield


app = FastAPI(
    title="Job Buddy",
    description="Find work with a clearer process.",
    lifespan=lifespan,
)


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    company: str = Field(min_length=2, max_length=80)
    relation: str = Field(default="knows", max_length=40)


class SwipeIn(BaseModel):
    job_id: str
    decision: str
    contact_id: int | None = None
    title: str = ""
    company: str = ""


def _error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"ok": False, "error": message}, status_code=status)


def _require_user(jobbuddy_session: str | None):
    user = user_for_session(jobbuddy_session)
    if not user:
        return None, _error("Create an account first.", 401)
    return user, None


def _next_step(user_id: int, has_resume: bool) -> str:
    if not has_resume:
        return "resume"
    if count_contacts(user_id) == 0:
        return "network"
    return "swipe"


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


@app.get("/api/config")
def api_config() -> dict[str, bool]:
    return {"linkedin": linkedin_auth.configured()}


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
    if user and user.get("linkedin_sub") and not user.get("password_hash"):
        return _error("This account uses LinkedIn. Continue with LinkedIn.", 401)
    if not user or not user.get("password_hash") or not verify_password(password, user["password_hash"]):
        return _error("Email or password is incorrect.", 401)
    token = new_session_token()
    create_session(user["id"], token)
    _set_session(response, token)
    resume = get_resume(user["id"])
    return {
        "ok": True,
        "user": public_user(user, resume),
        "next": _next_step(user["id"], bool(resume)),
    }


@app.post("/api/logout")
def logout(
    response: Response,
    jobbuddy_session: str | None = Cookie(default=None),
) -> dict[str, bool]:
    delete_session(jobbuddy_session)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/linkedin")
def linkedin_start():
    if not linkedin_auth.configured():
        return RedirectResponse(
            "/?auth_error=" + quote("LinkedIn sign-on is not configured yet."),
            status_code=302,
        )
    state = new_session_token()
    save_oauth_state(state)
    return RedirectResponse(linkedin_auth.authorization_url(state), status_code=302)


@app.get("/api/auth/linkedin/callback")
def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    if error:
        detail = error_description or error
        return RedirectResponse("/?auth_error=" + quote(detail), status_code=302)
    if not code or not pop_oauth_state(state):
        return RedirectResponse(
            "/?auth_error=" + quote("LinkedIn sign-on expired. Try again."),
            status_code=302,
        )
    try:
        token = linkedin_auth.exchange_code(code)
        profile = linkedin_auth.fetch_userinfo(token["access_token"])
    except Exception:
        return RedirectResponse(
            "/?auth_error=" + quote("LinkedIn could not finish sign-on. Try again."),
            status_code=302,
        )

    sub = str(profile.get("sub") or "").strip()
    email = normalize_email(str(profile.get("email") or ""))
    name = str(profile.get("name") or "").strip()
    picture = str(profile.get("picture") or "").strip() or None
    if not sub or not email:
        return RedirectResponse(
            "/?auth_error="
            + quote("LinkedIn did not share your email. Allow email access, or create an account here."),
            status_code=302,
        )

    user = upsert_linkedin_user(sub=sub, name=name, email=email, picture=picture)
    session = new_session_token()
    create_session(user["id"], session)
    redirect = RedirectResponse("/", status_code=302)
    _set_session(redirect, session)
    return redirect


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
    return {"ok": True, "user": public_user(user, record), "next": _next_step(user["id"], True)}


@app.get("/api/tips", response_model=None)
def tips(jobbuddy_session: str | None = Cookie(default=None)):
    if not user_for_session(jobbuddy_session):
        return _error("Create an account to read the full tip library.", 401)
    return {"tips": all_tips()}


@app.get("/api/contacts")
def api_contacts(jobbuddy_session: str | None = Cookie(default=None)):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    return {"contacts": list_contacts(user["id"])}


@app.post("/api/contacts", response_model=None)
def api_add_contact(
    body: ContactIn,
    jobbuddy_session: str | None = Cookie(default=None),
):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    name = body.name.strip()
    company = body.company.strip()
    relation = (body.relation or "knows").strip() or "knows"
    if len(name) < 2 or len(company) < 2:
        return _error("Add a person and the company where you know them.")
    contact = add_contact(user["id"], name, company, relation)
    return {"ok": True, "contact": contact, "contacts": list_contacts(user["id"])}


@app.delete("/api/contacts/{contact_id}", response_model=None)
def api_delete_contact(
    contact_id: int,
    jobbuddy_session: str | None = Cookie(default=None),
):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    if not delete_contact(user["id"], contact_id):
        return _error("That person was not on your list.", 404)
    return {"ok": True, "contacts": list_contacts(user["id"])}


@app.get("/api/swipe/deck", response_model=None)
def api_deck(jobbuddy_session: str | None = Cookie(default=None)):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    contacts = list_contacts(user["id"])
    cards = jobs_through_people(contacts, hidden_ids=swiped_ids(user["id"]))
    return {"jobs": cards, "remaining": len(cards), "contacts": len(contacts)}


@app.post("/api/swipe", response_model=None)
def api_swipe(
    body: SwipeIn,
    jobbuddy_session: str | None = Cookie(default=None),
):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    decision = body.decision.strip().lower()
    if decision not in {"pass", "intro"}:
        return _error("Swipe right for intro, left to pass.")
    record_swipe(
        user["id"],
        job_id=body.job_id,
        decision=decision,
        contact_id=body.contact_id,
        title=body.title.strip(),
        company=body.company.strip(),
    )
    contacts = list_contacts(user["id"])
    cards = jobs_through_people(contacts, hidden_ids=swiped_ids(user["id"]))
    return {"ok": True, "remaining": len(cards), "liked": liked_swipes(user["id"])}


@app.get("/api/swipe/liked")
def api_liked(jobbuddy_session: str | None = Cookie(default=None)):
    user, err = _require_user(jobbuddy_session)
    if err:
        return err
    return {"liked": liked_swipes(user["id"])}


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
