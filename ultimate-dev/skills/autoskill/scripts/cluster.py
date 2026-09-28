#!/usr/bin/env python3
"""Segment a screenpipe timeline into sessions and cluster the sessions.

Two stages, both local, no model involved:

``segment_sessions``
    Splits the event stream on idle gaps. An idle gap is longer than
    ``idle_gap_minutes``; a session shorter than ``min_session_minutes`` is
    dropped as a glance rather than as work.

``cluster_sessions``
    Groups sessions by an app signature and keeps clusters with at least
    ``min_cluster_size`` members. A cluster of one session is not a repeated
    workflow, which is the thing the whole skill exists to find.

Expected input
--------------
A list of ``fetch_window.py`` events (``ts``, ``app``, ``window_title``, ``text``,
``content_type``), already through ``redact.py``.

Usage
-----
    python scripts/cluster.py events.json --out sessions.json
    python scripts/cluster.py events.json --idle-gap-minutes 15 --min-cluster-size 3

Provenance
----------
Reconstructed to match the segmentation and clustering behaviour the SKILL.md
describes (idle-gap split at a default 10 minutes, short sessions dropped,
app-signature grouping, ``min_cluster_size`` default 2). The signature function
is this file's own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

DEFAULT_IDLE_GAP_MINUTES = 10
DEFAULT_MIN_SESSION_MINUTES = 5
DEFAULT_MIN_CLUSTER_SIZE = 2

# Window titles are noisy; these tokens carry the *kind* of work and are kept,
# while version numbers, file paths, and branch names are dropped.
_NOISE = re.compile(
    r"(\d+|[._-]v?\d+|\.py|\.js|\.ts|\.tsx|\.md|\.json|\.csv|\.tsv|\.ipynb"
    r"|/[^ ]*|[A-Z]:\\[^\s]*|@[a-z0-9_-]+|\s-\s.*$)",
    re.IGNORECASE,
)
_STOP_TOKENS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "at",
    "new", "untitled", "home", "index", "main", "app", "page", "window",
}


def _parse_ts(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def segment_sessions(
    events: list[dict],
    idle_gap_minutes: int = DEFAULT_IDLE_GAP_MINUTES,
    min_session_minutes: int = DEFAULT_MIN_SESSION_MINUTES,
) -> list[dict]:
    """Split the timeline on idle gaps and drop sessions that are too short.

    Returns sessions in chronological order, each with the start/end timestamps,
    the duration, the apps touched, and the event count.
    """
    if not events:
        return []

    ordered = sorted(events, key=lambda event: event.get("ts", ""))
    gap = idle_gap_minutes * 60

    sessions: list[dict] = []
    current: list[dict] = [ordered[0]]
    for event in ordered[1:]:
        try:
            delta = (_parse_ts(event["ts"]) - _parse_ts(current[-1]["ts"])).total_seconds()
        except (KeyError, ValueError):
            # An unparseable timestamp ends the current session rather than
            # silently joining two unrelated spans.
            sessions.append(_close(current))
            current = [event]
            continue
        if delta > gap:
            sessions.append(_close(current))
            current = [event]
        else:
            current.append(event)
    sessions.append(_close(current))

    kept = []
    for session in sessions:
        if session["duration_minutes"] < min_session_minutes:
            continue
        kept.append(session)
    return kept


def _close(events: list[dict]) -> dict:
    start = _parse_ts(events[0]["ts"])
    end = _parse_ts(events[-1]["ts"])
    seconds = max(0.0, (end - start).total_seconds())
    return {
        "start": events[0]["ts"],
        "end": events[-1]["ts"],
        "duration_minutes": round(seconds / 60.0, 2),
        "apps": sorted({e.get("app", "") for e in events if e.get("app")}),
        "event_count": len(events),
        "events": events,
    }


def app_signature(session: dict, max_tokens: int = 4) -> str:
    """Build a stable signature for what kind of work a session was.

    Combines the apps touched with the most frequent meaningful title tokens, so
    that "RStudio + ggplot" and "VS Code + deseq2" do not collapse together.
    """
    apps = "+".join(session.get("apps", [])) or "unknown"
    counter: Counter = Counter()
    for event in session.get("events", []):
        title = event.get("window_title", "") or ""
        cleaned = _NOISE.sub(" ", title)
        for token in re.split(r"[\s\-_/,;()\[\]]+", cleaned):
            token = token.strip().lower()
            if len(token) < 3 or token in _STOP_TOKENS or token.isdigit():
                continue
            counter[token] += 1
    top = [token for token, _count in counter.most_common(max_tokens)]
    return f"{apps}:{'+'.join(sorted(top))}" if top else apps


def cluster_sessions(
    sessions: list[dict],
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> list[dict]:
    """Group sessions by app signature, keeping clusters of at least the minimum size."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for session in sessions:
        grouped[session.get("signature") or app_signature(session)].append(session)

    clusters = []
    for signature, members in grouped.items():
        if len(members) < min_cluster_size:
            continue
        members = sorted(members, key=lambda s: s["start"])
        apps = sorted({app for m in members for app in m.get("apps", [])})
        titles = Counter(
            event.get("window_title", "")
            for m in members
            for event in m.get("events", [])
            if event.get("window_title")
        )
        clusters.append(
            {
                "signature": signature,
                "session_count": len(members),
                "total_minutes": round(sum(m["duration_minutes"] for m in members), 2),
                "apps": apps,
                "representative_titles": [t for t, _ in titles.most_common(5)],
                "sessions": members,
            }
        )

    clusters.sort(key=lambda c: (c["session_count"], c["total_minutes"]), reverse=True)
    return clusters


