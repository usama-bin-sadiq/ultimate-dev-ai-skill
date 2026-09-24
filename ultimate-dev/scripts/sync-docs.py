#!/usr/bin/env python3
"""sync-docs.py — keep README.md in sync with the repo (stdlib only).

The README carries facts that change on every release:
  version, agent count, category count, skill count, module count,
  SKILL.md line count, the agent tree, and the sub-skills table.

Two kinds of managed content:

  1. Inline facts — plain lines owned by this script, matched by regex
     and rewritten in place (no markers needed), e.g.:
         # ultimate-dev v2.5.0

  2. Generated blocks — delimited by HTML comments (invisible when the
     README is rendered):
         <!-- ud:begin agent-tree -->
         ...generated content...
         <!-- ud:end agent-tree -->

Usage:
  python3 scripts/sync-docs.py            # rewrite README.md if stale
  python3 scripts/sync-docs.py --check    # exit 1 if out of sync (pre-commit/CI)
  python3 scripts/sync-docs.py --readme path/to/README.md

Exit codes:
  0  in sync / successfully rewritten
  1  out of sync (--check), or a managed line/block/markers went missing
  2  usage error (README or VERSION not found)
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Short purposes for the README sub-skills table.
# Key = skills/<name>/SKILL.md; insertion order = display order.
# Skills missing from this dict fall back to their frontmatter
# description, so adding a skill never breaks the sync.
PURPOSE: dict[str, str] = {
    "self-evolve": "Auto-generates new skills from experience",
    "task-observer": "Capture reusable methodology from task work",
    "research": "Learn anything",
    "coding": "Build anything",
    "testing": "Verify anything",
    "review": "Evaluate anything",
    "architecture": "Design anything",
    "security": "Protect anything",
    "devops": "Deliver anything",
    "debugging": "Fix anything",
    "documentation": "Communicate anything",
    "performance": "Optimize anything",
    "monitoring": "Observe anything",
    "data": "Work with any data",
    "api-design": "Connect anything",
    "migration": "Transition anything",
    "mobile": "Build for any device",
    "ai-ml": "Build intelligent systems",
}


# --------------------------------------------------------------------- facts

def collect_stats(root: Path) -> dict:
    version_file = root.parent / "VERSION"
    if not version_file.is_file():
        raise SystemExit(f"sync-docs: VERSION not found at {version_file}")

    agents_dir = root / "agents"
    per_cat: dict[str, list[str]] = {}
    for d in sorted(p for p in agents_dir.iterdir() if p.is_dir() and p.name != "_shared"):
        names = sorted(f.stem for f in d.glob("*.md"))
        if names:
            per_cat[d.name] = names
        # Empty category dirs are skipped silently: git does not track
        # empty directories, so they exist locally but never on CI —
        # mentioning them in README would make --check fail there.
    root_agents = sorted(f.stem for f in agents_dir.glob("*.md"))

    skill_names = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    modules = list((root / "modules").rglob("*.md"))
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"sync-docs: SKILL.md not found at {skill_md}")

    return {
        "version": version_file.read_text(encoding="utf-8").strip(),
        "agents": len(root_agents) + sum(len(v) for v in per_cat.values()),
        "categories": len(per_cat),
        "per_cat": per_cat,
        "root_agents": root_agents,
        "skills": len(skill_names),
        "skill_names": skill_names,
        "modules": len(modules),
        "skill_lines": len(skill_md.read_text(encoding="utf-8").splitlines()),
    }


# ------------------------------------------------------------- inline facts

def inline_rules(s: dict) -> list[tuple[str, str, "object"]]:
    """(name, regex, replacement-from-match) for every single-line fact."""
    return [
        (
            "version-title",
            r"^# ultimate-dev v[\d.]+$",
            lambda m: f"# ultimate-dev v{s['version']}",
        ),
        (
            "agents-heading",
            r"^### \d+ Agents across [\d.+]+ Categories$",
            lambda m: f"### {s['agents']} Agents across {s['categories']} Categories",
        ),
        (
            "skills-heading",
            r"^### \d+ Meta-Cognitive Sub-Skills$",
            lambda m: f"### {s['skills']} Meta-Cognitive Sub-Skills",
        ),
        (
            "skill-md-lines",
            r"^(├── SKILL\.md\s+← Orchestrator )\(\d+ lines\)$",
            lambda m: f"{m.group(1)}({s['skill_lines']} lines)",
        ),
        (
            "structure-agents",
            r"^(├── agents/\s+← )\d+ specialized agents$",
            lambda m: f"{m.group(1)}{s['agents']} specialized agents",
        ),
        (
            "structure-skills",
            r"^(├── skills/\s+← )\d+ meta-cognitive sub-skills$",
            lambda m: f"{m.group(1)}{s['skills']} meta-cognitive sub-skills",
        ),
        (
            "structure-modules",
            r"^(├── modules/\s+← )\d+ internal pattern modules$",
            lambda m: f"{m.group(1)}{s['modules']} internal pattern modules",
        ),
    ]


# ---------------------------------------------------------- generated blocks

def gen_agent_tree(s: dict) -> str:
    cats = s["per_cat"]
    width = max((len(c) + 1 for c in cats), default=10) + 1

    lines = [
        f"agents/ — {s['agents']} agents, {s['categories']} categories, "
        f"{len(s['root_agents'])} root-level"
    ]
    for cat, names in cats.items():
        lines.append(f"├── {(cat + '/').ljust(width)} ({len(names):>2})  {', '.join(names)}")
    lines.append(
        f"└── {'root-level'.ljust(width)} ({len(s['root_agents']):>2})  "
        f"{', '.join(s['root_agents'])}"
    )
    return "```\n" + "\n".join(lines) + "\n```"


def _frontmatter_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        return ""
    dm = re.search(
        r"^description:\s*(?:>[+-]?\s*)?([^\n]*(?:\n[ \t]+[^\n]*)*)",
        fm.group(1),
        re.M,
    )
    if not dm:
        return ""
    desc = " ".join(dm.group(1).split())
    if len(desc) > 90:
        desc = desc[:87].rsplit(" ", 1)[0] + "…"
    return desc


def gen_skills_table(s: dict) -> str:
    known = [n for n in PURPOSE if n in s["skill_names"]]
    extra = sorted(s["skill_names"] - PURPOSE.keys())
    rows = []
    for name in known + extra:
        purpose = PURPOSE.get(name)
        if purpose is None:
            purpose = _frontmatter_description(ROOT / "skills" / name / "SKILL.md") or "(describe me)"
        rows.append(f"| `{name}` | {purpose} |")
    return "\n".join(["| Skill | Purpose |", "|-------|---------|", *rows])


BLOCKS: dict[str, "object"] = {
    "agent-tree": gen_agent_tree,
    "skills-table": gen_skills_table,
}


# ------------------------------------------------------- cross-file checks

def manifest_errors(s: dict) -> list[str]:
    """README must agree with skill-manifest.yaml (its own source: generate-manifest.py)."""
    path = root_manifest = ROOT / "skill-manifest.yaml"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    errors = []
    m = re.search(r"^version:\s*(\S+)", text, re.M)
    if m and m.group(1) != s["version"]:
        errors.append(
            f"skill-manifest.yaml version={m.group(1)} but VERSION={s['version']} "
            "— run: python3 scripts/generate-manifest.py"
        )
    m = re.search(r"^\s*total_agents:\s*(\d+)", text, re.M)
    if m and int(m.group(1)) != s["agents"]:
        errors.append(
            f"skill-manifest.yaml total_agents={m.group(1)} but disk has {s['agents']} "
            "— run: python3 scripts/generate-manifest.py"
        )
    del root_manifest
    return errors


# ------------------------------------------------------------------ driver

def apply_rules(text: str, s: dict, changes: list[str], errors: list[str]) -> str:
    for name, pattern, repl in inline_rules(s):
        m = re.search(pattern, text, re.M)
        if not m:
            errors.append(
                f"inline fact `{name}`: managed line no longer matches in README.md:\n"
                f"    /{pattern}/"
            )
            continue
        new_val = repl(m)
        if m.group(0) != new_val:
            changes.append(f"{name}:\n    - {m.group(0)}\n    + {new_val}")
        text = text[: m.start()] + new_val + text[m.end():]

    for name, gen in BLOCKS.items():
        rx = re.compile(
            rf"<!-- ud:begin {re.escape(name)} -->\n(.*?)<!-- ud:end {re.escape(name)} -->",
            re.S,
        )
        m = rx.search(text)
        if not m:
            errors.append(
                f"block `{name}`: markers not found "
                f"(<!-- ud:begin {name} --> … <!-- ud:end {name} -->)"
            )
            continue
        new_block = f"<!-- ud:begin {name} -->\n{gen(s)}\n<!-- ud:end {name} -->"
        if m.group(0) != new_block:
            n_rows = gen(s).count("\n") + 1
            changes.append(f"block `{name}`: regenerated ({n_rows} lines)")
        text = text[: m.start()] + new_block + text[m.end():]
    return text


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Sync README.md facts with the repo.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if README.md is stale; do not write")
    ap.add_argument("--readme", type=Path, default=ROOT / "README.md",
                    help="README to sync (default: repo root README.md)")
    args = ap.parse_args(argv)

    if not args.readme.is_file():
        print(f"sync-docs: README not found at {args.readme}", file=sys.stderr)
        return 2

    try:
        stats = collect_stats(ROOT)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    original = args.readme.read_text(encoding="utf-8")
    changes: list[str] = []
    errors: list[str] = []
    text = apply_rules(original, stats, changes, errors)
    errors.extend(manifest_errors(stats))

    summary = (
        f"version={stats['version']} agents={stats['agents']} "
        f"categories={stats['categories']} skills={stats['skills']} "
        f"modules={stats['modules']} SKILL.md={stats['skill_lines']} lines"
    )

    if args.check:
        if text != original:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                text.splitlines(keepends=True),
                fromfile="README.md (current)",
                tofile="README.md (expected)",
            )
            sys.stdout.writelines(diff)
            print("\nsync-docs: README.md is OUT OF SYNC — run: "
                  "python3 scripts/sync-docs.py", file=sys.stderr)
            return 1
        for err in errors:
            print(f"sync-docs: ERROR: {err}", file=sys.stderr)
        if errors:
            return 1
        print(f"sync-docs: README.md in sync ({summary})")
        return 0

    if text != original:
        args.readme.write_text(text, encoding="utf-8")
        print(f"sync-docs: updated {args.readme.name} ({summary})")
        for change in changes:
            print(f"  • {change}")
    else:
        print(f"sync-docs: already in sync ({summary})")

    for err in errors:
        print(f"sync-docs: ERROR: {err}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
