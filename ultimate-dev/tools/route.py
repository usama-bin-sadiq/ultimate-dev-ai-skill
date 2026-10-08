#!/usr/bin/env python3
"""Route a task to the capabilities that claim it, ranked, with their exclusions.

There was no dispatcher. The routing index existed, was rebuilt and checked in
CI, and was read by exactly two things: the builder that writes it and the eval
that scores it. Nothing executed a route, so "route this task to the right
skill" was decided by whoever was reading -- unrepeatable, unmeasured, and
invisible to every check in the pipeline. Hit@1 measured 23%, and the cause was
a tokenizer bug in the scorer, not in the index: the index was fine.

This is the dispatcher. One query in, a ranked shortlist out, and each candidate
carries its own `not` exclusions so the reader can see which lookalikes the
corpus already ruled out.

    python3 tools/route.py "add oauth to my api"
    python3 tools/route.py "audit the release pipeline" --kind agent
    python3 tools/route.py "edit a photo" --json
    python3 tools/route.py "ship it" --limit 10

Scoring is deliberately the same weighting eval-routing.py measures, so a
change to one is a change to both and the eval keeps its meaning:

    3x name tokens + 2x `when` clauses + 1x description + 2x body

The body term reads each file on every call, which is why the accurate-but-slow
path is also the default: a few seconds over the whole corpus and no index
staleness.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "skills" / "_routing-index.json"

STOP = set(
    "a an the and or of in on for to from with via this that it its is are be by as "
    "i you not do does don't no nor when use used using user ask wants want should "
    "can could will each other more get got that then than also such any all me my "
    "we our".split()
)

WEIGHTS = {"name": 3, "when": 2, "body": 2, "description": 1}


def toks(text):
    """Tokenise for overlap.

    Hyphens and underscores are separators. Treating "omnisend-automation" as
    one token made the strongest signal in the scorer unreachable for most of
    the corpus, and cost 64 points of Hit@1. The comment in eval-routing.py
    explains it at length; this is the same rule so the two agree.
    """
    cleaned = text.lower().replace("-", " ").replace("_", " ")
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]*", cleaned)
            if t not in STOP and len(t) > 2}


def entry_path(e):
    p = ROOT / e["path"]
    return p if p.is_file() else None


def score_entry(e, qt, cache):
    """Weighted overlap. Returns (score, breakdown), or None to exclude."""
    # Composio stubs are one per SaaS product and their descriptions are
    # near-identical, so 742 of them will out-score a real skill on any query
    # mentioning a word they all share. Require the query to name the product.
    if e.get("family") == "composio":
        product = e["name"].split("-")[0]
        if product not in qt and "automate" not in qt and "composio" not in qt:
            return None

    path = entry_path(e)
    if path is None:
        return None

    key = str(path)
    if key not in cache:
        cache[key] = toks(path.read_text(encoding="utf-8", errors="replace")[:4000])

    name_t = toks(e["name"])
    when_t = toks(" ".join(e.get("when") or []))
    desc_t = toks(e.get("description") or "") | toks(e.get("what") or "")
    body_t = cache[key]

    parts = {
        "name": WEIGHTS["name"] * len(qt & name_t),
        "when": WEIGHTS["when"] * len(qt & when_t),
        "body": WEIGHTS["body"] * len(qt & body_t),
        "description": WEIGHTS["description"] * len(qt & desc_t),
    }
    total = sum(parts.values())
    if total <= 0:
        return None
    return total, parts


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("task", help="what you are trying to do, in plain language")
    ap.add_argument("--limit", type=int, default=5, help="candidates to show (default 5)")
    ap.add_argument("--kind", choices=["skill", "agent"],
                    help="restrict to one kind; by default both are ranked together")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--min-score", type=int, default=1,
                    help="drop candidates scoring below this (default 1)")
    args = ap.parse_args()

    if not INDEX.is_file():
        print(f"{INDEX} is missing; rebuild with tools/build-routing-index.py",
              file=sys.stderr)
        return 1

    entries = json.loads(INDEX.read_text(encoding="utf-8"))["entries"]
    if args.kind:
        entries = [e for e in entries if e.get("kind", "skill") == args.kind]

    qt = toks(args.task)
    if not qt:
        print("task has no searchable tokens after stopword removal", file=sys.stderr)
        return 1

    cache, scored = {}, []
    for e in entries:
        r = score_entry(e, qt, cache)
        if r is None:
            continue
        total, parts = r
        if total < args.min_score:
            continue
        scored.append((total, e["name"], e, parts))

    # Ties broken by name so the same query always returns the same order.
    scored.sort(key=lambda x: (-x[0], x[1]))
    top = scored[: args.limit]

    # Checked before the JSON branch, not after. It used to sit below, so
    # `--json` returned 0 for a query that matched nothing, while the plain
    # form exited 1 for the same query. A caller asking for machine-readable
    # output is the one most likely to act on it without reading prose, so the
    # empty case has to be non-zero in both modes.
    if not top:
        if args.json:
            print(json.dumps({
                "task": args.task,
                "tokens": sorted(qt),
                "considered": len(entries),
                "scored_above_zero": 0,
                "candidates": [],
                "error": "nothing in the index matches; the capability does not "
                         "exist yet -- say so rather than forcing a fit",
            }, indent=2))
        else:
            print(f"nothing in the index matches {args.task!r}")
            print("the capability does not exist yet -- say so rather than "
                  "forcing a fit")
        return 1

    if args.json:
        print(json.dumps({
            "task": args.task,
            "tokens": sorted(qt),
            "considered": len(entries),
            "scored_above_zero": len(scored),
            "candidates": [
                {
                    "name": e["name"],
                    "kind": e.get("kind", "skill"),
                    "path": e["path"],
                    "score": total,
                    "breakdown": parts,
                    "what": e.get("what") or e.get("description", ""),
                    "when": e.get("when") or [],
                    "not": e.get("not") or [],
                    "family": e.get("family"),
                }
                for total, _, e, parts in top
            ],
        }, indent=2))
        return 0

    print(f"task: {args.task}")
    print(f"tokens: {', '.join(sorted(qt))}")
    print(f"ranked {len(scored)} of {len(entries)} entries\n")

    for i, (total, name, e, parts) in enumerate(top, 1):
        print(f"{i}. {name}  [{e.get('kind', 'skill')}]  score {total}")
        hit = {k: v for k, v in parts.items() if v}
        if hit:
            print("   matched: " + ", ".join(f"{k} {v}" for k, v in sorted(hit.items())))
        print(f"   path:    {e['path']}")
        what = (e.get("what") or e.get("description") or "").strip().splitlines()
        if what:
            print(f"   what:    {what[0][:150]}")
        for w in (e.get("when") or [])[:2]:
            print(f"   when:    {w[:150]}")
        if e.get("not"):
            print(f"   NOT for: {'; '.join(e['not'])[:200]}")
        print()

    print("A score is a starting point, not a decision. Read the candidate's")
    print("body, honour its `not` list, and if the top few all look wrong say")
    print("nothing matches rather than picking the least bad.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
