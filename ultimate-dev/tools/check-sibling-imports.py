#!/usr/bin/env python3
"""Check that every skill's scripts actually import each other.

Why this exists
---------------
22 skills shipped scripts that could not run. Each imported a sibling helper --
almost always `import _common as common` -- and that helper was never in the
tree. Nothing caught it, because:

  * `py_compile` passes. An unresolved import is a runtime error, not a syntax
    error, so every "do the recovered scripts compile?" check was green while
    the files were unusable.
  * The dangling-reference validator did not catch it either. It looks for
    paths a SKILL.md names in prose. A helper module is never named in prose --
    it appears only as an import inside a sibling script.

So a whole bug class sat in the tree behind a green build. This checks the one
thing neither of the others could: that the names a script imports are present
in its own directory.

What counts as a sibling
------------------------
Only modules that look like local helpers are checked: an underscore-prefixed
name, or one of a small set of conventional helper names. A missing
third-party package is not this tool's business -- `numpy` being uninstalled
says nothing about whether the tree is internally consistent. Excluding them
keeps the signal clean; a check that cries wolf about the environment is a
check people disable.

A directory counts as a module. `scripts/utils/` satisfies `from utils.scan
import ...` just as well as `scripts/utils.py` would, and treating only the
file form as present reported a working tree as broken.

Exit status
-----------
0 if every sibling import resolves, 1 otherwise. With --verbose, also report
the count of third-party imports deliberately not checked.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys

STDLIB = set(sys.stdlib_module_names)

# Names that indicate a module living next door rather than on PyPI.
HELPER_NAMES = {
    "_common",
    "common",
    "_catalog",
    "catalog",
    "utils",
    "util",
    "helpers",
    "shared",
    "config",
    "constants",
    "types",
    "io_utils",
    "cli",
}

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv"}


def modules_present(script_dir: str) -> set[str]:
    """Importable top-level names from a scripts/ directory.

    Both `foo.py` and a `foo/` package satisfy `import foo`, so both count.
    """
    names: set[str] = set()
    try:
        entries = os.listdir(script_dir)
    except OSError:
        return names
    for entry in entries:
        path = os.path.join(script_dir, entry)
        if os.path.isdir(path):
            if entry in SKIP_DIRS:
                continue
            if os.path.exists(os.path.join(path, "__init__.py")):
                names.add(entry)
        elif entry.endswith(".py"):
            names.add(entry[: -len(".py")])
    return names


def sibling_imports(path: str, present: set[str]) -> tuple[list[str], list[str]]:
    """Return (missing helper imports, third-party imports) for one file."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, OSError):
        return [], []

    missing: list[str] = []
    external: list[str] = []
    for node in ast.walk(tree):
        mods: list[str] = []
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods = [node.module.split(".")[0]]

        for mod in mods:
            if mod == "__future__" or mod in STDLIB or mod in present:
                continue
            # `m` may be provided by a sibling named m_something.py
            if any(p.startswith(mod + "_") for p in present):
                continue
            if mod in HELPER_NAMES:
                missing.append(mod)
            else:
                external.append(mod)
    return sorted(set(missing)), sorted(set(external))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="the skill root, e.g. ultimate-dev")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    skills_root = os.path.join(args.root, "skills")
    if not os.path.isdir(skills_root):
        print(f"no skills directory at {skills_root}", file=sys.stderr)
        return 2

    problems: list[tuple[str, str, str]] = []
    files = 0
    external_total = 0
    skills_with_scripts = 0

    for skill in sorted(os.listdir(skills_root)):
        script_dir = os.path.join(skills_root, skill, "scripts")
        if not os.path.isdir(script_dir):
            continue
        skills_with_scripts += 1
        present = modules_present(script_dir)
        for fname in sorted(os.listdir(script_dir)):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(script_dir, fname)
            files += 1
            missing, external = sibling_imports(path, present)
            external_total += len(external)
            for mod in missing:
                problems.append((skill, fname, mod))

    print(f"  skills with scripts/     : {skills_with_scripts}")
    print(f"  scripts checked          : {files}")
    print(f"  unresolved sibling import: {len(problems)}")
    if args.verbose:
        print(f"  third-party imports skipped (not this check's business): {external_total}")

    for skill, fname, mod in problems:
        print(f"    {skill}/scripts/{fname} imports {mod}, which is not in that directory")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
