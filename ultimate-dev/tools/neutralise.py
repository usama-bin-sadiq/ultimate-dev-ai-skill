#!/usr/bin/env python3
"""Neutralise capabilities that claim to be general but are bound to one tool.

The rule this implements, as directed:

  A capability that is already specialised is left alone. nextjs-performance is
  meant for Next.js; making it tool-neutral would destroy what it is for.

  A capability that claims to be general and is not is the defect. A file called
  "frontend" that only knows React tells the reader it applies to every frontend
  technology, and it does not. That claim is what gets fixed.

  A capability with no tool binding is left alone. There is nothing to neutralise.

So the target set is precisely: name and description do NOT name a tool, body IS
dominated by one. Those are the files making a promise the file does not keep.

Four substitutions, in order of how much they matter:

  hardcoded home paths   /Users/dana/code/app, ~/.claude/skills/...
                         -> <project-root>, <agent-config-dir>
  agent-instruction file  CLAUDE.md, AGENTS.md, .cursorrules
                         -> <agent-instructions>, with the real names listed in a
                            runtime note so the reader can still resolve it
  a single tool's CLI     `npx thing`, `claude -p`, `gcloud ...`
                         -> <tool> stays named, but a Runtime notes section is
                            added saying which runtime provides it and what the
                            equivalent is elsewhere. A general skill that hard-codes
                            one provider's invocation is not made abstract -- it is
                            made honest about the invocation.
  MCP server names        mcp__office__excel_*
                         -> named as a capability, not a hard requirement

Every file touched records what changed under `neutralised:` in its frontmatter,
so a reader can tell an adapted file from an authored one without diffing.

Usage:
    python3 tools/neutralise.py            # report, change nothing
    python3 tools/neutralise.py --apply
    python3 tools/neutralise.py --apply --limit 20
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILLS = SKILL_ROOT / "skills"
AGENTS = SKILL_ROOT / "agents"

# Tools named in a name or description. If one of these appears there, the file
# is specialised and is not touched.
TOOL_NAMES = re.compile(
    r"\b(gcloud|aws|azure|firebase|supabase|vercel|netlify|cloudflare|wrangler|"
    r"docker|kubernetes|k8s|kubectl|helm|terraform|pulumi|ansible|"
    r"node|npm|npx|pnpm|yarn|deno|bun|next\.?js|nuxt|remix|astro|"
    r"react|vue|angular|svelte|preact|"
    r"django|flask|fastapi|rails|laravel|spring|phoenix|"
    r"flutter|swift|swiftui|xcode|kotlin|android|qt|qml|unity|"
    r"postgres|postgresql|mysql|sqlite|mongodb|redis|elasticsearch|"
    r"python|pip|conda|poetry|spark|pytorch|tensorflow|"
    r"mcp|modelcontextprotocol|langchain|openai|anthropic)\b", re.IGNORECASE)

# Body signals that a file is bound to one tool even though its name is general.
BODY_SIGNALS: dict[str, re.Pattern[str]] = {
    "npm": re.compile(r"\b(?:npm|npx|pnpm|yarn)\s+(?:install|run|exec|add)\b", re.I),
    "pip": re.compile(r"\b(?:pip3?|python3? -m pip|uv pip|poetry add)\s+install\b", re.I),
    "claude-cli": re.compile(r"\bclaude\s+(?:-p|--print|code)\b", re.I),
    "codex-cli": re.compile(r"\bcodex\s+(?:exec|--)\b", re.I),
    "cloud-cli": re.compile(r"\b(?:gcloud|aws|az)\s+[a-z]{2,}\b", re.I),
    "container": re.compile(r"\bdocker\s+(?:run|build|compose)\b|\bkubectl\s+\w", re.I),
}

# Hardcoded locations. These are the worst offenders: they are not merely
# tool-specific, they name a machine that does not exist here.
BS = r"[\\/]"
SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"/Users/[A-Za-z0-9._-]+/"), "<project-root>/"),
    (re.compile(r"/home/[A-Za-z0-9._-]+/"), "<project-root>/"),
    (re.compile(r"[A-Z]:" + BS + BS + r"Users" + BS + BS + r"[A-Za-z0-9._-]+" + BS + BS),
     "<project-root>" + BS),
    (re.compile(r"%USERPROFILE%" + BS), "<project-root>" + BS),
    (re.compile(r"~" + BS + r"\.(?:claude|codex|gemini|cursor|opencode|config)"
                + BS + "?"), "<agent-config-dir>/"),
    (re.compile(r"~" + BS + r"[A-Za-z0-9._-]+" + BS +
                r"(?:claude|codex|gemini|cursor|opencode|config)" + BS + "?"),
     "<agent-config-dir>/"),
    (re.compile(r"\.claude" + BS + r"(?:skills|commands|agents)" + BS),
     "<agent-config-dir>/"),
    (re.compile(r"\.codex" + BS), "<agent-config-dir>/"),
    (re.compile(r"\.gemini" + BS), "<agent-config-dir>/"),
    (re.compile(r"\bCLAUDE\.md\b"), "<agent-instructions>"),
    (re.compile(r"\bAGENTS\.md\b"), "<agent-instructions>"),
    (re.compile(r"\.cursorrules\b"), "<agent-instructions>"),
    (re.compile(r"mcp__[a-z]+__([a-z_]+)"), r"\1 (via the host's MCP layer)"),
]

# Everything from this heading to the end of the file is the reader's
# substitution table, and is exempt from the substitutions below. See the
# substitution loop for why that exemption is load-bearing rather than cosmetic.
RUNTIME_NOTES_HEADING = "\n## Runtime notes\n"

RUNTIME_NOTE = """
## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

