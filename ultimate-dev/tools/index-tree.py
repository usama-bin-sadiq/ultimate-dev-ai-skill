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
    """Read the scalar keys of a skill's frontmatter.

    A YAML block scalar is a key on one line and its value on the following
    indented lines:

        description:
          A specialized skill for Gemini CLI that provides monitoring of
          GitHub Actions workflows.

    Reading one line at a time sees `description` with an empty value and calls
    the skill undiscoverable, which is the same defect that made a previous
    pass report thousands of missing descriptions that were present. The
    continuation lines are therefore collected into the key they belong to.
    """
    m = FM.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    key: str | None = None
    for line in m.group(1).splitlines():
        if line[:1] in (" ", "\t"):          # continuation of the key above
            if key and not line.strip().startswith("-"):
                out[key] = f"{out[key]} {line.strip()}".strip()
            continue
        f = FIELD.match(line)
        if f:
            key = f.group(1).strip().lower()
            out[key] = f.group(2).strip().strip("\"'")
        else:
            key = None
    return {k: re.sub(r"\s+", " ", v).strip() for k, v in out.items()}


def domain_of(name: str, desc: str) -> str:
    hay = f"{name} {desc}"
    for label, pat in DOMAINS:
        if pat.search(hay):
            return label
    return GENERAL


def tokens(name: str, desc: str) -> set[str]:
    raw = re.findall(r"[a-z][a-z0-9-]{2,}", f"{name} {desc}".lower())
    return {t for t in raw if t not in STOP}


def dispatch_rows() -> dict[str, str]:
    """Role name -> its "delegate when" cell, read from delegation.md.

    The condition text is returned, not just the presence of the name, because
    the distinction that matters is between a row that decides something and a
    row that was appended to silence a validator. A cell that is empty, or that
    is a literal `[bracketed placeholder]`, or that is a description truncated
    with an ellipsis, does not decide anything.

    SKILL.md said for a while that "almost none of the catalogue is routed" and
    that was measured with a filename-substring test that could not see any of
    this. The 267 derived rows that closed the gap were produced by appending
    each role's own `description:`, truncated. references/delegation.md says so
    itself. Four of them are empty or literal placeholders.

    So the split is computed here from the text, and reported, rather than
    asserted in prose and overwritten on the next regeneration.
    """
    rows: dict[str, str] = {}
    dpath = REFS / "delegation.md"
    if not dpath.is_file():
        return rows
    for line in dpath.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*`agents/([a-z0-9_-]+)\.md`\s*\|(.*)\|\s*$", line)
        if m:
            rows[m.group(1)] = m.group(2).strip()
    return rows


_STOPWORDS = {
    "a", "an", "and", "the", "of", "for", "to", "in", "with", "that", "this",
    "or", "is", "are", "as", "by", "on", "from", "it", "its", "be", "who",
    "which", "at", "into", "their", "his", "her", "they", "them", "per",
    "output", "contract", "used", "use", "using", "provides", "provide",
}


# Two thresholds, and the number is reported as a band rather than a point,
# because a single threshold would be a hand-set constant deciding a published
# figure. Measured on this tree: 18 roles at 0.10, 9 at 0.30. The 267 derived
# rows sit at ~0.00 at every threshold in that range, so the band does not
# change the finding -- they restate their own description and decide nothing.
STRICT_NOVEL = 0.30
LOOSE_NOVEL = 0.10


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z0-9-]{2,}", (text or "").lower())
            if w not in _STOPWORDS}


def condition_is_real(condition: str, description: str = "") -> bool:
    """Does this dispatch cell actually decide anything?

    A dispatch condition has to say something the role's own description does
    not. A description says what a role IS. A condition says WHEN TO CALL IT.
    Restating the first in the second column makes every role reachable to a
    validator that only checks whether the filename appears in the table, and
    dispatchable to nothing at run time.

    So the test is comparative. A cell that is empty, a literal bracketed
    placeholder, a leaked markdown table fragment, or a restatement of the
    role's own description, does not decide anything. The last of those is the
    common case: 267 rows were appended by truncating each role's `description:`
    and ending it with "Per its output contract", which made the reachability
    check pass without making a single role dispatchable.

    Measured as word overlap, because a substring test would flag a condition
    that quotes the description and then adds a trigger -- which is the shape a
    good condition should have.
    """
    c = (condition or "").strip()
    if not c:
        return False
    if re.search(r"\[[^\]]*\]", c):          # [bracketed placeholder]
        return False
    if c.count("|") >= 2:                       # a leaked table row
        return False
    if not description:
        return True
    cw, dw = _content_words(c), _content_words(description)
    if not cw:
        return False
    # Fraction of the cell's content words that the description does not
    # already contain. A restatement is near zero; a condition that adds a
    # trigger is a meaningful fraction.
    return len(cw - dw) / len(cw) >= STRICT_NOVEL


