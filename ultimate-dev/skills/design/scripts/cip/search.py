#!/usr/bin/env python3
"""Search the CIP catalogue, or write a corporate identity program brief.

What it does
------------
Runs a BM25 search over one of four domains — deliverable, style, industry,
mockup — and prints the ranked hits. With ``--cip-brief`` it assembles the brief a
human approves before any mockup is generated.

The catalogue lives in ``core.py`` next to this file, shared with
``generate.py`` and ``render-html.py``.

Usage
-----
    python3 scripts/cip/search.py "tech startup" --cip-brief -b "BrandName"
    python3 scripts/cip/search.py "business card letterhead" --domain deliverable
    python3 scripts/cip/search.py "luxury premium elegant" --domain style
    python3 scripts/cip/search.py "hospitality hotel" --domain industry
    python3 scripts/cip/search.py "office reception" --domain mockup
    python3 scripts/cip/search.py --list

Exit codes: 0 hits found, 1 nothing found, 2 bad input.

Provenance
----------
Reconstructed to match the invocations in this skill's SKILL.md and
``references/cip-design.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import (  # noqa: E402
    DELIVERABLES,
    DOMAINS,
    INDUSTRIES,
    MOCKUPS,
    STYLES,
    build_cip_brief,
    build_mockup_prompt,
    deliverables_for_set,
    search_domain,
)

DOMAIN_KEYS = {"deliverable": "deliverable", "style": "style", "industry": "industry", "mockup": "mockup"}


def show_hits(domain: str, hits: list[dict], verbose: bool) -> None:
    canonical = DOMAIN_KEYS[domain]
    print(f"{canonical} matches ({len(hits)}):")
    for position, hit in enumerate(hits, start=1):
        entry = hit["entry"]
        print(f"\n  {position}. {hit['name']}  (score {hit['score']})")
        print(f"     fits: {entry.get('best_for', '')}")
        if canonical == "deliverable":
            print(f"     group: {entry['group']}")
            print(f"     spec:  {entry['spec']}")
        elif canonical == "industry":
            print(f"     priorities: {', '.join(entry['priorities'])}")
            print(f"     caution: {entry['caution']}")
        elif canonical == "mockup":
            print(f"     setting: {entry['setting']}")
            print(f"     camera: {entry['camera']}")
        if verbose:
            if canonical == "style":
                for key in ("colors", "typography", "materials", "finishes"):
                    print(f"     {key}: {entry[key]}")
    print()


def list_all() -> None:
    print(f"deliverables ({len(DELIVERABLES)}):")
    for group in sorted({entry["group"] for entry in DELIVERABLES.values()}):
        names = sorted(name for name, entry in DELIVERABLES.items() if entry["group"] == group)
        print(f"  {group}:")
        for name in names:
            print(f"    {name:<24} {DELIVERABLES[name]['best_for']}")
    print(f"\nstyles ({len(STYLES)}):")
    for name in sorted(STYLES):
        print(f"  {name:<24} {STYLES[name]['best_for']}")
    print(f"\nindustries ({len(INDUSTRIES)}):")
    for name in sorted(INDUSTRIES):
        print(f"  {name:<24} {INDUSTRIES[name]['best_for']}")
    print(f"\nmockups ({len(MOCKUPS)}):")
    for name in sorted(MOCKUPS):
        print(f"  {name:<24} {MOCKUPS[name]['best_for']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search CIP deliverables, styles, industries, and mockup settings; build a CIP brief.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="", help="free-text description of the brand or the item")
    parser.add_argument("--domain", choices=DOMAINS, default=None,
                        help="restrict the search to one domain; omit to search all four")
    parser.add_argument("--cip-brief", action="store_true", help="print a CIP brief instead of hits")
    parser.add_argument("-b", "--brand", default=None, help="brand name, used in the brief")
    parser.add_argument("-l", "--limit", type=int, default=5, help="hits per domain")
    parser.add_argument("--list", action="store_true", help="list the whole catalogue and exit")
    parser.add_argument("--prompt", action="store_true", help="also print an assembled mockup prompt")
    parser.add_argument("-v", "--verbose", action="store_true", help="print the full entry per hit")
    args = parser.parse_args(argv)

    if args.list:
        list_all()
        return 0
    if not args.query.strip():
        parser.error("give a query, or --list to see the whole catalogue")
    if args.limit < 1:
        raise SystemExit("error: --limit must be at least 1")

    if args.cip_brief:
        brand = args.brand
        if not brand:
            raise SystemExit("error: --cip-brief needs a brand name: -b \"BrandName\"")
        print(build_cip_brief(brand, args.query), end="")
        if args.prompt:
            print("\n## Sample mockup prompt\n")
            print(build_mockup_prompt(brand, "business-card", None, None, None))
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
        if not args.brand:
            raise SystemExit("error: --prompt needs a brand name: -b \"BrandName\"")
        print("## Sample mockup prompt\n")
        print(build_mockup_prompt(args.brand, "business-card", None, None, None))

    if args.domain == "industry" and args.prompt:
        industry = search_domain("industry", args.query, limit=1)[0]["name"]
        print(f"\n## Deliverables a full set would cover for {industry}\n")
        for name in deliverables_for_set(industry)[:12]:
            print(f"- {name}: {DELIVERABLES[name]['best_for']}")

    if total == 0:
        print("Nothing matched. Try fewer, more general words, or run with --list.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
