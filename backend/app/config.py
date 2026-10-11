"""Environment-driven settings. All secrets stay server-side."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader so the backend needs no extra dependency."""
    for candidate in (Path(__file__).resolve().parents[1] / ".env", Path(__file__).resolve().parents[2] / ".env"):
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Real environment variables win over the file.
            os.environ.setdefault(key, value)


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _validate_settings(settings: Settings) -> None:
    """Validate critical configuration settings."""
    # Check if we're in production mode
    is_production = bool(os.getenv("PRODUCTION", os.getenv("IS_PRODUCTION", "false")).lower() in {"1", "true", "yes", "on"})
    
    # Ensure JWT_SECRET is set and strong in production (critical requirement for security)
    if is_production and not settings.jwt_secret:
        raise ValueError("JWT_SECRET environment variable is required for production")
    if is_production and len(settings.jwt_secret) < 32:
        raise ValueError("JWT_SECRET must be at least 32 characters for production security")
    
    # Validate other critical production settings
    if settings.seed_on_startup and not (settings.demo_email and settings.demo_password):
        raise ValueError("DEMO_EMAIL and DEMO_PASSWORD environment variables are required when SEED_ON_STARTUP is true")


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "Personalized Learning & Career Intelligence API"
    api_prefix: str = "/api"
    version: str = "1.0.0"

    mongodb_uri: str = field(default_factory=lambda: os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    mongodb_db: str = field(default_factory=lambda: os.getenv("MONGODB_DB", "career_intelligence"))

    jwt_secret: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET", "")
    )
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_TTL_MINUTES", "720")))
    session_cookie_name: str = field(default_factory=lambda: os.getenv("SESSION_COOKIE_NAME", "plcip_session"))
    csrf_cookie_name: str = field(default_factory=lambda: os.getenv("CSRF_COOKIE_NAME", "plcip_csrf"))
    cookie_path: str = field(default_factory=lambda: os.getenv("COOKIE_PATH", "/"))
    cookie_domain: str = field(default_factory=lambda: os.getenv("COOKIE_DOMAIN", ""))
    secure_cookies: bool = field(default_factory=lambda: _bool("COOKIE_SECURE", _bool("PRODUCTION", False)))

    cors_origins: list[str] = field(
        default_factory=lambda: _csv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        )
    )
    app_url: str = field(default_factory=lambda: os.getenv("APP_URL", ""))

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "auto").lower())
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))

    # --- OpenRouter LLM -----------------------------------------------------
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "openai/gpt-4o"))
    openrouter_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30")))
    openrouter_base_url: str = field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))

    # --- Local embeddings + RAG -----------------------------------------
    embed_model: str = field(default_factory=lambda: os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    embed_dim: int = field(default_factory=lambda: int(os.getenv("EMBED_DIM", "384")))
    rag_top_k: int = field(default_factory=lambda: int(os.getenv("RAG_TOP_K", "5")))

    # --- Uploads ---------------------------------------------------------
    max_upload_bytes: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024))))
    allowed_upload_types: list[str] = field(
        default_factory=lambda: _csv("ALLOWED_UPLOAD_TYPES", "application/pdf,text/plain,text/markdown")
    )

    # --- Rate limiting --------------------------------------------------
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
    sensitive_rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("SENSITIVE_RATE_LIMIT_PER_MINUTE", "20"))
    )
    trust_proxy_headers: bool = field(default_factory=lambda: _bool("TRUST_PROXY_HEADERS", False))

    reviewer_emails: list[str] = field(default_factory=lambda: [e.lower() for e in _csv("REVIEWER_EMAILS", "")])

    demo_email: str = field(default_factory=lambda: os.getenv("DEMO_EMAIL", ""))
    demo_password: str = field(default_factory=lambda: os.getenv("DEMO_PASSWORD", ""))
    seed_on_startup: bool = field(default_factory=lambda: _bool("SEED_ON_STARTUP", False))


# Create settings instance and validate
_settings_instance = Settings()
_validate_settings(_settings_instance)

# Replace the settings module variable with validated instance
settings = _settings_instance