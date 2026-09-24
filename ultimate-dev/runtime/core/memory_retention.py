"""Consent-based, bounded retention for provenance memory records."""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
import secrets
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .contracts import ContractError, fingerprint
from .memory import MemoryRecord, MemoryStore, MemoryStoreError


TOKEN_RE = re.compile(r"^memory-delete-[A-Za-z0-9_-]{20,}$")
DEFAULT_TTL_SECONDS = 15 * 60
MAX_REPORT_BYTES = 1_000_000


class MemoryRetentionError(RuntimeError):
    """Base error for memory retention operations."""


class MemoryRetentionPlanChanged(MemoryRetentionError):
    """The memory changed after a destructive plan was issued."""


@dataclass(frozen=True)
class MemoryRetentionPolicy:
    max_age_seconds: float = 30 * 86400.0
    preserve_ids: frozenset[str] = frozenset()
    preserve_scopes: frozenset[str] = frozenset()
    preserve_sensitivity: frozenset[str] = frozenset({"sensitive", "confidential", "secret"})
    include_inactive: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.max_age_seconds, bool) or not isinstance(self.max_age_seconds, (int, float)) or not math.isfinite(float(self.max_age_seconds)) or self.max_age_seconds < 0:
            raise MemoryRetentionError("max_age_seconds must be finite and non-negative")
        for name, value in (("preserve_ids", self.preserve_ids), ("preserve_scopes", self.preserve_scopes), ("preserve_sensitivity", self.preserve_sensitivity)):
            if not isinstance(value, (set, frozenset, tuple, list)) or any(not isinstance(item, str) or not item for item in value):
                raise MemoryRetentionError(f"{name} must contain strings")
        object.__setattr__(self, "max_age_seconds", float(self.max_age_seconds))
        object.__setattr__(self, "preserve_ids", frozenset(self.preserve_ids))
        object.__setattr__(self, "preserve_scopes", frozenset(self.preserve_scopes))
        object.__setattr__(self, "preserve_sensitivity", frozenset(self.preserve_sensitivity))
        if not isinstance(self.include_inactive, bool):
            raise MemoryRetentionError("include_inactive must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_age_seconds": self.max_age_seconds,
            "preserve_ids": sorted(self.preserve_ids),
            "preserve_scopes": sorted(self.preserve_scopes),
            "preserve_sensitivity": sorted(self.preserve_sensitivity),
            "include_inactive": self.include_inactive,
        }


@dataclass(frozen=True)
class MemoryRetentionEntry:
    record_id: str
    action: str
    reason: str
    digest: str
    scope: str
    sensitivity: str

    def to_dict(self) -> dict[str, str]:
        return {
            "record_id": self.record_id,
            "action": self.action,
            "reason": self.reason,
            "digest": self.digest,
            "scope": self.scope,
            "sensitivity": self.sensitivity,
        }


