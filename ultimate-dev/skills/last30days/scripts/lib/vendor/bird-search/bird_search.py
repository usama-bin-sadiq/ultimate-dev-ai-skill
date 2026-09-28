"""X API v2 recent-search client, standard library only.

No third-party dependency, no call at import time, and no credential anywhere
but the ``Authorization`` header. See the README in this directory for why this
is a reconstruction rather than a copy.

Usage from the engine:

    client = BirdSearchClient(bearer_token=os.environ["X_BEARER_TOKEN"])
    posts = client.search_recent(
        "some topic -is:retweet", start="2026-09-01", end="2026-09-28",
        max_results=30,
    )

Every post dict carries exactly the eight keys in ``POST_FIELDS``, which is the
same flat shape the ``last30days-x-posts/1`` envelope uses, so a live search and
a connector-fetched envelope are interchangeable downstream.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable, Mapping

API_BASE = "https://api.x.com/2"
STATUS_BASE = "https://x.com"

#: The flat post shape the engine consumes. Nothing else crosses this boundary.
POST_FIELDS = (
    "id",
    "author_handle",
    "created_at",
    "text",
    "likes",
    "reposts",
    "replies",
    "quotes",
)

TWEET_FIELDS = "created_at,public_metrics,lang,conversation_id"
USER_FIELDS = "username"
EXPANSIONS = "author_id"
MAX_RESULTS_CEILING = 100
DEFAULT_TIMEOUT = 30
USER_AGENT = "last30days-skill/3 (+https://github.com/mvanhorn/last30days-skill)"

# Short categories, never raw response bodies: a body can carry an account id.
_RETRY_AFTER_SECONDS = 15
_RETRYABLE_CATEGORIES = frozenset({"rate-limit", "unavailable"})


class BirdSearchError(RuntimeError):
    """An X search failed.

    ``category`` is one of ``auth``, ``rate-limit``, ``unavailable``,
    ``bad-response``, or ``not-configured``. The engine maps every one of them to
    a source outcome; none of them is a reason to abort the run.
    """

    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


def citation_url(post: Mapping[str, Any]) -> str:
    """Rebuild the canonical status URL from a post id and handle.

    The engine never trusts a URL that arrived inside a payload, so this is the
    only way a citation URL is produced.
    """
    post_id = str(post.get("id", "")).strip()
    handle = str(post.get("author_handle", "")).strip().lstrip("@")
    if not post_id or not handle:
        raise BirdSearchError("bad-response", "post is missing an id or an author handle")
    return f"{STATUS_BASE}/{handle}/status/{post_id}"


def normalize_post(
    tweet: Mapping[str, Any], users: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any] | None:
    """Flatten one API tweet into the eight-field post shape.

    Returns ``None`` for a row that cannot be normalised, so a partial payload
    drops one post rather than aborting a lane.
    """
    post_id = str(tweet.get("id", "")).strip()
    text = tweet.get("text")
    if not post_id or not isinstance(text, str) or not text.strip():
        return None

    author_id = str(tweet.get("author_id", "")).strip()
    author = users.get(author_id, {})
    handle = str(author.get("username", "")).strip().lstrip("@")
    if not handle:
        return None

    metrics = tweet.get("public_metrics") or {}
    if not isinstance(metrics, Mapping):
        metrics = {}

    def count(name: str) -> int:
        value = metrics.get(name, 0)
        return value if isinstance(value, int) else 0

    return {
        "id": post_id,
        "author_handle": handle,
        "created_at": str(tweet.get("created_at", "") or ""),
        "text": text,
        "likes": count("like_count"),
        "reposts": count("retweet_count"),
        "replies": count("reply_count"),
        "quotes": count("quote_count"),
    }


def _index_users(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    includes = payload.get("includes") or {}
    users = includes.get("users") or []
    if not isinstance(users, list):
        return {}
    return {
        str(user.get("id", "")): user
        for user in users
        if isinstance(user, Mapping) and user.get("id")
    }


class BirdSearchClient:
    """Minimal recent-search client for the X API v2.

    Holds a bearer token, keeps no history, and redacts itself by default so an
    accidental ``print(client)`` cannot leak the credential.
    """

    def __init__(
        self,
        bearer_token: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        base_url: str = API_BASE,
    ) -> None:
        token = bearer_token if bearer_token is not None else os.environ.get(
            "X_BEARER_TOKEN", ""
        )
        self._token = (token or "").strip()
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")

    # -- credential handling -------------------------------------------------

    @property
    def configured(self) -> bool:
        """True when a bearer token is present. Does not validate it."""
        return bool(self._token)

    def __repr__(self) -> str:  # pragma: no cover - defensive
        state = "set" if self._token else "absent"
        return f"<BirdSearchClient bearer={state} base_url={self.base_url!r}>"

    # -- transport -----------------------------------------------------------

    def _get(self, path: str, params: Mapping[str, str]) -> dict[str, Any]:
        if not self._token:
            raise BirdSearchError("not-configured", "no X bearer token is configured")

        url = f"{self.base_url}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            raise self._classify(exc.code) from None
        except urllib.error.URLError:
            raise BirdSearchError("unavailable", "X search could not be reached") from None
        except TimeoutError:
            raise BirdSearchError("unavailable", "X search timed out") from None

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise BirdSearchError("bad-response", "X search returned a non-JSON body") from None
        if not isinstance(payload, dict):
            raise BirdSearchError("bad-response", "X search returned an unexpected shape")
        return payload

    @staticmethod
    def _classify(status: int) -> BirdSearchError:
        """Map an HTTP status to a short category. Never echoes the body."""
        if status in (401, 403):
            return BirdSearchError("auth", f"X search rejected the bearer token (HTTP {status})")
        if status == 429:
            return BirdSearchError("rate-limit", "X search rate limit reached (HTTP 429)")
        if status == 400:
            return BirdSearchError("bad-response", f"X search rejected the query (HTTP {status})")
        return BirdSearchError("unavailable", f"X search failed (HTTP {status})")

    def _with_retry(self, path: str, params: Mapping[str, str], attempts: int = 3) -> dict[str, Any]:
        last: BirdSearchError | None = None
        for attempt in range(attempts):
            try:
                return self._get(path, params)
            except BirdSearchError as exc:
                if exc.category not in _RETRYABLE_CATEGORIES or attempt == attempts - 1:
                    raise
                last = exc
                time.sleep(_RETRY_AFTER_SECONDS * (attempt + 1))
        raise last or BirdSearchError("unavailable", "X search failed")

    # -- API -----------------------------------------------------------------

    def search_recent(
        self,
        query: str,
        start: str | None = None,
        end: str | None = None,
        max_results: int = 30,
        exclude: Iterable[str] = ("retweets", "replies"),
    ) -> list[dict[str, Any]]:
        """Search recent posts and return normalised post dicts.

        ``query`` is passed through to the API search grammar, so the caller owns
        its operators: the engine always appends ``-is:retweet`` and the
        ``from:``/``@``/``related:`` lanes build their own query strings here.
        ``start`` and ``end`` are ``YYYY-MM-DD`` bounds; they are widened to
        RFC 3339 because the API requires full timestamps.
        """
        if not query or not query.strip():
            raise BirdSearchError("bad-response", "search query is empty")

        params = {
            "query": query.strip(),
            "max_results": str(max(10, min(int(max_results), MAX_RESULTS_CEILING))),
            "tweet.fields": TWEET_FIELDS,
            "expansions": EXPANSIONS,
            "user.fields": USER_FIELDS,
        }
        for key, value in (("exclude", ",".join(exclude)),):
            if value:
                params[key] = value
        if start:
            params["start_time"] = f"{start}T00:00:00Z"
        if end:
            params["end_time"] = f"{end}T23:59:59Z"

        payload = self._with_retry("tweets/search/recent", params)
        users = _index_users(payload)
        tweets = payload.get("data") or []
        if not isinstance(tweets, list):
            return []

        posts: list[dict[str, Any]] = []
        for tweet in tweets:
            if not isinstance(tweet, Mapping):
                continue
            post = normalize_post(tweet, users)
            if post is not None:
                posts.append(post)
        return posts

    def lookup_posts(self, post_ids: Iterable[str]) -> list[dict[str, Any]]:
        """Fetch posts by id, in chunks the API accepts."""
        ids = [str(value).strip() for value in post_ids if str(value).strip()]
        if not ids:
            return []

        posts: list[dict[str, Any]] = []
        for start in range(0, len(ids), MAX_RESULTS_CEILING):
            chunk = ids[start : start + MAX_RESULTS_CEILING]
            payload = self._with_retry(
                "tweets",
                {
                    "ids": ",".join(chunk),
                    "tweet.fields": TWEET_FIELDS,
                    "expansions": EXPANSIONS,
                    "user.fields": USER_FIELDS,
                },
            )
            users = _index_users(payload)
            for tweet in payload.get("data") or []:
                if isinstance(tweet, Mapping):
                    post = normalize_post(tweet, users)
                    if post is not None:
                        posts.append(post)
        return posts

    def lookup_handles(self, handles: Iterable[str]) -> dict[str, str]:
        """Resolve usernames to user ids.

        Returns a mapping of handle to id for the ones the API knew about; an
        unknown handle is simply absent, which the engine reports as an
        unresolved handle rather than as a failure.
        """
        names = [name.strip().lstrip("@") for name in handles if name.strip()]
        if not names:
            return {}

        resolved: dict[str, str] = {}
        for start in range(0, len(names), MAX_RESULTS_CEILING):
            chunk = names[start : start + MAX_RESULTS_CEILING]
            payload = self._with_retry(
                "users/by", {"usernames": ",".join(chunk), "user.fields": USER_FIELDS}
            )
            for user in payload.get("data") or []:
                if isinstance(user, Mapping) and user.get("username") and user.get("id"):
                    resolved[str(user["username"])] = str(user["id"])
        return resolved
