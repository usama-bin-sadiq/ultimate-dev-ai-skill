#!/usr/bin/env python3
"""One place that decides which runtime to invoke, and how.

Why this file exists
--------------------

Three callers invoke a model -- ``run-pilot.py``, ``testbed/run-tasks.py`` and
``generate-skill-image.py`` -- and between them they had two copies of a list of
provider error strings, one hardcoded agent name, and one hardcoded pair of
agent-specific command-line flags.

Two copies of a list is one list that drifts, and the drift was already written:
``run-tasks.py`` carries a comment explaining that a second copy of the provider
error strings is a second list that drifts, immediately above its own second
copy. The rule this repository keeps breaking is *one rule implemented twice, one
copy wrong*. This file is the single implementation.

Provider neutrality
-------------------

Nothing here names a vendor, and there is no default agent.

There was one. ``run-pilot.py`` hardcoded ``--agent opencode`` at the call site
and then wrote ``"runtime": "opencode"`` into every report it produced,
regardless of what actually ran -- so a run against any other agent produced a
report attributing it to that one. Two false claims rather than one: the
hardcoded invocation, and a result file that lied about its own provenance.

The same call site also hardcoded ``--extra-args=--auto --extra-args=--standalone``.
Those are one runtime's flags. They are also load-bearing -- they were added
because without them the model could not approve the tool calls that let it read
the skill, and because without a private server per invocation the adapter's
working directory was silently not the one the agent operated in. Both were real
bugs found the expensive way. So they are not dropped: they are *caller
configuration*, documented as a recipe, and this module passes through whatever
it is given.

If the agent, adapter or flags are not configured, the caller is told. A harness
that silently defaults to one vendor measures that vendor and reports the result
as a property of the skill, which is the specific error this file exists to make
impossible.

Configuration
-------------

Precedence: explicit argument, then environment, then unset.

    ULTIMATE_DEV_AGENT          agent name passed to the adapter's --agent
    ULTIMATE_DEV_MODEL          model name, or unset for the runtime's default
    ULTIMATE_DEV_AGENT_RUNNER   path to the adapter script
    ULTIMATE_DEV_AGENT_ARGS     agent-specific flags, shell-quoted

Exit status
-----------

0 when the module imports. It is a library; it has no main().
"""

from __future__ import annotations

import os
import pathlib
import re
import shlex
import sys
from dataclasses import dataclass, field


# Environment failures, keyed by the kind of failure. Callers exclude a case
# with one of these from every accuracy rate: the run did not happen, so nothing
# is known about what the kernel would have done.
#
# Credit exhaustion is worded several ways by different gateways, and one variant
# is not exhaustion at all -- it is the request asking for more max_tokens than
# the remaining credit can afford, which is fixed by funding or by asking for
# less, not by retrying.
ENVIRONMENT_ERRORS: dict[str, re.Pattern] = {
    "quota": re.compile(
        r"exceed your available credits|requires more credits|add credits|"
        r"can only afford|insufficient_quota|quota", re.I),
    "rate_limit": re.compile(r"rate.?limit|too many requests|\b429\b", re.I),
    "auth": re.compile(r"unauthor|not logged in|invalid api key|\b401\b", re.I),
    "unavailable": re.compile(
        r"service unavailable|\b502\b|\b503\b|bad gateway|overloaded", re.I),
}


def classify_environment_failure(text: str) -> str | None:
    """The environment failure kind, or None if this looks like a real result.

    Note the direction: a match means *the run did not happen*, so a caller must
    record the case as undecided rather than as a routing mistake. Attributing a
    quota error to the skill's decision-making is the worst form of the false
    null, because it looks exactly like a measurement.
    """
    for kind, pattern in ENVIRONMENT_ERRORS.items():
        if pattern.search(text or ""):
            return kind
    return None


