#!/usr/bin/env python3
"""Report which host capabilities are actually available.

The prompt core issues shell commands unconditionally: five fenced ``bash``
blocks in ``AGENTS.md`` and more in ``SKILL.md``, plus every ``cat``, ``ls``,
``python3`` and ``git`` instruction. A host with no shell cannot run them, and a
host whose tool is named something other than ``bash`` cannot either.

This was observed rather than hypothesised. During development a tool call to
``bash`` failed with:

    No tool named "bash" is currently available.
    Please use a tool from the available tool list.

The session recovered, but the prompt core gave no warning, so the failure
surfaced as an error string instead of a capability gap. That is the same class
of defect as the undetected runtime: a capability was assumed, and its absence
was discovered by crashing rather than by asking.

The probe is advisory. It reports; it does not block. A host that lacks a shell
still runs the skill, in prompt-only mode, and says so.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def has_shell_binary() -> bool:
    """True when a POSIX shell exists on PATH."""
    return any(shutil.which(name) for name in ("sh", "bash", "zsh"))


def has_python() -> bool:
    return bool(sys.executable)


def runtime_available() -> bool:
    try:
        sys.path.insert(0, ROOT)
        from runtime.core.attestation import runtime_available as inner

        return bool(inner())
    except Exception:  # noqa: BLE001
        return False


def _safe(check, label: str) -> bool:
    """Run one capability check, treating a crash as absence.

    A probe that raises while describing a broken host is useless precisely
    when it is needed. Every check is therefore isolated.
    """
    try:
        return bool(check())
    except Exception:  # noqa: BLE001
        return False


def report() -> dict[str, Any]:
    """Describe the host's capabilities honestly.

    ``absent_capabilities`` is the part that matters. A host must be able to
    read this and degrade without crashing.
    """
    shell = _safe(has_shell_binary, "shell")
    python = _safe(has_python, "python")
    runtime = _safe(runtime_available, "durable_runtime")
    absent: list[str] = []
    if not shell:
        absent.append("shell")
    if not python:
        absent.append("python")
    if not runtime:
        absent.append("durable_runtime")
    return {
        "shell": shell,
        "python": python,
        "durable_runtime": runtime,
        # What a host may claim as a result. Mirrors the attestation grades.
        "evidence_grade": "TOOL_ATTESTED" if runtime else "SELF_REPORTED",
        "plane": "RUNTIME_AVAILABLE" if runtime else "PROMPT_ONLY",
        "absent_capabilities": absent,
        "note": (
            "Advisory. Without a shell, read the fenced blocks as instructions "
            "for a human and report what you could not run as not_run."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    result = report()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key in ("shell", "python", "durable_runtime"):
            print(f"  {'yes' if result[key] else 'no ':<4} {key}")
        print(f"  plane: {result['plane']}  evidence: {result['evidence_grade']}")
        if result["absent_capabilities"]:
            print(f"  absent: {', '.join(result['absent_capabilities'])}")
        else:
            print("  absent: none")
    # Always 0: this is a report, not a gate. A host must be able to ask
    # without being blocked by the answer.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