def novel_fraction(condition: str, description: str) -> float | None:
    """Fraction of the cell's content words the description does not contain."""
    cw, dw = _content_words(condition), _content_words(description)
    if not cw:
        return None
    return len(cw - dw) / len(cw)


def collect() -> list[dict]:
    rows = dispatch_rows()
    routed = set(rows)

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
            # A sub-skill is not dispatched through delegation.md; the runtime
            # discovers it from the `description` it puts in a system-reminder
            # listing, per references/capability-catalogue.md. Marking it routed
            # only when its directory name happened to match an AGENT filename
            # made 2,086 of 2,086 skills unrouted by construction, and the
            # resulting count was then quoted in SKILL.md as evidence that the
            # catalogue was unreachable. It was measuring a name collision.
            "dispatched": False,
            "routed": bool(desc),
            "condition_real": None,
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
            "dispatched": f.stem in routed,
            "routed": f.stem in routed,
            "condition_real": (condition_is_real(rows[f.stem], desc)
                               if f.stem in routed else None),
            "novel": (novel_fraction(rows[f.stem], desc)
                      if f.stem in routed else None),
            "condition_structural": (
                condition_is_real(rows[f.stem]) if f.stem in routed else None),
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
            # `routed` alone is not a number worth quoting, because it now
            # means "reachable by whatever mechanism applies to this kind" --
            # a description for a sub-skill, a dispatch row for a role. The
            # three figures below are the ones that can be acted on, and they
            # are computed from the delegation cells rather than asserted.
            "reachable": sum(1 for e in entries if e["routed"]),
            "not_reachable": sum(1 for e in entries if not e["routed"]),
            "roles_with_dispatch_row": sum(
                1 for e in entries if e["kind"] == "agent" and e["dispatched"]),
            "roles_with_a_deciding_condition": sum(
                1 for e in entries if e["kind"] == "agent"
                and e["condition_real"] is True),
            # The band is over STRUCTURALLY VALID rows only. Without that
            # qualifier the loose figure counted the four rows that are empty,
            # bracketed placeholders, or a leaked markdown table -- rows that
            # are not weak conditions but no conditions, and which no threshold
            # can rescue. They are counted in their own line below.
            "roles_with_a_deciding_condition_loose": sum(
                1 for e in entries if e["kind"] == "agent"
                and e.get("novel") is not None
                and e["condition_structural"] is not False
                and e["novel"] >= LOOSE_NOVEL),
            "roles_with_no_usable_condition": sum(
                1 for e in entries if e["kind"] == "agent"
                and e.get("condition_structural") is False),
            "roles_with_a_derived_row": sum(
                1 for e in entries if e["kind"] == "agent"
                and e["dispatched"] and e["condition_real"] is False),
            "skills_reachable_by_description": sum(
                1 for e in entries if e["kind"] == "skill" and e["routed"]),
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
        # Query words are dropped if they are not discriminative, and the test is
        # on length. Matching is substring, so a 1-2 character word matches inside
        # ordinary tokens: "a" is in "abstract", "validate", "parse" and "data",
        # so keeping it scored every one of the 2,397 entries and the search
        # reported the entire catalogue as a match for a four-word query. The
        # answer was not wrong, it was useless -- and a search that returns
        # everything has silently become "load the catalogue", which is the exact
        # failure the on-demand instruction in SKILL.md forbids.
        #
        # Three characters is the threshold because tokens are built with
        # [a-z][a-z0-9-]{2,}, so no token is shorter than 3. Below that a word
        # cannot discriminate between tokens at all.
        term = [w for w in args.search.lower().split() if len(w) >= 3]
        if not term:
            print("  no searchable words in that query; words of 1-2 characters "
                  "match almost every entry", file=sys.stderr)
            return 1
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
    print(f"  roles with a dispatch row        {c['roles_with_dispatch_row']}")
    print(f"  ...whose condition actually decides "
          f"{c['roles_with_a_deciding_condition_loose']}-"
          f"{c['roles_with_a_deciding_condition']} of {c['roles_with_dispatch_row']}"
          f"   <- a band, not a point: the threshold decides it")
    print(f"  ...row restates the role's own description {c['roles_with_a_derived_row']}")
    print(f"  ...row is empty, a placeholder, or a leaked table "
          f"{c['roles_with_no_usable_condition']}")
    print(f"  skills reachable by description    {c['skills_reachable_by_description']}"
          f"   <- no dispatch row needed")
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
        f"| roles with a dispatch row | {c['roles_with_dispatch_row']} |",
        f"| ...of which the condition decides something | "
        f"{c['roles_with_a_deciding_condition']} |",
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
    for e in sorted((x for x in entries
                     if x["routed"] and x.get("condition_real") is not False),
                    key=lambda x: x["name"]):
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