def summarize(clusters: list[dict], limit: int = 3) -> list[dict]:
    """Reduce each cluster to the fields that are safe and useful to show a model.

    This is the object that leaves the machine after redaction. It carries no raw
    OCR text, only what the user was doing, how long, and in which apps.
    """
    summary = []
    for cluster in clusters:
        samples = []
        for session in cluster["sessions"][:limit]:
            titles = []
            for event in session.get("events", []):
                title = event.get("window_title", "")
                if title and title not in titles:
                    titles.append(title)
                if len(titles) >= 3:
                    break
            samples.append(
                {
                    "start": session["start"],
                    "duration_minutes": session["duration_minutes"],
                    "representative_titles": titles,
                }
            )
        summary.append(
            {
                "signature": cluster["signature"],
                "apps": cluster["apps"],
                "session_count": cluster["session_count"],
                "total_minutes": cluster["total_minutes"],
                "sample_sessions": samples,
            }
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Segment screenpipe events into sessions and cluster repeated patterns.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("events", help="JSON list of events, or - for stdin")
    parser.add_argument("--out", default=None, help="write the cluster summary here; default stdout")
    parser.add_argument(
        "--idle-gap-minutes",
        type=int,
        default=DEFAULT_IDLE_GAP_MINUTES,
        help="gap longer than this ends a session",
    )
    parser.add_argument(
        "--min-session-minutes",
        type=int,
        default=DEFAULT_MIN_SESSION_MINUTES,
        help="sessions shorter than this are dropped as glances",
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=DEFAULT_MIN_CLUSTER_SIZE,
        help="clusters smaller than this are not repeated workflows",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    events = json.load(sys.stdin) if args.events == "-" else json.load(open(args.events, encoding="utf-8"))
    if not isinstance(events, list):
        raise SystemExit("error: expected a JSON list of events")

    sessions = segment_sessions(events, args.idle_gap_minutes, args.min_session_minutes)
    for session in sessions:
        session["signature"] = app_signature(session)
    clusters = cluster_sessions(sessions, args.min_cluster_size)
    summary = summarize(clusters)

    print(
        f"{len(events)} event(s) -> {len(sessions)} session(s) -> {len(clusters)} cluster(s)",
        file=sys.stderr,
    )
    payload = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        print(f"wrote {len(summary)} cluster summary entry/entries to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
