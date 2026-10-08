#!/usr/bin/env python3
"""Routing eval: does the routing index put the right skill on top?

Input: evals/routing/queries.jsonl
  {"query": "...", "expect": ["skill"], "not_expect": ["skill"]}

Scorer: score = 3*name-token-overlap + 2*when-clause-overlap + 1*description-token-overlap
against the query's token set. Reports Hit@1, MRR@10, R@5, and negative
violations (a `not_expect` name at rank 1).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "skills" / "_routing-index.json"
QUERIES = ROOT / "evals" / "routing" / "queries.jsonl"
HELDOUT = ROOT / "evals" / "routing" / "heldout.jsonl"

STOP = set("a an the and or of in on for to from with via this that it its is are be by as i you not do does don't no nor when use used using user ask wants want should can could will each other more get got that then than also such any all me my we our".split())

def toks(text):
    # Hyphens are separators, not part of a token.
    #
    # The pattern `[a-z0-9][a-z0-9-]+` treats "omnisend-automation" as one
    # token. A query of "omnisend automation" tokenises to {omnisend,
    # automation}, so the name contributed nothing to the very query it exists
    # to answer -- and the strongest signal in the scorer, 3x name overlap,
    # was structurally unreachable for every hyphenated skill. Most of this
    # corpus is hyphenated, which is why Hit@1 sat at 23%.
    #
    # Splitting first costs nothing: a hyphen is never meaningful inside a
    # word in a natural-language query, and it restores the name weight the
    # scorer already claims to give it.
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]*", text.lower().replace("-", " ").replace("_", " "))
            if t not in STOP and len(t) > 2}

def body_tokens(name):
    p = ROOT / "skills" / name / "SKILL.md"
    if not p.is_file():
        p = ROOT / "agents" / f"{name}.md"
    if not p.is_file():
        return set()
    return toks(p.read_text(encoding="utf-8", errors="replace")[:4000])

def score_set(entries, qs):
    hits, mrr, recall, neg = 0, 0.0, 0, 0
    for q in qs:
        qt = toks(q["query"])
        scored = []
        for e in entries:
            if e.get("family") == "composio":
                # only score composio stubs when the query names its product.
                # The product is every non-generic segment of the name, not the
                # first: "the-odds-api-automation" reduced to "the", a
                # stopword no query contains, so the gate excluded the correct
                # answer for that entry and the miss was invisible. Kept in
                # step with route.py; see product_tokens there.
                generic = {"api", "automation", "automate", "mcp", "tools", "tool",
                           "cli", "sdk", "connector", "integration", "plugin", "agent"}
                product = {seg for seg in e["name"].lower().split("-")
                           if len(seg) > 2 and seg not in STOP and seg not in generic}
                if not (qt & product) and "automate" not in qt and "composio" not in qt:
                    continue
            bt = body_tokens(e["name"])
            s = (3 * len(qt & toks(e["name"]))
                 + 2 * len(qt & toks(" ".join(e["when"])))
                 + 1 * len(qt & toks(e["description"]))
                 + 2 * len(qt & bt))
            scored.append((s, e["name"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        top5 = [n for _, n in scored[:5]]
        if scored and scored[0][0] > 0:
            if scored[0][1] in q["expect"]:
                hits += 1
            for r, (_, n) in enumerate(scored[:10], 1):
                if n in q["expect"]:
                    mrr += 1.0 / r
                    break
            if any(n in q["expect"] for n in top5):
                recall += 1
        if scored and scored[0][0] > 0 and scored[0][1] in q.get("not_expect", []):
            neg += 1
    return hits, mrr, recall, neg, len(qs)


def report(label, path):
    if not path.is_file():
        print(f"{label}: MISSING ({path})")
        return None
    qs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    hits, mrr, recall, neg, n = score_set(entries, qs)
    print(f"{label}")
    print(f"  queries:  {n}")
    print(f"  Hit@1:    {hits}/{n} ({hits/n*100:.0f}%)")
    print(f"  MRR@10:   {mrr/n:.3f}")
    print(f"  R@5:      {recall}/{n} ({recall/n*100:.0f}%)")
    print(f"  negative violations (not_expect at #1): {neg}")
    return hits / n, neg


def main():
    global entries
    entries = json.loads(INDEX.read_text())["entries"]

    print("== tuning corpus ==")
    tuned = report("queries.jsonl (used to develop the scorer)", QUERIES)
    print()
    print("== held out ==")
    # Written without looking at what the scorer returns, and never tuned
    # against. It exists because the tuning number alone is misleading: a
    # scorer can be walked to 100% on a fixed 60-query set without improving
    # routing at all. The gap between the two is the honest measure, and it
    # was 18 points when this file was added.
    held = report("heldout.jsonl (written after the scorer was frozen)", HELDOUT)
    print()
    if held is None or tuned is None:
        return 1
    if held[1] > 0:
        print("a held-out query put a not_expect skill at rank 1")
        return 1
    # Floors, not targets. Set where the number actually is, so a regression
    # is loud and an improvement is not blocked by a bar it has to be argued
    # past.
    if tuned[0] < 0.80:
        print(f"tuning Hit@1 fell to {tuned[0]*100:.0f}% (floor 80%)")
        return 1
    if held[0] < 0.65:
        print(f"held-out Hit@1 fell to {held[0]*100:.0f}% (floor 65%)")
        return 1
    return 0

if __name__ == "__main__":
    main()
