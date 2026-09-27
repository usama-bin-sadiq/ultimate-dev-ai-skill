#!/usr/bin/env python3
"""Find overlapping capabilities in the catalogue and propose one winner per group.

Two skills that cover the same ground split the trigger signal: a request that
should reach one of them may reach both, and the user gets two half-processes
instead of one. That is the same failure the delegation reference calls
unnecessary delegation, applied at the catalogue level instead of the run level,
and it is the reason deduplication is a correctness concern rather than tidiness.

The grouping is computed, not declared. Names and descriptions are tokenised,
stopwords removed, and entries are clustered by Jaccard overlap on the surviving
terms. That is a proxy and is reported as one: two skills with different words for
the same judgement will not be grouped, and the report says so rather than
implying completeness.

Within a group the winner is chosen by stated criteria, in order:

  1. no disqualifier     a file carrying one of decision 0005's disqualifiers
                         cannot win, however good its judgement is
  2. tool-neutral        a capability requiring a specific CLI cannot be the
                         default in a runtime that may not have it
  3. substance           named failure modes, prohibitions, and thresholds
  4. length              longer, among equals, because it has more to say
  5. name                alphabetical, so the result does not depend on the
                         filesystem's ordering

Every loser is reported with the criterion that beat it, so a merge decision can
be reviewed rather than accepted.

Usage:
    python3 tools/dedupe-catalog.py                 # report
    python3 tools/dedupe-catalog.py --threshold 0.5 # looser grouping
    python3 tools/dedupe-catalog.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
INDEX = SKILL_ROOT / "catalog" / "INDEX.json"
REPORT = SKILL_ROOT / "catalog" / "OVERLAPS.json"

STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "in", "is", "it", "its", "of", "on", "or", "that", "the", "this",
    "to", "was", "were", "when", "which", "with", "you", "your", "not", "but",
    "if", "so", "than", "then", "there", "these", "they", "what", "will",
    "use", "using", "used", "into", "out", "up", "down", "can", "should",
    "would", "do", "does", "did", "been", "being", "more", "most", "other",
    "any", "all", "each", "own", "same", "such", "only", "also", "about",
    "after", "before", "over", "under", "between", "both", "because", "while",
    "how", "why", "who", "where", "agent", "skill", "task", "user", "users",
    "add", "added", "adding", "new", "one", "two", "get", "got", "make",
    "made", "need", "needs", "want", "work", "works", "way", "ways", "time",
}

TOKEN = re.compile(r"[a-z][a-z0-9-]{2,}")


def terms(entry: dict) -> set[str]:
    text = f"{entry['name']} {entry['description']}"
    return {t for t in TOKEN.findall(text.lower()) if t not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b)


def rank(entry: dict) -> tuple:
    """Sort key. Lower is better. The criteria in the order they are stated."""
    return (
        len(entry["disqualifiers"]),          # 1. no disqualifier
        len(entry["tool_bound"]),            # 2. tool-neutral
        -entry["substance"],                  # 3. substance
        -entry["lines"],                      # 4. length
        entry["name"].lower(),                # 5. stable
    )


def cluster(entries: list[dict], threshold: float) -> list[list[dict]]:
    """Greedy agglomerative clustering. Order is deterministic by name."""
    ordered = sorted(entries, key=lambda e: (e["name"].lower(), e["path"]))
    tcache = {e["path"]: terms(e) for e in ordered}
    groups: list[list[dict]] = []
    for e in ordered:
        placed = False
        for g in groups:
            # Compare against the group's current winner, not every member, so a
            # group does not grow by chaining through weak similarity.
            if jaccard(tcache[e["path"]], tcache[g[0]["path"]]) >= threshold:
                g.append(e)
                placed = True
                break
        if not placed:
            groups.append([e])
    return [g for g in groups if len(g) > 1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--threshold", type=float, default=0.35)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-group", type=int, default=2)
    args = ap.parse_args()

    if not INDEX.is_file():
        print(f"error: {INDEX} not found; run tools/index-catalog.py first",
              file=sys.stderr)
        return 2
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    entries = data["entries"]
    if not entries:
        print("error: index is empty", file=sys.stderr)
        return 2

    groups = [g for g in cluster(entries, args.threshold)
              if len(g) >= args.min_group]
    groups.sort(key=lambda g: (-len(g), rank(g[0])))

    def cohesion(g: list[dict]) -> float:
        """Mean pairwise similarity inside a group.

        A group whose members are near-identical is not a set of overlapping
        capabilities that needs a winner chosen -- it is one file committed under
        many names, and the correct action is to keep one or keep none. The
        732-member Composio group is the case in point: raising the threshold
        from 0.35 to 0.65 barely shrank it, because the members really are the
        same text with a noun substituted. Naming a "winner" there would be a
        number that means nothing.
        """
        if len(g) < 2:
            return 0.0
        t = {e["path"]: terms(e) for e in g}
        pairs = [(i, j) for i in range(len(g)) for j in range(i + 1, len(g))]
        sample = pairs[:: max(1, len(pairs) // 60)][:60]
        return sum(jaccard(t[g[i]["path"]], t[g[j]["path"]])
                   for i, j in sample) / max(1, len(sample))

    measured = [{"members": g, "size": len(g),
                 "cohesion": round(cohesion(g), 3)} for g in groups]
    for m in measured:
        m["template_family"] = m["size"] >= 5 and m["cohesion"] >= 0.65

    out = {
        "disclaimer": (
            "Grouping is Jaccard overlap on name and description tokens, a "
            "proxy. Two capabilities expressing one judgement in different words "
            "will not be grouped here. tool_bound and disqualifiers are "
            "pattern-detected, not read."
        ),
        "threshold": args.threshold,
        "entries_considered": len(entries),
        "groups": [],
    }
    for m in measured:
        g = m["members"]
        fam = m["template_family"]
        ranked = sorted(g, key=rank)
        win = ranked[0]
        out["groups"].append({
            "winner": None if fam else win["name"],
            "winner_path": None if fam else win["path"],
            "action": ("template-family: keep one or keep none, the members are "
                       "one file under many names" if fam else "pick-winner"),
            "cohesion": m["cohesion"],
            "size": len(g),
            "members": [
                {
                    "name": e["name"],
                    "path": e["path"],
                    "lines": e["lines"],
                    "substance": e["substance"],
                    "tool_bound": e["tool_bound"],
                    "disqualifiers": e["disqualifiers"],
                    "beat_by": (
                        "disqualifier" if e["disqualifiers"] else
                        "tool-binding" if e["tool_bound"] else
                        "substance" if e["substance"] < win["substance"] else
                        "length" if e["lines"] < win["lines"] else
                        "name-order"),
                }
                for e in ranked
            ],
        })

    REPORT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    covered = sum(g["size"] for g in out["groups"])
    print(f"  {len(entries)} entries, threshold {args.threshold}")
    print(f"  {len(out['groups'])} overlapping group(s) covering {covered} entries\n")
    shown = 0
    for g in out["groups"]:
        if g["action"].startswith("template-family") and shown:
            continue
        shown += 1
        if shown > 16: break
        if g["action"].startswith("template-family"):
            print(f"  [{g['size']:4}] TEMPLATE FAMILY  cohesion={g['cohesion']}  "
                  f"-> {g['action'].split(':')[1]}")
            names = ", ".join(m["name"][:18] for m in g["members"][:4])
            print(f"        e.g. {names}, and {g['size'] - 4} more")
            print()
            continue
        print(f"  [{g['size']:3}] winner: {g['winner']}  "
              f"(cohesion {g['cohesion']})")
        for m in g["members"][1:6]:
            flags = []
            if m["disqualifiers"]:
                flags.append("DISQ:" + ",".join(m["disqualifiers"])[:28])
            if m["tool_bound"]:
                flags.append("tools:" + ",".join(m["tool_bound"])[:22])
            print(f"        - {m['name'][:44]:44} {m['lines']:5}ln "
                  f"beat by {m['beat_by']:12} {' '.join(flags)}")
        if g["size"] > 7:
            print(f"        ... and {g['size'] - 7} more")
        print()
    if len(out["groups"]) > 18:
        print(f"  ... and {len(out['groups']) - 18} more groups")
    print(f"  report: {REPORT.relative_to(SKILL_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
