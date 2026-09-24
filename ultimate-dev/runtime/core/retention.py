"""Safe task retention, archival, and confirmed deletion.

The Runtime stores each task at::

    <project>/.memory/ultimate-dev/tasks/<task-id>/

This module deliberately operates beside :class:`runtime.core.state.TaskStore`
rather than changing the task-state contract.  It selects only tasks that match
an explicit age *and* status policy, preserves in-flight and uncertain work by
default, and fails closed on malformed state or unsafe paths.

Deletion is a two-step operation:

1. ``cleanup(..., dry_run=True, delete=True)`` returns a report with a random,
   process-local confirmation token and a plan digest.
2. ``cleanup(..., delete=True, confirmation_token=...)`` revalidates that exact
   plan, moves every selected task into the contained task-archive, writes an
   archive manifest, and only then recursively deletes the archived copy.

With ``delete=False`` the same archive step is retained without deletion.  Dry
runs and archive-only runs do not require confirmation because they are
reversible containment operations.  Reports are returned in memory and, for
mutating non-empty runs, are also written below project-local memory.
"""
from __future__ import annotations

import contextlib
import datetime as datetime_module
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import stat
import tempfile
import threading
import uuid
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable


try:  # POSIX hosts get cross-process cleanup locking.
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = "1.0"
TASKS_RELATIVE = Path(".memory") / "ultimate-dev" / "tasks"
ARCHIVES_RELATIVE = Path(".memory") / "ultimate-dev" / "task-archives"
REPORTS_RELATIVE = Path(".memory") / "ultimate-dev" / "retention" / "reports"

DEFAULT_RETENTION = datetime_module.timedelta(days=30)
DEFAULT_ELIGIBLE_STATUSES = frozenset({"completed", "abandoned", "cancelled"})
ACTIVE_TASK_STATUSES = frozenset(
    {
        "created",
        "ready",
        "planning",
        "planned",
        "executing",
        "observing",
        "verifying",
        "recovering",
        "replanned",
        "paused",
        "interrupted",
    }
)
DEFAULT_PRESERVE_STATUSES = ACTIVE_TASK_STATUSES | frozenset(
    {"blocked", "failed", "uncertain"}
)
UNCERTAIN_OPERATION_STATUSES = frozenset({"pending", "running", "uncertain"})

DEFAULT_MAX_STATE_BYTES = 2_000_000
DEFAULT_MAX_OPERATION_FILES = 10_000
DEFAULT_LOCK_TIMEOUT_SECONDS = 10.0
DEFAULT_CONFIRMATION_TTL_SECONDS = 15 * 60

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_STATUS_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_DURATION_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d|weeks?|w)\s*$",
    re.IGNORECASE,
)
_ISO_DURATION_RE = re.compile(
    r"^P(?:(\d+(?:\.\d+)?)D)?(?:T(?:(\d+(?:\.\d+)?)H)?"
    r"(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?$",
    re.IGNORECASE,
)
_DURATION_MULTIPLIERS = {
    "s": 1.0,
    "m": 60.0,
    "h": 3600.0,
    "d": 86400.0,
    "w": 604800.0,
}
_FALLBACK_LOCK_NAMES = frozenset(
    {".retention.lock", ".retention.lock.exclusive"}
)


class RetentionError(RuntimeError):
    """Base error for task-retention operations."""


class RetentionContractError(RetentionError, ValueError):
    """Raised when a retention policy or confirmation is malformed."""


class UnsafeRetentionPath(RetentionError):
    """Raised when a storage path is not safely contained."""


class ConfirmationRequired(RetentionError, PermissionError):
    """Raised when destructive cleanup lacks a valid issued token."""


class RetentionPlanChanged(ConfirmationRequired):
    """Raised when a confirmed plan no longer matches durable task state."""


@dataclass(frozen=True)
class RetentionPolicy:
    """Selection and fail-closed safeguards for task cleanup.

    A task is eligible only when its status appears in ``eligible_statuses``,
    it does not appear in ``preserve_statuses``, it has no protected uncertainty,
    and it is at least ``max_age`` old according to ``state.json.updated_at``.
    ``preserve_statuses`` wins if a caller deliberately lists a status in both
    sets.  Set it explicitly to an empty collection to opt out of the defaults.
    """

    max_age: datetime_module.timedelta | float | str | None = DEFAULT_RETENTION
    eligible_statuses: Iterable[str] = DEFAULT_ELIGIBLE_STATUSES
    preserve_statuses: Iterable[str] = DEFAULT_PRESERVE_STATUSES
    protect_uncertain_operations: bool = True
    max_state_bytes: int = DEFAULT_MAX_STATE_BYTES
    max_operation_files: int = DEFAULT_MAX_OPERATION_FILES

    def __post_init__(self) -> None:
        max_age = _duration_seconds(self.max_age, "max_age")
        object.__setattr__(
            self,
            "max_age",
            None if max_age is None else datetime_module.timedelta(seconds=max_age),
        )
        object.__setattr__(
            self,
            "eligible_statuses",
            _status_set(
                self.eligible_statuses,
                "eligible_statuses",
                default=DEFAULT_ELIGIBLE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "preserve_statuses",
            _status_set(
                self.preserve_statuses,
                "preserve_statuses",
                default=DEFAULT_PRESERVE_STATUSES,
            ),
        )
        if not isinstance(self.protect_uncertain_operations, bool):
            raise RetentionContractError("protect_uncertain_operations must be boolean")
        for name, value, minimum in (
            ("max_state_bytes", self.max_state_bytes, 1),
            ("max_operation_files", self.max_operation_files, 1),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise RetentionContractError(f"{name} must be an integer >= {minimum}")

    @property
    def max_age_seconds(self) -> float | None:
        if self.max_age is None:
            return None
        return self.max_age.total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_age_seconds": self.max_age_seconds,
            "eligible_statuses": sorted(self.eligible_statuses),
            "preserve_statuses": sorted(self.preserve_statuses),
            "protect_uncertain_operations": self.protect_uncertain_operations,
            "max_state_bytes": self.max_state_bytes,
            "max_operation_files": self.max_operation_files,
        }


@dataclass(frozen=True)
class TaskDisposition:
    """One task's retention decision in a :class:`CleanupReport`."""

    task_id: str
    action: str
    reason: str
    eligible: bool = False
    status: str | None = None
    revision: int | None = None
    age_seconds: float | None = None
    source_path: str | None = None
    archive_path: str | None = None
    archived: bool = False
    deleted: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "action": self.action,
            "reason": self.reason,
            "eligible": self.eligible,
            "status": self.status,
            "revision": self.revision,
            "age_seconds": self.age_seconds,
            "source_path": self.source_path,
            "archive_path": self.archive_path,
            "archived": self.archived,
            "deleted": self.deleted,
            "error": self.error,
        }


