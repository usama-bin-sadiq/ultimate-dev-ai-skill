"""Optional host session hooks for graceful interruption and shutdown."""
from __future__ import annotations

import signal
import threading
from contextlib import AbstractContextManager
from types import FrameType
from typing import Any, Iterable


class SessionHookError(RuntimeError):
    """Session hooks could not be installed or restored."""


class SessionHooks(AbstractContextManager):
    """Install process signal handlers only when explicitly requested by a host."""

    def __init__(self, runtime: Any, task_id: str | None = None, signals: Iterable[int] | None = None) -> None:
        if not hasattr(runtime, "interrupt_task") or not hasattr(runtime, "close"):
            raise SessionHookError("runtime must expose interrupt_task() and close()")
        self.runtime = runtime
        self.task_id = task_id
        self.signals = tuple(signals or (signal.SIGINT, signal.SIGTERM))
        self._previous: dict[int, Any] = {}
        self._installed = False
        self._lock = threading.Lock()

    def _handle(self, signum: int, frame: FrameType | None) -> None:
        with self._lock:
            if not self._installed:
                return
            if self.task_id is not None:
                try:
                    self.runtime.interrupt_task(self.task_id, reason=f"signal_{signum}")
                except Exception:
                    # Closing remains the final safe boundary; preserve the
                    # signal handler's original contract and do not raise.
                    pass
            try:
                self.runtime.close()
            except Exception:
                pass

    def install(self) -> "SessionHooks":
        if self._installed:
            return self
        if threading.current_thread() is not threading.main_thread():
            raise SessionHookError("signal hooks must be installed on the main thread")
        for signum in self.signals:
            try:
                self._previous[signum] = signal.getsignal(signum)
                signal.signal(signum, self._handle)
            except (OSError, ValueError) as exc:
                self.restore()
                raise SessionHookError(f"unable to install signal handler {signum}") from exc
        self._installed = True
        return self

    def restore(self) -> None:
        with self._lock:
            if not self._installed and not self._previous:
                return
            for signum, previous in self._previous.items():
                try:
                    signal.signal(signum, previous)
                except (OSError, ValueError):
                    continue
            self._previous.clear()
            self._installed = False

    def __enter__(self) -> "SessionHooks":
        return self.install()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.restore()


def install_session_hooks(runtime: Any, task_id: str | None = None, signals: Iterable[int] | None = None) -> SessionHooks:
    return SessionHooks(runtime, task_id=task_id, signals=signals).install()


__all__ = ["SessionHookError", "SessionHooks", "install_session_hooks"]
