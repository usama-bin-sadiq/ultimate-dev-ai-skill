#!/usr/bin/env python3
"""Assert the tool's fence reader and the validator's agree, file by file.

This is the check that would have caught the pointer written inside a
```markdown template in health/SKILL.md. The tool reasoned that a heading was a
real section boundary; the validator, reading the same file, thought it was
inside a code block. Both were "right" about their own rule, they were just
different rules, and the disagreement only became visible as a broken pointer
in one file.

Two readers that both claim to read fences will drift. The only thing worth
asserting is that they agree, on every file, today -- so that a change to
either one has to be a change to both.

Run:  python3 tools/test-fence-parity.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


apd = load(HERE / "apply-progressive-disclosure.py", "apd")
val = load(HERE / "validate-skills.py", "val")

files = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
print(f"  comparing on {len(files)} markdown files")

mismatched: list[tuple[str, int, int]] = []
length_bad: list[tuple[str, int, int]] = []
balanced_mismatch: list[tuple[str, bool, bool]] = []

for p in files:
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    mine = apd.fence_state_at(lines)
    if len(mine) != len(lines):
        length_bad.append((str(p.relative_to(ROOT)), len(lines), len(mine)))
        continue
    for i, line in enumerate(lines):
        if bool(mine[i]) != bool(val.in_fenced_code(p, i + 1)):
            mismatched.append((str(p.relative_to(ROOT)), i + 1, 0))
    # `balanced` and the validator's whole-file view must agree too: a document
    # one calls balanced and the other does not is the same drift, later.
    theirs = val.in_fenced_code(p, len(lines))
    if apd.balanced(text) == bool(theirs):
        balanced_mismatch.append((str(p.relative_to(ROOT)), apd.balanced(text), bool(theirs)))

print(f"  length mismatches : {len(length_bad)}")
print(f"  line mismatches   : {len(mismatched)}")
print(f"  balance mismatch  : {len(balanced_mismatch)}")

for path, a, b in length_bad[:5]:
    print(f"    LEN  {path}: {a} lines, reader returned {b}")
for path, line, _ in mismatched[:5]:
    print(f"    LINE {path}:{line}")
for path, a, b in balanced_mismatch[:5]:
    print(f"    BAL  {path}: tool balanced={a}, validator sees fence={b}")

bad = length_bad or mismatched or balanced_mismatch
if bad:
    print(f"\n  FAILED: {len(length_bad) + len(mismatched) + len(balanced_mismatch)}")
    raise SystemExit(1)
print("\n  the two readers agree on every file")
