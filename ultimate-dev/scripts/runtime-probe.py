#!/usr/bin/env python3
"""Report whether the durable runtime is available to this process.

Prints exactly one of:

    RUNTIME_AVAILABLE   the durable runtime is importable and usable
    PROMPT_ONLY         it is not; the caller must not self-certify side effects

This is the single implementation of that decision. The recipe in ``AGENTS.md``
calls this script rather than inlining the probe, so the logic cannot drift
between the prompt and the runtime, and the always-loaded prompt stays small.

Exit status is always 0. The outcome is the printed word, not the status code:
a host must be able to read the answer without treating failure as an error.
"""
from __future__ import annotations

import importlib.util
import os
import sys

#: Probed by module name, not by path. Path guessing with a relative
#: ``os.path.isdir`` silently matches nothing when the skill sits one level
#: down, which would report PROMPT_ONLY while a working runtime is present.
MARKER_MODULE = "runtime.core.attestation"
MARKER_FILE = os.path.join("runtime", "core", "attestation.py")

AVAILABLE = "RUNTIME_AVAILABLE"
PROMPT_ONLY = "PROMPT_ONLY"


def _importable() -> bool:
    try:
        return importlib.util.find_spec(MARKER_MODULE) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def candidate_roots() -> list[str]:
    """Directories that might contain the skill payload, nearest first."""
    here = os.getcwd()
    seeds = [here, os.path.dirname(here), os.path.join(here, "ultimate-dev")]
    seen: set[str] = set()
    roots: list[str] = []
    for seed in seeds:
        if not seed:
            continue
        resolved = os.path.abspath(seed)
        if resolved not in seen:
            seen.add(resolved)
            roots.append(resolved)
    return roots


def locate() -> str | None:
    """Return an importable root for the runtime, or None if absent."""
    if _importable():
        return os.getcwd()
    for root in candidate_roots():
        if os.path.isfile(os.path.join(root, MARKER_FILE)):
            sys.path.insert(0, root)
            if _importable():
                return root
    return None


def detect() -> str:
    """Return AVAILABLE or PROMPT_ONLY. Never raises."""
    try:
        root = locate()
        if root is None:
            return PROMPT_ONLY
        from runtime.core.attestation import runtime_available

        return AVAILABLE if runtime_available() else PROMPT_ONLY
    except Exception:
        # An unimportable or half-installed runtime is a prompt-only host.
        return PROMPT_ONLY


def main() -> int:
    print(detect())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
