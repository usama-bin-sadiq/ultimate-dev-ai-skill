#!/usr/bin/env python3
"""Validate an Agent Skill directory.

Checks, in order of severity:

* ``SKILL.md`` exists and has parseable YAML frontmatter.
* The frontmatter contains only keys the Agent Skills convention defines.
* ``name`` is present, kebab-case, within the length limit, and (outside
  ``--strict``) matches the directory name.
* ``description`` is present, within the length limit, and free of angle
  brackets.
* Every ``scripts/``, ``references/``, ``assets/``, ``agents/`` and
  ``eval-viewer/`` path mentioned in backticks inside SKILL.md exists. This is
  the check that catches documentation pointing at a file that was renamed or
  removed.
* ``SKILL.md`` stays under the progressive-disclosure size guidance.

Runs with or without PyYAML. Exits non-zero on errors, or on warnings when
``--strict`` is given.

Usage:
    python scripts/quick_validate.py <skill_directory> [--strict] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/quick_validate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import (  # noqa: E402
    ALLOWED_FRONTMATTER_KEYS,
    COMPATIBILITY_MAX_LENGTH,
    DESCRIPTION_MAX_LENGTH,
    NAME_MAX_LENGTH,
    have_yaml,
    parse_frontmatter,
    split_frontmatter,
)

# Directories whose backticked paths in SKILL.md are checked for existence.
_REFERENCED_DIRS = ("scripts", "references", "assets", "agents", "evals", "eval-viewer")
_REF_PATTERN = re.compile(
    r"`((?:" + "|".join(_REFERENCED_DIRS) + r")/[A-Za-z0-9_./-]+)`"
)
# Progressive-disclosure guidance: keep the main instructions short.
MAX_SKILL_MD_LINES = 500


class ValidationResult:
    """Outcome of a validation pass. Truthy when there are no errors."""

    def __init__(self, errors: list[str], warnings: list[str], name: str = ""):
        self.errors = errors
        self.warnings = warnings
        self.name = name

    @property
    def ok(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.ok

    def message(self) -> str:
        if self.ok:
            return f"Skill is valid! ({self.name})" if self.name else "Skill is valid!"
        return "Skill is invalid: " + "; ".join(self.errors)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_skill(skill_path: str | Path, strict: bool = False) -> ValidationResult:
    """Validate a skill directory and return a structured result."""
    # Resolve so that a relative argument such as "." still yields a usable
    # directory name for the name-vs-directory check.
    skill_path = Path(skill_path).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_path.exists():
        return ValidationResult([f"skill path not found: {skill_path}"], [])
    if not skill_path.is_dir():
        return ValidationResult([f"not a directory: {skill_path}"], [])

    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return ValidationResult([f"SKILL.md not found in {skill_path}"], [])

    content = skill_md.read_text(encoding="utf-8")
    front_text, body = split_frontmatter(content)
    if not front_text:
        return ValidationResult(["no YAML frontmatter found in SKILL.md"], [])

    try:
        front = parse_frontmatter(content)
    except ValueError as exc:
        return ValidationResult([str(exc)], [])
    if not front:
        return ValidationResult(["frontmatter is empty or not a mapping"], [])

    # --- key set -----------------------------------------------------------
    unexpected = sorted(set(front) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected:
        errors.append(
            f"unexpected frontmatter key(s): {', '.join(unexpected)}; "
            f"allowed: {', '.join(sorted(ALLOWED_FRONTMATTER_KEYS))}"
        )

    # --- name --------------------------------------------------------------
    name = front.get("name")
    if "name" not in front:
        errors.append("missing 'name' in frontmatter")
        name = skill_path.name
    elif not isinstance(name, str):
        errors.append(f"'name' must be a string, got {type(name).__name__}")
        name = skill_path.name
    else:
        name = name.strip()
        if not name:
            errors.append("'name' must not be empty")
        elif not re.fullmatch(r"[a-z0-9-]+", name):
            errors.append(
                f"'name' must be kebab-case (lowercase letters, digits, hyphens), got '{name}'"
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            errors.append("'name' cannot start or end with a hyphen, or contain '--'")
        if len(name) > NAME_MAX_LENGTH:
            errors.append(f"'name' is {len(name)} characters, maximum is {NAME_MAX_LENGTH}")

    if isinstance(name, str) and name and name != skill_path.name:
        message = (
            f"frontmatter name '{name}' does not match directory name "
            f"'{skill_path.name}'; most runtimes install by directory name"
        )
        (errors if strict else warnings).append(message)

    # --- description -------------------------------------------------------
    description = front.get("description")
    if "description" not in front:
        errors.append("missing 'description' in frontmatter")
    elif not isinstance(description, str):
        errors.append(f"'description' must be a string, got {type(description).__name__}")
    else:
        description = description.strip()
        if not description:
            errors.append("'description' must not be empty")
        if "<" in description or ">" in description:
            errors.append("'description' must not contain angle brackets (< or >)")
        if len(description) > DESCRIPTION_MAX_LENGTH:
            errors.append(
                f"'description' is {len(description)} characters, "
                f"maximum is {DESCRIPTION_MAX_LENGTH}"
            )

    # --- compatibility (optional) -----------------------------------------
    compatibility = front.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            errors.append(f"'compatibility' must be a string, got {type(compatibility).__name__}")
        elif len(compatibility) > COMPATIBILITY_MAX_LENGTH:
            errors.append(
                f"'compatibility' is {len(compatibility)} characters, "
                f"maximum is {COMPATIBILITY_MAX_LENGTH}"
            )

    # --- referenced paths --------------------------------------------------
    for ref in sorted(set(_REF_PATTERN.findall(body))):
        ref_clean = ref.rstrip(".,;:")
        if not (skill_path / ref_clean).exists():
            errors.append(f"SKILL.md references missing file: {ref_clean}")

    # --- size --------------------------------------------------------------
    line_count = content.count("\n") + 1
    if line_count > MAX_SKILL_MD_LINES:
        warnings.append(
            f"SKILL.md is {line_count} lines, over the {MAX_SKILL_MD_LINES}-line "
            "progressive-disclosure guidance; move detail into references/"
        )

    # --- Python scripts must not depend on PyYAML being installed ---------
    if not have_yaml():
        warnings.append(
            "PyYAML is not installed; frontmatter was parsed with the built-in "
            "fallback parser"
        )

    return ValidationResult(errors, warnings, name if isinstance(name, str) else "")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory",
    )
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    result = validate_skill(args.skill_path, strict=args.strict)

    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        for warning in result.warnings:
            print(f"warning: {warning}")
        print(result.message())
        for error in result.errors:
            print(f"  - {error}")

    if result.ok and not (args.strict and result.warnings):
        return 0
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
