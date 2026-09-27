#!/usr/bin/env python3
"""Repair the mechanically-fixable frontmatter defects in an imported corpus.

The validator found about 10,000 of them. Most are one of three shapes, and all
three are decidable without judgement, so fixing them by hand would be 10,000
copies of the same edit and a large chance of one being wrong.

  unquoted scalar containing ': '   6,199 files. A YAML plain scalar may not
                                    contain ': ', so `description: Use this when
                                    you need: a thing` is not merely ugly, it
                                    fails to parse in a strict parser. Fixed by
                                    quoting the value. Nothing is invented: the
                                    text is unchanged, only quoted.

  name does not match directory     576 files. Two skills can be named `review`
                                    and `review-alirezarezvani` while their
                                    frontmatter both say `review`. The directory
                                    is what the runtime resolves, so the
                                    frontmatter is corrected to match it.

  name is not kebab-case            257 files. `Name: Code Reviewer` resolves
                                    nowhere. Kebab-cased from the directory
                                    name, which is already a valid slug.

Deliberately NOT fixed here:

  unfilled placeholders             These say "Placeholder prose." or
                                    "TODO: describe this". Writing a real
                                    description means knowing what the file
                                    does, which is reading, not rewriting. Left
                                    for review and reported.

  unknown frontmatter keys          2,606 files carry keys this repository does
                                    not recognise. Some are harmless upstream
                                    metadata; some change behaviour. Widening
                                    the allowlist to make the count zero would
                                    be silencing the check, not fixing it.

Usage:
    python3 tools/repair-frontmatter.py            # report
    python3 tools/repair-frontmatter.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
# Matches both a top-level key and an indented list item, because a frontmatter
# list like `- description: Use this when: you need` is broken YAML in exactly
# the same way a top-level one is, and the first version of this only handled
# the top-level case and silently left every list item unfixed.
KEYLINE = re.compile(r"^(\s*(?:-\s+)?)([A-Za-z_][A-Za-z0-9_-]*)(\s*):(\s)(.*)$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def needs_quoting(v: str) -> bool:
    """A plain YAML scalar cannot contain ': ' or start with a quote or brace."""
    if not v:
        return False
    if v[0] in "\"'[{>|*&!%@`":
        return True
    if ": " in v or v.endswith(":"):
        return True
    if v.strip() != v:
        return True
    return False


def quote(v: str) -> str:
    if v.startswith(("'", '"')) and len(v) > 1:
        return v                                  # already quoted
    if '"' in v:
        return "'" + v.replace("'", "''") + "'"
    return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:64] or "unnamed"


def repair(text: str, dir_name: str) -> tuple[str, Counter]:
    stats: Counter = Counter()
    m = FM.match(text)
    if not m:
        return text, stats
    head, body = m.group(1), text[m.end():]
    out: list[str] = []
    for line in head.splitlines():
        km = KEYLINE.match(line)
        if not km:
            out.append(line)
            continue
        indent, key, value = km.group(1), km.group(2), km.group(4)
        if needs_quoting(value):
            # Already a quoted scalar or a block indicator: leave it. A '>-' or
            # '|' line is a block scalar header and the text follows indented;
            # rewriting that is a different edit.
            if not re.match(r"^>[-+]?\s*$", value):
                line = f"{indent}{key}: {quote(value)}"
                stats["quoted"] += 1
        out.append(line)
    head2 = "\n".join(out)

    # name must match the directory the runtime resolves, and be kebab-case
    nm = re.search(r"^name\s*:\s*(.+)$", head2, re.M)
    if nm:
        current = nm.group(1).strip().strip("\"'")
        want = slug(dir_name)
        if current != want:
            head2 = head2[:nm.start()] + f"name: {want}" + head2[nm.end():]
            stats["name-fixed"] += 1
    return "---\n" + head2 + "\n---\n" + body, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted((ROOT / "skills").glob("*/SKILL.md")) + \
        sorted(p for p in (ROOT / "agents").glob("*.md") if p.stem.islower())
    total: Counter = Counter()
    touched = 0
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        fixed, stats = repair(text, p.parent.name if p.parent.name != "agents"
                              else p.stem)
        if not stats:
            continue
        touched += 1
        total.update(stats)
        if args.apply:
            p.write_text(fixed, encoding="utf-8")
    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"  {mode}")
    print(f"  files examined   {len(files)}")
    print(f"  files changed    {touched}")
    print(f"  values quoted    {total['quoted']}")
    print(f"  names corrected  {total['name-fixed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
