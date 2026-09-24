"""Hash-chained local task event journal.

The journal is an additional integrity signal, not a replacement for the
runtime's state store or an external immutable audit sink.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Mapping


class AuditJournalError(ValueError):
    """The local event journal is malformed or fails an integrity check."""


class AuditJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    @staticmethod
    def _hash(value: Mapping[str, Any]) -> str:
        encoded = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def append(self, event: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(event, Mapping):
            raise AuditJournalError("journal event must be an object")
        previous_hash = ""
        sequence = 0
        if self.path.exists():
            last = None
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        last = json.loads(line)
            if last is not None:
                previous_hash = str(last.get("event_hash", ""))
                sequence = int(last.get("sequence", -1)) + 1
        record = {
            "schema_version": "1.0",
            "sequence": sequence,
            "previous_hash": previous_hash,
            "event": dict(event),
        }
        record["event_hash"] = self._hash(record)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        previous = ""
        expected_sequence = 0
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AuditJournalError("journal contains invalid JSON") from exc
                if not isinstance(record, dict) or record.get("sequence") != expected_sequence:
                    raise AuditJournalError("journal sequence is not contiguous")
                if record.get("previous_hash") != previous:
                    raise AuditJournalError("journal hash chain is broken")
                event_hash = record.get("event_hash")
                probe = dict(record)
                probe.pop("event_hash", None)
                if not isinstance(event_hash, str) or not hmac.compare_digest(event_hash, self._hash(probe)):
                    raise AuditJournalError("journal event hash does not match")
                previous = event_hash
                expected_sequence += 1
        return True


__all__ = ["AuditJournal", "AuditJournalError"]
