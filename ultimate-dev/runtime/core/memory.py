"""Bounded, provenance-aware project memory.

This module deliberately has no dependency on the Runtime, model providers, or
network services.  It stores append-only records under
``<project>/.memory/ultimate-dev/memory/records.json`` and exposes a small
query/projection API for a host to use when building model context.

The store is intentionally conservative:

* record payloads are JSON-shaped, bounded, and scanned for common credentials
  before they are written;
* expired, stale, revoked, and superseded records remain auditable but are not
  returned as active memory;
* a replacement never overwrites history; it links to the prior record and
  changes only the prior record's lifecycle status;
* projections are deterministic for a given persisted state and ``as_of`` time.

The module is a compatibility surface rather than a replacement for task state.
Callers must not use memory as authorization, verification, or an audit log.
"""
from __future__ import annotations

import contextlib
import datetime as _datetime
import hashlib
import json
import math
import os
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

try:  # pragma: no cover - exercised on POSIX, harmless fallback elsewhere
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = "1.0"
STORAGE_RELATIVE = Path(".memory") / "ultimate-dev" / "memory"
DEFAULT_RETENTION_SECONDS: float | None = None
DEFAULT_MAX_RECORDS = 10_000
DEFAULT_MAX_VALUE_CHARS = 1_000_000
MAX_RECORD_CHARS = 1_000_000
MAX_STORE_BYTES = 64_000_000
DEFAULT_PROJECTION_BUDGET = 4_000

# These are intentionally conservative limits.  They prevent an untrusted
# source from turning memory into an unbounded context or disk sink.
MAX_RECORDS = DEFAULT_MAX_RECORDS
MAX_VALUE_CHARS = DEFAULT_MAX_VALUE_CHARS
MAX_FIELD_CHARS = 4_096
MAX_ID_CHARS = 128

_MISSING = object()

SENSITIVITY_VALUES = frozenset({"public", "internal", "sensitive", "confidential", "secret"})
SENSITIVITY_RANK = {
    "public": 0,
    "internal": 1,
    "sensitive": 2,
    "confidential": 3,
    "secret": 4,
}
STATUS_VALUES = frozenset(
    {
        "active",
        "unverified",
        "stale",
        "expired",
        "superseded",
        "revoked",
        "rejected",
    }
)
TERMINAL_STATUSES = frozenset({"superseded", "revoked", "rejected"})
TRUST_VALUES = frozenset({"unverified", "untrusted", "low", "medium", "high", "verified"})

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_KIND_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,128}$")
_DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([smhdw])\s*$", re.IGNORECASE)

_SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "secret",
        "clientsecret",
        "token",
        "accesstoken",
        "refreshtoken",
        "sessiontoken",
        "signature",
        "idtoken",
        "authtoken",
        "apikey",
        "privatekey",
        "privatereasoning",
        "credential",
        "credentials",
        "authorization",
        "auth",
        "cookie",
        "setcookie",
    }
)
_SECRET_KEY_SUFFIXES = (
    "apikey",
    "accesstoken",
    "authtoken",
    "clientsecret",
    "privatekey",
    "privatereasoning",
    "refreshtoken",
    "password",
    "secret",
)
_PII_KEYS = frozenset(
    {
        "address",
        "creditcard",
        "credit_card",
        "dateofbirth",
        "dob",
        "email",
        "fullname",
        "name",
        "phone",
        "phonenumber",
        "ssn",
        "taxid",
    }
)
_PII_STRINGS = {
    "address",
    "creditcard",
    "dateofbirth",
    "dob",
    "email",
    "fullname",
    "name",
    "phone",
    "phonenumber",
    "ssn",
    "taxid",
}

# A value-based scan is in addition to key-based scanning.  The error and
# refusal paths never include the matched value in their message.
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"),
    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|"
        r"client[_-]?secret|password|passwd|secret|authorization)\s*[:=]\s*"
        r"[\"']?([^\s\"',;]{4,})"
    ),
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
_CARD_RE = re.compile(r"(?<!\w)(?:\d[ -]?){13,19}(?!\w)")


class MemoryStoreError(ValueError):
    """Base class for invalid memory records or unavailable persistence."""


class MemoryRecordError(MemoryStoreError):
    """The supplied record cannot be safely represented."""


class SecretDetected(MemoryRecordError):
    """A payload appears to contain a credential and was refused."""


class SecretRefused(SecretDetected):
    """Compatibility name for callers that prefer an explicit refusal label."""


class DigestMismatch(MemoryRecordError):
    """The supplied digest does not match the canonical safe payload."""


class ScopeViolation(MemoryStoreError):
    """An operation would cross a memory scope boundary."""


class DuplicateRecord(MemoryStoreError):
    """A record ID is already bound to different content."""


class RecordNotFound(MemoryStoreError):
    """A requested memory record does not exist."""


class CapacityError(MemoryStoreError):
    """The configured record bound would be exceeded."""


# Keep common alternate names available without forcing a host to know the
# implementation's exact exception spelling.
MemoryError = MemoryStoreError
SecretRefusal = SecretDetected
SecretRedactionError = SecretDetected
ScopeError = ScopeViolation
MemoryConflict = MemoryStoreError
RetentionError = MemoryStoreError


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise MemoryRecordError(f"value is not canonical JSON: {type(exc).__name__}") from exc


def _new_record_id() -> str:
    return f"mem-{uuid.uuid4().hex}"


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if not normalized or normalized in {"redacted", "[redacted]", "***", "none", "null", "unknown"}:
        return True
    return len(normalized) >= 3 and set(normalized) <= {"*", "_", "-", "."}


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _is_secret_key(key: str) -> bool:
    normalized = _normalized_key(key)
    return normalized in _SECRET_KEYS or any(
        normalized.endswith(suffix) for suffix in _SECRET_KEY_SUFFIXES
    )


def _is_pii_key(key: str) -> bool:
    normalized = _normalized_key(key)
    return normalized in _PII_STRINGS or normalized in _PII_KEYS


def _string_has_secret(value: str) -> bool:
    # Already-redacted markers are safe to retain, including when embedded in
    # a URL or an authorization-shaped field.
    candidate = re.sub(r"\[REDACTED\]|\*{3,}", "", value)
    return any(pattern.search(candidate) for pattern in _SECRET_PATTERNS)


def _clone_json(value: Any, path: str = "$", seen: set[int] | None = None) -> Any:
    """Validate and copy a JSON-shaped value while rejecting cycles/NaN."""
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    if seen is None:
        seen = set()
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str) and len(value) > MAX_VALUE_CHARS:
            raise MemoryRecordError(f"{path} exceeds the maximum string length")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MemoryRecordError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in seen:
            raise MemoryRecordError(f"{path} contains a cycle")
        seen.add(marker)
        result: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not key or len(key) > MAX_FIELD_CHARS:
                raise MemoryRecordError(f"{path} contains an invalid key")
            result[key] = _clone_json(child, f"{path}.{key}", seen)
        seen.remove(marker)
        return result
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in seen:
            raise MemoryRecordError(f"{path} contains a cycle")
        seen.add(marker)
        result_list = [_clone_json(item, f"{path}[{index}]", seen) for index, item in enumerate(value)]
        seen.remove(marker)
        return result_list
    raise MemoryRecordError(f"{path} must contain only JSON values")


def _redact_value(
    value: Any,
    *,
    sensitivity: str = "internal",
    path: str = "$",
    refuse_secrets: bool = True,
    seen: set[int] | None = None,
) -> tuple[Any, bool]:
    """Return a safe copy and whether redaction changed the value."""
    if seen is None:
        seen = set()
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    rank = SENSITIVITY_RANK[sensitivity]
    if value is None or isinstance(value, (bool, int, float)):
        _clone_json(value, path, seen)
        return value, False
    if isinstance(value, str):
        if len(value) > MAX_VALUE_CHARS:
            raise MemoryRecordError(f"{path} exceeds the maximum string length")
        if _string_has_secret(value):
            if refuse_secrets:
                raise SecretDetected("sensitive credential material was refused")
            return "[REDACTED]", True
        if rank >= SENSITIVITY_RANK["sensitive"]:
            redacted = _EMAIL_RE.sub("[REDACTED]", value)
            redacted = _PHONE_RE.sub("[REDACTED]", redacted)
            redacted = _CARD_RE.sub("[REDACTED]", redacted)
            return redacted, redacted != value
        return value, False
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in seen:
            raise MemoryRecordError(f"{path} contains a cycle")
        seen.add(marker)
        result: dict[str, Any] = {}
        changed = False
        for key in sorted(value, key=str):
            child = value[key]
            if not isinstance(key, str) or not key or len(key) > MAX_FIELD_CHARS:
                raise MemoryRecordError(f"{path} contains an invalid key")
            if _is_secret_key(key) and not _is_placeholder(child):
                if refuse_secrets:
                    raise SecretDetected("sensitive credential material was refused")
                result[key] = "[REDACTED]"
                changed = True
                continue
            if rank >= SENSITIVITY_RANK["sensitive"] and _is_pii_key(key):
                # Do not attempt to preserve structure for a field that is
                # itself identifying; a marker is safer than a partial value.
                result[key] = "[REDACTED]"
                changed = True
                continue
            safe_child, child_changed = _redact_value(
                child,
                sensitivity=sensitivity,
                path=f"{path}.{key}",
                refuse_secrets=refuse_secrets,
                seen=seen,
            )
            result[key] = safe_child
            changed = changed or child_changed
        seen.remove(marker)
        return result, changed
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in seen:
            raise MemoryRecordError(f"{path} contains a cycle")
        seen.add(marker)
        result_list: list[Any] = []
        changed = False
        for index, child in enumerate(value):
            safe_child, child_changed = _redact_value(
                child,
                sensitivity=sensitivity,
                path=f"{path}[{index}]",
                refuse_secrets=refuse_secrets,
                seen=seen,
            )
            result_list.append(safe_child)
            changed = changed or child_changed
        seen.remove(marker)
        return result_list, changed
    _clone_json(value, path, seen)
    return value, False


