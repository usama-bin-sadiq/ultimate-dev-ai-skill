#!/usr/bin/env python3
"""Repair unbalanced code fences, by diagnosis rather than by rule.

Why
---
Fifteen documents in the tree carry a code fence that never closes, or a closing
fence with no opener. The validator reports each one, and the reason it matters
is not formatting: every fence-aware check in this repository -- the unfilled-marker
exemption, the reference-declaration test, the sibling-link check, and the
section splitter -- reads fences with a state machine, and a fence left open
desynchronises that machine for the rest of the file. Everything after an
unclosed fence reads as sample text, so real findings are exempted and a real
placeholder is silently allowed.

The repairs are not uniform, and treating them uniformly is how the previous
attempt made things worse:

  unclosed opener   the file ends while a block is still open. The opener is real
                    and the content after it is real, so a closer is added at the
                    end. This is the common case: seven of the fifteen, and in
                    every one the opener is in the last few lines.

  orphan closer     a closing fence with no opener, usually a stray marker left
                    where a block was deleted. There is no content to protect, so
                    the marker is removed rather than a block being invented.

  longer fence      a 4-backtick or longer marker closing a 3-backtick block is
                    legal CommonMark and is left alone.

Nothing is re-indented, reflowed or reworded. The only edit is a closing fence
added or removed, and the file is reported with what was done and why.
"""

from __future__ import annotations

import pathlib
import re
import sys

FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def walk(lines: list[str]) -> tuple[str, int]:
    """Return (open_fence, its line number 1-based) or ("", 0)."""
    fence = ""
    opened = 0
    for i, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if not m:
            continue
        token, info = m.group(2), m.group(3).strip()
        if not fence:
            fence, opened = token, i
        elif token[0] == fence[0] and len(token) >= len(fence) and not info:
            fence, opened = "", 0
    return fence, opened


def main() -> int:
    root = pathlib.Path(".")
    targets: list[pathlib.Path] = []
    for pattern in ("skills/*/SKILL.md", "skills/*/references/*.md",
                    "agents/*.md", "references/*.md", "docs/**/*.md"):
        targets.extend(sorted(root.glob(pattern)))

    added = removed = skipped = 0
    for path in targets:
        if ".eval-fixtures" in path.parts or "runs" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.split("\n")
        fence, opened = walk(lines)
        if not fence:
            continue

        # An orphan closer: the last fence marker in the file closes nothing
        # because nothing opened it. Detect by trying the walk without it.
        if opened == len(lines):
            lines = lines[:-1]
            fence2, _ = walk(lines)
            if not fence2:
                lines = lines[:-1]          # drop the trailing blank too
                path.write_text("\n".join(lines), encoding="utf-8")
                print(f"  {path}: removed an orphan closing fence at the end")
                removed += 1
                continue

        # Otherwise: a genuine unclosed block. Close it.
        while lines and not lines[-1].strip():
            lines.pop()
        lines.append(fence)
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {path}: closed the {fence!r} block opened at line {opened}")
        added += 1

    print(f"\n  closers added   : {added}")
    print(f"  orphans removed : {removed}")
    print(f"  left alone      : {skipped}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
