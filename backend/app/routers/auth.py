"""Authentication: register, sign in, session introspection and the demo login.

Passwords are PBKDF2 hashes (``security.py``); sessions are stateless JWTs the
frontend stores and sends as ``Authorization: Bearer <token>``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from ..config import settings
from ..db import col
from ..security import (
    StudentId,
    create_access_token,
    hash_password,
    hash_reset_token,
    iso_now,
    new_id,
    new_reset_token,
    sanitize_text,
    verify_password,
    validate_password_strength,
)

# Password strength validation error messages
PASSWORD_TOO_SHORT = "Password must be at least 8 characters long."
PASSWORD_MISSING_UPPERCASE = "Password must contain at least one uppercase letter."
PASSWORD_MISSING_LOWERCASE = "Password must contain at least one lowercase letter."
PASSWORD_MISSING_DIGIT = "Password must contain at least one digit."
PASSWORD_MISSING_SPECIAL = "Password must contain at least one special character."

logger = logging.getLogger("plcip.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


def _student_payload(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "studentId": user["studentId"],
        "email": user["email"],
        "name": user.get("name", ""),
        "createdAt": user.get("createdAt"),
    }


def _token_response(user: dict[str, Any]) -> dict[str, Any]:
    token, expires_in = create_access_token(user["studentId"], user["email"])
    return {"token": token, "expiresIn": expires_in, "student": _student_payload(user)}


async def _find_user(email: str) -> Optional[dict[str, Any]]:
    return await col("users").find_one({"email": email.lower()})


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> dict[str, Any]:
    # Validate password strength
    if not validate_password_strength(payload.password):
        if len(payload.password) < 8:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_TOO_SHORT)
        has_upper = any(c.isupper() for c in payload.password)
        has_lower = any(c.islower() for c in payload.password)
        has_digit = any(c.isdigit() for c in payload.password)
        has_special = any(not c.isalnum() for c in payload.password)

        if not has_upper:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_MISSING_UPPERCASE)
        if not has_lower:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_MISSING_LOWERCASE)
        if not has_digit:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_MISSING_DIGIT)
        if not has_special:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_MISSING_SPECIAL)

    email = str(payload.email).lower()
    if await _find_user(email):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    student_id = new_id("stu")
    user = {
        "studentId": student_id,
        "email": email,
        "name": sanitize_text(payload.name, max_length=120, allow_newlines=False),
        "passwordHash": hash_password(payload.password),
        "createdAt": iso_now(),
    }
    await col("users").insert_one(user)
    from ..seed.persona import PROFILE
    profile = {k: (False if isinstance(v, bool) else 0 if isinstance(v, int) else [] if isinstance(v, list) else '') for k, v in PROFILE.items()}
    profile.update(studentId=student_id, name=user['name'], email=email, targetCareerId='career-ai-engineer', weeklyAvailabilityHours=10, createdAt=iso_now())
    await col('profiles').insert_one(profile)
    from ..engine.state import recalculate
    await recalculate(student_id)
    logger.info("Registered new student %s", student_id)
    return _token_response(user)


@router.post("/login")
async def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    email = str(payload.email).lower()
    user = await _find_user(email)

    if not user or not verify_password(payload.password, user.get("passwordHash", "")):
        # Same message for unknown email and wrong password: no account probing.
        logger.warning("Failed login attempt for email: %s", email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")

    # Successful login
    logger.info("Successful login for user: %s", user.get('studentId'))
    return _token_response(user)


# --- Password reset -----------------------------------------------------
#
# Security contract:
#   * A reset token is never returned in an HTTP response and never logged.
#   * Only a one-way digest of the token is persisted; the raw value exists
#     solely for the out-of-band delivery (email) to the account owner.
#   * Tokens expire and are single-use.
#   * The reset-request response is identical whether or not the email exists,
#     so it cannot be used to enumerate accounts.

RESET_GENERIC_MESSAGE = "If the email exists, a password reset link has been sent."
RESET_TOKEN_TTL_MINUTES = 60


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=16, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


def _reset_token_digest(token: str) -> str:
    return hash_reset_token(token)


async def _deliver_password_reset(email: str, raw_token: str) -> bool:
    """Send the reset token out of band (email) and return True when configured.

    No delivery channel is configured in this environment, so the caller must
    fall back to the same generic response used for unknown accounts, and any
    delivery tooling added later must never log the token. The ``raw_token``
    value is intentionally not logged or returned anywhere in this module.
    """
    return False


async def _invalidate_open_reset_tokens(email: str) -> None:
    """Retire any outstanding reset tokens for the account (single active token)."""
    await col("password_resets").update_many(
        {"email": email, "used": False}, {"$set": {"used": True, "usedAt": iso_now()}}
    )


async def generate_password_reset_token(email: str) -> str:
    """Create an expiring, single-use reset token and store only its digest.

    Returns the raw token for out-of-band delivery; it must not be placed in a
    response body or a log record.
    """
    token = new_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    await _invalidate_open_reset_tokens(email)
    await col("password_resets").update_one(
        {"email": email},
        {
            "$set": {
                "studentId": (await _find_user(email) or {}).get("studentId"),
                "tokenHash": hash_reset_token(token),
                "expires": expires.isoformat(),
                "used": False,
                "createdAt": iso_now(),
            }
        },
        upsert=True,
    )
    return token


async def validate_password_reset_token(token: str, email: Optional[str] = None) -> bool:
    """Return True only for an unexpired, unused token whose digest matches."""
    digest = hash_reset_token(token)
    query: dict[str, Any] = {"tokenHash": digest, "used": False}
    if email is not None:
        query["email"] = email.lower().strip()
    record = await col("password_resets").find_one(query)
    if not record:
        return False
    try:
        expires = datetime.fromisoformat(str(record.get("expires")).replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) <= expires


async def invalidate_password_reset_token(email: str) -> None:
    """Invalidate a password reset token after use (single-use guarantee)."""
    await _invalidate_open_reset_tokens(email)


@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest) -> dict[str, Any]:
    """Request a password reset. The response never reveals account state."""
    email = str(payload.email).lower().strip()

    user = await _find_user(email)
    if user:
        try:
            raw_token = await generate_password_reset_token(email)
            delivered = await _deliver_password_reset(email, raw_token)
            if not delivered:
                # No email channel configured: keep the generic response and
                # retire the undeliverable token so nothing sensitive lingers.
                await _invalidate_open_reset_tokens(email)
                logger.info("Password reset requested for an existing account; delivery channel not configured.")
        except Exception as exc:  # noqa: BLE001 - never leak internals to the caller
            logger.warning("Password reset request could not be processed (%s).", type(exc).__name__)

    return {"message": RESET_GENERIC_MESSAGE}


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm) -> dict[str, Any]:
    """Reset password using a valid, unexpired, single-use token."""
    token = payload.token
    new_password = payload.new_password

    record = await col("password_resets").find_one({"tokenHash": hash_reset_token(token), "used": False})
    if not record or not await validate_password_reset_token(token, record.get("email")):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid or expired password reset token.")

    email = str(record["email"]).lower().strip()

    # Preserve the established password contract used by register/login.
    if not validate_password_strength(new_password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, PASSWORD_TOO_SHORT)

    hashed_password = hash_password(new_password)
    await col("users").update_one({"email": email}, {"$set": {"passwordHash": hashed_password}})

    # Single-use: retire the token immediately after a successful reset.
    await invalidate_password_reset_token(email)

    logger.info("Password reset completed for an account.")
    
    return {"message": "Password has been successfully reset."}


@router.post("/demo")
async def demo_login(request: Request) -> dict[str, Any]:
    """One-click demo account (also (re)seeds its baseline so a demo never fails)."""
    if not settings.demo_email or not settings.demo_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 
                          "Demo login is not configured. Set DEMO_EMAIL and DEMO_PASSWORD environment variables.")
    
    user = await _find_user(settings.demo_email)
    if not user:
        # Auto-seed demo account if credentials are configured
        student_id = new_id("stu")
        user = {
            "studentId": student_id,
            "email": settings.demo_email.lower(),
            "name": "Demo User",
            "passwordHash": hash_password(settings.demo_password),
            "createdAt": iso_now(),
        }
        await col("users").insert_one(user)
        from ..seed.persona import PROFILE
        profile = {k: (False if isinstance(v, bool) else 0 if isinstance(v, int) else [] if isinstance(v, list) else '') for k, v in PROFILE.items()}
        profile.update(studentId=student_id, name=user['name'], email=user['email'], targetCareerId='career-ai-engineer', weeklyAvailabilityHours=10, createdAt=iso_now())
        await col('profiles').insert_one(profile)
        from ..engine.state import recalculate
        await recalculate(student_id)
        logger.info("Auto-seeded demo account %s", student_id)
    
    return _token_response(user)


@router.get("/me")
async def me(student_id: str = StudentId) -> dict[str, Any]:
    user = await col("users").find_one({"studentId": student_id})
    if not user:  # pragma: no cover - dependency already validates this
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account no longer exists.")
    return _student_payload(user)
