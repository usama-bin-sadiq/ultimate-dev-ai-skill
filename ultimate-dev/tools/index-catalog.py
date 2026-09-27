#!/usr/bin/env python3
"""Index a cloned catalogue of agent roles and skills.

Cloning a corpus is not the same as making it usable. After the clone there are
thousands of files with no way to answer the only question that matters: given a
task, which of these is relevant, does it collide with something else, and is it
safe to route to.

This builds that answer. It is deliberately mechanical and it is deliberately
sceptical, because the three questions it answers are all decidable without
reading a file closely:

  kind          is this a role (a judgement applied at a decision) or a skill (a
                procedure with its own lifecycle)? The path says so.
  tool-bound    does it require a specific CLI, API, SDK, or file format? Those
                are nameable, so they can be counted rather than judged.
  collision     do two entries cover the same ground? Description tokens and the
                title are a proxy, and a proxy that is reported as a proxy.

Duplicates are removed by content hash, not by name, because the surveyed
corpora contain repositories where the same file is committed under several
paths and a name-based dedupe silently keeps one copy per name.

Usage:
    python3 tools/index-catalog.py                 # build catalog/INDEX.json
    python3 tools/index-catalog.py --report        # human summary
    python3 tools/index-catalog.py --search "auth"  # query the index
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG = SKILL_ROOT / "catalog"
SRC = CATALOG / "_src"
INDEX = CATALOG / "INDEX.json"

# Nameable tool bindings. A file requiring one of these cannot be routed to in a
# runtime that does not have it, whatever its judgement is worth.
TOOL_PATTERNS: dict[str, re.Pattern[str]] = {
    "cli": re.compile(
        r"`(?:npm|npx|pnpm|yarn|brew|pip|pipx|uv|uvx|poetry|cargo|go|gem|apt|"
        r"docker|kubectl|helm|terraform|gh|glab|git|make|jq|yq|curl|wget|"
        r"aws|gcloud|az|vercel|netlify|wrangler|bun|deno|tsc|pytest|ruff|"
        r"eslint|prettier|mypy|black|gradle|mvn|dotnet)\s+[\w-]",
        re.IGNORECASE),
    "sdk": re.compile(
        r"\b(?:import |require\(|from \w+ import|pip install|npm install|"
        r"@anthropic-ai|openai|langchain|transformers|numpy|pandas|requests|"
        r"boto3|playwright|puppeteer|selenium)\b"),
    "mcp": re.compile(r"\bmcp[:_]|modelcontextprotocol|MCP server", re.IGNORECASE),
    "vendor-api": re.compile(
        r"\b(?:API key|api_key|bearer token|oauth|STRIPE_|GITHUB_TOKEN|"
        r"AWS_|service account|client secret)\b", re.IGNORECASE),
    "file-format": re.compile(
        r"\.(docx|pptx|xlsx|pdf|qmd|base|canvas)\b|\bOOXML\b", re.IGNORECASE),
    "framework": re.compile(
        r"\b(?:Next\.js|React|Vue|Angular|Django|Rails|Spring|Laravel|"
        r"Svelte|Nuxt|Flutter|SwiftUI|QML|Qt)\b"),
}

# The four standing disqualifiers from decision 0005.
DISQUALIFIERS: dict[str, re.Pattern[str]] = {
    "advertises-absent-rules": re.compile(
        r"\b(?:100\+ rules|audits your code for|as (?:shown|described) in the "
        r"template above)\b", re.IGNORECASE),
    "self-excellence": re.compile(
        r"\byou are (?:an?|the)\b[^.\n]{0,60}?\b(?:expert|specialist|senior|"
        r"staff|principal|elite|world-class|renowned|master)\b|"
        r"\bwith (?:over |more than )?\d+ years\b|"
        r"\b(?:state-of-the-art|cutting-edge|passionate about)\b",
        re.IGNORECASE),
    "fabricated-utterance": re.compile(
        r"\*\*The user ALREADY|^\s*>\s*\"?(?:I've|I've been|Can you review|"
        r"I need|I'd like)", re.IGNORECASE | re.MULTILINE),
    "writes-agent-config": re.compile(
        r"(?:add|write|append|insert|edit|update)[^.\n]{0,40}"
        r"\b(?:CLAUDE\.md|AGENTS\.md|\.cursorrules|\.clinerules)\b", re.IGNORECASE),
    "self-certified-completion": re.compile(
        r"<promise>|I (?:will|have) (?:completed|finished)[^.\n]{0,20}(?:done|"
        r"success)|auto-decide[ds]?\b", re.IGNORECASE),
}

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
NEGATIVE = re.compile(
    r"\b(never|do not|don't|must not|no\b|refuse|forbidden|may not)\b",
    re.IGNORECASE)
FAILURE = re.compile(
    r"\b(failure mode|fails? when|bug|defect|regression|drift|corrupt\w*|"
    r"hallucinat\w+|fabricat\w+|wrong|breaks?|trap|footgun|anti-pattern)\b",
    re.IGNORECASE)
THRESHOLD = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?\s*(?:%|ms|s\b|sec|minutes?|min|hours?|days?|"
    r"lines?|items?|times|attempts?|retries|x\b)", re.IGNORECASE)


def frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip("\"'")
    return out


def kind_of(path: Path, text: str) -> str:
    if path.name == "SKILL.md":
        return "skill"
    parts = {p.lower() for p in path.parts}
    if "agents" in parts or "agent" in path.stem.lower() or \
            path.stem.lower().endswith("-agent"):
        return "agent"
    return "skill"


def walk() -> list[Path]:
    if not SRC.is_dir():
        return []
    out: list[Path] = []
    for p in SRC.rglob("*.md"):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        if p.name.lower() in ("readme.md", "license.md", "changelog.md",
                              "contributing.md", "security.md"):
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--search", metavar="TERM")
    ap.add_argument("--min-lines", type=int, default=40)
    args = ap.parse_args()

    files = walk()
    if not files:
        print(f"error: nothing to index under {SRC}", file=sys.stderr)
        return 2

    seen: dict[str, str] = {}
    entries: list[dict] = []
    dupes = 0

    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        h = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
        if h in seen:
            dupes += 1
            continue
        seen[h] = str(p)

        fm = frontmatter(text)
        rel = str(p.relative_to(SKILL_ROOT))
        name = fm.get("name") or p.parent.name if p.name == "SKILL.md" \
            else fm.get("name") or p.stem
        desc = " ".join(fm.get("description", "").split())
        if not desc:
            m = re.search(r"^#\s+(.+)$", text, re.M)
            desc = m.group(1).strip() if m else ""

        body = text[FRONTMATTER.match(text).end():] if FRONTMATTER.match(text) \
            else text
        tools = sorted(k for k, pat in TOOL_PATTERNS.items()
                       if pat.search(body))
        dq = sorted(k for k, pat in DISQUALIFIERS.items() if pat.search(text))
        lines = len(text.splitlines())
        substance = (3 * len(FAILURE.findall(body))
                     + 2 * len(NEGATIVE.findall(body))
                     + len(THRESHOLD.findall(body)))

        entries.append({
            "name": name,
            "kind": kind_of(p, text),
            "path": rel,
            "repo": rel.split("/")[2] if rel.startswith("catalog/_src/") else "",
            "lines": lines,
            "description": desc[:400],
            "tool_bound": tools,
            "disqualifiers": dq,
            "substance": substance,
            "usable": lines >= args.min_lines and not dq,
        })

    entries.sort(key=lambda e: (-e["substance"], e["name"]))
    by_repo: dict[str, int] = defaultdict(int)
    for e in entries:
        by_repo[e["repo"]] += 1
    by_kind: dict[str, int] = defaultdict(int)
    for e in entries:
        by_kind[e["kind"]] += 1

    payload = {
        "generated_from": "catalog/_src",
        "disclaimer": (
            "Mechanical classification. tool_bound is pattern-detected and "
            "collisions are NOT computed here. A usable:true entry is a file "
            "that is long enough and carries no disqualifier -- it is not "
            "evidence the capability is good."
        ),
        "totals": {
            "files_seen": len(files),
            "unique": len(entries),
            "duplicates_removed": dupes,
            "by_kind": dict(by_kind),
            "repos": len(by_repo),
            "usable": sum(1 for e in entries if e["usable"]),
        },
        "entries": entries,
    }
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.search:
        t = args.search.lower()
        hits = [e for e in entries
                if t in e["name"].lower() or t in e["description"].lower()]
        print(f"  {len(hits)} match(es) for {args.search!r}\n")
        for e in hits[:25]:
            flag = "ok " if e["usable"] else "NO "
            tb = ",".join(e["tool_bound"]) or "-"
            print(f"  {flag}{e['kind'][:5]:5} {e['name'][:34]:34} "
                  f"{e['repo'][:22]:22} {e['lines']:5}ln s={e['substance']:<4} "
                  f"tools={tb}")
        return 0

    if args.report:
        tot = payload["totals"]
        print(f"  files seen      {tot['files_seen']}")
        print(f"  unique          {tot['unique']}  "
              f"({tot['duplicates_removed']} duplicate copies removed by hash)")
        print(f"  repos           {tot['repos']}")
        print(f"  kinds           " + ", ".join(
            f"{k}={v}" for k, v in sorted(by_kind.items())))
        print(f"  usable          {tot['usable']}  "
              f"(>= {args.min_lines} lines, no disqualifier)\n")
        dq_counts: dict[str, int] = defaultdict(int)
        for e in entries:
            for d in e["disqualifiers"]:
                dq_counts[d] += 1
        print("  disqualifiers found:")
        for d, n in sorted(dq_counts.items(), key=lambda kv: -kv[1]):
            print(f"    {n:5}  {d}")
        tb_counts: dict[str, int] = defaultdict(int)
        for e in entries:
            for t in e["tool_bound"]:
                tb_counts[t] += 1
        print("\n  tool bindings detected:")
        for t, n in sorted(tb_counts.items(), key=lambda kv: -kv[1]):
            print(f"    {n:5}  {t}")
        print(f"\n  index: {INDEX.relative_to(SKILL_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
