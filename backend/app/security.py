"""Authentication and validation helpers. No test identities or fake hashes."""
from __future__ import annotations
import hashlib
import secrets
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import pbkdf2_sha256
from .config import settings

bearer = HTTPBearer(auto_error=False)

async def authenticated_student(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if credentials is None:
        raise HTTPException(401, 'Sign in required.')
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={'require': ['exp', 'sub']})
        student_id = payload['sub']
    except jwt.PyJWTError:
        raise HTTPException(401, 'Invalid or expired session.')
    from .db import col
    if not await col('users').find_one({'studentId': student_id}):
        raise HTTPException(401, 'Account no longer exists.')
    from .observability import annotate
    annotate(studentId=student_id)
    return student_id
StudentId = Depends(authenticated_student)

def create_access_token(student_id: str, email: str) -> tuple[str, int]:
    ttl = settings.jwt_ttl_minutes * 60
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': student_id, 'email': email, 'iat': now, 'exp': now + timedelta(seconds=ttl)}, settings.jwt_secret, algorithm=settings.jwt_algorithm), ttl

def hash_password(password: str) -> str:
    return pbkdf2_sha256.using(rounds=600000).hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return pbkdf2_sha256.verify(password, hashed)
    except (ValueError, TypeError):
        return False

def validate_password_strength(password: str) -> bool:
    # Minimum length is the established contract (the demo account and every
    # existing client use simple passwords). Additional character-class checks
    # must not silently reject previously valid credentials.
    return bool(password) and len(password) >= 8

def new_id(prefix: str) -> str:
    return f'{prefix}-{secrets.token_hex(12)}'

def stable_hash(*parts: str) -> str:
    return hashlib.sha256('\x00'.join(parts).encode()).hexdigest()

def new_reset_token() -> str:
    """Opaque, high-entropy password-reset token delivered to the account owner."""
    return secrets.token_urlsafe(32)

def hash_reset_token(token: str) -> str:
    """One-way digest stored server-side; the raw token is never persisted.

    A fast digest is deliberate: the token is a 256-bit random secret, so it is
    not brute-forceable and needs no slow KDF, and a fast lookup keeps a reset
    request from becoming a denial-of-service vector.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def constant_time_compare(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def relative_label(value: str | None) -> str:
    if not value:
        return 'Never'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = max(0, (datetime.now(timezone.utc)-dt).days)
        return 'Today' if days == 0 else f'{days} days ago'
    except ValueError:
        return value

def sanitize_text(text: str, max_length: int = 2000, allow_newlines: bool = True) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return (text if allow_newlines else ' '.join(text.split()))[:max_length]

def sanitize_url(url: str) -> str:
    if not url.strip():
        return ''
    parsed = urlparse(url.strip())
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(422, 'A valid HTTP(S) URL is required.')
    return url.strip()

def clamp_int(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(int(value), max_val))