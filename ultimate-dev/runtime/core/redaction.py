"""Conservative redaction for durable runtime evidence and diagnostics."""
from __future__ import annotations

import re
from typing import Any, Mapping


_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "pwd", "secret", "token", "access_token",
    "refresh_token", "id_token", "auth_token", "api_key", "apikey",
    "private_key", "credential", "credentials", "authorization", "cookie",
})
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|token|password|passwd|secret|authorization)\s*[:=]\s*([^\s,;]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")


def _key_is_sensitive(key: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return normalized in _SENSITIVE_KEYS or normalized.endswith(("password", "secret", "token", "apikey", "privatekey"))


def redact_sensitive(value: Any) -> Any:
    """Return a JSON-shaped copy with common credentials removed."""
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _key_is_sensitive(key) else redact_sensitive(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        value = _PRIVATE_KEY.sub("[REDACTED PRIVATE KEY]", value)
        value = _BEARER.sub("Bearer [REDACTED]", value)
        value = _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        return value
    return value


__all__ = ["redact_sensitive"]
