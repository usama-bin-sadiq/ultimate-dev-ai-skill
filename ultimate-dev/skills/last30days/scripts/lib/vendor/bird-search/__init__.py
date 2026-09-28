"""Vendored X (Twitter) search client used by the last30days engine.

Import as ``from lib.vendor.bird_search import BirdSearchClient``.

Reconstruction note: ``SKILL.md`` records this directory as a vendored,
MIT-licensed X search client, but the upstream source was not available when this
was written. What follows is an independent implementation of the surface the
engine needs, against the official X API v2, under the same licence SKILL.md
records. See ``README.md`` in this directory for what that means in practice.

Only the app-only bearer path lives here. Browser cookies (``AUTH_TOKEN`` /
``CT0``), the xAI API, and the xurl CLI are separate backends elsewhere in the
engine, and mixing them here would put a second credential in the one module
whose whole job is to hold a single header.
"""

from __future__ import annotations

from .bird_search import (
    POST_FIELDS,
    BirdSearchClient,
    BirdSearchError,
    citation_url,
    normalize_post,
)

__all__ = [
    "POST_FIELDS",
    "BirdSearchClient",
    "BirdSearchError",
    "citation_url",
    "normalize_post",
]