class CleanupReport(Mapping[str, Any]):
    """Immutable, JSON-compatible cleanup report with mapping ergonomics."""

    def __init__(
        self,
        *,
        generated_at: str,
        dry_run: bool,
        mode: str,
        storage_root: str,
        policy: RetentionPolicy,
        entries: Iterable[TaskDisposition],
        plan_digest: str,
        confirmation_token: str | None = None,
        confirmation_required: bool = False,
        confirmation_verified: bool = False,
        report_path: str | None = None,
    ) -> None:
        self.generated_at = generated_at
        self.dry_run = bool(dry_run)
        self.mode = mode
        self.storage_root = storage_root
        self.policy = policy
        self.entries = tuple(entries)
        self.plan_digest = plan_digest
        self.confirmation_token = confirmation_token
        self.confirmation_required = bool(confirmation_required)
        self.confirmation_verified = bool(confirmation_verified)
        self.report_path = report_path

    @property
    def selected_count(self) -> int:
        return sum(1 for entry in self.entries if entry.eligible)

    @property
    def would_archive_count(self) -> int:
        return sum(1 for entry in self.entries if entry.action == "would_archive")

    @property
    def would_delete_count(self) -> int:
        return sum(1 for entry in self.entries if entry.action == "would_delete")

    @property
    def archived_count(self) -> int:
        return sum(1 for entry in self.entries if entry.archived)

    @property
    def deleted_count(self) -> int:
        return sum(1 for entry in self.entries if entry.deleted)

    @property
    def preserved_count(self) -> int:
        return sum(1 for entry in self.entries if entry.action == "preserved")

    @property
    def error_count(self) -> int:
        return sum(1 for entry in self.entries if entry.error is not None)

    @property
    def success(self) -> bool:
        return self.error_count == 0

    def with_report_path(self, report_path: str) -> "CleanupReport":
        """Return a detached report carrying its persisted relative path."""
        return CleanupReport(
            generated_at=self.generated_at,
            dry_run=self.dry_run,
            mode=self.mode,
            storage_root=self.storage_root,
            policy=self.policy,
            entries=self.entries,
            plan_digest=self.plan_digest,
            confirmation_token=self.confirmation_token,
            confirmation_required=self.confirmation_required,
            confirmation_verified=self.confirmation_verified,
            report_path=report_path,
        )

    def to_dict(self, *, include_confirmation_token: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": self.generated_at,
            "dry_run": self.dry_run,
            "mode": self.mode,
            "storage_root": self.storage_root,
            "policy": self.policy.to_dict(),
            "plan_digest": self.plan_digest,
            "confirmation_required": self.confirmation_required,
            "confirmation_verified": self.confirmation_verified,
            "report_path": self.report_path,
            "counts": {
                "selected": self.selected_count,
                "would_archive": self.would_archive_count,
                "would_delete": self.would_delete_count,
                "archived": self.archived_count,
                "deleted": self.deleted_count,
                "preserved": self.preserved_count,
                "errors": self.error_count,
            },
            "entries": [entry.to_dict() for entry in self.entries],
        }
        if include_confirmation_token:
            value["confirmation_token"] = self.confirmation_token
        return value

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def __repr__(self) -> str:
        return (
            "CleanupReport("
            f"mode={self.mode!r}, dry_run={self.dry_run!r}, "
            f"selected={self.selected_count}, deleted={self.deleted_count}, "
            f"archived={self.archived_count}, errors={self.error_count})"
        )


@dataclass(frozen=True)
class _TaskSnapshot:
    task_id: str
    path: Path
    identity: tuple[int, int]
    state: dict[str, Any]
    state_digest: str
    snapshot_digest: str
    uncertain_reasons: tuple[str, ...]


