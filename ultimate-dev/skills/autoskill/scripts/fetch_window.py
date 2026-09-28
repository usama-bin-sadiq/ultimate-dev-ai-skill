#!/usr/bin/env python3
"""Fetch a screenpipe window as normalized timeline events.

What it does
------------
Pages screenpipe's local HTTP ``/search`` endpoint over a time range and returns a
flat list of dicts with exactly these keys::

    {"ts": <ISO-8601 str>, "app": <str>, "window_title": <str>,
     "text": <str>, "content_type": <str>}

Nothing else in the pipeline touches the screenpipe wire format, so the shape
screenpipe changes is contained in this file.

Expected input
--------------
A running screenpipe daemon (default ``http://localhost:3030``) and a bearer
token in ``SCREENPIPE_TOKEN``. App and window filtering should already have been
applied at capture time via screenpipe's ``ignored_apps`` /
``ignored_windows`` — see ``references/screenpipe-config.yaml``. This script does
no filtering of its own beyond dropping empty records.

Usage
-----
    python scripts/fetch_window.py --start 2026-04-17T00:00:00Z --end 2026-04-17T23:59:59Z
    python scripts/fetch_window.py --start ... --end ... --content-type ocr --out events.json

Provenance
----------
Reconstructed to match the API surface described in this skill's SKILL.md. The
call shape follows screenpipe's documented ``POST /search`` (body carries
``content_type``, ``limit``, ``offset``, ``start_time``, ``end_time``; auth is a
``Bearer`` header), but this file is not upstream screenpipe code and the paging
and normalization are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# screenpipe's /search caps `limit`; 100 is the largest value it reliably honours.
DEFAULT_PAGE_SIZE = 100
MAX_PAGES = 2000

INSTALL_HINT = (
    "screenpipe is not reachable, and this skill has no other data source.\n"
    "Install and start the daemon, then export a token:\n"
    "  git clone --depth 1 https://github.com/mediar-ai/screenpipe.git\n"
    "  cd screenpipe && cargo build -p screenpipe-engine --release\n"
    "  ./target/release/screenpipe doctor\n"
    "  ./target/release/screenpipe record --disable-audio --use-pii-removal\n"
    "  export SCREENPIPE_TOKEN=$(screenpipe auth token)\n"
    "See references/screenpipe-config.yaml for a starter capture deny-list."
)


class ScreenpipeUnreachable(RuntimeError):
    """The screenpipe daemon is not reachable, or refused the token."""


def _parse_time(value: str | None, label: str) -> str | None:
    """Normalize a timestamp to the ISO form screenpipe expects (UTC, Z suffix)."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit(f"error: --{label} is not an ISO-8601 timestamp: {value!r} ({exc})")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _client():
    """Build an httpx client, or explain what to install."""
    try:
        import httpx
    except ImportError:
        raise SystemExit(
            "error: httpx is not installed. Run `pipenv install httpx pyyaml "
            "sentence-transformers` from the repo root."
        )
    return httpx


def _headers(token: str | None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(url: str, token: str | None, payload: dict, timeout: float) -> dict:
    """POST one /search page, converting every failure mode into one exception."""
    httpx = _client()
    try:
        response = httpx.post(
            f"{url.rstrip('/')}/search", json=payload, headers=_headers(token), timeout=timeout
        )
    except Exception as exc:  # connection refused, DNS, timeout, TLS
        raise ScreenpipeUnreachable(f"{url}/search did not answer: {exc}\n\n{INSTALL_HINT}")

    if response.status_code in (401, 403):
        raise ScreenpipeUnreachable(
            f"screenpipe returned {response.status_code} for /search. The local API "
            "requires a bearer token: export SCREENPIPE_TOKEN=$(screenpipe auth token)."
        )
    if response.status_code == 404:
        raise ScreenpipeUnreachable(
            f"screenpipe returned 404 for /search. Check that screenpipe.url points at "
            f"the daemon root (currently {url}), not at a sub-path."
        )
    if response.status_code >= 400:
        raise ScreenpipeUnreachable(
            f"screenpipe returned {response.status_code}: {response.text[:200]}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise ScreenpipeUnreachable(f"screenpipe /search did not return JSON: {exc}")


def _record_text(record: dict) -> str:
    """Best-effort text for a record; content type changes which field carries it."""
    frame = record.get("frame") or {}
    for key in ("text", "transcript", "ocr_text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    value = frame.get("text") if isinstance(frame, dict) else None
    return value if isinstance(value, str) else ""


def normalize(record: dict) -> dict | None:
    """Turn one screenpipe record into the pipeline's event shape, or None to drop it."""
    frame = record.get("frame") or {}
    if not isinstance(frame, dict):
        return None

    text = _record_text(record).strip()
    title = (frame.get("window_name") or "").strip()
    app = (frame.get("app_name") or "").strip()
    if not text and not title and not app:
        return None

    ts = frame.get("timestamp")
    if not isinstance(ts, str) or not ts:
        return None

    return {
        "ts": ts,
        "app": app,
        "window_title": title,
        "text": text,
        "content_type": record.get("content_type") or "unknown",
    }


def fetch_window(
    start: str,
    end: str,
    url: str = "http://localhost:3030",
    token: str | None = None,
    content_type: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = MAX_PAGES,
) -> list[dict]:
    """Page /search until it stops returning data, and return normalized events.

    ``start``/``end`` are ISO-8601 strings. ``content_type`` restricts to one of
    screenpipe's content types ("ocr", "audio", "input", "accessibility"); omit it
    for everything the daemon holds.
    """
    payload: dict = {
        "limit": page_size,
        "offset": 0,
        "start_time": _parse_time(start, "start"),
        "end_time": _parse_time(end, "end"),
    }
    if content_type:
        payload["content_type"] = content_type

    events: list[dict] = []
    for _page in range(max_pages):
        body = _request(url, token, payload, timeout=30.0)
        records = body.get("data") if isinstance(body, dict) else body
        if not records:
            break
        for record in records:
            event = normalize(record)
            if event is not None:
                events.append(event)
        payload["offset"] += len(records)
        if len(records) < page_size:
            break
    else:
        raise SystemExit(
            f"error: /search still had results after {max_pages} pages of {page_size}. "
            "Narrow the window or raise max_pages rather than truncating silently."
        )

    events.sort(key=lambda event: event["ts"])
    return events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a screenpipe time window as normalized timeline events.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--start", required=True, help="window start, ISO-8601 (UTC assumed)")
    parser.add_argument("--end", required=True, help="window end, ISO-8601 (UTC assumed)")
    parser.add_argument("--url", default=None, help="screenpipe base URL; overrides config.yaml")
    parser.add_argument(
        "--token",
        default=None,
        help="bearer token; defaults to $SCREENPIPE_TOKEN",
    )
    parser.add_argument(
        "--content-type",
        default=None,
        help="restrict to one content type: ocr, audio, input, accessibility",
    )
    parser.add_argument(
        "--page-size", type=int, default=DEFAULT_PAGE_SIZE, help="records requested per page"
    )
    parser.add_argument("--out", default=None, help="write JSON here; default stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    url = args.url or os.environ.get("SCREENPIPE_URL") or "http://localhost:3030"
    token = args.token if args.token is not None else os.environ.get("SCREENPIPE_TOKEN")

    try:
        events = fetch_window(
            start=args.start,
            end=args.end,
            url=url,
            token=token,
            content_type=args.content_type,
            page_size=args.page_size,
        )
    except ScreenpipeUnreachable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(events, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
        print(f"wrote {len(events)} event(s) to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
