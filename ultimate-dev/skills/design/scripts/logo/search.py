#!/usr/bin/env python3
"""Search the logo catalogue, or write a design brief from a description.

What it does
------------
Runs a BM25 search over one of three domains — style, colour palette, industry
— and prints the ranked hits. With ``--design-brief`` it assembles a short brief a
human reviews before anything is generated.

The catalogue and the ranking live in ``core.py`` next to this file, so the
prompt builder and the search index cannot drift apart.

Usage
-----
    python3 scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"
    python3 scripts/logo/search.py "minimalist clean" --domain style
    python3 scripts/logo/search.py "tech professional" --domain color
    python3 scripts/logo/search.py "healthcare medical" --domain industry
    python3 scripts/logo/search.py --list

Exit codes: 0 hits found, 1 nothing found, 2 bad input.

Provenance
----------
Reconstructed to match the invocations and flags in this skill's SKILL.md and
``references/logo-design.md``. The catalogue contents and the BM25 ranking are
this pair of files' own work.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import (  # noqa: E402
    DOMAINS,
    INDUSTRIES,
    PALETTES,
    STYLES,
    build_design_brief,
    build_prompt,
    search_domain,
)


def show_hits(domain: str, hits: list[dict], verbose: bool) -> None:
    """Print ranked hits with enough context to choose between them."""
    canonical = {"color": "color", "palette": "color"}.get(domain, domain)
    print(f"{canonical} matches ({len(hits)}):")
    for position, hit in enumerate(hits, start=1):
        entry = hit["entry"]
        print(f"\n  {position}. {hit['name']}  (score {hit['score']})")
        print(f"     fits: {entry.get('best_for', '')}")
        if canonical == "color":
            roles = "  ".join(f"{role}={value}" for role, value in entry["colors"].items())
            print(f"     roles: {roles}")
            print(f"     note: {entry['note']}")
        elif canonical == "industry":
            print(f"     caution: {entry['caution']}")
        if verbose:
            detail = entry.get("prompt") or entry.get("note") or ""
            print(f"     detail: {detail}")
    print()


def list_all() -> None:
    print(f"styles ({len(STYLES)}):")
    for name in sorted(STYLES):
        print(f"  {name:<20} {STYLES[name]['best_for']}")
    print(f"\ncolour palettes ({len(PALETTES)}):")
    for name in sorted(PALETTES):
        print(f"  {name:<20} {PALETTES[name]['best_for']}")
    print(f"\nindustries ({len(INDUSTRIES)}):")
    for name in sorted(INDUSTRIES):
        print(f"  {name:<20} {INDUSTRIES[name]['best_for']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search logo styles, colour palettes, and industry guides; build a design brief.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="free-text description of the brand or mood")
    parser.add_argument(
        "--domain", choices=(*DOMAINS, "palette"),
        default=None,
        help="restrict the search to one domain; omit to search all three",
    )
    parser.add_argument("--design-brief", action="store_true", help="print a design brief instead of hits")
    parser.add_argument("-p", "--brand", default=None, help="brand name, used in the brief and prompt")
    parser.add_argument("-b", "--limit", type=int, default=5, help="hits per domain")
    parser.add_argument("--list", action="store_true", help="list the whole catalogue and exit")
    parser.add_argument("--prompt", action="store_true", help="also print the assembled generation prompt")
    parser.add_argument("-v", "--verbose", action="store_true", help="print the full prompt fragment per hit")
    args = parser.parse_args(argv)

    if args.list:
        list_all()
        return 0
    if not args.query.strip():
        parser.error("give a query, or --list to see the whole catalogue")
    if args.limit < 1:
        raise SystemExit("error: --limit must be at least 1")

    if args.design_brief:
        brand = args.brand
        if not brand:
            raise SystemExit(
                "error: --design-brief needs a brand name: -p \"BrandName\". A brief for an "
                "unnamed brand is not a brief."
            )
        brief = build_design_brief(brand, args.query)
        print(brief, end="")
        if args.prompt:
            style = search_domain("style", args.query, limit=1)[0]["name"]
            palette = search_domain("color", args.query, limit=1)[0]["name"]
            industry = search_domain("industry", args.query, limit=1)[0]["name"]
            print("\n## Assembled generation prompt\n")
            print(build_prompt(brand, style, palette, industry))
        return 0

    domains = [args.domain] if args.domain else list(DOMAINS)
    total = 0
    for domain in domains:
        hits = search_domain(domain, args.query, limit=args.limit)
        if not hits:
            print(f"{domain}: nothing matched {args.query!r}\n")
            continue
        show_hits(domain, hits, args.verbose)
        total += len(hits)

    if args.prompt:
        style = search_domain("style", args.query, limit=1)[0]["name"]
        palette = search_domain("color", args.query, limit=1)[0]["name"]
        industry = search_domain("industry", args.query, limit=1)[0]["name"]
        print("## Assembled generation prompt\n")
        print(build_prompt(args.brand, style, palette, industry, provider="gemini"))

    if total == 0:
        print("Nothing matched. Try fewer, more general words, or run with --list.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