@dataclass
class Invocation:
    """A resolved, runnable target, plus enough provenance to report it."""

    runner: pathlib.Path | None = None
    agent: str | None = None
    model: str | None = None
    agent_args: tuple[str, ...] = field(default_factory=tuple)

    # -- configuration ---------------------------------------------------

    @classmethod
    def resolve(cls, *, runner: str | os.PathLike | None = None,
                agent: str | None = None, model: str | None = None,
                agent_args: list[str] | tuple[str, ...] | None = None,
                env: dict[str, str] | None = None) -> "Invocation":
        """Resolve from arguments and environment, in that order.

        ``agent_args`` from the environment is split with :func:`shlex.split`, so
        a value containing quotes can express a flag with a space in it. Passing
        an explicit list bypasses the environment entirely rather than extending
        it, because "add one more flag" and "use these instead" are different
        requests and only one of them should be able to surprise you.
        """
        e = os.environ if env is None else env

        if agent_args is None:
            raw = e.get("ULTIMATE_DEV_AGENT_ARGS", "").strip()
            parsed = tuple(shlex.split(raw)) if raw else ()
        else:
            parsed = tuple(agent_args)

        return cls(
            runner=pathlib.Path(runner) if runner else _maybe_path(
                e.get("ULTIMATE_DEV_AGENT_RUNNER", "").strip()),
            agent=agent or (e.get("ULTIMATE_DEV_AGENT", "").strip() or None),
            model=model or (e.get("ULTIMATE_DEV_MODEL", "").strip() or None),
            agent_args=parsed,
        )

    # -- readiness -------------------------------------------------------

    def missing(self) -> list[str]:
        """What still has to be configured, in the order it will bite.

        Returned rather than raised so a caller can report every gap at once
        instead of one per run. A harness that discovers its agent is unset on
        run 14 of 14 has wasted fourteen runs.
        """
        out: list[str] = []
        if self.runner is None:
            out.append("adapter path (--runner, or ULTIMATE_DEV_AGENT_RUNNER)")
        elif not self.runner.is_file():
            out.append(f"adapter path does not exist: {self.runner}")
        if not self.agent:
            out.append("agent name (--agent, or ULTIMATE_DEV_AGENT)")
        return out

    def is_ready(self) -> bool:
        return not self.missing()

    def require(self) -> None:
        gaps = self.missing()
        if gaps:
            raise InvocationUnconfigured(gaps)

    # -- running ---------------------------------------------------------

    def command(self, prompt: str, *, timeout: int,
                cwd: str | os.PathLike | None = None) -> list[str]:
        """The full argv. Raises rather than guessing when unconfigured."""
        self.require()
        assert self.runner is not None and self.agent is not None
        argv = [sys.executable, str(self.runner), "--agent", self.agent]
        for extra in self.agent_args:
            argv += ["--extra-args=" + extra]
        if self.model:
            argv += ["--model", self.model]
        if cwd is not None:
            argv += ["--cwd", str(cwd)]
        argv += ["--prompt", prompt, "--timeout", str(timeout)]
        return argv

    # -- provenance ------------------------------------------------------

    def describe(self) -> dict:
        """What will be invoked, for a results file.

        Recorded so a number can be attributed to a runtime. The field that used
        to be a literal -- ``"runtime": "opencode"`` in every report whatever ran
        -- was the reason this method exists.
        """
        return {
            "agent": self.agent,
            "model": self.model,
            "runner": str(self.runner) if self.runner else None,
            "agent_args": list(self.agent_args),
            "configured": self.is_ready(),
            "missing": self.missing(),
        }


class InvocationUnconfigured(RuntimeError):
    """Raised when an invocation is attempted without a runtime configured."""

    def __init__(self, gaps: list[str]) -> None:
        self.gaps = gaps
        super().__init__("; ".join(gaps))


def _maybe_path(value: str) -> pathlib.Path | None:
    if not value:
        return None
    return pathlib.Path(os.path.expanduser(value))


# Documented recipes for callers who do not want to rediscover them. These are
# examples, not defaults: nothing in this module reads them. Each was added
# because a run was wrong without it, and the reason is kept with it so the next
# person does not delete the flag that is not obviously needed.
RECIPES: dict[str, dict] = {
    "private-server-per-run": {
        "agent_args": ["--auto", "--standalone"],
        "why": (
            "--auto lets the runtime approve the tool calls that let the agent "
            "read the skill; without it every run degenerates into the model "
            "narrating that it would read the file. --standalone forces a private "
            "server per invocation; without it the CLI attaches to a long-lived "
            "background service carrying its own working directory, and the "
            "adapter's cwd is silently not the directory the agent operates in. "
            "Both bugs presented as the grader reporting correct answers as wrong."
        ),
    },
}


def main() -> int:
    """Report the resolved configuration. Never fails on a missing setting."""
    inv = Invocation.resolve()
    gaps = inv.missing()
    print("  invocation configuration")
    for key, value in inv.describe().items():
        if key == "missing":
            continue
        print(f"    {key:<12} {value}")
    if gaps:
        print()
        print("  NOT CONFIGURED:")
        for gap in gaps:
            print(f"    - {gap}")
        print()
        print("  There is deliberately no default. A harness that falls back to")
        print("  one vendor measures that vendor and reports the result as a")
        print("  property of the skill. Set the flag, or the environment variable")
        print("  named above.")
        print()
        print("  Recipes for the flags a known-good configuration used:")
        for name, recipe in RECIPES.items():
            print(f"    {name}: ULTIMATE_DEV_AGENT_ARGS="
                  f"{shlex.join(recipe['agent_args'])}")
    else:
        print()
        print(f"  ready. command preview:\n    {shlex.join(inv.command('<prompt>', timeout=0))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
