#!/usr/bin/env python3
"""Build a routing index: per-capability metadata extracted from frontmatter.

The SkillRouter benchmark (2026) shows routing on descriptions alone drops
accuracy 37-44pp. The fix this applies: every skill and agent gets its
`use when` triggers and explicit negatives lifted out of its description into
a single searchable file the router can read instead of grepping 2,088 files.

Output: ultimate-dev/skills/_routing-index.json
Also prints overlap candidates (two capabilities sharing most of their
trigger keywords) for human disambiguation.
"""
import json, re, sys, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
OUT = ROOT / "skills" / "_routing-index.json"

STOP = set("""a an the and or of in on for to from with via this that it its is are be by as i you
not do does don't no nor when use used using user ask asks asked mentions mention mentioning
wants want should can could will would each other more get got that then than also such any all
me my we our they them their give given take takes one two first last over under about around
before after during while between across through into onto out up down off again further
""".split())

def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.+?)\n---\n", text, re.S)
    if not m:
        return {}
    block = m.group(1)
    name = re.search(r"^name:\s*(.+)$", block, re.M)
    desc = re.search(r'^description:\s*(.+)$', block, re.M)
    return {"name": name.group(1).strip().strip('"') if name else "",
            "description": desc.group(1).strip().strip('"') if desc else ""}

def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]+", text.lower())
            if t not in STOP and len(t) > 2}

WHEN_HINTS = ("use when", "triggers", "use for", "invoke", "activate", "when the user",
              "when a user", "whenever", "apply", "handles", "covers")
NOT_HINTS = ("not for", "do not", "don't", "never", "must not", "excludes")

def split_clauses(desc: str):
    # descriptions are sentences; classify each clause
    clauses = re.split(r"(?<=[.!?])\s+|;\s+|,\s+(?=use |trigger|not |when |do )", desc)
    when, neg, what = [], [], []
    for c in clauses:
        low = c.lower()
        if any(h in low for h in NOT_HINTS) or re.search(r"\bnot\b", low):
            neg.append(c.strip())
        elif any(h in low for h in WHEN_HINTS):
            when.append(c.strip())
        else:
            what.append(c.strip())
    return what, when, neg

def main():
    entries = []
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        meta = frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        if not meta.get("name"):
            continue
        what, when, neg = split_clauses(meta["description"])
        entries.append({
            "name": meta["name"],
            "kind": "skill",
            "family": "composio" if re.search(r"Automate .+ via Rube", meta["description"]) else "",
            "path": f"skills/{skill_md.parent.name}/SKILL.md",
            "description": meta["description"],
            "what": what[0] if what else "",
            "when": when,
            "not": neg,
            "keywords": sorted(tokens(" ".join(when))) if when else sorted(tokens(meta["description"])),
        })
    for role in sorted(AGENTS.glob("*.md")):
        text = role.read_text(encoding="utf-8", errors="replace")
        meta = frontmatter(text)
        if not meta.get("name"):
            # agents use 'name:' frontmatter too; fall back to header
            m = re.search(r"^name:\s*(.+)$", text, re.M)
            if not m:
                continue
            meta = {"name": m.group(1).strip(), "description": ""}
        what, when, neg = split_clauses(meta["description"])
        entries.append({
            "name": meta["name"],
            "kind": "agent",
            "path": f"agents/{role.name}",
            "description": meta["description"],
            "what": what[0] if what else "",
            "when": when,
            "not": neg,
            "keywords": sorted(tokens(" ".join(when))) if when else sorted(tokens(meta["description"])),
        })

    payload = json.dumps({"count": len(entries), "entries": entries}, indent=1)
    if sys.argv[-1] == "--check":
        if OUT.is_file() and OUT.read_text(encoding="utf-8", errors="replace") == payload:
            print("routing index is current")
            sys.exit(0)
        print("routing index is STALE: rebuild with `python3 tools/build-routing-index.py`")
        sys.exit(1)
    OUT.write_text(payload, encoding="utf-8")

    # overlap candidates: Jaccard over keywords, thresholded, same-domain-ish (name token overlap helps too)
    by_name = {}
    templates = set()
    for e in entries:
        by_name[e["name"]] = set(e["keywords"])
        if re.search(r"Automate .+ via Rube", e["description"]):
            templates.add(e["name"])
    names = sorted(by_name)
    candidates = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = by_name[names[i]], by_name[names[j]]
            if not a or not b:
                continue
            if names[i] in templates and names[j] in templates:
                continue  # one template family; the merge-automation-pairs tool owns it
            overlap = len(a & b) / len(a | b)
            if overlap >= 0.55:
                candidates.append((overlap, names[i], names[j]))
    candidates.sort(reverse=True)
    print(f"indexed {len(entries)} capabilities -> {OUT.relative_to(ROOT.parent)}")
    print(f"overlap candidates (>=0.55 keyword Jaccard): {len(candidates)}")
    for o, a, b in candidates[:25]:
        print(f"  {o:.2f}  {a}  <->  {b}")

    if "--overlap-fail" in sys.argv:
        idx = sys.argv.index("--overlap-fail")
        try:
            max_pairs = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            sys.exit(2)
        if len(candidates) > max_pairs:
            print(f"FAIL: {len(candidates)} overlap pairs exceeds allowed {max_pairs}")
            sys.exit(1)
        print(f"overlap pairs within budget ({len(candidates)} <= {max_pairs})")

if __name__ == "__main__":
    main()
