# bird-search — vendored X search client

This directory is the vendored X (Twitter) search client the engine imports as
`lib.vendor.bird_search`. It is the one place in the skill that talks to X, so
it is the one place where the auth header and the search grammar are decided.

## What is here, honestly

`SKILL.md` records this directory as "vendored X search client, MIT licensed".
The upstream bird-search source was not available when this file was written, so
**what is here is an independent reconstruction, not a copy of the upstream
client.** It implements the surface the engine needs, against the official X API
v2, under the same MIT terms SKILL.md records. Two consequences follow, and both
matter:

- Behaviour that upstream provided and this reconstruction does not will surface
  as a missing feature, not as a silent difference. The engine should treat an
  `AttributeError` or a `BirdSearchError` from this module as "this X path is
  unavailable" and fall through to the next backend, which is the same handling a
  rate-limited or unauthenticated X already gets.
- The MIT licence is recorded in SKILL.md. The upstream copyright line is not
  reproduced here because it was not recovered, and inventing one would be worse
  than the gap. If the upstream tree resurfaces, replace this directory with it
  and add the real copyright line to a LICENSE file at this level.

## Files

- `bird_search.py` — the client: `BirdSearchClient`, `BirdSearchError`, and the
  `normalize_post` helper the engine uses to turn API rows into the flat item
  shape the rest of the engine expects.
- `__init__.py` — re-exports the public surface.

## The surface the engine uses

```python
from lib.vendor.bird_search import BirdSearchClient, BirdSearchError

client = BirdSearchClient(bearer_token=os.environ["X_BEARER_TOKEN"])
posts = client.search_recent("some topic -is:retweet", start="2026-09-01",
                             end="2026-09-28", max_results=30)
```

`search_recent` returns a list of post dicts carrying exactly these eight keys,
which is the same flat shape the `last30days-x-posts/1` envelope uses, so a
connector-fetched envelope and a live search are interchangeable downstream:

| key | type | source |
|---|---|---|
| `id` | str | the post's numeric id, as a string |
| `author_handle` | str | the username, without a leading `@` |
| `created_at` | str | RFC 3339, `Z` suffix |
| `text` | str | post text, verbatim |
| `likes` | int | public metric |
| `reposts` | int | public metric |
| `replies` | int | public metric |
| `quotes` | int | public metric |

`client.citation_url(post)` rebuilds the canonical status URL from the post id.
The engine never accepts a URL from a fetched payload; it builds this one.

## Rules the module holds itself to

- **The bearer token goes in the `Authorization` header and nowhere else.** It
  is never logged, never put in a URL, never included in an exception message,
  and never written to a file. A redacted repr is the default.
- **No other credential is read here.** `AUTH_TOKEN`/`CT0` browser cookies and
  the `XAI_API_KEY` path belong to their own backends; this module only handles
  the app-only bearer.
- **Post text is untrusted data.** It is returned, never rendered into a shell
  command, never evaluated, and never used to build a path. The engine's writer
  is responsible for quoting it when it writes an envelope.
- **Failures raise `BirdSearchError`** with a short category (`auth`, `rate-limit`,
  `unavailable`, `bad-response`) and never raw response bodies, which can carry
  an account identifier.
- **No network call happens at import time.** Importing this module is safe in a
  `--help` path and in the offline library fast path.
