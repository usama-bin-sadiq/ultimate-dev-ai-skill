import signal

from runtime.core.session_hooks import SessionHooks


class FakeRuntime:
    def __init__(self):
        self.events = []

    def interrupt_task(self, task_id, reason):
        self.events.append(("interrupt", task_id, reason))

    def close(self):
        self.events.append(("close",))


def test_session_hooks_interrupt_and_close_then_restore():
    runtime = FakeRuntime()
    hooks = SessionHooks(runtime, task_id="task-1", signals=(signal.SIGUSR1,))
    hooks.install()
    try:
        signal.raise_signal(signal.SIGUSR1)
    finally:
        hooks.restore()
    assert runtime.events == [("interrupt", "task-1", f"signal_{int(signal.SIGUSR1)}"), ("close",)]
