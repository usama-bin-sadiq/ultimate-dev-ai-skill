#!/usr/bin/env python3
"""Self-test for check-links.py.

The point of this checker is to catch a link that points at nothing, so every
case below is synthetic: a minimal tree built in a temp directory, exercising
one classification. If the checker only works because it remembers the shape of
the repository it was written against, these fail and the checker is decoration.

  L1  link to a file that exists                         -> not broken
  L2  link to a bare sibling .md that does not exist      -> must FAIL (broken)
  L3  `chapters/ch01-....md` in a book companion          -> must PASS (external)
  L4  bare `foo.md` inside a `*_template.md`              -> must PASS (external)
  L5  `../references/real.md` inside a template           -> must FAIL (broken)
  L6  `${CLAUDE_SKILL_DIR}/x.md`                          -> not broken (unresolved)
  L7  http/https/mailto links                             -> not broken
  L8  the real repository keeps reporting its real gaps   -> exit 1, but no crash

L5 is the one that matters most. The template exemption exists because template
assets link to bare `foo.md` slots describing the shape of a document generated
later. Widening it to every link inside a template would let a template hide a
real dead reference -- so only slash-free targets are excused, and a template
pointing at a real subdirectory reference is still checked and still fails.
"""

from __future__ import annotations

import importlib.util
import io
import contextlib
import pathlib
import shutil
import sys
import tempfile

TOOL = pathlib.Path(__file__).resolve().parent / "check-links.py"

spec = importlib.util.spec_from_file_location("check_links", TOOL)
assert spec and spec.loader, f"cannot load {TOOL}"
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def run_tree(files: dict[str, str]) -> tuple[int, str]:
    """Run the checker against a synthetic skill tree. Returns (exit, output)."""
    root = pathlib.Path(tempfile.mkdtemp())
    real_root = cl.ROOT
    try:
        for rel, text in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        cl.ROOT = root
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cl.main()
        return rc, buf.getvalue()
    finally:
        cl.ROOT = real_root
        shutil.rmtree(root, ignore_errors=True)


def n(out: str, key: str) -> int:
    for line in out.splitlines():
        if line.startswith(key):
            return int(line.split(":")[1].strip().split()[0])
    return -1


# L1: a link to a file that exists is not broken.
rc, out = run_tree({
    "SKILL.md": "# s\n\n[guide](references/guide.md)\n",
    "references/guide.md": "# guide\n",
})
check("L1 existing target not broken", rc == 0 and n(out, "broken markdown links") == 0, out)

# L2: a bare sibling that does not exist IS broken and fails the exit code.
rc, out = run_tree({
    "SKILL.md": "# s\n\n[missing](missing.md)\n",
})
check("L2 missing sibling flagged", rc == 1 and n(out, "broken markdown links") == 1, out)

# L3: a book-chapter pointer is a documented external reference, not breakage.
rc, out = run_tree({
    "SKILL.md": "# s\n\n[ch01](chapters/ch01-introduction.md)\n",
})
check("L3 chapter pointer external", rc == 0 and n(out, "external (not bundled)") == 1, out)

# L4: a bare `foo.md` slot inside a template asset is a shape, not a dead link.
rc, out = run_tree({
    "skills/x/assets/index_template.md": "# t\n\n[glossary](glossary.md)\n",
})
check("L4 template bare-slot external", rc == 0 and n(out, "external (not bundled)") == 1, out)

# L5: a template pointing at a real subdirectory reference is STILL checked.
rc, out = run_tree({
    "skills/x/assets/index_template.md": "# t\n\n[real](../references/real.md)\n",
})
check("L5 template slash-ref still broken", rc == 1 and n(out, "broken markdown links") == 1, out)

# L6: a runtime-variable placeholder is unresolved, never broken.
rc, out = run_tree({
    "SKILL.md": "# s\n\n[jobs](${CLAUDE_SKILL_DIR}/jobs/x.md)\n",
})
check("L6 placeholder unresolved", rc == 0 and n(out, "unresolved (judge me)") == 1, out)

# L7: absolute URLs are never filesystem-resolved.
rc, out = run_tree({
    "SKILL.md": "# s\n\n[a](https://example.com/x) [b](mailto:y@z.co)\n",
})
check("L7 urls ignored", rc == 0 and n(out, "broken markdown links") == 0, out)

# L8: the real repository runs clean and still reports its genuine content gap.
buf = io.StringIO()
real_rc = None
with contextlib.redirect_stdout(buf):
    real_rc = cl.main()
real_out = buf.getvalue()
check(
    "L8 real repo runs, keeps its real gaps",
    "files scanned:" in real_out and n(real_out, "broken markdown links") > 0,
    real_out,
)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILED: {', '.join(FAILURES)}")
    sys.exit(1)
print("check-links self-test: all cases pass")