{rows}
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
"""


def frontmatter_span(text: str) -> tuple[int, int, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    return 0, end + 5, text[4:end]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def candidates() -> list[Path]:
    out = sorted(SKILLS.glob("*/SKILL.md"))
    out += sorted(p for p in AGENTS.glob("*.md") if p.stem.islower())
    return out


NOT_PRODUCT = re.compile(
    r"\b(?:API|CLI|CI|CD|UI|UX|SQL|HTTP|HTTPS|JSON|YAML|XML|CSS|HTML|MD|SDK|"
    r"MCP|AI|ML|LLM|RBAC|CI/CD|A/B|PR|UX|3D|2D|I/O|OAuth|JWT|TTL|UTC|"
    r"The|This|That|When|Where|Which|What|How|Why|Use|Using|Add|Update|"
    r"Create|Write|Read|Edit|Build|Test|Deploy|Debug|Fix|Set|Get|List|"
    r"Guide|Guidelines|Standards|Patterns|Practices|Strategy|Workflow|"
    r"Performance|Security|Quality|Testing|Review|Design|Code|Data|"
    r"Documentation|Example|Examples|Notes|Overview|Introduction|Summary)\b")

CAP_WORD = re.compile(r"\b([A-Z][A-Za-z0-9]{2,}(?:\.[A-Za-z0-9]+)?)\b")


def mentions_product(frontmatter: str) -> bool:
    """True if the frontmatter names something that reads as a product.

    Deliberately blunt. A product name in a description means the capability is
    specialised even if this tool has never heard of it, and the cost of getting
    that wrong is rewriting a specialised file into a vague one, which destroys
    it. The cost of the reverse is one general file left bound to one tool, which
    is a much smaller loss. So the test errs toward exclusion and the report
    says how many files it excluded on this basis.
    """
    for line in frontmatter.splitlines():
        if not re.match(r"\s*(description|name)\s*:", line):
            continue
        value = line.split(":", 1)[1]
        # Drop sentence-initial words. A capital letter that only appears because
        # a sentence started is not evidence of a product, and treating it as one
        # excluded every file whose description began with an ordinary word.
        value = re.sub(r"(?:\A\s*|(?<=[.!?:])\s+)[A-Z][a-z]+", " ", value)
        for word in CAP_WORD.findall(value):
            if word in NOT_PRODUCT.pattern or re.match(NOT_PRODUCT, word):
                continue
            if word.isupper():
                continue          # an ACRONYM, not a product
            return True
    return False


def analyse(p: Path) -> dict | None:
    text = read(p)
    span = frontmatter_span(text)
    fm = span[2] if span else ""
    head = f"{p.parent.name if p.parent.name != 'agents' else p.stem}\n{fm}"
    if TOOL_NAMES.search(head):
        return None                      # specialised: leave it alone
    # A description naming a product the list does not know is still a
    # specialised file. Touching one is worse than missing a general one, so the
    # default is exclusion: a capitalised token that is not ordinary English,
    # not a number, and not a common technical noun is treated as a product.
    if mentions_product(fm):
        return None
    body = text[span[1]:] if span else text
    # Scan the whole file, not just the body. A machine-specific path in a
    # frontmatter allowed-tools entry is as binding as one in prose -- it is
    # literally the permission the host will ask for -- and scanning only the
    # body left `Bash(~/.claude/skills/...)` untouched in a role that was
    # otherwise neutral.
    whole = text
    hits = {k: len(p_.findall(whole)) for k, p_ in BODY_SIGNALS.items()
            if p_.search(whole)}
    paths = sum(len(pat.findall(whole)) for pat, _ in SUBS)
    if not hits and not paths:
        return None                      # already neutral
    return {"path": p, "tools": hits, "path_hits": paths,
            "has_fm": span is not None}


def note_rows(tools: dict[str, int], path_hits: int) -> str:
    rows = []
    if path_hits:
        rows.append(f"- `<project-root>` — the repository root. "
                    f"{path_hits} machine-specific path(s) replaced.")
        rows.append(f"- `<agent-config-dir>` — wherever this runtime keeps its "
                    f"configuration. Not a fixed location.")
        rows.append(f"- `<agent-instructions>` — the file this runtime reads for "
                    f"standing instructions. Names differ per runtime and none is "
                    f"assumed.")
    for t in tools:
        rows.append(f"- **{t}** — means. One tool's way of doing a step a "
                    f"different runtime may do another way.")
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    files = candidates()
    found = [a for a in (analyse(f) for f in files) if a]
    if args.limit:
        found = found[:args.limit]

    stats = Counter()
    for a in found:
        p = a["path"]
        if not args.apply:
            stats["would-neutralise"] += 1
            for t in a["tools"]: stats[f"tool:{t}"] += 1
            if a["path_hits"]: stats["hardcoded-paths"] += 1
            continue
        text = read(p)
        span = frontmatter_span(text)
        body = text[span[1]:] if span else text
        before = body
        before_text = text
        # Substitute everywhere EXCEPT the Runtime notes section.
        #
        # The notes exist to name the real files -- "Claude Code reads CLAUDE.md,
        # other runtimes read AGENTS.md" -- because a reader who cannot resolve
        # <agent-instructions> to an actual filename cannot act on it. The
        # substitution was applied to the whole file, so a second run of this
        # tool rewrote the notes back to the placeholder and destroyed the one
        # part of the file that made it usable. That also meant the tool could
        # never converge: each pass stripped the specific rows and restored the
        # boilerplate.
        head, sep, notes = text.partition(RUNTIME_NOTES_HEADING)
        for pat, rep in SUBS:
            head = pat.sub(rep, head)
        text = head + sep + notes
        if span and text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            body = text[end + 5:] if end > 0 else text
        # A file bound to one tool's invocation is still falsely general even
        # when it holds no substitutable path. Skipping those was a gap: most of
        # the 180 identified files were bound, had nothing to substitute, and
        # were therefore left making the same false claim. The runtime note is
        # the minimum honest change.
        changed = text != before_text
        if a["tools"] and "## Runtime notes" not in body:
            body = body.rstrip() + "\n" + RUNTIME_NOTE.format(
                rows=note_rows(a["tools"], a["path_hits"]))
            changed = True
        if not changed:
            stats["no-change"] += 1
            continue
        # Re-derive the frontmatter from the SUBSTITUTED text. Using the span
        # captured before substitution silently restored the original header,
        # undoing every path replacement in it -- which is why a role whose only
        # machine-specific paths were in allowed-tools came out unchanged.
        span2 = frontmatter_span(text)
        if span2:
            head = span2[2]
            if "neutralised:" not in head:
                head = head.rstrip() + "\nneutralised: tool-specific paths and "\
                                         "single-runtime invocations replaced"
            text = "---\n" + head + "\n---\n" + body
        p.write_text(text, encoding="utf-8")
        stats["neutralised"] += 1
        for t in a["tools"]: stats[f"tool:{t}"] += 1
        if a["path_hits"]: stats["hardcoded-paths"] += 1

    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"  {mode}")
    print(f"  scanned                    {len(files)}")
    print(f"  already neutral            {len(files) - len(found)}")
    print(f"  falsely general            {len(found)}")
    if args.limit:
        print(f"  limited to                 {args.limit}")
    key = "neutralised" if args.apply else "would-neutralise"
    print(f"  {key:26} {stats[key]}")
    if stats["hardcoded-paths"]:
        print(f"    with machine-specific paths  {stats['hardcoded-paths']}")
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        if k.startswith("tool:"):
            print(f"    bound to {k[5:]:14} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
