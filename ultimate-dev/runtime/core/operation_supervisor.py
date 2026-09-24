"""Bounded operation lease supervisor for host runtimes."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class OperationContext:
    operation_id: str
    task_id: str
    cancel_event: threading.Event
    deadline: float | None = None

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def remaining(self) -> float | None:
        return None if self.deadline is None else max(0.0, self.deadline - time.monotonic())


class OperationSupervisor:
    """Renew owned leases and reap expired operations without replaying them."""

    def __init__(
        self,
        store: Any,
        worker_id: str,
        *,
        lease_seconds: float = 300.0,
        clock: Callable[[], float] = time.time,
        recovery: Callable[[str], int] | None = None,
    ) -> None:
        if not callable(getattr(store, "list_operations", None)):
            raise TypeError("store must provide list_operations()")
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id is required")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self.store = store
        self.worker_id = worker_id
        self.lease_seconds = float(lease_seconds)
        self.clock = clock
        self.recovery = recovery
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def tick(self, task_id: str) -> dict[str, int]:
        now = float(self.clock())
        renewed = 0
        stale = 0
        for operation in self.store.list_operations(task_id):
            status = operation.get("status")
            if status not in {"pending", "running"}:
                continue
            lease = operation.get("lease_expires_at_epoch")
            if operation.get("worker_id") == self.worker_id and isinstance(lease, (int, float)):
                if lease - now <= self.lease_seconds / 3:
                    try:
                        self.store.renew_operation_lease(task_id, operation["operation_id"], self.worker_id, self.lease_seconds)
                        renewed += 1
                    except (PermissionError, ValueError, OSError):
                        pass
            if isinstance(lease, (int, float)) and lease <= now:
                stale += 1
        recovered = 0
        if stale and self.recovery is not None:
            recovered = int(self.recovery(task_id) or 0)
        elif stale and callable(getattr(self.store, "recover_stale_operations", None)):
            recovered = int(self.store.recover_stale_operations(task_id) or 0)
        return {"renewed": renewed, "stale": stale, "recovered": recovered}

    def start(self, task_id: str, interval_seconds: float = 1.0) -> "OperationSupervisor":
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        with self._lock:
            if self._thread is not None:
                return self
            self._stop.clear()

            def loop() -> None:
                while not self._stop.wait(interval_seconds):
                    try:
                        self.tick(task_id)
                    except Exception:
                        # A supervisor must not die silently; the next tick
                        # retries and the Runtime health surface reports state.
                        continue

            self._thread = threading.Thread(target=loop, name="ultimate-operation-supervisor", daemon=True)
            self._thread.start()
        return self

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            thread = self._thread
            self._thread = None
            self._stop.set()
        if thread is not None:
            thread.join(timeout=max(0.0, timeout))

    def __enter__(self) -> "OperationSupervisor":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()


__all__ = ["OperationContext", "OperationSupervisor"]