def redact(value: Any, *, sensitivity: str = "internal") -> Any:
    """Return a recursively redacted JSON-shaped value.

    Unlike :func:`MemoryStore.add`, this helper is deliberately total: secret-
    looking values become ``[REDACTED]`` rather than raising.  The store still
    refuses secret-looking input before persistence.
    """
    normalized = _normalize_sensitivity(sensitivity)
    if isinstance(value, MemoryRecord):
        return value.to_projection_dict()
    # The standalone helper is a safe-output boundary, so its default also
    # masks common PII even when the caller did not attach a sensitivity label.
    redaction_level = "sensitive" if normalized == "internal" else normalized
    safe, _ = _redact_value(value, sensitivity=redaction_level, refuse_secrets=False)
    return safe


# Match the naming used by the evaluation/evolution adapters.
redact_value = redact


def _normalize_sensitivity(value: Any) -> str:
    if not isinstance(value, str):
        raise MemoryRecordError("sensitivity must be a string")
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "low": "public",
        "medium": "internal",
        "private": "sensitive",
        "restricted": "sensitive",
        "redacted": "sensitive",
        "high": "sensitive",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SENSITIVITY_VALUES:
        raise MemoryRecordError("sensitivity is not supported")
    return normalized


def _normalize_status(value: Any) -> str:
    if not isinstance(value, str):
        raise MemoryRecordError("status must be a string")
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "valid": "active",
        "verified": "active",
        "invalid": "rejected",
        "deleted": "revoked",
        "inactive": "revoked",
        "retired": "superseded",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in STATUS_VALUES:
        raise MemoryRecordError("status is not supported")
    return normalized


def _normalize_trust(value: Any) -> str:
    if not isinstance(value, str):
        raise MemoryRecordError("trust must be a string")
    normalized = value.strip().lower()
    if normalized not in TRUST_VALUES:
        raise MemoryRecordError("trust is not supported")
    return normalized


def _normalize_scope(value: Any) -> str:
    if value is None:
        return "global"
    if isinstance(value, os.PathLike):
        candidate = os.fspath(value).strip()
    elif isinstance(value, str):
        candidate = value.strip()
    else:
        try:
            candidate = _canonical_json(_clone_json(value))
        except MemoryRecordError as exc:
            raise MemoryRecordError("scope must be a string or JSON object") from exc
    if not candidate or len(candidate) > MAX_FIELD_CHARS:
        raise MemoryRecordError("scope must be non-empty and bounded")
    if "\x00" in candidate or "\n" in candidate or "\r" in candidate:
        raise MemoryRecordError("scope contains control characters")
    if "\\" in candidate or any(part == ".." for part in candidate.replace(":", "/").split("/")):
        raise MemoryRecordError("scope contains an unsafe path component")
    if _string_has_secret(candidate):
        raise SecretDetected("sensitive credential material was refused")
    return candidate


def _scope_is_child(child: str, parent: str) -> bool:
    if child == parent:
        return True
    if parent == "global":
        return True
    return child.startswith(parent + "/") or child.startswith(parent + ":")


def _scope_matches(
    record_scope: str,
    requested_scope: Any,
    *,
    include_parent_scopes: bool = False,
    include_child_scopes: bool = False,
    include_global: bool = True,
) -> bool:
    requested = _normalize_scope(requested_scope)
    if record_scope == requested and not (record_scope == "global" and not include_global):
        return True
    if record_scope == "global" and include_global:
        return True
    if include_parent_scopes and _scope_is_child(requested, record_scope):
        return True
    if include_child_scopes and _scope_is_child(record_scope, requested):
        return True
    return False


def _parse_timestamp(value: Any, *, default: _datetime.datetime | None = None) -> _datetime.datetime | None:
    if value is None:
        return default
    if isinstance(value, _datetime.datetime):
        result = value
    elif isinstance(value, _datetime.date):
        result = _datetime.datetime.combine(value, _datetime.time())
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            result = _datetime.datetime.fromtimestamp(float(value), tz=_datetime.timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise MemoryRecordError("timestamp is outside the supported range") from exc
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise MemoryRecordError("timestamp must not be empty")
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            result = _datetime.datetime.fromisoformat(text)
        except ValueError as exc:
            raise MemoryRecordError("timestamp must be ISO-8601 or epoch seconds") from exc
    else:
        raise MemoryRecordError("timestamp must be datetime-like, ISO-8601, or epoch seconds")
    if result.tzinfo is None:
        result = result.replace(tzinfo=_datetime.timezone.utc)
    return result.astimezone(_datetime.timezone.utc)


def _format_timestamp(value: _datetime.datetime | None) -> str | None:
    if value is None:
        return None
    value = value.astimezone(_datetime.timezone.utc)
    if value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_now() -> _datetime.datetime:
    return _datetime.datetime.now(_datetime.timezone.utc)


def _duration_seconds(value: Any, *, label: str = "duration") -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise MemoryRecordError(f"{label} must be a non-negative duration")
    if isinstance(value, _datetime.timedelta):
        seconds = value.total_seconds()
    elif isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        match = _DURATION_RE.fullmatch(value)
        if match:
            amount = float(match.group(1))
            multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[match.group(2).lower()]
            seconds = amount * multiplier
        else:
            try:
                seconds = float(value.strip())
            except ValueError as exc:
                raise MemoryRecordError(f"{label} must be seconds or a duration such as '30m'") from exc
    elif isinstance(value, Mapping):
        raw: Any = None
        multiplier = 1
        for key, factor in (("seconds", 1), ("minutes", 60), ("hours", 3600), ("days", 86400), ("weeks", 604800)):
            if key in value:
                raw = value[key]
                multiplier = factor
                break
        else:
            raise MemoryRecordError(f"{label} must be a non-negative duration")
        if isinstance(raw, bool):
            raise MemoryRecordError(f"{label} must be a non-negative duration")
        seconds = float(raw) * multiplier
    else:
        raise MemoryRecordError(f"{label} must be a non-negative duration")
    if not math.isfinite(seconds) or seconds < 0:
        raise MemoryRecordError(f"{label} must be a non-negative duration")
    return seconds


def _retention_days_seconds(value: Any) -> float:
    if isinstance(value, _datetime.timedelta):
        return value.total_seconds()
    if isinstance(value, Mapping) and "days" in value:
        raw = value["days"]
        if isinstance(raw, bool):
            raise MemoryRecordError("retention_days must be a non-negative duration")
        return float(raw) * 86400
    if isinstance(value, str) and _DURATION_RE.fullmatch(value):
        parsed = _duration_seconds(value, label="retention_days")
        assert parsed is not None
        return parsed
    days = _duration_seconds(value, label="retention_days")
    assert days is not None
    return days * 86400


def _validate_id(value: Any, label: str = "record_id") -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise MemoryRecordError(f"{label} is invalid")
    return value


def _normalize_supersedes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Sequence):
        values = list(value)
    else:
        raise MemoryRecordError("supersedes must be a record ID or sequence of IDs")
    result: list[str] = []
    for item in values:
        item = _validate_id(item, "supersedes record ID")
        if item not in result:
            result.append(item)
    return tuple(result)


