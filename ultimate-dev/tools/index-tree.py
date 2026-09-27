#!/usr/bin/env python3
"""Index the distributed capability tree so it can be found, not just stored.

Copying 2,882 capabilities into the tree made them present. It did not make them
usable: a file nothing can find is not a capability, it is disk. The kernel names
nineteen of them and has no index to the rest, so every other one is invisible
to the agent that is supposed to route to it.

This builds the index that makes the rest reachable, and it is deliberately
searchable rather than browsable. A catalogue of 2,882 entries printed into a
context window is worse than no catalogue, because it crowds out the task. So
this writes a compact grouped index for the model to read, plus a machine-readable
one for tooling, and the grouped index carries a *how to search* line rather than
2,882 rows.

What it records per capability: name, kind, one-line purpose, the domain it
belongs to, its trigger, whether it is tool-bound, and whether anything routes to
it. The last field is the one that matters -- an unrouted capability is reported
as such rather than being counted as available.

Usage:
    python3 tools/index-tree.py            # build TREE.json and report
    python3 tools/index-tree.py --search auth
    python3 tools/index-tree.py --write-catalogue   # references/capability-catalogue.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
REFS = ROOT / "references"
OUT = ROOT / "TREE.json"
CATALOGUE = REFS / "capability-catalogue.md"

FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FIELD = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")

# Domains, most specific first. Order matters: the first match wins, so a skill
# tagged 'security-review' lands in review rather than in security.
DOMAINS: list[tuple[str, re.Pattern[str]]] = [
    ("testing",      re.compile(r"\b(test|tdd|spec|fixture|mock|coverage|assert)\w*", re.I)),
    ("verification", re.compile(r"\b(review|audit|verify|validation|lint|check)\w*", re.I)),
    ("security",     re.compile(r"\b(security|auth|crypto|secret|threat|vuln|permiss)\w*", re.I)),
    ("planning",     re.compile(r"\b(plan|roadmap|estimat|schedul|project|milestone)\w*", re.I)),
    ("design",       re.compile(r"\b(design|ui|ux|brand|style|typograph|accessib)\w*", re.I)),
    ("documentation",re.compile(r"\b(doc|readme|changelog|adr|write|technical writ)\w*", re.I)),
    ("data",         re.compile(r"\b(data|dataset|sql|query|metric|analytic|schema|migrat)\w*", re.I)),
    ("devops",       re.compile(r"\b(ci|cd|deploy|docker|kubernetes|k8s|terraform|infra|pipeline|release)\w*", re.I)),
    ("debugging",    re.compile(r"\b(debug|incident|troubleshoot|root.?cause|postmortem)\w*", re.I)),
    ("performance",  re.compile(r"\b(perf|optimi|latency|throughput|profil|benchmark|cache)\w*", re.I)),
    ("code-quality", re.compile(r"\b(refactor|simplif|clean|lint|style|technical.?debt|maintain)\w*", re.I)),
    ("research",     re.compile(r"\b(research|investigat|analy|compar|synthes)\w*", re.I)),
    ("frontend",     re.compile(r"\b(react|vue|angular|svelte|css|html|component|tailwind|next)\w*", re.I)),
    ("backend",      re.compile(r"\b(api|server|endpoint|database|queue|cache|service|auth)\w*", re.I)),
    ("business",     re.compile(r"\b(business|market|sales|pricing|finance|legal|contract|hiring)\w*", re.I)),
    ("agent",        re.compile(r"\b(agent|skill|prompt|orchestrat|delegat|subagent|context)\w*", re.I)),
]
GENERAL = "general"

TOOLBOUND = re.compile(
    r"\b(?:npm|npx|pnpm|yarn|pip3?|docker|kubectl|terraform|aws|gcloud|az|"
    r"vercel|netlify|cloudflare|supabase|firebase|postgres|mysql|sqlite|"
    r"mcp__|claude code|codex exec)\b", re.I)

STOP = set("""a an and are as at be by for from has have in is it its of on or that the
this to was were when which with you your not but if so than then there these they
what will use using used into out can should would do does did been being more
most other any all each own same such only also about after before over under
both because while how why who where agent skill task user add added adding new
one two get make made need needs want work works way ways time via per any each
""".split())


def frontmatter(text: str) -> dict[str, str]:
    m = FM.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        f = FIELD.match(line)
        if f and not line.startswith(" "):
            out[f.group(1).strip().lower()] = f.group(2).strip().strip("\"'")
    return out


def domain_of(name: str, desc: str) -> str:
    hay = f"{name} {desc}"
    for label, pat in DOMAINS:
        if pat.search(hay):
            return label
    return GENERAL


def tokens(name: str, desc: str) -> set[str]:
    raw = re.findall(r"[a-z][a-z0-9-]{2,}", f"{name} {desc}".lower())
    return {t for t in raw if t not in STOP}


def collect() -> list[dict]:
    routed = set()
    dpath = REFS / "delegation.md"
    if dpath.is_file():
        routed = set(re.findall(r"`agents/([a-z0-9_-]+)\.md`", dpath.read_text()))

    out: list[dict] = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        name = fm.get("name") or d.name
        desc = " ".join(fm.get("description", "").split())
        body = text[FM.match(text).end():] if FM.match(text) else text
        out.append({
            "name": name, "dir": d.name, "kind": "skill",
            "purpose": desc[:220],
            "domain": domain_of(name, desc),
            "tool_bound": bool(TOOLBOUND.search(body)),
            "routed": d.name in routed,
            "discoverable": bool(desc),
            "has_frontmatter": bool(fm),
            "path": f"skills/{d.name}/SKILL.md",
            "tokens": sorted(tokens(name, desc)),
        })
    for f in sorted(AGENTS.glob("*.md")):
        if f.stem == "readme" or not f.stem.islower():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        name = fm.get("name") or f.stem
        desc = " ".join(fm.get("description", "").split())
        out.append({
            "name": name, "dir": f.stem, "kind": "agent",
            "purpose": desc[:220],
            "domain": domain_of(name, desc),
            "tool_bound": bool(TOOLBOUND.search(text)),
            "routed": f.stem in routed,
            "discoverable": bool(desc),
            "has_frontmatter": bool(fm),
            "path": f"agents/{f.stem}.md",
            "tokens": sorted(tokens(name, desc)),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--search", metavar="TERM")
    ap.add_argument("--write-catalogue", action="store_true")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()

    entries = collect()
    if not entries:
        print("error: no capabilities found", file=sys.stderr)
        return 2

    payload = {
        "counts": {
            "total": len(entries),
            "skills": sum(1 for e in entries if e["kind"] == "skill"),
            "agents": sum(1 for e in entries if e["kind"] == "agent"),
            "routed": sum(1 for e in entries if e["routed"]),
            "unrouted": sum(1 for e in entries if not e["routed"]),
            "discoverable": sum(1 for e in entries if e["discoverable"]),
            "undiscoverable": sum(1 for e in entries if not e["discoverable"]),
            "no_frontmatter": sum(1 for e in entries if not e["has_frontmatter"]),
            "tool_bound": sum(1 for e in entries if e["tool_bound"]),
        },
        "domains": sorted(Counter(e["domain"] for e in entries).items(),
                          key=lambda kv: -kv[1]),
        "entries": [{k: v for k, v in e.items() if k != "tokens"} | {"tokens": e["tokens"]}
                    for e in entries],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.search:
        term = args.search.lower().split()
        hits = []
        for e in entries:
            score = 0
            for w in term:
                if w in e["name"].lower():
                    score += 10          # the name is the strongest signal
                if w in e["purpose"].lower():
                    score += 4
                score += sum(2 for tk in e["tokens"] if w in tk)
            if score:
                hits.append((score, e))
        # Routed first, then by score. An unrouted hit that outscores a routed
        # one is still the wrong thing to open first.
        hits.sort(key=lambda se: (not se[1]["routed"], -se[0], se[1]["name"]))
        print(f"  {len(hits)} match(es) for {args.search!r}\n")
        for _, e in hits[:args.limit]:
            flag = "routed" if e["routed"] else "UNROUTED"
            print(f"  {flag:9} {e['kind'][:5]:5} {e['name'][:36]:36} {e['domain'][:12]:12} "
                  f"{e['path']}")
        return 0

    if args.write_catalogue:
        write_catalogue(entries, payload)
        print(f"  catalogue: {CATALOGUE.relative_to(ROOT)}")
        return 0

    c = payload["counts"]
    print(f"  total            {c['total']}")
    print(f"    skills         {c['skills']}")
    print(f"    agents         {c['agents']}")
    print(f"  DISCOVERABLE     {c['discoverable']}   <- has a description; the runtime can find it")
    print(f"  undiscoverable   {c['undiscoverable']}   <- no description; invisible to every runtime")
    print(f"  roles dispatched {c['routed']}   <- have a condition in delegation.md")
    print(f"  tool-bound       {c['tool_bound']}")
    print(f"\n  index: {OUT.relative_to(ROOT)}")
    print("\n  by domain:")
    for d, n in payload["domains"][:14]:
        print(f"    {n:5}  {d}")
    return 0


def write_catalogue(entries: list[dict], payload: dict) -> None:
    by_dom: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_dom[e["domain"]].append(e)

    c = payload["counts"]
    L: list[str] = [
        "# Capability catalogue",
        "",
        "Generated by `tools/index-tree.py --write-catalogue`. Do not hand-edit;",
        "regenerate instead, or the index and this file disagree and the reader",
        "cannot tell which is right.",
        "",
        "## What this is",
        "",
        f"{c['total']} capabilities are installed: {c['skills']} sub-skills and",
        f"{c['agents']} roles. This file is the map, not the territory — it tells",
        "you a capability exists and where it lives, and it does not load any of",
        "them. A catalogue printed into context would cost more than the task.",
        "",
        "## How to search",
        "",
        "Do not read this file looking for a capability. Search the index:",
        "",
        "```text",
        "python3 tools/index-tree.py --search <term>",
        "```",
        "",
        "which matches on name, purpose, and keywords, and reports whether each",
        "hit is **routed** — whether a decision can actually reach it — or",
        "**UNROUTED**, meaning it is installed but nothing dispatches to it.",
        "",
        "## What the numbers say",
        "",
        "| | |",
        "|---|---|",
        f"| sub-skills | {c['skills']} |",
        f"| roles | {c['agents']} |",
        f"| **discoverable** (has a description) | **{c['discoverable']}** |",
        f"| **undiscoverable** (no description) | **{c['undiscoverable']}** |",
        f"| roles with a dispatch condition | {c['routed']} |",
        f"| tool-bound | {c['tool_bound']} |",
        "",
        "## Two different mechanisms, not one count",
        "",
        "A **sub-skill is discovered.** The runtime scans every",
        "`skills/*/SKILL.md`, puts the `description` into a system-reminder",
        "listing, and the model chooses from that listing. The description IS the",
        "registration: there is no registry to update and no kernel to edit. So a",
        "sub-skill with a description is already reachable, and a count of",
        "\"dispatch rows\" says nothing about it.",
        "",
        "A **role is dispatched.** Something has to decide to call it, so it needs",
        "a condition in `delegation.md`.",
        "",
        "This catalogue previously reported a single `unrouted` figure covering",
        "both, which made 2,584 perfectly discoverable sub-skills look unreachable.",
        "The two counts are separate and are now separate here.",
        "",
        "## By domain",
        "",
    ]
    L.append("## Routed capabilities — the ones a decision can reach")
    L.append("")
    L.append("These have a row in `delegation.md`, so a run can select them. They")
    L.append("are the only entries reachable without editing anything.")
    L.append("")
    for e in sorted((x for x in entries if x["routed"]), key=lambda x: x["name"]):
        L.append(f"- `{e['name']}` ({e['kind']}) — "
                 f"{e['purpose'][:120] or '(no description)'}")
    L.append("")
    L.append("## Everything else")
    L.append("")
    L.append("Installed, indexed, and **not reachable from a decision**. They are")
    L.append("given by domain and count, with a sample of names. Printing every")
    L.append("entry would cost more context than the task they would help with,")
    L.append("which is the mistake progressive disclosure exists to prevent.")
    L.append("")
    L.append("```text")
    L.append("python3 tools/index-tree.py --search <term>")
    L.append("```")
    L.append("")
    for dom, n in sorted(payload["domains"], key=lambda kv: -kv[1]):
        g = [e for e in by_dom[dom] if not e["routed"]]
        r = len(by_dom[dom]) - len(g)
        L.append(f"### {dom} — {len(by_dom[dom])} installed, {r} routed, {len(g)} not")
        L.append("")
        sample = [e["name"] for e in sorted(g, key=lambda e: e["name"].lower())][:12]
        if sample:
            L.append("  " + ", ".join(f"`{s}`" for s in sample)
                     + (f", ... ({len(g)} total)" if len(g) > 12 else ""))
            L.append("")

    CATALOGUE.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