class _TaskReadError(RetentionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_PROCESS_LOCKS: dict[str, threading.RLock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()
_CONFIRMATION_LOCK = threading.Lock()
_ISSUED_CONFIRMATIONS: dict[tuple[str, str], str] = {}
_MAX_REMEMBERED_CONFIRMATIONS = 256


def _duration_seconds(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, datetime_module.timedelta):
        seconds = value.total_seconds()
    elif isinstance(value, bool):
        raise RetentionContractError(f"{label} must be a non-negative duration")
    elif isinstance(value, (int, float)):
        seconds = float(value)
    elif isinstance(value, str):
        raw = value.strip()
        match = _DURATION_RE.fullmatch(raw)
        if match:
            amount = float(match.group(1))
            unit = match.group(2).lower()
            multiplier = next(
                value
                for suffix, value in _DURATION_MULTIPLIERS.items()
                if unit.startswith(suffix) or (suffix == "m" and unit.startswith("min"))
            )
            seconds = amount * multiplier
        else:
            iso_match = _ISO_DURATION_RE.fullmatch(raw)
            if not iso_match or not any(iso_match.groups()):
                raise RetentionContractError(
                    f"{label} must be seconds or a duration such as '30d' or 'P30D'"
                )
            days, hours, minutes, seconds_part = (
                float(group or 0.0) for group in iso_match.groups()
            )
            seconds = (
                days * 86400.0 + hours * 3600.0 + minutes * 60.0 + seconds_part
            )
    else:
        raise RetentionContractError(f"{label} must be a duration")
    if not math.isfinite(seconds) or seconds < 0:
        raise RetentionContractError(f"{label} must be a finite non-negative duration")
    return seconds


def _status_set(
    value: Any,
    label: str,
    *,
    default: frozenset[str],
) -> frozenset[str]:
    if value is None:
        return default
    if isinstance(value, str):
        values = [value]
    else:
        try:
            values = list(value)
        except TypeError as exc:
            raise RetentionContractError(f"{label} must be an iterable of statuses") from exc
    normalized: set[str] = set()
    for status in values:
        if not isinstance(status, str) or not _STATUS_RE.fullmatch(status.strip().lower()):
            raise RetentionContractError(f"{label} contains an invalid status")
        normalized.add(status.strip().lower())
    return frozenset(normalized)


def _timestamp(value: Any, label: str) -> datetime_module.datetime:
    if isinstance(value, datetime_module.datetime):
        moment = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            moment = datetime_module.datetime.fromtimestamp(float(value), tz=datetime_module.timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise RetentionContractError(f"{label} is not a valid timestamp") from exc
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith(("Z", "z")):
            raw = raw[:-1] + "+00:00"
        try:
            moment = datetime_module.datetime.fromisoformat(raw)
        except ValueError as exc:
            raise RetentionContractError(f"{label} is not a valid ISO-8601 timestamp") from exc
    else:
        raise RetentionContractError(f"{label} is not a valid timestamp")
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=datetime_module.timezone.utc)
    return moment.astimezone(datetime_module.timezone.utc)


def _utc_text(moment: datetime_module.datetime) -> str:
    normalized = moment.astimezone(datetime_module.timezone.utc)
    if normalized.microsecond:
        return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_digest(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise _TaskReadError("malformed_state", "Task state is not canonical JSON") from exc
    return hashlib.sha256(encoded).hexdigest()


def _is_contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _lstat(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise UnsafeRetentionPath(f"Unable to inspect retention path: {path.name}") from exc


def _assert_existing_chain(path: Path, project_root: Path, label: str) -> None:
    """Reject symlinks in every existing component, even when they stay inside."""
    if not _is_contained(path, project_root):
        raise UnsafeRetentionPath(f"{label} escapes the project root")
    current = project_root
    for part in path.relative_to(project_root).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise UnsafeRetentionPath(f"Unable to inspect {label}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise UnsafeRetentionPath(f"{label} must not contain symlink components")
        if not stat.S_ISDIR(metadata.st_mode):
            raise UnsafeRetentionPath(f"{label} must be a directory")


def _ensure_directory(path: Path, project_root: Path, label: str) -> None:
    _assert_existing_chain(path, project_root, label)
    current = project_root
    for part in path.relative_to(project_root).parts:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise UnsafeRetentionPath(f"Unable to create {label}") from exc
        metadata = _lstat(current)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise UnsafeRetentionPath(f"{label} must be a real directory")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise UnsafeRetentionPath(f"Unable to resolve {label}") from exc
    if not _is_contained(resolved, project_root):
        raise UnsafeRetentionPath(f"{label} escapes the project root")


def _open_secure_directory(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise _TaskReadError("unsafe_path", f"Unable to open directory safely: {path.name}") from exc
    try:
        descriptor_stat = os.fstat(descriptor)
        path_stat = path.lstat()
        if (
            not stat.S_ISDIR(descriptor_stat.st_mode)
            or stat.S_ISLNK(path_stat.st_mode)
            or descriptor_stat.st_dev != path_stat.st_dev
            or descriptor_stat.st_ino != path_stat.st_ino
        ):
            raise _TaskReadError("unsafe_path", "Directory identity changed during inspection")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _read_regular_at(directory_fd: int, name: str, max_bytes: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_fd)
    except OSError as exc:
        raise _TaskReadError("unsafe_path", f"Unable to read {name} safely") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise _TaskReadError("unsafe_path", f"{name} must be a regular file")
        if metadata.st_size > max_bytes:
            raise _TaskReadError("state_too_large", f"{name} exceeds the configured size limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, max_bytes - total + 1))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise _TaskReadError("state_too_large", f"{name} exceeds the configured size limit")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _json_at(directory_fd: int, name: str, max_bytes: int) -> dict[str, Any]:
    payload = _read_regular_at(directory_fd, name, max_bytes)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _TaskReadError("malformed_state", f"{name} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise _TaskReadError("malformed_state", f"{name} must contain an object")
    return value


def _validate_task_state(state: Mapping[str, Any], task_id: str) -> None:
    required = {
        "schema_version",
        "task_id",
        "status",
        "revision",
        "contract",
        "verification",
        "events",
        "updated_at",
    }
    missing = sorted(required - set(state))
    if missing:
        raise _TaskReadError(
            "malformed_state",
            f"Task state is missing required fields: {', '.join(missing)}",
        )
    if state.get("schema_version") != "2.5":
        raise _TaskReadError("unsupported_schema", "Task state schema is unsupported")
    if state.get("task_id") != task_id:
        raise _TaskReadError("identity_mismatch", "Task state identity does not match its directory")
    if not isinstance(state.get("status"), str) or not state["status"].strip():
        raise _TaskReadError("malformed_state", "Task state status must be a non-empty string")
    if (
        isinstance(state.get("revision"), bool)
        or not isinstance(state.get("revision"), int)
        or state["revision"] < 0
    ):
        raise _TaskReadError("malformed_state", "Task state revision must be a non-negative integer")
    if not isinstance(state.get("contract"), dict) or not isinstance(state.get("verification"), dict):
        raise _TaskReadError("malformed_state", "Task contract and verification must be objects")
    if not isinstance(state.get("events"), list):
        raise _TaskReadError("malformed_state", "Task state events must be an array")
    if "in_progress" in state and not isinstance(state.get("in_progress"), list):
        raise _TaskReadError("malformed_state", "Task in_progress must be an array")
    if "pending" in state["verification"] and not isinstance(
        state["verification"].get("pending"), list
    ):
        raise _TaskReadError("malformed_state", "Task verification pending must be an array")
    try:
        _timestamp(state.get("updated_at"), "state.updated_at")
    except RetentionContractError as exc:
        raise _TaskReadError("invalid_updated_at", str(exc)) from exc
    operation_ids = state.get("operation_ids", [])
    if not isinstance(operation_ids, list) or any(
        not isinstance(item, str) or not _IDENTIFIER_RE.fullmatch(item)
        for item in operation_ids
    ):
        raise _TaskReadError("malformed_state", "Task operation_ids are malformed")
    if len(operation_ids) != len(set(operation_ids)):
        raise _TaskReadError("malformed_state", "Task operation_ids must be unique")


def _snapshot_task(
    task_path: Path,
    task_id: str,
    policy: RetentionPolicy,
) -> _TaskSnapshot:
    task_fd = _open_secure_directory(task_path)
    try:
        task_stat = os.fstat(task_fd)
        identity = (task_stat.st_dev, task_stat.st_ino)
        state = _json_at(task_fd, "state.json", policy.max_state_bytes)
        _validate_task_state(state, task_id)
        state_digest = _canonical_digest(state)

        operation_flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            operations_fd = os.open("operations", operation_flags, dir_fd=task_fd)
        except FileNotFoundError:
            operations_fd = None
        except OSError as exc:
            raise _TaskReadError("unsafe_path", "Unable to inspect operations safely") from exc

        operation_records: list[dict[str, Any]] = []
        try:
            if operations_fd is not None:
                try:
                    names = sorted(os.listdir(operations_fd))
                except OSError as exc:
                    raise _TaskReadError("malformed_state", "Unable to list operation records") from exc
                operation_names = [name for name in names if name.endswith(".json")]
                if len(operation_names) > policy.max_operation_files:
                    raise _TaskReadError("too_many_operations", "Task has too many operation records")
                for name in operation_names:
                    operation = _json_at(operations_fd, name, policy.max_state_bytes)
                    operation_id = name[:-5]
                    if (
                        not _IDENTIFIER_RE.fullmatch(operation_id)
                        or operation.get("operation_id") != operation_id
                        or operation.get("task_id") != task_id
                        or not isinstance(operation.get("status"), str)
                        or not operation.get("status")
                    ):
                        raise _TaskReadError("malformed_operation", "An operation record is malformed")
                    operation_records.append(
                        {
                            "name": name,
                            "digest": _canonical_digest(operation),
                            "status": operation["status"],
                        }
                    )
        finally:
            if operations_fd is not None:
                os.close(operations_fd)

        declared_ids = set(state.get("operation_ids", []))
        present_ids = {record["name"][:-5] for record in operation_records}
        if declared_ids != present_ids:
            raise _TaskReadError(
                "incomplete_operation_state",
                "Task operation records do not match state.json",
            )

        uncertain_reasons: list[str] = []
        if state.get("uncertain") is True:
            uncertain_reasons.append("state_uncertain")
        verification = state["verification"]
        if isinstance(verification.get("pending"), list) and verification["pending"]:
            uncertain_reasons.append("verification_pending")
        if isinstance(state.get("in_progress"), list) and state["in_progress"]:
            uncertain_reasons.append("work_in_progress")
        if policy.protect_uncertain_operations:
            uncertain_reasons.extend(
                f"operation_{record['status']}"
                for record in operation_records
                if record["status"] in UNCERTAIN_OPERATION_STATUSES
            )

        snapshot_value = {
            "state_digest": state_digest,
            "operations": sorted(operation_records, key=lambda item: item["name"]),
        }
        snapshot_digest = _canonical_digest(snapshot_value)
        return _TaskSnapshot(
            task_id=task_id,
            path=task_path,
            identity=identity,
            state=dict(state),
            state_digest=state_digest,
            snapshot_digest=snapshot_digest,
            uncertain_reasons=tuple(dict.fromkeys(uncertain_reasons)),
        )
    finally:
        os.close(task_fd)


def _process_lock(path: Path) -> threading.RLock:
    key = str(path)
    with _PROCESS_LOCKS_GUARD:
        return _PROCESS_LOCKS.setdefault(key, threading.RLock())


@contextlib.contextmanager
def _cleanup_lock(
    tasks_root: Path,
    project_root: Path,
    timeout_seconds: float,
) -> Iterator[None]:
    if not tasks_root.exists():
        yield
        return
    _assert_existing_chain(tasks_root, project_root, "Task storage")
    initial = _lstat(tasks_root)
    if stat.S_ISLNK(initial.st_mode) or not stat.S_ISDIR(initial.st_mode):
        raise UnsafeRetentionPath("Task storage must be a real directory")
    with _process_lock(tasks_root):
        current = _lstat(tasks_root)
        if (current.st_dev, current.st_ino) != (initial.st_dev, initial.st_ino):
            raise UnsafeRetentionPath("Task storage changed before lock acquisition")
        if fcntl is not None:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(tasks_root, flags)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                try:
                    locked = os.fstat(descriptor)
                    if (locked.st_dev, locked.st_ino) != (initial.st_dev, initial.st_ino):
                        raise UnsafeRetentionPath("Task storage changed while acquiring lock")
                    yield
                finally:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
            return

        lock_path = tasks_root / ".retention.lock.exclusive"  # pragma: no cover
        deadline = datetime_module.datetime.now().timestamp() + timeout_seconds  # pragma: no cover
        descriptor = None  # pragma: no cover
        while descriptor is None:  # pragma: no cover
            try:
                descriptor = os.open(
                    lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                )
            except FileExistsError:
                try:
                    if datetime_module.datetime.now().timestamp() - lock_path.stat().st_mtime > 30:
                        lock_path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if datetime_module.datetime.now().timestamp() >= deadline:
                    raise TimeoutError("Timed out acquiring task-retention lock")
                threading.Event().wait(0.01)
        try:  # pragma: no cover
            yield
        finally:  # pragma: no cover
            os.close(descriptor)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


@contextlib.contextmanager
def _task_lock(task_path: Path) -> Iterator[int]:
    task_fd = _open_secure_directory(task_path)
    lock_fd = None
    try:
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            lock_fd = os.open(".lock", flags, 0o600, dir_fd=task_fd)
        except OSError as exc:
            raise _TaskReadError("unsafe_path", "Task lock path is unsafe") from exc
        if fcntl is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            yield task_fd
        finally:
            if fcntl is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        os.close(task_fd)


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _write_json_atomic(path: Path, value: Mapping[str, Any], project_root: Path) -> None:
    _assert_existing_chain(path.parent, project_root, "Retention report path")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-retention-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.name


def _archive_record_name(task_id: str, moment: datetime_module.datetime) -> str:
    timestamp = moment.astimezone(datetime_module.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{task_id}-{timestamp}-{uuid.uuid4().hex[:12]}"


def _confirmation_path(project_root: Path, token: str) -> Path:
    if not isinstance(token, str) or not re.fullmatch(r"retention-delete-[A-Za-z0-9_-]{20,}", token):
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid")
    root = project_root / REPORTS_RELATIVE / "confirmations"
    _assert_existing_chain(root, project_root, "Retention confirmation storage")
    return root / f"{token}.json"


def _issue_confirmation(
    project_key: str,
    plan_digest: str,
    project_root: Path,
    now: datetime_module.datetime,
) -> str:
    token = f"retention-delete-{secrets.token_urlsafe(32)}"
    expires_at = now + datetime_module.timedelta(seconds=DEFAULT_CONFIRMATION_TTL_SECONDS)
    record = {
        "schema_version": SCHEMA_VERSION,
        "project_key": project_key,
        "plan_digest": plan_digest,
        "issued_at": _utc_text(now),
        "expires_at": _utc_text(expires_at),
        "consumed_at": None,
    }
    path = _confirmation_path(project_root, token)
    _ensure_directory(path.parent, project_root, "Retention confirmation storage")
    _write_json_atomic(path, record, project_root)
    with _CONFIRMATION_LOCK:
        _ISSUED_CONFIRMATIONS[(project_key, token)] = plan_digest
        while len(_ISSUED_CONFIRMATIONS) > _MAX_REMEMBERED_CONFIRMATIONS:
            _ISSUED_CONFIRMATIONS.pop(next(iter(_ISSUED_CONFIRMATIONS)))
    return token


def _verify_confirmation(
    project_key: str,
    token: Any,
    plan_digest: str,
    project_root: Path,
    now: datetime_module.datetime,
) -> None:
    if not isinstance(token, str) or not token:
        raise ConfirmationRequired(
            "Destructive task deletion requires a token from cleanup(dry_run=True, delete=True)"
        )
    path = _confirmation_path(project_root, token)
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ConfirmationRequired("The destructive cleanup confirmation token is invalid")
        record = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid") from exc
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid") from exc
    if not isinstance(record, Mapping):
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid")
    if record.get("project_key") != project_key or not isinstance(record.get("plan_digest"), str):
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid")
    if not secrets.compare_digest(str(record["plan_digest"]), plan_digest):
        raise RetentionPlanChanged("Task state changed after confirmation; run dry-run again")
    if record.get("consumed_at") is not None:
        raise ConfirmationRequired("The destructive cleanup confirmation token was already consumed")
    try:
        expires_at = _timestamp(record.get("expires_at"), "confirmation expiry")
    except RetentionContractError as exc:
        raise ConfirmationRequired("The destructive cleanup confirmation token is invalid") from exc
    if expires_at <= now:
        raise ConfirmationRequired("The destructive cleanup confirmation token has expired")
    consumed = dict(record)
    consumed["consumed_at"] = _utc_text(now)
    _write_json_atomic(path, consumed, project_root)
    with _CONFIRMATION_LOCK:
        _ISSUED_CONFIRMATIONS.pop((project_key, token), None)



class TaskRetentionManager:
    """Retention service for one project's durable Runtime task store."""

    def __init__(
        self,
        project_root: str | os.PathLike[str],
        policy: RetentionPolicy | None = None,
        *,
        max_age: datetime_module.timedelta | float | str | None = None,
        retention: datetime_module.timedelta | float | str | None = None,
        retention_days: float | None = None,
        retention_seconds: float | None = None,
        eligible_statuses: Iterable[str] | None = None,
        preserve_statuses: Iterable[str] | None = None,
        protect_uncertain_operations: bool | None = None,
        max_state_bytes: int | None = None,
        max_operation_files: int | None = None,
        clock: Callable[[], Any] | None = None,
        persist_reports: bool = True,
        lock_timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        root = Path(project_root).expanduser()
        try:
            resolved_root = root.resolve(strict=True)
        except OSError as exc:
            raise RetentionContractError("project_root must be an existing directory") from exc
        if not resolved_root.is_dir():
            raise RetentionContractError("project_root must be an existing directory")
        if isinstance(lock_timeout_seconds, bool) or not isinstance(lock_timeout_seconds, (int, float)):
            raise RetentionContractError("lock_timeout_seconds must be a number")
        if not math.isfinite(float(lock_timeout_seconds)) or lock_timeout_seconds < 0:
            raise RetentionContractError("lock_timeout_seconds must be non-negative")
        if not isinstance(persist_reports, bool):
            raise RetentionContractError("persist_reports must be boolean")
        if clock is not None and not callable(clock):
            raise RetentionContractError("clock must be callable")

        self.project_root = resolved_root
        self.tasks_root = self.project_root / TASKS_RELATIVE
        self.archive_root = self.project_root / ARCHIVES_RELATIVE
        self.report_root = self.project_root / REPORTS_RELATIVE
        self.policy = self._build_policy(
            policy,
            max_age=max_age,
            retention=retention,
            retention_days=retention_days,
            retention_seconds=retention_seconds,
            eligible_statuses=eligible_statuses,
            preserve_statuses=preserve_statuses,
            protect_uncertain_operations=protect_uncertain_operations,
            max_state_bytes=max_state_bytes,
            max_operation_files=max_operation_files,
        )
        self.clock = clock or (lambda: datetime_module.datetime.now(datetime_module.timezone.utc))
        self.persist_reports = persist_reports
        self.lock_timeout_seconds = float(lock_timeout_seconds)
        self._validate_storage_paths()

    @staticmethod
    def _build_policy(
        policy: RetentionPolicy | None,
        *,
        max_age: Any,
        retention: Any,
        retention_days: Any,
        retention_seconds: Any,
        eligible_statuses: Any,
        preserve_statuses: Any,
        protect_uncertain_operations: Any,
        max_state_bytes: Any,
        max_operation_files: Any,
    ) -> RetentionPolicy:
        if policy is not None and not isinstance(policy, RetentionPolicy):
            raise RetentionContractError("policy must be a RetentionPolicy")
        base = policy or RetentionPolicy()
        age_values = [value for value in (max_age, retention, retention_days, retention_seconds) if value is not None]
        if len(age_values) > 1:
            raise RetentionContractError(
                "specify only one of max_age, retention, retention_days, or retention_seconds"
            )
        overrides: dict[str, Any] = {}
        if max_age is not None:
            overrides["max_age"] = max_age
        elif retention is not None:
            overrides["max_age"] = retention
        elif retention_days is not None:
            days = _duration_seconds(retention_days, "retention_days")
            assert days is not None
            overrides["max_age"] = datetime_module.timedelta(seconds=days * 86400.0)
        elif retention_seconds is not None:
            overrides["max_age"] = retention_seconds
        if eligible_statuses is not None:
            overrides["eligible_statuses"] = eligible_statuses
        if preserve_statuses is not None:
            overrides["preserve_statuses"] = preserve_statuses
        if protect_uncertain_operations is not None:
            overrides["protect_uncertain_operations"] = protect_uncertain_operations
        if max_state_bytes is not None:
            overrides["max_state_bytes"] = max_state_bytes
        if max_operation_files is not None:
            overrides["max_operation_files"] = max_operation_files
        return replace(base, **overrides) if overrides else base

    def _validate_storage_paths(self) -> None:
        _assert_existing_chain(self.tasks_root, self.project_root, "Task storage")
        _assert_existing_chain(self.archive_root, self.project_root, "Task archive storage")
        _assert_existing_chain(self.report_root, self.project_root, "Retention report storage")

    def _now(self) -> datetime_module.datetime:
        try:
            return _timestamp(self.clock(), "clock value")
        except RetentionContractError:
            raise
        except Exception as exc:
            raise RetentionContractError("clock returned an invalid value") from exc

    def _report(
        self,
        *,
        now: datetime_module.datetime,
        dry_run: bool,
        delete: bool,
        policy: RetentionPolicy,
        entries: Iterable[TaskDisposition],
        plan_digest: str,
        token: str | None = None,
        confirmation_required: bool = False,
        confirmation_verified: bool = False,
    ) -> CleanupReport:
        return CleanupReport(
            generated_at=_utc_text(now),
            dry_run=dry_run,
            mode="delete" if delete else "archive",
            storage_root=TASKS_RELATIVE.as_posix(),
            policy=policy,
            entries=entries,
            plan_digest=plan_digest,
            confirmation_token=token,
            confirmation_required=confirmation_required,
            confirmation_verified=confirmation_verified,
        )

    def _empty_report(
        self,
        now: datetime_module.datetime,
        *,
        dry_run: bool,
        delete: bool,
        policy: RetentionPolicy,
    ) -> CleanupReport:
        plan_digest = _canonical_digest({"policy": policy.to_dict(), "tasks": []})
        return self._report(
            now=now,
            dry_run=dry_run,
            delete=delete,
            policy=policy,
            entries=(),
            plan_digest=plan_digest,
        )

    def _disposition(
        self,
        snapshot: _TaskSnapshot,
        now: datetime_module.datetime,
        policy: RetentionPolicy,
    ) -> TaskDisposition:
        state = snapshot.state
        status = state["status"].strip().lower()
        base = {
            "task_id": snapshot.task_id,
            "status": state["status"],
            "revision": state["revision"],
            "source_path": _display_path(snapshot.path, self.project_root),
        }
        if status in policy.preserve_statuses:
            return TaskDisposition(action="preserved", reason="status_preserved", **base)
        if status not in policy.eligible_statuses:
            return TaskDisposition(action="preserved", reason="status_not_eligible", **base)
        if snapshot.uncertain_reasons:
            return TaskDisposition(
                action="preserved",
                reason="uncertain_task",
                error="uncertainty: " + ", ".join(snapshot.uncertain_reasons),
                **base,
            )
        age_seconds: float | None = None
        if policy.max_age_seconds is not None:
            try:
                updated_at = _timestamp(state.get("updated_at"), "state.updated_at")
            except RetentionContractError as exc:
                return TaskDisposition(
                    action="preserved",
                    reason="invalid_updated_at",
                    error=str(exc),
                    **base,
                )
            if updated_at > now:
                return TaskDisposition(
                    action="preserved",
                    reason="future_updated_at",
                    error="Task updated_at is in the future",
                    **base,
                )
            age_seconds = max(0.0, (now - updated_at).total_seconds())
            if age_seconds < policy.max_age_seconds:
                return TaskDisposition(
                    action="preserved",
                    reason="within_retention",
                    age_seconds=age_seconds,
                    **base,
                )
        return TaskDisposition(
            action="preserved",
            reason="eligible",
            eligible=True,
            age_seconds=age_seconds,
            **base,
        )

    def _error_disposition(
        self,
        task_name: str,
        task_path: Path,
        code: str,
        message: str,
    ) -> TaskDisposition:
        return TaskDisposition(
            task_id=task_name[:128],
            action="preserved",
            reason=code,
            source_path=_display_path(task_path, self.project_root),
            error=message,
        )

    def _scan(
        self,
        now: datetime_module.datetime,
        *,
        policy: RetentionPolicy,
        delete: bool,
    ) -> tuple[list[TaskDisposition], dict[str, _TaskSnapshot], str]:
        entries: list[TaskDisposition] = []
        selected: dict[str, _TaskSnapshot] = {}
        try:
            names = sorted(os.listdir(self.tasks_root))
        except OSError as exc:
            raise UnsafeRetentionPath("Unable to list task storage") from exc

        for name in names:
            if name in _FALLBACK_LOCK_NAMES:
                continue
            task_path = self.tasks_root / name
            if not _IDENTIFIER_RE.fullmatch(name):
                entries.append(
                    self._error_disposition(
                        name,
                        task_path,
                        "invalid_task_id",
                        "Task directory name is not a valid identifier",
                    )
                )
                continue
            try:
                metadata = task_path.lstat()
            except OSError:
                entries.append(
                    self._error_disposition(
                        name,
                        task_path,
                        "unreadable_task",
                        "Unable to inspect task directory",
                    )
                )
                continue
            if stat.S_ISLNK(metadata.st_mode):
                entries.append(
                    self._error_disposition(
                        name,
                        task_path,
                        "symlink_escape",
                        "Task storage symlinks are never followed or removed",
                    )
                )
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                entries.append(
                    self._error_disposition(
                        name,
                        task_path,
                        "not_task_directory",
                        "Task entry is not a directory",
                    )
                )
                continue
            try:
                snapshot = _snapshot_task(task_path, name, policy)
            except _TaskReadError as exc:
                entries.append(
                    self._error_disposition(name, task_path, exc.code, str(exc))
                )
                continue
            disposition = self._disposition(snapshot, now, policy)
            if disposition.eligible:
                selected[name] = snapshot
                disposition = replace(
                    disposition,
                    action="would_delete" if delete else "would_archive",
                )
            entries.append(disposition)

        plan_digest = _canonical_digest(
            {
                "policy": policy.to_dict(),
                "tasks": [
                    {"task_id": task_id, "snapshot_digest": selected[task_id].snapshot_digest}
                    for task_id in sorted(selected)
                ],
            }
        )
        return entries, selected, plan_digest

    def cleanup(
        self,
        *,
        policy: RetentionPolicy | None = None,
        dry_run: bool = False,
        delete: bool = False,
        confirmation_token: str | None = None,
        persist_report: bool | None = None,
    ) -> CleanupReport:
        """Plan or execute contained task archival and optional deletion.

        ``delete=False`` archives eligible tasks and retains them.  ``delete=True``
        archives and then deletes them, but only after a token issued by an exact
        matching dry-run is supplied.  A no-op replay after successful deletion
        remains idempotent even though its old token has already been consumed.
        """
        if policy is not None and not isinstance(policy, RetentionPolicy):
            raise RetentionContractError("policy must be a RetentionPolicy")
        if not isinstance(dry_run, bool) or not isinstance(delete, bool):
            raise RetentionContractError("dry_run and delete must be boolean")
        if persist_report is not None and not isinstance(persist_report, bool):
            raise RetentionContractError("persist_report must be boolean")
        if delete is False and confirmation_token is not None:
            raise RetentionContractError(
                "confirmation_token is only valid for destructive delete=True cleanup"
            )

        effective_policy = policy or self.policy
        self._validate_storage_paths()
        now = self._now()
        should_persist = self.persist_reports if persist_report is None else persist_report
        if not self.tasks_root.exists():
            return self._empty_report(
                now,
                dry_run=dry_run,
                delete=delete,
                policy=effective_policy,
            )

        project_key = str(self.tasks_root)
        with _cleanup_lock(
            self.tasks_root,
            self.project_root,
            self.lock_timeout_seconds,
        ):
            entries, selected, plan_digest = self._scan(
                now,
                policy=effective_policy,
                delete=delete,
            )
            if not selected:
                report = self._report(
                    now=now,
                    dry_run=dry_run,
                    delete=delete,
                    policy=effective_policy,
                    entries=entries,
                    plan_digest=plan_digest,
                )
                return self._maybe_persist_report(report, now, enabled=should_persist)

            if dry_run:
                token = (
                    _issue_confirmation(
                        project_key,
                        plan_digest,
                        self.project_root,
                        now,
                    ) if delete else None
                )
                return self._report(
                    now=now,
                    dry_run=True,
                    delete=delete,
                    policy=effective_policy,
                    entries=entries,
                    plan_digest=plan_digest,
                    token=token,
                    confirmation_required=delete,
                )

            confirmation_required = bool(delete)
            confirmation_verified = False
            if delete:
                _verify_confirmation(
                    project_key,
                    confirmation_token,
                    plan_digest,
                    self.project_root,
                    now,
                )
                confirmation_verified = True

            if should_persist:
                _ensure_directory(self.report_root, self.project_root, "Retention report storage")

            updated_entries: list[TaskDisposition] = []
            for entry in entries:
                snapshot = selected.get(entry.task_id)
                if snapshot is None:
                    updated_entries.append(entry)
                    continue
                try:
                    updated_entries.append(
                        self._archive_task(
                            snapshot,
                            entry,
                            now=now,
                            delete=delete,
                            plan_digest=plan_digest,
                            policy=effective_policy,
                        )
                    )
                except (OSError, RetentionError, _TaskReadError) as exc:
                    updated_entries.append(
                        replace(
                            entry,
                            action="preserved",
                            reason=(
                                "concurrent_state_change"
                                if isinstance(exc, RetentionPlanChanged)
                                else "archive_failed"
                            ),
                            eligible=False,
                            error=str(exc),
                        )
                    )

            report = self._report(
                now=now,
                dry_run=False,
                delete=delete,
                policy=effective_policy,
                entries=updated_entries,
                plan_digest=plan_digest,
                confirmation_required=confirmation_required,
                confirmation_verified=confirmation_verified,
            )
            return self._maybe_persist_report(report, now, enabled=should_persist)

    def _maybe_persist_report(
        self,
        report: CleanupReport,
        now: datetime_module.datetime,
        *,
        enabled: bool,
    ) -> CleanupReport:
        if report.dry_run or not enabled or not (report.selected_count or report.error_count):
            return report
        try:
            report_path = self._persist_report(report, now)
            return report.with_report_path(report_path)
        except (OSError, RetentionError) as exc:
            return CleanupReport(
                generated_at=report.generated_at,
                dry_run=report.dry_run,
                mode=report.mode,
                storage_root=report.storage_root,
                policy=report.policy,
                entries=report.entries
                + (
                    TaskDisposition(
                        task_id="<retention-report>",
                        action="preserved",
                        reason="report_write_failed",
                        error=str(exc),
                    ),
                ),
                plan_digest=report.plan_digest,
                confirmation_token=report.confirmation_token,
                confirmation_required=report.confirmation_required,
                confirmation_verified=report.confirmation_verified,
                report_path=report.report_path,
            )

    def _persist_report(
        self,
        report: CleanupReport,
        now: datetime_module.datetime,
    ) -> str:
        _ensure_directory(self.report_root, self.project_root, "Retention report storage")
        timestamp = now.astimezone(datetime_module.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.report_root / f"cleanup-{timestamp}-{uuid.uuid4().hex[:12]}.json"
        _write_json_atomic(
            path,
            report.to_dict(include_confirmation_token=False),
            self.project_root,
        )
        return _display_path(path, self.project_root)

    def _archive_task(
        self,
        snapshot: _TaskSnapshot,
        planned: TaskDisposition,
        *,
        now: datetime_module.datetime,
        delete: bool,
        plan_digest: str,
        policy: RetentionPolicy,
    ) -> TaskDisposition:
        with _task_lock(snapshot.path):
            current = _snapshot_task(snapshot.path, snapshot.task_id, policy)
            if current.snapshot_digest != snapshot.snapshot_digest:
                raise RetentionPlanChanged(
                    f"Task {snapshot.task_id!r} changed while cleanup was running"
                )
            current_disposition = self._disposition(current, now, policy)
            if not current_disposition.eligible:
                return replace(
                    planned,
                    action="preserved",
                    reason="concurrent_state_change",
                    eligible=False,
                )

            _assert_existing_chain(self.tasks_root, self.project_root, "Task storage")
            _ensure_directory(self.archive_root, self.project_root, "Task archive storage")
            record_id = _archive_record_name(snapshot.task_id, now)
            record_path = self.archive_root / record_id
            archived_path = record_path / "task"
            archive_display = _display_path(archived_path, self.project_root)
            record_fd: int | None = None
            task_moved = False
            try:
                try:
                    record_path.mkdir(mode=0o700)
                except FileExistsError as exc:  # UUID collision is not expected.
                    raise RetentionError("Archive record collision") from exc
                record_metadata = _lstat(record_path)
                if stat.S_ISLNK(record_metadata.st_mode) or not stat.S_ISDIR(record_metadata.st_mode):
                    raise UnsafeRetentionPath("Archive record path is not a real directory")
                record_fd = os.open(
                    record_path,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
                if archived_path.exists() or archived_path.is_symlink():
                    raise UnsafeRetentionPath("Archive destination already exists")
                # The task directory identity was checked while holding both the
                # global cleanup lock and the TaskStore-compatible task lock.
                os.rename(snapshot.path, archived_path)
                task_moved = True
                archived_metadata = archived_path.lstat()
                if (
                    stat.S_ISLNK(archived_metadata.st_mode)
                    or not stat.S_ISDIR(archived_metadata.st_mode)
                    or (archived_metadata.st_dev, archived_metadata.st_ino) != current.identity
                ):
                    raise UnsafeRetentionPath("Archived task identity could not be verified")
                manifest = {
                    "schema_version": SCHEMA_VERSION,
                    "task_id": snapshot.task_id,
                    "source_path": planned.source_path,
                    "archive_path": archive_display,
                    "archived_at": _utc_text(now),
                    "state_digest": snapshot.state_digest,
                    "snapshot_digest": snapshot.snapshot_digest,
                    "plan_digest": plan_digest,
                    "delete_requested": bool(delete),
                }
                _write_json_atomic(
                    record_path / "retention.json",
                    manifest,
                    self.project_root,
                )
                _fsync_directory(record_path)
                _fsync_directory(self.tasks_root)
            except Exception as exc:
                if not task_moved:
                    with contextlib.suppress(OSError):
                        record_path.rmdir()
                    raise
                # A partially moved task is intentionally left in the archive.
                # It is never removed without the already-validated confirmation.
                return replace(
                    planned,
                    action="preserved",
                    reason="archive_incomplete",
                    eligible=False,
                    archive_path=archive_display,
                    archived=archived_path.exists() and not archived_path.is_symlink(),
                    error=f"archive incomplete: {exc}",
                )
            finally:
                if record_fd is not None:
                    os.close(record_fd)

            if not delete:
                return replace(
                    planned,
                    action="archived",
                    reason="retention_eligible",
                    archive_path=archive_display,
                    archived=True,
                )

            _assert_existing_chain(record_path, self.project_root, "Archive record")
            record_metadata = record_path.lstat()
            if stat.S_ISLNK(record_metadata.st_mode) or not stat.S_ISDIR(record_metadata.st_mode):
                raise UnsafeRetentionPath("Refusing to delete an unsafe archive record")
            try:
                resolved_record = record_path.resolve(strict=True)
                resolved_archive_root = self.archive_root.resolve(strict=True)
            except OSError as exc:
                raise UnsafeRetentionPath("Unable to resolve archive record") from exc
            if not _is_contained(resolved_record, self.project_root):
                raise UnsafeRetentionPath("Archive record escapes the project root")
            if not _is_contained(resolved_record, resolved_archive_root):
                raise UnsafeRetentionPath("Archive record escapes task archive storage")
            try:
                shutil.rmtree(record_path)
            except OSError as exc:
                return replace(
                    planned,
                    action="preserved",
                    reason="archive_deletion_failed",
                    eligible=False,
                    archive_path=archive_display,
                    archived=True,
                    error=f"archived copy retained after deletion failure: {exc}",
                )
            if record_path.exists() or record_path.is_symlink():
                return replace(
                    planned,
                    action="preserved",
                    reason="archive_deletion_incomplete",
                    eligible=False,
                    archive_path=archive_display,
                    archived=True,
                    error="Archived task deletion did not complete",
                )
            return replace(
                planned,
                action="deleted",
                reason="retention_eligible",
                archive_path=archive_display,
                archived=True,
                deleted=True,
            )

    def _resolve_archive_task_path(self, archive_path: str | os.PathLike[str]) -> tuple[Path, Path]:
        candidate = Path(archive_path)
        if not candidate.is_absolute():
            candidate = self.project_root / candidate
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            if candidate.name == "task":
                record_candidate = candidate.parent
                try:
                    resolved = record_candidate.resolve(strict=True)
                except OSError as exc:
                    raise UnsafeRetentionPath("Archive path does not exist") from exc
            else:
                raise UnsafeRetentionPath("Archive path does not exist")
        except OSError as exc:
            raise UnsafeRetentionPath("Archive path does not exist") from exc
        archive_root = self.archive_root.resolve(strict=True)
        if not _is_contained(resolved, archive_root):
            raise UnsafeRetentionPath("Archive path escapes task archive storage")
        if resolved.name == "task":
            record = resolved.parent
            task_path = resolved
        else:
            record = resolved
            task_path = resolved / "task"
        _assert_existing_chain(record, self.project_root, "Archive record")
        _assert_existing_chain(task_path, self.project_root, "Archived task")
        if task_path.exists() and (not task_path.is_dir() or task_path.is_symlink()):
            raise UnsafeRetentionPath("Archived task is not a real directory")
        return record, task_path

    def _read_archive_manifest(self, record_path: Path) -> dict[str, Any]:
        manifest_path = record_path / "retention.json"
        _assert_existing_chain(record_path, self.project_root, "Archive record")
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise UnsafeRetentionPath("Archive manifest is missing or unsafe")
        try:
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise UnsafeRetentionPath("Archive manifest is invalid") from exc
        if not isinstance(value, dict):
            raise UnsafeRetentionPath("Archive manifest must be an object")
        if value.get("schema_version") != SCHEMA_VERSION:
            raise UnsafeRetentionPath("Unsupported archive manifest schema")
        task_id = value.get("task_id")
        if not isinstance(task_id, str) or not _IDENTIFIER_RE.fullmatch(task_id):
            raise UnsafeRetentionPath("Archive manifest task_id is invalid")
        for key in ("state_digest", "snapshot_digest"):
            if not isinstance(value.get(key), str) or not re.fullmatch(r"[a-f0-9]{64}", value[key]):
                raise UnsafeRetentionPath(f"Archive manifest {key} is invalid")
        return value

    def restore(
        self,
        archive_path: str | os.PathLike[str],
        *,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Restore a validated archive without overwriting an existing task."""
        if task_id is not None:
            if not isinstance(task_id, str) or not _IDENTIFIER_RE.fullmatch(task_id):
                raise RetentionContractError("task_id is invalid")
        self._validate_storage_paths()
        record_path, archived_task = self._resolve_archive_task_path(archive_path)
        manifest = self._read_archive_manifest(record_path)
        archived_id = str(manifest["task_id"])
        if task_id is not None and task_id != archived_id:
            raise RetentionContractError("Archive task_id does not match the requested task")
        destination = self.tasks_root / archived_id
        _assert_existing_chain(destination, self.project_root, "Restore destination")
        if not archived_task.exists() or archived_task.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                try:
                    existing = _snapshot_task(destination, archived_id, self.policy)
                except _TaskReadError:
                    existing = None
                if existing and existing.snapshot_digest == manifest["snapshot_digest"]:
                    return {
                        "success": True,
                        "task_id": archived_id,
                        "status": "already_restored",
                        "task_path": _display_path(destination, self.project_root),
                    }
            raise UnsafeRetentionPath("Archived task is missing and destination is not a matching restore")
        snapshot = _snapshot_task(archived_task, archived_id, self.policy)
        if snapshot.state_digest != manifest["state_digest"] or snapshot.snapshot_digest != manifest["snapshot_digest"]:
            raise UnsafeRetentionPath("Archived task digest does not match its manifest")
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                try:
                    existing = _snapshot_task(destination, archived_id, self.policy)
                except _TaskReadError:
                    existing = None
                if existing and existing.snapshot_digest == snapshot.snapshot_digest:
                    return {
                        "success": True,
                        "task_id": archived_id,
                        "status": "already_restored",
                        "task_path": _display_path(destination, self.project_root),
                    }
            raise RetentionContractError("Restore destination already exists")
        _ensure_directory(self.tasks_root, self.project_root, "Task storage")
        intent = {
            "schema_version": SCHEMA_VERSION,
            "task_id": archived_id,
            "archive_record": _display_path(record_path, self.project_root),
            "destination": _display_path(destination, self.project_root),
            "state_digest": snapshot.state_digest,
            "snapshot_digest": snapshot.snapshot_digest,
            "started_at": _utc_text(self._now()),
        }
        intent_path = record_path / "restore-intent.json"
        _write_json_atomic(intent_path, intent, self.project_root)
        os.rename(archived_task, destination)
        _fsync_directory(self.tasks_root)
        restored_manifest = dict(manifest)
        restored_manifest["restored_at"] = _utc_text(self._now())
        restored_manifest["restored_path"] = _display_path(destination, self.project_root)
        _write_json_atomic(record_path / "retention.json", restored_manifest, self.project_root)
        try:
            intent_path.unlink()
        except FileNotFoundError:
            pass
        return {
            "success": True,
            "task_id": archived_id,
            "status": "restored",
            "task_path": _display_path(destination, self.project_root),
        }

    def recover_archives(self) -> list[dict[str, Any]]:
        """Finalize or report archive moves interrupted after the rename."""
        self._validate_storage_paths()
        if not self.archive_root.exists():
            return []
        results: list[dict[str, Any]] = []
        for record_path in sorted(self.archive_root.iterdir()):
            if record_path.is_symlink() or not record_path.is_dir():
                continue
            intent_path = record_path / "restore-intent.json"
            if not intent_path.exists() or intent_path.is_symlink():
                continue
            try:
                intent = json.loads(intent_path.read_text(encoding="utf-8"))
                if not isinstance(intent, dict):
                    raise UnsafeRetentionPath("Restore intent is not an object")
                task_id = intent.get("task_id")
                if not isinstance(task_id, str) or not _IDENTIFIER_RE.fullmatch(task_id):
                    raise UnsafeRetentionPath("Restore intent task_id is invalid")
                destination = self.project_root / str(intent["destination"])
                _assert_existing_chain(destination, self.project_root, "Restore destination")
                if destination.exists() and not destination.is_symlink():
                    snapshot = _snapshot_task(destination, task_id, self.policy)
                    if snapshot.snapshot_digest != intent.get("snapshot_digest"):
                        raise UnsafeRetentionPath("Restore destination digest does not match intent")
                    manifest = self._read_archive_manifest(record_path)
                    manifest["restored_at"] = _utc_text(self._now())
                    manifest["restored_path"] = _display_path(destination, self.project_root)
                    _write_json_atomic(record_path / "retention.json", manifest, self.project_root)
                    intent_path.unlink()
                    results.append({"success": True, "task_id": task_id, "status": "recovered"})
                    continue
                archived_task = record_path / "task"
                if archived_task.exists() and not archived_task.is_symlink():
                    results.append({"success": False, "task_id": task_id, "status": "pending", "error": "archived task still exists"})
                else:
                    results.append({"success": False, "task_id": task_id, "status": "incomplete", "error": "restore destination is missing"})
            except (OSError, json.JSONDecodeError, TypeError, ValueError, RetentionError, _TaskReadError) as exc:
                results.append({"success": False, "task_id": "<unknown>", "status": "failed", "error": str(exc)})
        return results

    restore_task = restore

    def plan_cleanup(self, policy: RetentionPolicy | None = None) -> CleanupReport:
        """Return a deletion plan and process-local confirmation token."""
        return self.cleanup(policy=policy, dry_run=True, delete=True)

    def archive_tasks(self, policy: RetentionPolicy | None = None) -> CleanupReport:
        """Archive eligible tasks without deleting the archived copies."""
        return self.cleanup(policy=policy, delete=False)

    def delete_tasks(
        self,
        confirmation_token: str,
        policy: RetentionPolicy | None = None,
    ) -> CleanupReport:
        """Apply a previously planned destructive cleanup."""
        return self.cleanup(
            policy=policy,
            delete=True,
            confirmation_token=confirmation_token,
        )

    plan = plan_cleanup
    archive = archive_tasks
    delete = delete_tasks
    run_cleanup = cleanup


def cleanup_tasks(
    project_root: str | os.PathLike[str],
    *,
    policy: RetentionPolicy | None = None,
    **kwargs: Any,
) -> CleanupReport:
    """Convenience facade for callers that do not need to retain a manager."""
    manager = TaskRetentionManager(project_root, policy=policy)
    return manager.cleanup(policy=policy, **kwargs)


__all__ = [
    "ACTIVE_TASK_STATUSES",
    "ARCHIVES_RELATIVE",
    "ConfirmationRequired",
    "CleanupReport",
    "DEFAULT_ELIGIBLE_STATUSES",
    "DEFAULT_PRESERVE_STATUSES",
    "DEFAULT_RETENTION",
    "REPORTS_RELATIVE",
    "RetentionContractError",
    "RetentionError",
    "RetentionPlanChanged",
    "RetentionPolicy",
    "TASKS_RELATIVE",
    "TaskDisposition",
    "TaskRetentionManager",
    "UnsafeRetentionPath",
    "cleanup_tasks",
]
