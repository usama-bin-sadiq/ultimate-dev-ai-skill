#!/usr/bin/env python3
"""Package a skill directory into a distributable ``.skill`` archive.

The archive is a zip whose entries are rooted at ``<skill-name>/`` so it
unpacks into a correctly named skill directory. The skill is validated first;
packaging fails rather than shipping a skill that does not load.

Excluded from the archive: build artifacts (``__pycache__``, ``*.pyc``,
``node_modules``, virtualenvs), VCS metadata, and editor droppings
(``.DS_Store``).

An eval set is *not* excluded. ``evals/`` ships with the skill: SKILL.md points
at it as the canonical example, the test suite asserts against it, and a
package that cannot validate itself is not a deliverable.

Usage:
    python scripts/package_skill.py <path/to/skill-folder> [output-directory]
    python scripts/package_skill.py my-skill ./dist
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import zipfile
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/package_skill.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quick_validate import validate_skill  # noqa: E402

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
EXCLUDE_GLOBS = {"*.pyc", "*.pyo", "*.swp"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}


def should_exclude(rel_path: Path) -> bool:
    """True when a path (relative to the skill's parent) should be excluded."""
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDE_GLOBS)


def write_archive(skill_path: Path, output_dir: str | Path | None) -> Path | None:
    """Zip a validated skill folder, rooted at ``<skill-name>/``."""
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = skill_path.parent

    archive = output_path / f"{skill_path.name}.skill"
    try:
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for file_path in sorted(skill_path.rglob("*")):
                if not file_path.is_file():
                    continue
                arcname = file_path.relative_to(skill_path.parent)
                if should_exclude(arcname):
                    print(f"  skipped: {arcname}")
                    continue
                bundle.write(file_path, arcname)
                print(f"  added:   {arcname}")
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not create {archive}: {exc}", file=sys.stderr)
        return None

    print(f"Packaged: {archive}")
    return archive


def package_skill(
    skill_path: str | Path, output_dir: str | Path | None = None, skip_validate: bool = False
) -> Path | None:
    """Validate and zip a skill folder. Returns the archive path, or None on failure."""
    skill_path = Path(skill_path).resolve()

    if not skill_path.exists():
        print(f"error: skill folder not found: {skill_path}", file=sys.stderr)
        return None
    if not skill_path.is_dir():
        print(f"error: not a directory: {skill_path}", file=sys.stderr)
        return None
    if not (skill_path / "SKILL.md").is_file():
        print(f"error: SKILL.md not found in {skill_path}", file=sys.stderr)
        return None

    if skip_validate:
        print("warning: skipping validation as requested", file=sys.stderr)
    else:
        print("Validating skill...")
        result = validate_skill(skill_path)
        for warning in result.warnings:
            print(f"  warning: {warning}")
        if not result.ok:
            print("error: validation failed:", file=sys.stderr)
            for error in result.errors:
                print(f"  - {error}", file=sys.stderr)
            print("Fix the errors before packaging.", file=sys.stderr)
            return None
        print(f"  {result.message()}")

    return write_archive(skill_path, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a skill folder into a .skill archive")
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument(
        "output_dir", nargs="?", default=None,
        help="Directory for the .skill file (default: the skill's parent)",
    )
    parser.add_argument(
        "--skip-validate", action="store_true",
        help="Package without validating first (discouraged)",
    )
    args = parser.parse_args()

    archive = package_skill(args.skill_path, args.output_dir, args.skip_validate)
    return 0 if archive else 1


if __name__ == "__main__":
    raise SystemExit(main())
