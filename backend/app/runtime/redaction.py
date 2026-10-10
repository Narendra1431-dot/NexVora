"""Adapted from Open Dots; MIT attribution in OPEN_DOTS_LICENSE.txt."""
import re
from typing import Any,Mapping
_SENSITIVE_TEXT = re.compile(
    r"(?i)\b(api[_ -]?key|access[_ -]?token|refresh[_ -]?token|authorization|password|secret|token)\b"
    r"\s*[:=]\s*['\"]?([^\s,'\"]+)"
)

def redact_sensitive(value: Any, key: str = "") -> Any:
    """Return a JSON-safe copy with credential-like fields removed."""

    sensitive_markers = (
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "credential",
        "password",
        "secret",
        "token",
    )
    if key and any(marker in key.lower() for marker in sensitive_markers):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(item_key): redact_sensitive(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_sensitive(item, key) for item in value]
    if isinstance(value, str):
        return _SENSITIVE_TEXT.sub(r"\1=[REDACTED]", value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)

_KEY_VALUE=re.compile(r'(?i)\b(?:sk-or-v1-|gsk_|ghp_|github_pat_)[A-Za-z0-9_-]{12,}')
def redact(value):
    result=redact_sensitive(value)
    if isinstance(result,str):return _KEY_VALUE.sub('[REDACTED]',result)
    if isinstance(result,dict):return {k:redact(v) for k,v in result.items()}
    if isinstance(result,list):return [redact(v) for v in result]
    return result