def _digest_payload(
    *,
    kind: str,
    content: Any,
    reference: Any,
    source: Any,
    scope: str,
) -> str:
    payload = {
        "kind": kind,
        "content": content,
        "reference": reference,
        "source": source,
        "scope": scope,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def compute_digest(
    content: Any = _MISSING,
    reference: Any = _MISSING,
    *,
    kind: str = "memory",
    source: Any = "local",
    scope: Any = "global",
) -> str:
    """Return the deterministic digest used by :class:`MemoryRecord`.

    The digest covers the safe payload plus its identity/provenance fields.  It
    is an integrity/freshness aid, not a signature or proof of authenticity.
    """
    content_missing = content is _MISSING or content is None or content == ""
    reference_missing = reference is _MISSING or reference is None or reference == ""
    if content_missing and reference_missing:
        raise MemoryRecordError("content or reference is required for a digest")
    if content is _MISSING:
        content = None
    if reference is _MISSING:
        reference = None
    normalized_scope = _normalize_scope(scope)
    return _digest_payload(
        kind=str(kind),
        content=_clone_json(content),
        reference=_clone_json(reference),
        source=_clone_json(source),
        scope=normalized_scope,
    )


# Common alternate spelling for hosts that think in terms of references.
digest_for = compute_digest


@dataclass(frozen=True)
class MemoryRecord:
    """An immutable, JSON-serializable memory record.

    ``content`` and ``reference`` are both optional individually, but at least
    one must be present.  Lifecycle changes are made with ``dataclasses.replace``
    by the store so that prior content is never silently overwritten.
    """

    kind: str
    content: Any = None
    reference: Any = None
    source: Any = "local"
    digest: str = ""
    observed_at: Any = None
    verified_at: Any = None
    scope: Any = "global"
    sensitivity: str = "internal"
    confidence: float = 1.0
    ttl: float | _datetime.timedelta | str | None = None
    status: str = "active"
    supersedes: str | Sequence[str] = ()
    contradicts: str | Sequence[str] = ()
    record_id: str = field(default_factory=_new_record_id)
    created_at: Any = None
    updated_at: Any = None
    expires_at: Any = None
    stale_after: float | _datetime.timedelta | str | None = None
    superseded_by: str | None = None
    status_reason: str | None = None
    key: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    authoritative: bool = False
    trust: str = "unverified"
    redacted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not _KIND_RE.fullmatch(self.kind.strip()):
            raise MemoryRecordError("kind must be a non-empty bounded string")
        kind = self.kind.strip()
        if _string_has_secret(kind):
            raise SecretDetected("sensitive credential material was refused")
        if (self.content is None or self.content == "") and (
            self.reference is None or self.reference == ""
        ):
            raise MemoryRecordError("a record requires content or reference")

        sensitivity = _normalize_sensitivity(self.sensitivity)
        if sensitivity == "secret":
            raise SecretDetected("secret-sensitivity records are refused")
        status = _normalize_status(self.status)
        trust = _normalize_trust(self.trust)
        if isinstance(self.source, Mapping) and self.trust == "unverified" and "trust" in self.source:
            candidate_trust = self.source.get("trust")
            if candidate_trust is not None:
                trust = _normalize_trust(candidate_trust)
        if not isinstance(self.authoritative, bool):
            raise MemoryRecordError("authoritative must be boolean")
        if not isinstance(self.redacted, bool):
            raise MemoryRecordError("redacted must be boolean")
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise MemoryRecordError("confidence must be a number between 0 and 1")
        confidence = float(self.confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise MemoryRecordError("confidence must be between 0 and 1")

        scope = _normalize_scope(self.scope)
        observed = _parse_timestamp(self.observed_at, default=_utc_now())
        assert observed is not None
        verified = _parse_timestamp(self.verified_at)
        if verified is not None and verified < observed:
            raise MemoryRecordError("verified_at cannot precede observed_at")
        created = _parse_timestamp(self.created_at, default=observed)
        updated = _parse_timestamp(self.updated_at, default=created)
        assert created is not None and updated is not None
        ttl = _duration_seconds(self.ttl, label="ttl")
        stale_after = _duration_seconds(self.stale_after, label="stale_after")
        expires = _parse_timestamp(self.expires_at)
        if expires is None and ttl is not None:
            expires = observed + _datetime.timedelta(seconds=ttl)

        safe_content, content_redacted = _redact_value(
            self.content,
            sensitivity=sensitivity,
            path="content",
            refuse_secrets=True,
        )
        safe_reference, reference_redacted = _redact_value(
            self.reference,
            sensitivity=sensitivity,
            path="reference",
            refuse_secrets=True,
        )
        if self.source is None:
            raise MemoryRecordError("source is required")
        if isinstance(self.source, str) and not self.source.strip():
            raise MemoryRecordError("source must be non-empty")
        safe_source, source_redacted = _redact_value(
            self.source,
            sensitivity="internal",
            path="source",
            refuse_secrets=True,
        )
        if isinstance(safe_source, (Mapping, list, tuple)) and not safe_source:
            raise MemoryRecordError("source must identify provenance")
        metadata_value = {} if self.metadata is None else self.metadata
        if not isinstance(metadata_value, Mapping):
            raise MemoryRecordError("metadata must be an object")
        safe_metadata, metadata_redacted = _redact_value(
            metadata_value,
            sensitivity=sensitivity,
            path="metadata",
            refuse_secrets=True,
        )

        record_id = _validate_id(self.record_id, "record_id")
        supersedes = _normalize_supersedes(self.supersedes)
        contradicts = _normalize_supersedes(self.contradicts)
        if record_id in supersedes or record_id in contradicts:
            raise MemoryRecordError("a record cannot supersede itself")
        superseded_by = self.superseded_by
        if superseded_by is not None:
            superseded_by = _validate_id(superseded_by, "superseded_by")
            if superseded_by == record_id:
                raise MemoryRecordError("a record cannot supersede itself")
        key = self.key
        if key is not None:
            if not isinstance(key, str) or not key.strip() or len(key) > MAX_FIELD_CHARS:
                raise MemoryRecordError("key must be a non-empty bounded string")
            key = key.strip()
            if _string_has_secret(key):
                raise SecretDetected("sensitive credential material was refused")
        status_reason = self.status_reason
        if status_reason is not None:
            if not isinstance(status_reason, str) or len(status_reason) > MAX_FIELD_CHARS:
                raise MemoryRecordError("status_reason must be a bounded string")
            status_reason = status_reason.strip() or None
            if status_reason and _string_has_secret(status_reason):
                raise SecretDetected("sensitive credential material was refused")
        redacted = bool(self.redacted) or any(
            (content_redacted, reference_redacted, source_redacted, metadata_redacted)
        )
        safe_size = len(
            _canonical_json(
                {
                    "kind": kind,
                    "content": safe_content,
                    "reference": safe_reference,
                    "source": safe_source,
                    "metadata": safe_metadata,
                }
            )
        )
        if safe_size > MAX_RECORD_CHARS:
            raise MemoryRecordError("record exceeds the maximum bounded payload size")
        digest = self.digest
        if isinstance(digest, str) and digest.lower().startswith("sha256:"):
            digest = digest.split(":", 1)[1]
        computed_digest = _digest_payload(
            kind=kind,
            content=safe_content,
            reference=safe_reference,
            source=safe_source,
            scope=scope,
        )
        if digest:
            if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
                raise MemoryRecordError("digest must be a SHA-256 hex digest")
            digest = digest.lower()
            if digest != computed_digest:
                raise DigestMismatch("digest does not match the canonical safe record payload")
        else:
            digest = computed_digest

        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "content", safe_content)
        object.__setattr__(self, "reference", safe_reference)
        object.__setattr__(self, "source", safe_source)
        object.__setattr__(self, "digest", digest)
        object.__setattr__(self, "observed_at", _format_timestamp(observed))
        object.__setattr__(self, "verified_at", _format_timestamp(verified))
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "sensitivity", sensitivity)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "ttl", ttl)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "supersedes", supersedes)
        object.__setattr__(self, "contradicts", contradicts)
        object.__setattr__(self, "record_id", record_id)
        object.__setattr__(self, "created_at", _format_timestamp(created))
        object.__setattr__(self, "updated_at", _format_timestamp(updated))
        object.__setattr__(self, "expires_at", _format_timestamp(expires))
        object.__setattr__(self, "stale_after", stale_after)
        object.__setattr__(self, "superseded_by", superseded_by)
        object.__setattr__(self, "status_reason", status_reason)
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "metadata", safe_metadata)
        object.__setattr__(self, "trust", trust)
        object.__setattr__(self, "redacted", redacted)

    @classmethod
    def create(cls, **values: Any) -> "MemoryRecord":
        return cls(**values)

    def compute_digest(self) -> str:
        return _digest_payload(
            kind=self.kind,
            content=self.content,
            reference=self.reference,
            source=self.source,
            scope=self.scope,
        )

    @property
    def id(self) -> str:
        """Short alias used by hosts that call the primary key ``id``."""

        return self.record_id

    @property
    def ttl_seconds(self) -> float | None:
        return self.ttl

    @property
    def stale_after_seconds(self) -> float | None:
        return self.stale_after

    @property
    def observed(self) -> str:
        return str(self.observed_at)

    @property
    def verified(self) -> str | None:
        return self.verified_at

    @property
    def observed_at_datetime(self) -> _datetime.datetime:
        return self._observed_datetime()

    @property
    def verified_at_datetime(self) -> _datetime.datetime | None:
        return self._verified_datetime()

    @property
    def expires_at_datetime(self) -> _datetime.datetime | None:
        return _parse_timestamp(self.expires_at)

    @property
    def active_statuses(self) -> frozenset[str]:
        return frozenset({"active", "unverified", "stale"})

    def _observed_datetime(self) -> _datetime.datetime:
        result = _parse_timestamp(self.observed_at)
        if result is None:  # pragma: no cover - normalized records always have it
            raise MemoryRecordError("record has no observed timestamp")
        return result

    def _verified_datetime(self) -> _datetime.datetime | None:
        return _parse_timestamp(self.verified_at)

    def age_seconds(self, now: Any = None) -> float:
        current = _parse_timestamp(now, default=_utc_now())
        assert current is not None
        return max(0.0, (current - self._observed_datetime()).total_seconds())

    def is_expired(self, now: Any = None) -> bool:
        if self.status in TERMINAL_STATUSES:
            return False
        expires = _parse_timestamp(self.expires_at)
        if expires is None:
            return False
        current = _parse_timestamp(now, default=_utc_now())
        assert current is not None
        return current >= expires

    def is_stale(self, now: Any = None) -> bool:
        if self.status == "stale":
            return True
        if self.stale_after is None or self.status in TERMINAL_STATUSES:
            return False
        base = self._verified_datetime() or self._observed_datetime()
        current = _parse_timestamp(now, default=_utc_now())
        assert current is not None
        return current >= base + _datetime.timedelta(seconds=self.stale_after)

    def effective_status(self, now: Any = None) -> str:
        if self.status in TERMINAL_STATUSES:
            return self.status
        if self.is_expired(now):
            return "expired"
        if self.is_stale(now):
            return "stale"
        return self.status

    @property
    def is_contradicted(self) -> bool:
        return self.status_reason == "contradiction"

    @property
    def contradicted_by(self) -> str | None:
        return self.superseded_by if self.is_contradicted else None

    def is_active(self, now: Any = None, *, include_stale: bool = False) -> bool:
        status = self.effective_status(now)
        if status in {"active", "unverified"}:
            return True
        return include_stale and status == "stale"

    def is_fresh(self, now: Any = None) -> bool:
        return self.effective_status(now) in {"active", "unverified"}

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation of the record."""

        return {
            "schema_version": SCHEMA_VERSION,
            "id": self.record_id,
            "record_id": self.record_id,
            "kind": self.kind,
            "content": self.content,
            "reference": self.reference,
            "source": self.source,
            "digest": self.digest,
            "observed_at": self.observed_at,
            "verified_at": self.verified_at,
            "scope": self.scope,
            "sensitivity": self.sensitivity,
            "confidence": self.confidence,
            "ttl": self.ttl,
            "ttl_seconds": self.ttl,
            "status": self.status,
            "supersedes": list(self.supersedes),
            "contradicts": list(self.contradicts),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "stale_after": self.stale_after,
            "superseded_by": self.superseded_by,
            "status_reason": self.status_reason,
            "key": self.key,
            "metadata": self.metadata,
            "authoritative": self.authoritative,
            "trust": self.trust,
            "redacted": self.redacted,
        }

    as_dict = to_dict
    to_json_dict = to_dict

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MemoryRecord":
        if not isinstance(value, Mapping):
            raise MemoryRecordError("record must be an object")
        data = dict(value)
        data.pop("schema_version", None)
        if "record_id" not in data and "id" in data:
            data["record_id"] = data["id"]
        if "ttl" not in data and "ttl_seconds" in data:
            data["ttl"] = data["ttl_seconds"]
        if "observed_at" not in data and "observed" in data:
            data["observed_at"] = data["observed"]
        if "verified_at" not in data and "verified" in data:
            data["verified_at"] = data["verified"]
        for alias in ("id", "ttl_seconds", "observed", "verified"):
            data.pop(alias, None)
        return cls(**data)

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())

    @classmethod
    def from_json(cls, value: str) -> "MemoryRecord":
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError) as exc:
            raise MemoryRecordError("record JSON is malformed") from exc
        return cls.from_dict(decoded)

    def freshness(self, now: Any = None) -> dict[str, Any]:
        current = _parse_timestamp(now, default=_utc_now())
        assert current is not None
        return {
            "state": self.effective_status(current),
            "age_seconds": max(0.0, (current - self._observed_datetime()).total_seconds()),
            "observed_at": self.observed_at,
            "verified_at": self.verified_at,
            "expires_at": self.expires_at,
        }

    def to_projection_dict(self, now: Any = None) -> dict[str, Any]:
        """Return the bounded, provenance-bearing form used in context."""

        effective = self.effective_status(now)
        observed = self.observed_at
        verified = self.verified_at
        item: dict[str, Any] = {
            "id": self.record_id,
            "kind": self.kind,
            "content": self.content,
            "source": self.source,
            "digest": self.digest,
            "observed_at": observed,
            "verified_at": verified,
            "created_at": self.created_at,
            "verified": verified is not None,
            "scope": self.scope,
            "sensitivity": self.sensitivity,
            "confidence": self.confidence,
            "ttl": self.ttl,
            "stale_after": self.stale_after,
            "status": effective,
            "freshness": {
                "state": effective if effective in {"active", "unverified", "stale", "expired"} else "terminal",
                "observed_at": observed,
                "verified_at": verified,
                "expires_at": self.expires_at,
            },
            "provenance": {
                "source": self.source,
                "digest": self.digest,
                "observed_at": observed,
                "verified_at": verified,
            },
            "authoritative": self.authoritative,
            "trust": self.trust,
        }
        if self.reference is not None:
            item["reference"] = self.reference
        if self.key is not None:
            item["key"] = self.key
        if self.supersedes:
            item["supersedes"] = list(self.supersedes)
        if self.superseded_by is not None:
            item["superseded_by"] = self.superseded_by
        if self.status_reason is not None:
            item["status_reason"] = self.status_reason
        if self.is_contradicted:
            item["contradiction"] = True
        return item

    projection_dict = to_projection_dict

    def __getitem__(self, key: str) -> Any:
        # Mapping-style access is convenient for small host adapters while the
        # dataclass attributes remain the canonical Python surface.
        if key == "id":
            return self.record_id
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MemoryRecord):
            return self.to_dict() == other.to_dict()
        if isinstance(other, Mapping):
            return self.to_dict() == dict(other)
        return NotImplemented

    def keys(self) -> tuple[str, ...]:
        return tuple(self.to_dict().keys())


# Alternate names used by a few host integrations.
Record = MemoryRecord
MemoryEntry = MemoryRecord
MemoryItem = MemoryRecord
ProvenanceRecord = MemoryRecord
Memory = MemoryRecord


_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _thread_lock_for(path: Path) -> threading.RLock:
    key = str(path)
    with _LOCKS_GUARD:
        lock = _LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCKS[key] = lock
        return lock


class MemoryStore:
    """A bounded JSON-file store for scoped project memory.

    Args:
        project_root: Project directory.  The store writes only below its
            ``.memory/ultimate-dev/memory`` directory.
        retention_seconds: Optional default age used by :meth:`cleanup`.
        retention_days: Convenience alternative to ``retention_seconds``.
        default_ttl_seconds: Optional TTL applied when an added record does
            not provide ``ttl``/``ttl_seconds``.
        max_records: Maximum number of retained records, bounded by
            :data:`MAX_RECORDS`.
        clock: Optional callable returning a datetime-like value; useful for
            deterministic hosts and tests.
        now: Alias for ``clock`` used by older runtime callers.
    """

    def __init__(
        self,
        project_root: str | Path,
        *,
        retention_seconds: float | _datetime.timedelta | str | None = None,
        retention_days: float | _datetime.timedelta | str | None = None,
        default_ttl_seconds: float | _datetime.timedelta | str | None = None,
        max_records: int = DEFAULT_MAX_RECORDS,
        clock: Any = None,
        now: Any = None,
    ) -> None:
        if project_root is None:
            raise MemoryStoreError("project_root is required")
        root = Path(project_root).expanduser().resolve()
        if root.exists() and not root.is_dir():
            raise MemoryStoreError("project_root must be a directory")
        self.project_root = root
        base = (root / STORAGE_RELATIVE).resolve()
        if base != root and root not in base.parents:
            raise MemoryStoreError("memory storage escapes the project root")
        self.base = base
        self.records_path = self.base / "records.json"
        # Common aliases for hosts inspecting the durable location.
        self.path = self.records_path
        self.file_path = self.records_path
        self.store_path = self.records_path
        self.memory_path = self.records_path
        self.directory = self.base
        if isinstance(max_records, bool) or not isinstance(max_records, int) or max_records <= 0:
            raise MemoryStoreError("max_records must be a positive integer")
        self.max_records = min(max_records, MAX_RECORDS)
        if retention_seconds is not None and retention_days is not None:
            raise MemoryStoreError("specify only one retention period")
        if retention_days is not None:
            retention_seconds = _retention_days_seconds(retention_days)
        self.retention_seconds = _duration_seconds(retention_seconds, label="retention_seconds")
        self.default_ttl_seconds = _duration_seconds(default_ttl_seconds, label="default_ttl_seconds")
        self.retention_days = (
            self.retention_seconds / 86400 if self.retention_seconds is not None else None
        )
        if clock is not None and now is not None:
            raise MemoryStoreError("specify only one of clock or now")
        selected_clock = clock if clock is not None else now
        if selected_clock is not None and not callable(selected_clock):
            raise MemoryStoreError("clock must be callable")
        self.clock = selected_clock
        try:
            self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:
            raise MemoryStoreError("unable to create project memory storage") from exc
        with contextlib.suppress(OSError):
            self.base.chmod(0o700)
        with self._lock():
            if not self.records_path.exists():
                self._write_unlocked([])

    def _assert_store_path(self, path: Path) -> None:
        root = self.project_root.resolve()
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            raise MemoryStoreError("memory path escapes the project root")
        if path.is_symlink():
            raise MemoryStoreError("memory storage paths must not be symlinks")

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        return None

    def close(self) -> None:
        return None

    def _now(self, value: Any = None) -> _datetime.datetime:
        if value is None and self.clock is not None:
            try:
                value = self.clock()
            except Exception as exc:
                raise MemoryStoreError("memory clock is unavailable") from exc
        result = _parse_timestamp(value, default=_utc_now())
        assert result is not None
        return result

    @contextlib.contextmanager
    def _lock(self) -> Iterator[None]:
        self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = self.base / ".lock"
        if lock_path.is_symlink():
            raise MemoryStoreError("memory lock path escapes the project root")
        thread_lock = _thread_lock_for(lock_path)
        with thread_lock:
            with open(lock_path, "a+", encoding="utf-8") as lock_file:
                with contextlib.suppress(OSError, AttributeError):
                    os.fchmod(lock_file.fileno(), 0o600)
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_unlocked(self) -> list[MemoryRecord]:
        if self.records_path.is_symlink():
            raise MemoryStoreError("memory records path escapes the project root")
        if not self.records_path.exists():
            return []
        with contextlib.suppress(OSError):
            self.records_path.chmod(0o600)
        try:
            if self.records_path.stat().st_size > MAX_STORE_BYTES:
                raise MemoryStoreError("memory records file exceeds the maximum size")
            with open(self.records_path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise MemoryStoreError("memory records file is unreadable or malformed") from exc
        if isinstance(raw, list):
            raw_records = raw
        elif isinstance(raw, Mapping):
            if raw.get("schema_version") not in (None, SCHEMA_VERSION):
                raise MemoryStoreError("unsupported memory records schema version")
            raw_records = raw.get("records")
            if not isinstance(raw_records, list):
                raise MemoryStoreError("memory records file must contain a records array")
        else:
            raise MemoryStoreError("memory records file must contain an object or array")
        records: list[MemoryRecord] = []
        seen: set[str] = set()
        for index, item in enumerate(raw_records):
            if not isinstance(item, Mapping):
                raise MemoryStoreError(f"memory record at index {index} is not an object")
            try:
                record = self._record_from_mapping(item)
            except (MemoryRecordError, TypeError) as exc:
                raise MemoryStoreError(f"memory record at index {index} is invalid") from exc
            if record.record_id in seen:
                raise MemoryStoreError("memory records contain duplicate record IDs")
            seen.add(record.record_id)
            records.append(record)
        return records

    def _write_unlocked(self, records: Iterable[MemoryRecord]) -> None:
        unique: dict[str, MemoryRecord] = {}
        for record in records:
            if record.record_id in unique:
                raise MemoryStoreError("cannot persist duplicate record IDs")
            unique[record.record_id] = record
        ordered = sorted(unique.values(), key=lambda item: (item.created_at or "", item.record_id))
        if len(ordered) > self.max_records:
            raise CapacityError("memory record capacity exceeded")
        payload = {"schema_version": SCHEMA_VERSION, "records": [record.to_dict() for record in ordered]}
        if len(_canonical_json(payload).encode("utf-8")) > MAX_STORE_BYTES:
            raise MemoryStoreError("memory records exceed the maximum persisted size")
        if self.records_path.is_symlink():
            raise MemoryStoreError("memory records path escapes the project root")
        self.base.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(prefix=".records-", suffix=".tmp", dir=self.base)
        try:
            with contextlib.suppress(OSError, AttributeError):
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.records_path)
            with contextlib.suppress(OSError):
                self.records_path.chmod(0o600)
        finally:
            with contextlib.suppress(OSError):
                if os.path.exists(temporary):
                    os.unlink(temporary)

    @staticmethod
    def _record_from_mapping(value: Mapping[str, Any]) -> MemoryRecord:
        data = dict(value)
        # ``to_dict`` includes a schema marker for the file, while the record
        # dataclass intentionally accepts only record fields.
        data.pop("schema_version", None)
        if "record_id" not in data and "id" in data:
            data["record_id"] = data["id"]
        if "ttl" not in data and "ttl_seconds" in data:
            data["ttl"] = data["ttl_seconds"]
        if "observed_at" not in data and "observed" in data:
            data["observed_at"] = data["observed"]
        if "verified_at" not in data and "verified" in data:
            data["verified_at"] = data["verified"]
        # These aliases are accepted on the wire but never persisted as
        # duplicate authority fields.
        data.pop("id", None)
        data.pop("ttl_seconds", None)
        data.pop("observed", None)
        data.pop("verified", None)
        return MemoryRecord(**data)

    @staticmethod
    def _sort_records(records: Iterable[MemoryRecord]) -> list[MemoryRecord]:
        return sorted(records, key=lambda item: (item.created_at or "", item.record_id))

    @staticmethod
    def _refresh_record(record: MemoryRecord, now: _datetime.datetime) -> tuple[MemoryRecord, bool]:
        effective = record.effective_status(now)
        if effective == record.status:
            return record, False
        # Expiry/staleness is derived lifecycle state.  Persisting it makes
        # restart behavior match the current query, while retaining timestamps.
        return replace(record, status=effective, updated_at=_format_timestamp(now)), True

    def _refresh_records(
        self,
        records: list[MemoryRecord],
        now: _datetime.datetime,
    ) -> tuple[list[MemoryRecord], bool]:
        refreshed: list[MemoryRecord] = []
        changed = False
        for record in records:
            item, item_changed = self._refresh_record(record, now)
            refreshed.append(item)
            changed = changed or item_changed
        return refreshed, changed

    @staticmethod
    def _identity(record: MemoryRecord) -> tuple[Any, ...] | None:
        if record.key:
            return (record.scope, record.kind, "key", record.key)
        if record.reference is not None:
            try:
                reference = _canonical_json(record.reference)
            except MemoryRecordError:
                reference = repr(record.reference)
            return (record.scope, record.kind, "reference", reference)
        return None

    @staticmethod
    def _same_record_payload(left: MemoryRecord, right: MemoryRecord) -> bool:
        return (
            left.digest == right.digest
            and left.kind == right.kind
            and left.scope == right.scope
        )

    def _find_conflicts(
        self,
        record: MemoryRecord,
        records: Sequence[MemoryRecord],
        now: _datetime.datetime,
    ) -> list[str]:
        identity = self._identity(record)
        if identity is None:
            return []
        return sorted(
            old.record_id
            for old in records
            if old.record_id != record.record_id
            and old.status not in TERMINAL_STATUSES
            and not old.is_expired(now)
            and self._identity(old) == identity
            and old.digest != record.digest
        )

    def _parse_add_arguments(
        self,
        kind: Any,
        content: Any,
        kwargs: dict[str, Any],
    ) -> tuple[str, Any, dict[str, Any]]:
        if kind is None and content is _MISSING and "record" in kwargs:
            record = kwargs["record"]
            if not isinstance(record, MemoryRecord):
                raise MemoryRecordError("record must be a MemoryRecord")
            return record.kind, record.content, {"record": record}
        if isinstance(kind, MemoryRecord):
            if content is not _MISSING or kwargs:
                raise TypeError("cannot combine a MemoryRecord with add fields")
            return kind.kind, kind.content, {"record": kind}
        if isinstance(kind, Mapping):
            if content is not _MISSING:
                raise TypeError("mapping records do not accept a separate content argument")
            data = dict(kind)
            data.update(kwargs)
            data.pop("schema_version", None)
            record_kind = data.pop("kind", data.pop("type", None))
            if record_kind is None:
                raise MemoryRecordError("record kind is required")
            # Keep ``reference`` in the field mapping when a caller supplies a
            # reference-only record; it must not be silently converted into
            # inline content.
            record_content = data.pop("content", None)
            if "content" not in kind and "value" in data:
                record_content = data.pop("value")
            if "reference" not in data and "ref" in data:
                data["reference"] = data.pop("ref")
            return record_kind, record_content, data
        if kind is None:
            raise MemoryRecordError("kind is required")
        return kind, content, kwargs

    def add(
        self,
        kind: str | MemoryRecord | Mapping[str, Any] | None = None,
        content: Any = _MISSING,
        **kwargs: Any,
    ) -> MemoryRecord:
        """Add a record and return its immutable durable representation.

        ``supersedes`` may name prior records explicitly.  In addition, a
        different payload with the same ``(scope, kind, key)`` or
        ``(scope, kind, reference)`` identity is treated as a contradiction and
        automatically supersedes the prior active record.  Records without an
        identity can coexist unless the caller supplies ``supersedes``.
        """
        kind_value, content_value, options = self._parse_add_arguments(kind, content, kwargs)
        record_value = options.pop("record", None)
        auto_supersede = True
        allow_multiple = False
        if record_value is not None:
            if not isinstance(record_value, MemoryRecord):
                raise MemoryRecordError("record must be a MemoryRecord")
            record = record_value
            # A dataclass passed directly is still checked for scope/secret
            # invariants, but lifecycle timestamps remain caller-controlled.
        else:
            if content_value is _MISSING:
                content_value = options.pop("value", None)
            operation_now = self._now(options.pop("now", None))
            observed = options.pop("observed_at", options.pop("observed", operation_now))
            verified = options.pop("verified_at", options.pop("verified", None))
            digest = options.pop("digest", "")
            source = options.pop("source", options.pop("provenance", "local"))
            if "reference" in options:
                reference = options.pop("reference")
            elif "ref" in options:
                reference = options.pop("ref")
            else:
                reference = None
            ttl = options.pop("ttl", _MISSING)
            if ttl is _MISSING and "ttl_seconds" in options:
                ttl = options.pop("ttl_seconds")
            if ttl is _MISSING and "expires_in" in options:
                ttl = options.pop("expires_in")
            if ttl is _MISSING:
                ttl = self.default_ttl_seconds
            stale_after = options.pop("stale_after", None)
            supersedes = options.pop("supersedes", ())
            contradicts = options.pop("contradicts", ())
            record_id = options.pop("record_id", options.pop("id", None))
            created_at = options.pop("created_at", operation_now)
            updated_at = options.pop("updated_at", operation_now)
            expires_at = options.pop("expires_at", None)
            status_reason = options.pop("status_reason", None)
            scope = options.pop("scope", "global")
            sensitivity = options.pop("sensitivity", "internal")
            confidence = options.pop("confidence", 1.0)
            status = options.pop("status", "active")
            key = options.pop(
                "key",
                options.pop(
                    "subject",
                    options.pop("claim", options.pop("fact_key", options.pop("identity", None))),
                ),
            )
            metadata = options.pop("metadata", None)
            authoritative = options.pop("authoritative", False)
            trust = options.pop("trust", "unverified")
            auto_supersede = options.pop("auto_supersede", True)
            allow_multiple = options.pop("allow_multiple", False)
            if options:
                unknown = ", ".join(sorted(options))
                raise TypeError(f"unsupported memory record fields: {unknown}")
            record = MemoryRecord(
                kind=kind_value,
                content=content_value,
                reference=reference,
                source=source,
                digest=digest,
                observed_at=observed,
                verified_at=verified,
                scope=scope,
                sensitivity=sensitivity,
                confidence=confidence,
                ttl=ttl,
                status=status,
                supersedes=supersedes,
                contradicts=contradicts,
                record_id=record_id or _new_record_id(),
                created_at=created_at,
                updated_at=updated_at,
                expires_at=expires_at,
                stale_after=stale_after,
                status_reason=status_reason,
                key=key,
                metadata=metadata or {},
                authoritative=authoritative,
                trust=trust,
            )

        with self._lock():
            records = self._read_unlocked()
            by_id = {item.record_id: item for item in records}
            if record.record_id in by_id:
                existing = by_id[record.record_id]
                if self._same_record_payload(existing, record):
                    return existing
                raise DuplicateRecord("record_id is already bound to different content")

            now = self._now(options.pop("now", None) if record_value is not None else operation_now)
            refreshed, refreshed_changed = self._refresh_records(records, now)
            by_id = {item.record_id: item for item in refreshed}
            if not allow_multiple and not record.supersedes and not record.contradicts:
                identity = self._identity(record)
                if identity is not None:
                    for existing in refreshed:
                        if (
                            existing.status in {"active", "unverified", "stale"}
                            and self._identity(existing) == identity
                            and existing.digest == record.digest
                        ):
                            return existing
            explicit = list(record.supersedes)
            contradiction_targets = list(record.contradicts)
            for target_id in explicit + contradiction_targets:
                target = by_id.get(target_id)
                if target is None:
                    raise RecordNotFound("supersedes refers to an unknown record")
                if target.scope != record.scope:
                    raise ScopeViolation("supersession cannot cross a scope boundary")
                if record.record_id in target.supersedes or record.record_id in target.contradicts:
                    raise MemoryStoreError("supersession cycle detected")
            conflicts = self._find_conflicts(record, refreshed, now) if auto_supersede and not allow_multiple else []
            target_ids: list[str] = []
            for target_id in explicit + contradiction_targets + conflicts:
                if target_id not in target_ids:
                    target_ids.append(target_id)
            if len(records) + 1 > self.max_records:
                raise CapacityError("memory record capacity exceeded")

            if target_ids:
                record = replace(record, supersedes=tuple(target_ids), updated_at=_format_timestamp(now))
                for target_id in target_ids:
                    target = by_id[target_id]
                    reason = (
                        "contradiction"
                        if target_id in conflicts or target_id in contradiction_targets
                        else "explicit_supersession"
                    )
                    by_id[target_id] = replace(
                        target,
                        status="superseded",
                        superseded_by=record.record_id,
                        status_reason=reason,
                        updated_at=_format_timestamp(now),
                    )
            elif refreshed_changed:
                # A direct dataclass may carry a stale/expired initial state;
                # do not rewrite it merely because the file was read.
                pass
            by_id[record.record_id] = record
            self._write_unlocked(by_id.values())
        return record

    record = add

    def add_record(self, record: MemoryRecord | Mapping[str, Any]) -> MemoryRecord:
        if isinstance(record, MemoryRecord):
            return self.add(record)
        if isinstance(record, Mapping):
            return self.add(record)
        raise MemoryRecordError("record must be a MemoryRecord or object")

    def create_record(self, record: MemoryRecord | Mapping[str, Any]) -> MemoryRecord:
        return self.add_record(record)

    def upsert(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        return self.add(*args, **kwargs)

    def remember(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        return self.add(*args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        return self.add(*args, **kwargs)

    def write(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        return self.add(*args, **kwargs)

    def store(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        return self.add(*args, **kwargs)

    def append(self, *args: Any, **kwargs: Any) -> MemoryRecord:
        kwargs.setdefault("auto_supersede", False)
        kwargs.setdefault("allow_multiple", True)
        return self.add(*args, **kwargs)

    def get(
        self,
        record_id: str,
        *,
        include_inactive: bool = False,
        include_stale: bool = False,
        include_expired: bool = False,
        now: Any = None,
    ) -> MemoryRecord | None:
        record_id = _validate_id(record_id, "record_id")
        if include_expired:
            include_inactive = True
        with self._lock():
            records = self._read_unlocked()
            current = self._now(now)
            refreshed, changed = self._refresh_records(records, current)
            if changed:
                self._write_unlocked(refreshed)
            for record in refreshed:
                if record.record_id == record_id:
                    if not include_inactive and not record.is_active(current, include_stale=include_stale):
                        return None
                    return record
            return None

    def get_record(self, record_id: str, **kwargs: Any) -> MemoryRecord | None:
        return self.get(record_id, **kwargs)

    def require(self, record_id: str, **kwargs: Any) -> MemoryRecord:
        record = self.get(record_id, **kwargs)
        if record is None:
            raise RecordNotFound("record does not exist")
        return record

    def get_required(self, record_id: str, **kwargs: Any) -> MemoryRecord:
        return self.require(record_id, **kwargs)

    def list(
        self,
        scope: Any = None,
        *,
        kind: str | Sequence[str] | None = None,
        status: str | Sequence[str] | None = None,
        include_inactive: bool = False,
        include_stale: bool = False,
        include_expired: bool = False,
        min_confidence: float = 0.0,
        query: str | None = None,
        limit: int | None = None,
        now: Any = None,
        include_parent_scopes: bool = False,
        include_child_scopes: bool = False,
        include_global: bool = True,
    ) -> list[MemoryRecord]:
        if include_expired:
            include_inactive = True
        if isinstance(min_confidence, bool) or not isinstance(min_confidence, (int, float)):
            raise MemoryStoreError("min_confidence must be a number")
        if not math.isfinite(float(min_confidence)) or not 0 <= float(min_confidence) <= 1:
            raise MemoryStoreError("min_confidence must be between 0 and 1")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise MemoryStoreError("limit must be a non-negative integer")
        current = self._now(now)
        with self._lock():
            records = self._read_unlocked()
            refreshed, changed = self._refresh_records(records, current)
            if changed:
                self._write_unlocked(refreshed)
            kinds = self._as_filter_set(kind)
            statuses = self._as_filter_set(status)
            if statuses is not None:
                statuses = {_normalize_status(item) for item in statuses}
                if statuses.intersection({"expired", "stale", "superseded", "revoked", "rejected"}):
                    include_inactive = True
                if "stale" in statuses:
                    include_stale = True
            query_text = query.casefold() if isinstance(query, str) else None
            result: list[MemoryRecord] = []
            for record in refreshed:
                if scope is not None and not _scope_matches(
                    record.scope,
                    scope,
                    include_parent_scopes=include_parent_scopes,
                    include_child_scopes=include_child_scopes,
                    include_global=include_global,
                ):
                    continue
                if kinds is not None and record.kind not in kinds:
                    continue
                effective = record.effective_status(current)
                if statuses is not None and effective not in statuses:
                    continue
                if not include_inactive and not record.is_active(current, include_stale=include_stale):
                    continue
                if record.confidence < float(min_confidence):
                    continue
                if query_text is not None:
                    haystack = _canonical_json({"content": record.content, "reference": record.reference})
                    if query_text not in haystack.casefold():
                        continue
                result.append(record)
            result = self._sort_records(result)
            if limit is not None:
                result = result[:limit]
            return result

    @staticmethod
    def _as_filter_set(value: str | Sequence[str] | None) -> set[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return {value}
        if isinstance(value, Sequence):
            return {str(item) for item in value}
        raise MemoryStoreError("filters must be a string or sequence")

    def all(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def list_records(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def query(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def retrieve(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def find(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def active(self, scope: Any = None, **kwargs: Any) -> list[MemoryRecord]:
        kwargs["include_inactive"] = False
        return self.list(scope, **kwargs)

    def __iter__(self) -> Iterator[MemoryRecord]:
        return iter(self.list())

    def __len__(self) -> int:
        return len(self.list())

    def __contains__(self, record_id: object) -> bool:
        if isinstance(record_id, MemoryRecord):
            record_id = record_id.record_id
        return isinstance(record_id, str) and self.get(record_id) is not None

    def __getitem__(self, record_id: str) -> MemoryRecord:
        record = self.get(record_id)
        if record is None:
            raise KeyError(record_id)
        return record

    def _replace_record(
        self,
        record_id: str,
        changes: Mapping[str, Any],
        *,
        now: Any = None,
    ) -> MemoryRecord:
        record_id = _validate_id(record_id, "record_id")
        with self._lock():
            records = self._read_unlocked()
            current = self._now(now)
            refreshed, _ = self._refresh_records(records, current)
            found = None
            for item in refreshed:
                if item.record_id == record_id:
                    found = item
                    break
            if found is None:
                raise RecordNotFound("record does not exist")
            requested_status = changes.get("status")
            if found.status in TERMINAL_STATUSES and requested_status not in {None, found.status}:
                raise MemoryStoreError("terminal memory records cannot be silently reactivated")
            if found.status == "expired" and requested_status not in {None, "expired"}:
                raise MemoryStoreError("expired memory records require a new record")
            updated = replace(found, **dict(changes), updated_at=_format_timestamp(current))
            # Recompute digest only when payload/provenance fields change.
            payload_fields = {"kind", "content", "reference", "source", "scope"}
            if payload_fields.intersection(changes):
                updated = replace(updated, digest="")
            result: list[MemoryRecord] = []
            for item in refreshed:
                result.append(updated if item.record_id == record_id else item)
            self._write_unlocked(result)
            return updated

    def update(self, record_id: str, **changes: Any) -> MemoryRecord:
        """Update mutable lifecycle/metadata fields without erasing history."""

        allowed = {
            "verified_at",
            "confidence",
            "status",
            "status_reason",
            "stale_after",
            "ttl",
            "metadata",
            "authoritative",
            "trust",
            "key",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise TypeError(f"unsupported mutable fields: {', '.join(sorted(unknown))}")
        return self._replace_record(record_id, changes)

    def mark_verified(
        self,
        record_id: str,
        *,
        verified_at: Any = None,
        confidence: float | None = None,
        authoritative: bool | None = None,
        now: Any = None,
    ) -> MemoryRecord:
        current = self._now(now)
        changes: dict[str, Any] = {
            "verified_at": _format_timestamp(current if verified_at is None else verified_at),
        }
        if confidence is not None:
            changes["confidence"] = confidence
        if authoritative is not None:
            changes["authoritative"] = authoritative
        existing = self.get(record_id, include_inactive=True, now=current)
        if existing is None:
            raise RecordNotFound("record does not exist")
        if existing.status in {"unverified", "stale"}:
            changes["status"] = "active"
        return self._replace_record(record_id, changes, now=current)

    def mark_stale(self, record_id: str, *, reason: str = "manually marked stale", now: Any = None) -> MemoryRecord:
        return self._replace_record(record_id, {"status": "stale", "status_reason": reason}, now=now)

    def mark_expired(self, record_id: str, *, now: Any = None) -> MemoryRecord:
        return self._replace_record(record_id, {"status": "expired"}, now=now)

    def revoke(
        self,
        record_id: str,
        *,
        reason: str = "revoked",
        restore_superseded: bool = True,
        now: Any = None,
    ) -> MemoryRecord:
        """Revoke a record and optionally restore the record it replaced."""

        record_id = _validate_id(record_id, "record_id")
        with self._lock():
            records = self._read_unlocked()
            current = self._now(now)
            refreshed, _ = self._refresh_records(records, current)
            by_id = {item.record_id: item for item in refreshed}
            target = by_id.get(record_id)
            if target is None:
                raise RecordNotFound("record does not exist")
            replacement_id = target.superseded_by
            by_id[record_id] = replace(
                target,
                status="revoked",
                status_reason=reason,
                updated_at=_format_timestamp(current),
            )
            prior_ids = set(target.supersedes) | set(target.contradicts)
            if restore_superseded and replacement_id and replacement_id in by_id:
                replacement = by_id[replacement_id]
                by_id[replacement_id] = replace(
                    replacement,
                    status="revoked",
                    status_reason="superseding record was revoked",
                    updated_at=_format_timestamp(current),
                )
            if restore_superseded and prior_ids:
                # Restore the most recent prior record in the chain, whether
                # the caller revoked a replacement or a superseded record.
                prior = [item for item in refreshed if item.record_id in prior_ids]
                if prior:
                    latest = max(prior, key=lambda item: (item.created_at or "", item.record_id))
                    by_id[latest.record_id] = replace(
                        latest,
                        status="active",
                        superseded_by=None,
                        status_reason="restored after revocation",
                        updated_at=_format_timestamp(current),
                    )
            self._write_unlocked(by_id.values())
            return by_id[record_id]

    def supersede(
        self,
        old_record_id: str,
        new_record: MemoryRecord | Mapping[str, Any] | Any = None,
        **kwargs: Any,
    ) -> MemoryRecord:
        """Create a replacement linked to ``old_record_id``."""

        old_record_id = _validate_id(old_record_id, "record_id")
        if new_record is not None and not isinstance(new_record, (MemoryRecord, Mapping)):
            # Convenient form: supersede(old_id, "new content", kind=...).
            kwargs.setdefault("content", new_record)
            new_record = None
        if new_record is None and "kind" not in kwargs:
            prior = self.get(old_record_id, include_inactive=True)
            if prior is not None:
                kwargs["kind"] = prior.kind
        if new_record is None:
            return self.add(supersedes=[old_record_id], **kwargs)
        if isinstance(new_record, MemoryRecord):
            supersedes = list(new_record.supersedes)
            if old_record_id not in supersedes:
                supersedes.append(old_record_id)
            new_record = replace(new_record, supersedes=tuple(supersedes))
            return self.add(new_record)
        if isinstance(new_record, Mapping):
            data = dict(new_record)
            existing = data.get("supersedes", ())
            if isinstance(existing, str):
                existing = [existing]
            data["supersedes"] = list(existing) + [old_record_id]
            return self.add(data)
        raise MemoryRecordError("new_record must be a MemoryRecord or object")

    def remove(self, record_id: str, *, hard: bool = True) -> MemoryRecord:
        record_id = _validate_id(record_id, "record_id")
        with self._lock():
            records = self._read_unlocked()
            found = next((item for item in records if item.record_id == record_id), None)
            if found is None:
                raise RecordNotFound("record does not exist")
            if hard:
                self._write_unlocked(item for item in records if item.record_id != record_id)
            else:
                revoked = replace(found, status="revoked", status_reason="removed by caller")
                self._write_unlocked(
                    revoked if item.record_id == record_id else item for item in records
                )
                return revoked
            return found

    def delete(self, record_id: str, *, hard: bool = True) -> MemoryRecord:
        return self.remove(record_id, hard=hard)

    def cleanup(
        self,
        retention_seconds: float | _datetime.timedelta | str | None = None,
        *,
        retention: float | _datetime.timedelta | str | None = None,
        retention_days: float | _datetime.timedelta | str | None = None,
        now: Any = None,
        preserve: Iterable[str] = (),
        scope: Any = None,
        include_global: bool = True,
    ) -> int:
        """Remove expired records and records older than the retention period.

        The method returns the number of removed records.  It is idempotent and
        never removes a record whose ID is in ``preserve``.
        """

        if (
            now is None
            and isinstance(retention_seconds, (_datetime.datetime, _datetime.date))
        ):
            now = retention_seconds
            retention_seconds = None
        supplied = [value for value in (retention_seconds, retention, retention_days) if value is not None]
        if len(supplied) > 1:
            raise MemoryStoreError("specify only one cleanup retention period")
        if retention_days is not None:
            retention_seconds = _retention_days_seconds(retention_days)
        elif retention is not None:
            retention_seconds = retention
        if retention_seconds is not None:
            retention_value = _duration_seconds(retention_seconds, label="retention_seconds")
        else:
            retention_value = self.retention_seconds
        assert retention_value is None or retention_value >= 0
        current = self._now(now)
        if isinstance(preserve, str):
            protected = {preserve}
        else:
            protected = {item for item in preserve if isinstance(item, str)}
        with self._lock():
            records = self._read_unlocked()
            refreshed, _ = self._refresh_records(records, current)
            retained: list[MemoryRecord] = []
            cutoff = current - _datetime.timedelta(seconds=retention_value) if retention_value is not None else None
            for record in refreshed:
                if scope is not None and not _scope_matches(
                    record.scope,
                    scope,
                    include_global=include_global,
                ):
                    retained.append(record)
                    continue
                if record.record_id in protected:
                    retained.append(record)
                    continue
                remove = record.effective_status(current) == "expired"
                if not remove and cutoff is not None:
                    created = _parse_timestamp(record.created_at)
                    observed = _parse_timestamp(record.observed_at)
                    assert created is not None and observed is not None
                    remove = min(created, observed) <= cutoff
                if not remove:
                    retained.append(record)
            removed = len(refreshed) - len(retained)
            if removed:
                self._write_unlocked(retained)
            return removed

    def retention_cleanup(self, *args: Any, **kwargs: Any) -> int:
        return self.cleanup(*args, **kwargs)

    def prune(self, *args: Any, **kwargs: Any) -> int:
        return self.cleanup(*args, **kwargs)

    def cleanup_retention(self, *args: Any, **kwargs: Any) -> int:
        return self.cleanup(*args, **kwargs)

    def cleanup_expired(self, *, now: Any = None) -> int:
        return self.cleanup(now=now)

    def expire(self, record_id: str, *, now: Any = None) -> MemoryRecord:
        return self.mark_expired(record_id, now=now)

    def mark_retired(self, record_id: str, *, reason: str = "retired", now: Any = None) -> MemoryRecord:
        return self._replace_record(record_id, {"status": "superseded", "status_reason": reason}, now=now)

    def records(self, *args: Any, **kwargs: Any) -> list[MemoryRecord]:
        return self.list(*args, **kwargs)

    def get_active(self, record_id: str, **kwargs: Any) -> MemoryRecord | None:
        kwargs.setdefault("include_inactive", False)
        return self.get(record_id, **kwargs)

    @staticmethod
    def _projection_cost(item: Mapping[str, Any]) -> int:
        return len(_canonical_json(item))

    @staticmethod
    def _truncate_projection_item(item: dict[str, Any], budget: int) -> dict[str, Any] | None:
        """Try to fit a string payload while retaining provenance metadata.

        A compact fallback is used when the full projection envelope cannot
        fit.  It keeps identity and provenance but drops duplicated freshness
        fields, so a small budget still has useful deterministic context.
        """

        content = item.get("content")
        reference = item.get("reference")
        if isinstance(content, str):
            payload_field = "content"
            payload = content
        elif isinstance(reference, str):
            payload_field = "reference"
            payload = reference
        else:
            return None
        if budget <= 0:
            return None
        candidates: list[dict[str, Any]] = [dict(item)]
        compact = {
            "id": item.get("id"),
            "kind": item.get("kind"),
            "source": item.get("source"),
            "digest": item.get("digest"),
            "observed_at": item.get("observed_at"),
            "verified_at": item.get("verified_at"),
            "scope": item.get("scope"),
            "sensitivity": item.get("sensitivity"),
            "confidence": item.get("confidence"),
            "status": item.get("status"),
            "reason": item.get("reason"),
            "truncated": True,
        }
        if payload_field == "content":
            compact["content"] = ""
        else:
            compact["reference"] = ""
        candidates.append(compact)
        for candidate in candidates:
            candidate[payload_field] = ""
            candidate["truncated"] = True
            overhead = MemoryStore._projection_cost(candidate)
            available = budget - overhead
            if available <= 0:
                continue
            low, high = 0, len(payload)
            best: dict[str, Any] | None = None
            while low <= high:
                middle = (low + high) // 2
                trial = dict(candidate)
                trial[payload_field] = payload[:middle]
                if MemoryStore._projection_cost(trial) <= budget:
                    best = trial
                    low = middle + 1
                else:
                    high = middle - 1
            if best is not None:
                return best
        return None

    def project_context(
        self,
        scope: Any = "global",
        *,
        budget: int = DEFAULT_PROJECTION_BUDGET,
        budget_chars: int | None = None,
        max_chars: int | None = None,
        now: Any = None,
        kind: str | Sequence[str] | None = None,
        status: str | Sequence[str] | None = None,
        max_sensitivity: str | None = None,
        min_confidence: float = 0.0,
        query: str | None = None,
        limit: int | None = None,
        include_inactive: bool = False,
        include_stale: bool = False,
        include_expired: bool = False,
        include_parent_scopes: bool = False,
        include_child_scopes: bool = False,
        include_global: bool = True,
        include_metadata: bool = False,
        auto_supersede: bool = True,
    ) -> dict[str, Any]:
        """Return deterministic, budgeted context items.

        ``budget`` is a character budget for the serialized ``items`` array;
        metadata in the outer envelope is not charged.  The output contains
        both ``items`` and ``records`` aliases for host adapters with different
        naming conventions.
        """

        if budget_chars is not None:
            budget = budget_chars
        if max_chars is not None:
            budget = max_chars
        if include_expired:
            include_inactive = True
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            raise MemoryStoreError("projection budget must be a non-negative integer")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise MemoryStoreError("projection limit must be a non-negative integer")
        if isinstance(min_confidence, bool) or not isinstance(min_confidence, (int, float)):
            raise MemoryStoreError("min_confidence must be a number")
        if not math.isfinite(float(min_confidence)) or not 0 <= float(min_confidence) <= 1:
            raise MemoryStoreError("min_confidence must be between 0 and 1")
        max_rank = None
        if max_sensitivity is not None:
            max_rank = SENSITIVITY_RANK[_normalize_sensitivity(max_sensitivity)]
        current = self._now(now)
        with self._lock():
            records = self._read_unlocked()
            refreshed, changed = self._refresh_records(records, current)
            if changed:
                self._write_unlocked(refreshed)
            kinds = self._as_filter_set(kind)
            statuses = self._as_filter_set(status)
            if statuses is not None:
                statuses = {_normalize_status(item) for item in statuses}
                if statuses.intersection({"expired", "stale", "superseded", "revoked", "rejected"}):
                    include_inactive = True
                if "stale" in statuses:
                    include_stale = True
            query_text = query.casefold() if isinstance(query, str) else None
            candidates: list[MemoryRecord] = []
            for record in refreshed:
                if not _scope_matches(
                    record.scope,
                    scope,
                    include_parent_scopes=include_parent_scopes,
                    include_child_scopes=include_child_scopes,
                    include_global=include_global,
                ):
                    continue
                if kinds is not None and record.kind not in kinds:
                    continue
                effective = record.effective_status(current)
                if statuses is not None and effective not in statuses:
                    continue
                if not include_inactive and not record.is_active(current, include_stale=include_stale):
                    continue
                if max_rank is not None and SENSITIVITY_RANK[record.sensitivity] > max_rank:
                    continue
                if record.confidence < float(min_confidence):
                    continue
                if query_text is not None:
                    haystack = _canonical_json({"content": record.content, "reference": record.reference})
                    if query_text not in haystack.casefold():
                        continue
                candidates.append(record)

            def projection_sort(record: MemoryRecord) -> tuple[Any, ...]:
                verified = _parse_timestamp(record.verified_at)
                observed = _parse_timestamp(record.observed_at)
                freshness = verified or observed
                assert freshness is not None
                return (
                    -int(record.authoritative),
                    -record.confidence,
                    -freshness.timestamp(),
                    record.kind,
                    record.record_id,
                )

            candidates.sort(key=projection_sort)
            omitted: list[str] = []
            if limit is not None and len(candidates) > limit:
                omitted.extend(record.record_id for record in candidates[limit:])
                candidates = candidates[:limit]
            selected: list[dict[str, Any]] = []
            used = 0
            for record in candidates:
                remaining = budget - used
                item = record.to_projection_dict(current)
                if include_metadata:
                    item["metadata"] = record.metadata
                item["reason"] = "fresh_verified" if record.verified_at else "fresh_unverified"
                if record.status == "active" and record.verified_at is None:
                    item["reason"] = "fresh_unverified"
                cost = self._projection_cost(item)
                if cost > remaining:
                    truncated = self._truncate_projection_item(item, remaining)
                    if truncated is not None:
                        selected.append(truncated)
                        used += self._projection_cost(truncated)
                        continue
                    omitted.append(record.record_id)
                    continue
                selected.append(item)
                used += cost
            return {
                "schema_version": SCHEMA_VERSION,
                "scope": _normalize_scope(scope),
                "budget": budget,
                "used": used,
                "used_budget": used,
                "budget_used": used,
                "total_chars": used,
                "remaining": max(0, budget - used),
                "items": selected,
                "records": list(selected),
                "selected": list(selected),
                "memory": list(selected),
                "omitted": omitted,
                "omitted_count": len(omitted),
                "truncated": bool(omitted),
                "deterministic": True,
            }

    # Projection naming variants keep the store usable without coupling to a
    # particular context manager implementation.
    def context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def project(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def project_for_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def project_memory(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def context_projection(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def build_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def select_for_context(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.project_context(*args, **kwargs)

    def project_items(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return self.project_context(*args, **kwargs)["items"]

    def export(self, *, include_inactive: bool = True, now: Any = None) -> list[dict[str, Any]]:
        records = self.list(include_inactive=include_inactive, now=now)
        return [record.to_dict() for record in records]

    def clear(self, *, hard: bool = True) -> int:
        with self._lock():
            records = self._read_unlocked()
            if not hard:
                revoked = [
                    replace(item, status="revoked", status_reason="store cleared") for item in records
                ]
                self._write_unlocked(revoked)
                return len(revoked)
            count = len(records)
            self._write_unlocked([])
            return count


# Alternate names for host-neutral integrations.
ProvenanceMemoryStore = MemoryStore
MemoryRepository = MemoryStore
BoundedMemoryStore = MemoryStore


def create_memory_store(project_root: str | Path, **kwargs: Any) -> MemoryStore:
    """Construct a :class:`MemoryStore` without importing Runtime internals."""

    return MemoryStore(project_root, **kwargs)


__all__ = [
    "BoundedMemoryStore",
    "CapacityError",
    "DigestMismatch",
    "DuplicateRecord",
    "MAX_RECORD_CHARS",
    "MAX_RECORDS",
    "MAX_STORE_BYTES",
    "Memory",
    "MemoryConflict",
    "MemoryEntry",
    "MemoryItem",
    "MemoryError",
    "MemoryRecord",
    "MemoryRecordError",
    "MemoryRepository",
    "MemoryStore",
    "MemoryStoreError",
    "ProvenanceMemoryStore",
    "ProvenanceRecord",
    "Record",
    "RecordNotFound",
    "RetentionError",
    "SCHEMA_VERSION",
    "STORAGE_RELATIVE",
    "ScopeError",
    "ScopeViolation",
    "SecretRedactionError",
    "SecretDetected",
    "SecretRefusal",
    "SecretRefused",
    "compute_digest",
    "create_memory_store",
    "digest_for",
    "redact",
    "redact_value",
]
