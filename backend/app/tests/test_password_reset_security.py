"""Regression tests for the password-reset security contract.

These tests prove the critical leak fixed in this change cannot silently return:

* no reset token (and no ``debug_token`` field) appears in any HTTP response;
* no raw token is written to application logs;
* only a digest of the token is persisted server-side;
* a delivered token is expiring and single-use;
* unknown emails and known emails produce an identical generic response.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.db import col
from app import security
from app.routers.auth import generate_password_reset_token


def register(c):
    password = "qa-secure-pass"
    email = f"reset-{uuid4().hex}@example.com"
    r = c.post(
        "/api/v1/auth/register",
        json={"name": "Reset QA", "email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    return r.json()["token"], email, password


class _LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial
        self.records.append(self.format(record))


def test_register_password_contract_is_unchanged():
    """The reset hardening must not weaken the register/login password rules."""
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
        weak = c.post(
            "/api/v1/auth/register",
            json={"name": "Weak", "email": f"weak-{uuid4().hex}@example.com", "password": "short"},
        )
        assert weak.status_code == 422


def test_reset_request_never_returns_or_logs_a_token():
    """Response bodies and logs must contain no token, and no debug_token field."""
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
        _, email, _ = register(c)

        capture = _LogCapture()
        capture.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
        auth_logger = logging.getLogger("plcip.auth")
        root = logging.getLogger()
        auth_logger.addHandler(capture)
        root.addHandler(capture)
        try:
            response = c.post("/api/v1/auth/request-password-reset", json={"email": email})
        finally:
            auth_logger.removeHandler(capture)
            root.removeHandler(capture)

        assert response.status_code == 200, response.text
        body = response.json()
        assert "debug_token" not in body
        assert "token" not in body
        # The message is intentionally generic and carries no account information.
        assert body == {"message": "If the email exists, a password reset link has been sent."}

        joined_logs = "\n".join(capture.records)
        # No token-shaped value anywhere in the captured log records.
        assert not re.search(r"[A-Za-z0-9_-]{24,}", joined_logs), joined_logs
        assert "token:" not in joined_logs.lower()


def test_unknown_and_known_email_responses_are_indistinguishable():
    """Account enumeration must not be possible from the reset-request response."""
    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
        _, email, _ = register(c)
        known = c.post("/api/v1/auth/request-password-reset", json={"email": email})
        unknown = c.post(
            "/api/v1/auth/request-password-reset",
            json={"email": f"nobody-{uuid4().hex}@example.com"},
        )
        assert known.status_code == 200
        assert unknown.status_code == 200
        assert known.json() == unknown.json()


def test_only_a_digest_of_the_token_is_persisted():
    """The raw token must never be stored; a matching digest must be."""
    from app.db import col

    async def scenario():
        with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
            _, email, _ = register(c)
            with c.portal.start_task_soon(_noop) if False else _NullCtx():
                # Exercise the generator directly inside the running portal.
                raw = c.portal.call(generate_and_read, email)

    async def generate_and_read(email: str) -> str:
        from app.routers.auth import generate_password_reset_token

        raw_token = await generate_password_reset_token(email)
        stored = await col("password_resets").find_one({"email": email})
        assert stored is not None
        assert "token" not in stored  # no plaintext field
        assert stored["tokenHash"] == security.hash_reset_token(raw_token)
        assert stored["tokenHash"] != raw_token
        assert stored["used"] is False
        return raw_token

    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
        _, email, _ = register(c)
        raw = c.portal.call(generate_and_read, email)
        assert raw and len(raw) >= 16


class _NullCtx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


async def _noop():  # pragma: no cover - placeholder guard
    return None


def test_token_is_single_use_and_expires():
    """A consumed token is rejected; an expired token is rejected."""
    from datetime import datetime, timedelta, timezone

    from app.db import col
    from app.routers.auth import generate_password_reset_token

    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as c:
        _, email, old_password = register(c)
        raw = c.portal.call(generate_password_reset_token, email)

        new_password = "Brand-New-Pass1"
        ok = c.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": new_password},
        )
        assert ok.status_code == 200, ok.text

        # Same token cannot be reused.
        reused = c.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "Another-Pass2"},
        )
        assert reused.status_code == 422

        # The new password works and the old one no longer does.
        login_new = c.post("/api/v1/auth/login", json={"email": email, "password": new_password})
        assert login_new.status_code == 200, login_new.text
        login_old = c.post("/api/v1/auth/login", json={"email": email, "password": old_password})
        assert login_old.status_code == 401

        # An expired token is rejected outright.
        expired_raw = c.portal.call(generate_password_reset_token, email)
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()

        async def expire():
            await col("password_resets").update_one(
                {"email": email}, {"$set": {"expires": past}}
            )

        c.portal.call(expire)
        expired = c.post(
            "/api/v1/auth/reset-password",
            json={"token": expired_raw, "new_password": "Yet-Another3"},
        )
        assert expired.status_code == 422
