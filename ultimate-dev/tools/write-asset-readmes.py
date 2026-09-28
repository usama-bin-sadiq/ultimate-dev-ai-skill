#!/usr/bin/env python3
"""Give every references/ directory a README.md.

Why
---
Five skills ship a references/ directory holding only non-prose assets: QML
components, JSON policy files, shell scripts, a TSV template. A directory of
assets is a legitimate shape, but two things were wrong with it.

The validator reported all five as "contains no reference files", which reads as
a defect and is not one. Rather than weaken the check -- and rather than exempt
the five, which is how the exemption lists in this repository grew to fourteen
markers -- each directory now carries a README.md saying what the assets are and
when they load. That makes the directory self-describing for a reader as well as
satisfying the check, and it is the same file a person would have written.

The check itself is not loosened. It still globs *.md and still reports a
directory that has none, which is what caught this.
"""

from __future__ import annotations

import pathlib
import sys

SK = pathlib.Path("skills")

# One line per file type, so the generated README describes what is actually
# there rather than a generic sentence.
DESCRIBE = {
    ".qml": "a Qt Quick component",
    ".json": "a structured data file",
    ".sh": "a shell script",
    ".tsx": "a TypeScript React component",
    ".ts": "a TypeScript module",
    ".py": "a Python script",
    ".tsv": "a tab-separated template",
    ".csv": "a CSV template",
    ".txt": "a plain-text template",
    ".html": "an HTML asset",
    ".css": "a stylesheet",
}


def describe(skill: str, path: pathlib.Path) -> str:
    files = sorted(p for p in path.rglob("*") if p.is_file())
    rel = [p.relative_to(path).as_posix() for p in files]
    kinds: dict[str, list[str]] = {}
    for p in files:
        kinds.setdefault(p.suffix or "(none)", []).append(p.relative_to(path).as_posix())
    lines = [
        f"# {skill} reference assets",
        "",
        f"This directory holds {len(files)} file(s) that the skill loads on demand:",
        "",
    ]
    for suffix, names in sorted(kinds.items()):
        what = DESCRIBE.get(suffix, f"a {suffix} asset")
        shown = ", ".join(f"`{n}`" for n in names[:6])
        more = f", and {len(names) - 6} more" if len(names) > 6 else ""
        lines.append(f"- {len(names)} {what}: {shown}{more}")
    lines += [
        "",
        "They are assets rather than prose, so nothing here is read during triage.",
        "Load a file when the current work unit needs it, not before.",
        "",
        "The skill's own `SKILL.md` says which file answers which situation.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    written = 0
    for path in sorted(SK.glob("*/references")):
        if not path.is_dir():
            continue
        if any(p.suffix == ".md" for p in path.rglob("*")):
            continue  # already has prose
        readme = path / "README.md"
        readme.write_text(describe(path.parent.name, path), encoding="utf-8")
        print(f"  {path}/README.md")
        written += 1
    print(f"\n  wrote {written} README.md files")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
