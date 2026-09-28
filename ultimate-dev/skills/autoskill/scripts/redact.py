#!/usr/bin/env python3
"""Redact secrets and personal identifiers from screenpipe events.

What it does
------------
Applies a fixed set of regex passes over the ``text`` and ``window_title`` of each
normalized event from ``fetch_window.py`` and returns new events. Four classes are
scrubbed:

1. email addresses
2. API keys and long opaque tokens
3. ``Bearer`` / ``Basic`` authorization values
4. phone numbers

This is defense in depth, not the primary control. Screenpipe's own PII removal
(``screenpipe record --use-pii-removal``) and the capture-time deny-list in
``references/screenpipe-config.yaml`` are the primary controls; this module exists
so that a bug in one of those, or a secret that reached the OCR buffer by another
route, does not become a cluster summary sent to an LLM.

Expected input
--------------
A list of dicts with the ``fetch_window.py`` shape:
``{"ts", "app", "window_title", "text", "content_type"}``. Events with any other
keys pass through untouched, so an upstream field addition is not silently dropped.

Usage
-----
    python scripts/redact.py events.json --out redacted.json
    python scripts/redact.py events.json --stats

Provenance
----------
Reconstructed to match the four classes the SKILL.md names. The patterns are
generic, deliberately broad ones written for this file, not a tuned secret-scanner
corpus; run them and read the ``--stats`` output before trusting a result.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter

# Each entry is (name, compiled pattern, replacement). Order matters: the more
# specific credential shapes run before the generic long-token pass, so that a
# bearer token is reported as a bearer token and not as an opaque blob.
RULES: list[tuple[str, re.Pattern, str]] = [
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[redacted-email]",
    ),
    (
        "authorization-header",
        re.compile(r"\b(Bearer|Basic|Token)\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
        r"\1 [redacted-token]",
    ),
    (
        "api-key-assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|apikey|access[_-]?token|secret|client[_-]?secret|"
            r"password|passwd|auth)\b\s*[=:]\s*[\"']?([^\s\"',;]{6,})[\"']?"
        ),
        r"\1=[redacted-secret]",
    ),
    (
        "known-vendor-key",
        re.compile(
            r"\b(sk-[A-Za-z0-9_-]{16,}|"
            r"sk-ant-[A-Za-z0-9_-]{16,}|"
            r"gh[pousr]_[A-Za-z0-9]{16,}|"
            r"github_pat_[A-Za-z0-9_]{20,}|"
            r"AKIA[0-9A-Z]{16}|"
            r"ASIA[0-9A-Z]{16}|"
            r"AIza[0-9A-Za-z_-]{30,}|"
            r"xox[abposr]-[A-Za-z0-9-]{10,}|"
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,})"
        ),
        "[redacted-key]",
    ),
    (
        "long-opaque-token",
        re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{32,}(?![A-Za-z0-9+/=_-])"),
        "[redacted-token]",
    ),
    (
        "phone",
        re.compile(
            r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)"
        ),
        "[redacted-phone]",
    ),
]

# Window titles that are only ever a person or a document get kept as app text
# rather than a title, so the title never reaches a model verbatim.
DEFAULT_TITLE_LIMIT = 160
DEFAULT_TEXT_LIMIT = 4000


def redact_text(value: str, stats: Counter | None = None) -> str:
    """Run every rule over one string, in order, and return the scrubbed result."""
    if not value:
        return value
    result = value
    for name, pattern, replacement in RULES:
        result, hits = pattern.subn(replacement, result)
        if hits and stats is not None:
            stats[name] += hits
    return result


def redact_event(event: dict, stats: Counter | None = None) -> dict:
    """Return a copy of one event with its text and window title scrubbed.

    Keys other than ``text`` and ``window_title`` are passed through unchanged, so
    adding a field upstream is not a reason to lose it here.
    """
    scrubbed = dict(event)
    if isinstance(scrubbed.get("text"), str):
        scrubbed["text"] = redact_text(scrubbed["text"], stats)
    if isinstance(scrubbed.get("window_title"), str):
        title = redact_text(scrubbed["window_title"], stats)
        # Window titles routinely carry a document name, an email subject, or a
        # path. The clusterer only needs the app, so keep the head and the shape.
        if len(title) > DEFAULT_TITLE_LIMIT:
            title = title[:DEFAULT_TITLE_LIMIT].rstrip() + " …"
        scrubbed["window_title"] = title
    if isinstance(scrubbed.get("text"), str) and len(scrubbed["text"]) > DEFAULT_TEXT_LIMIT:
        scrubbed["text"] = scrubbed["text"][:DEFAULT_TEXT_LIMIT].rstrip() + " …"
    return scrubbed


def redact(events: list[dict], stats: Counter | None = None) -> list[dict]:
    """Redact a whole timeline, returning new events and discarding the originals.

    Pass a ``Counter`` as ``stats`` to get a per-rule hit count. The original list
    and its dicts are not modified.
    """
    return [redact_event(event, stats) for event in events]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scrub emails, API keys, bearer tokens, and phone numbers from screenpipe events.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("events", help="JSON file of events from fetch_window.py, or - for stdin")
    parser.add_argument("--out", default=None, help="write redacted JSON here; default stdout")
    parser.add_argument(
        "--stats", action="store_true", help="print a per-rule hit count to stderr"
    )
    args = parser.parse_args(argv)

    if args.events == "-":
        events = json.load(sys.stdin)
    else:
        with open(args.events, encoding="utf-8") as handle:
            events = json.load(handle)

    if not isinstance(events, list):
        raise SystemExit("error: expected a JSON list of events")

    stats: Counter = Counter()
    redacted = redact(events, stats)

    payload = json.dumps(redacted, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        print(f"wrote {len(redacted)} redacted event(s) to {args.out}", file=sys.stderr)
    else:
        print(payload)

    if args.stats:
        print(f"{len(redacted)} event(s) scanned", file=sys.stderr)
        for name, _pattern, _replacement in RULES:
            print(f"  {name}: {stats[name]}", file=sys.stderr)
        if not stats:
            print("  no rule fired", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
