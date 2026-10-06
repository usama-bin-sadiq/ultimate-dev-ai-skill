#!/usr/bin/env python3
"""Report broken internal references.

Two classes are checked, and code is excluded from both:

  links   markdown links to a sibling file that does not exist
  paths   shell/Python invocations naming a `skills/...` file that does not exist

Code is stripped first — fenced blocks, indented blocks and inline spans — so a
parenthesised token in a code sample is never mistaken for a link. Placeholder
targets (`<agent-instructions>`, `chapters/ch01-<slug>.md`) and paths that
depend on a variable or an external mount are reported separately as
`unresolved`, because a human has to judge those.

Usage:
    python3 tools/check-links.py            # report, exit 1 if broken > 0
    python3 tools/check-links.py --quiet    # only the summary
    python3 tools/check-links.py --all      # include the unresolved bucket
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FENCE = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$")
INLINE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# A bare invocation path: appears in prose or a code line as skills/<...>/file.ext
SCRIPT_REF = re.compile(r"(?<![A-Za-z0-9_./-])(skills/[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh|md|json|ya?ml|txt|tgz|svg|png|html|csv))")
PLACEHOLDER = re.compile(r"[<>]|\.\.\.|\\\$\{|\$[A-Z_]{3,}")

EXTS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".svg", ".png", ".csv"}


def strip_code(text: str) -> str:
    text = FENCE.sub("", text)
    return INLINE.sub(" ", text)


def docs() -> list[Path]:
    out = [ROOT / "SKILL.md"]
    out += sorted((ROOT / "skills").glob("*/**/*.md"))
    out += sorted((ROOT / "agents").glob("*.md"))
    out += sorted((ROOT / "tools").glob("*.md"))
    out += sorted((ROOT / "evals").glob("**/*.md"))
    return [p for p in out if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--all", action="store_true", help="also list unresolved targets")
    a = ap.parse_args()

    broken_links: dict[Path, set[str]] = {}
    broken_paths: dict[Path, set[str]] = {}
    unresolved: dict[Path, set[str]] = {}

    for doc in docs():
        raw = doc.read_text(errors="ignore")
        clean = strip_code(raw)

        for target in LINK.findall(clean):
            t = target.split("#")[0].strip()
            if not t or t.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if PLACEHOLDER.search(t):
                unresolved.setdefault(doc, set()).add(t)
                continue
            if t.startswith("/"):
                cand = ROOT / t.lstrip("/")
            else:
                cand = (doc.parent / t).resolve()
            if cand.exists():
                continue
            # a bare `foo.md` or `foo.py` sibling is usually a real target
            broken_links.setdefault(doc, set()).add(t)

        # Command paths are checked against the RAW text: they live inside code
        # fences, which is exactly what strip_code() removes.
        for ref in SCRIPT_REF.findall(raw):
            if PLACEHOLDER.search(ref):
                unresolved.setdefault(doc, set()).add(ref)
            elif not (ROOT / ref).exists():
                broken_paths.setdefault(doc, set()).add(ref)

    n_links = sum(len(v) for v in broken_links.values())
    n_paths = sum(len(v) for v in broken_paths.values())
    n_unres = sum(len(v) for v in unresolved.values())

    print(f"files scanned:        {len(docs())}")
    print(f"broken markdown links: {n_links} in {len(broken_links)} files")
    print(f"broken script paths:   {n_paths} in {len(broken_paths)} files")
    print(f"unresolved (judge me): {n_unres} in {len(unresolved)} files")

    if not a.quiet:
        for label, table in (("broken link", broken_links), ("broken path", broken_paths)):
            for f, targets in sorted(table.items()):
                print(f"\n  {label} in {f.relative_to(ROOT)}")
                for t in sorted(targets):
                    print(f"      {t}")
        if a.all:
            for f, targets in sorted(unresolved.items()):
                print(f"\n  unresolved in {f.relative_to(ROOT)}")
                for t in sorted(targets)[:12]:
                    print(f"      {t}")

    return 1 if (n_links or n_paths) else 0


if __name__ == "__main__":
    sys.exit(main())
