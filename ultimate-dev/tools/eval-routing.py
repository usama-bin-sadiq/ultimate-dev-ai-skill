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

STOP = set("a an the and or of in on for to from with via this that it its is are be by as i you not do does don't no nor when use used using user ask wants want should can could will each other more get got that then than also such any all me my we our".split())

def toks(text):
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]+", text.lower()) if t not in STOP and len(t) > 2}

def body_tokens(name):
    p = ROOT / "skills" / name / "SKILL.md"
    if not p.is_file():
        p = ROOT / "agents" / f"{name}.md"
    if not p.is_file():
        return set()
    return toks(p.read_text(encoding="utf-8", errors="replace")[:4000])

def main():
    idx = json.loads(INDEX.read_text())
    entries = idx["entries"]
    qs = [json.loads(l) for l in QUERIES.read_text().splitlines() if l.strip()]
    hits, mrr, recall, neg_violations = 0, 0.0, 0, 0
    for q in qs:
        qt = toks(q["query"])
        scored = []
        for e in entries:
            if e.get("family") == "composio":
                # only score composio stubs when the query names its product
                product = e["name"].split("-")[0]
                if product not in qt and "automate" not in qt and "composio" not in qt:
                    continue
            bt = body_tokens(e["name"])
            s = (3 * len(qt & toks(e["name"]))
                 + 2 * len(qt & toks(" ".join(e["when"])))
                 + 1 * len(qt & toks(e["description"]))
                 + 2 * len(qt & bt))
            scored.append((s, e["name"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        top5 = [n for _, n in scored[:5]]
        top10 = [n for _, n in scored[:10]]
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
            neg_violations += 1
    n = len(qs)
    print(f"queries: {n}")
    print(f"Hit@1:  {hits}/{n} ({hits/n*100:.0f}%)")
    print(f"MRR@10: {mrr/n:.3f}")
    print(f"R@5:    {recall}/{n} ({recall/n*100:.0f}%)")
    print(f"negative violations (not_expect at #1): {neg_violations}")
    if neg_violations or hits/n < 0.5:
        sys.exit(1)

if __name__ == "__main__":
    main()
