#!/usr/bin/env python3
"""Rewrite upstream-collection skill references to this repo's flat layout.

Skills here were imported from many upstream plugin collections, so their
cross-references still carry the collection they came from:

    c-level-advisor/skills/ceo-advisor   ->  skills/ceo-advisor
    ../../product-team/skills/prd        ->  skills/prd

A reference is only rewritten when the target actually exists under `skills/`,
which makes the pass self-limiting: anything it cannot resolve is left for a
human. Two shapes are deliberately skipped even when the name resolves:

  * install paths   ~/.claude/skills/gstack/...   (a different skill, installed)
  * URLs            https://github.com/x/y/tree/main/skills/z

Usage:
    python3 tools/normalize-collection-refs.py --dry-run
    python3 tools/normalize-collection-refs.py
"""

import argparse
import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

# <optional ../s><optional collection>/>skills/<name>
REF = re.compile(r"(?:\.\./)*(?:[a-z][a-z0-9-]*/)?skills/([A-Za-z0-9_][A-Za-z0-9_.-]*)")
# Lines that must not be touched: URLs and absolute install locations.
SKIP_LINE = re.compile(r"https?://|github\.com|~/\.claude|\$HOME|/home/|/Users/|\.claude/skills")

# Collections that are already correct in this repo.
LOCAL = {"skills"}


def docs():
    out = [ROOT / "SKILL.md"]
    out += sorted(SKILLS.glob("*/**/*.md"))
    out += sorted((ROOT / "agents").glob("*.md"))
    out += sorted((ROOT / "tools").glob("*.md"))
    return [p for p in out if p.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any rewrite is still pending (for CI)")
    a = ap.parse_args()

    rewrites = collections.Counter()
    touched = []

    for doc in docs():
        original = doc.read_text(errors="ignore")
        lines = original.splitlines(keepends=True)
        changed = False
        for i, line in enumerate(lines):
            if SKIP_LINE.search(line):
                continue
            if "skills/" not in line:
                continue

            def repl(m):
                name = m.group(1)
                coll = m.group(0).split("skills/")[0].strip("./")
                if coll in LOCAL:
                    return m.group(0)
                # only rewrite when the flat target really exists
                if not (SKILLS / name).is_dir():
                    return m.group(0)
                rewritten = f"skills/{name}"
                # count only real changes, not already-flat references
                if rewritten != m.group(0):
                    rewrites[f"{coll}skills/{name}"] += 1
                return rewritten

            new = REF.sub(repl, line)
            if new != line:
                lines[i] = new
                changed = True
        if changed:
            touched.append(doc)
            if not a.dry_run:
                doc.write_text("".join(lines))

    total = sum(rewrites.values())
    print(f"files touched: {len(touched)}")
    print(f"references rewritten: {total}")
    print(f"distinct collection/name pairs: {len(rewrites)}")
    if a.dry_run:
        print("\ntop pairs:")
        for k, v in rewrites.most_common(15):
            print(f"  {v:>4}  {k}")
    if a.check:
        if total:
            print(f"\nFAIL {total} stale collection reference(s) remain; "
                  f"run without --check to fix")
            for k, v in rewrites.most_common(10):
                print(f"  {v:>4}  {k}")
            return 1
        print("\nno stale collection references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