class MemoryRetentionManager:
    """Plan and apply memory deletion with a durable, expiring confirmation."""

    def __init__(self, store: MemoryStore, *, policy: MemoryRetentionPolicy | None = None, clock: Callable[[], Any] | None = None) -> None:
        if not isinstance(store, MemoryStore):
            raise MemoryRetentionError("store must be a MemoryStore")
        self.store = store
        self.policy = policy or MemoryRetentionPolicy()
        self.clock = clock or store._now
        self.root = store.base / "retention"
        self._validate_path(self.root)

    def _validate_path(self, path: Path) -> None:
        root = self.store.project_root.resolve()
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            raise MemoryRetentionError("memory retention path escapes the project")
        current = root
        for part in path.relative_to(root).parts:
            current = current / part
            if current.is_symlink():
                raise MemoryRetentionError("memory retention paths must not be symlinks")

    def _now(self) -> dt.datetime:
        value = self.clock()
        result = self.store._now(value)
        if result.tzinfo is None:
            result = result.replace(tzinfo=dt.timezone.utc)
        return result.astimezone(dt.timezone.utc)

    def _eligible(self, record: MemoryRecord, now: dt.datetime) -> tuple[bool, str]:
        if record.record_id in self.policy.preserve_ids:
            return False, "preserved_id"
        if str(record.scope) in self.policy.preserve_scopes:
            return False, "preserved_scope"
        if str(record.sensitivity) in self.policy.preserve_sensitivity:
            return False, "preserved_sensitivity"
        if record.effective_status(now) in {"expired", "revoked", "superseded", "rejected"}:
            return True, "terminal_status"
        observed = record.observed_at_datetime
        created = record.created_at_datetime if hasattr(record, "created_at_datetime") else observed
        if now - min(observed, created) >= dt.timedelta(seconds=self.policy.max_age_seconds):
            return True, "retention_age"
        return False, "within_retention"

    def _snapshot(self) -> tuple[list[MemoryRecord], str, list[MemoryRetentionEntry], dt.datetime]:
        now = self._now()
        with self.store._lock():
            records = self.store._read_unlocked()
        entries: list[MemoryRetentionEntry] = []
        selected: list[MemoryRecord] = []
        for record in sorted(records, key=lambda item: item.record_id):
            eligible, reason = self._eligible(record, now)
            if eligible:
                selected.append(record)
                entries.append(MemoryRetentionEntry(record.record_id, "would_delete", reason, record.digest, str(record.scope), str(record.sensitivity)))
            else:
                entries.append(MemoryRetentionEntry(record.record_id, "preserved", reason, record.digest, str(record.scope), str(record.sensitivity)))
        plan = fingerprint({
            "policy": self.policy.to_dict(),
            "records": [{"id": item.record_id, "digest": item.digest} for item in selected],
        })
        return records, plan, entries, now

    def _token_path(self, token: str) -> Path:
        if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
            raise MemoryRetentionError("invalid memory cleanup confirmation token")
        path = self.root / "confirmations" / f"{token}.json"
        self._validate_path(path)
        return path

    def _write_json(self, path: Path, value: Mapping[str, Any]) -> None:
        self._validate_path(path.parent)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        encoded = json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > MAX_REPORT_BYTES:
            raise MemoryRetentionError("memory retention receipt exceeds its size limit")
        fd, temporary = tempfile.mkstemp(prefix=".memory-retention-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary)

    def plan(self) -> dict[str, Any]:
        _, plan_digest, entries, now = self._snapshot()
        token = f"memory-delete-{secrets.token_urlsafe(32)}"
        self._write_json(
            self._token_path(token),
            {
                "schema_version": "1.0",
                "plan_digest": plan_digest,
                "issued_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": (now + dt.timedelta(seconds=DEFAULT_TTL_SECONDS)).isoformat().replace("+00:00", "Z"),
                "consumed_at": None,
            },
        )
        return {
            "ok": True,
            "dry_run": True,
            "plan_digest": plan_digest,
            "confirmation_token": token,
            "entries": [entry.to_dict() for entry in entries],
        }

    def apply(self, token: str) -> dict[str, Any]:
        path = self._token_path(token)
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MemoryRetentionError("memory cleanup confirmation is unavailable") from exc
        if not isinstance(metadata, Mapping) or metadata.get("consumed_at") is not None:
            raise MemoryRetentionError("memory cleanup confirmation is invalid or already consumed")
        now = self._now()
        try:
            expires = dt.datetime.fromisoformat(str(metadata["expires_at"]).replace("Z", "+00:00"))
        except (KeyError, ValueError) as exc:
            raise MemoryRetentionError("memory cleanup confirmation expiry is invalid") from exc
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=dt.timezone.utc)
        if expires <= now:
            raise MemoryRetentionError("memory cleanup confirmation has expired")
        _, current_digest, entries, _ = self._snapshot()
        if current_digest != metadata.get("plan_digest"):
            raise MemoryRetentionPlanChanged("memory changed after cleanup planning; plan again")
        with self.store._lock():
            records = self.store._read_unlocked()
            selected_ids = {entry.record_id for entry in entries if entry.action == "would_delete"}
            retained = [record for record in records if record.record_id not in selected_ids]
            self.store._write_unlocked(retained)
        metadata = dict(metadata)
        metadata["consumed_at"] = now.isoformat().replace("+00:00", "Z")
        self._write_json(path, metadata)
        receipt = {
            "schema_version": "1.0",
            "deleted_at": metadata["consumed_at"],
            "plan_digest": current_digest,
            "record_ids": sorted(selected_ids),
        }
        receipt_path = self.root / "receipts" / f"delete-{now.strftime('%Y%m%dT%H%M%S%fZ')}-{secrets.token_hex(6)}.json"
        self._write_json(receipt_path, receipt)
        return {"ok": True, "dry_run": False, "deleted": len(selected_ids), "plan_digest": current_digest, "receipt_path": str(receipt_path.relative_to(self.store.project_root))}

    def cleanup(self, *, dry_run: bool = True, confirmation_token: str | None = None) -> dict[str, Any]:
        if dry_run:
            return self.plan()
        if not confirmation_token:
            raise MemoryRetentionError("destructive memory cleanup requires a confirmation token")
        return self.apply(confirmation_token)


__all__ = [
    "MemoryRetentionEntry",
    "MemoryRetentionError",
    "MemoryRetentionManager",
    "MemoryRetentionPlanChanged",
    "MemoryRetentionPolicy",
]
