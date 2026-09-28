#!/usr/bin/env python3
"""Lint the plugin's manifests, check the shell and PowerShell scripts, and install the pre-commit hook.

Run it from the repository root, not the plugin directory:

    python3 scripts/check.py

What it checks
--------------
* **Manifests** — every ``*.json`` in the plugin parses, and the ones with a
  schema (``.claude-plugin/plugin.json``) have the required keys with the right
  types.
* **Skill and command frontmatter** — every ``SKILL.md`` and command ``*.md``
  starts with a ``---`` block carrying ``name`` and, for skills, a ``description``.
  A missing description means the harness can never select it, and nothing else
  in the repository will notice.
* **Shell scripts** — ``bash -n`` on every ``*.sh``, because the Bash tool runs
  zsh and a script that parses under zsh can still be invalid bash. This is not
  a substitute for running them; it catches the typo before the admin does.
* **PowerShell scripts** — **pure ASCII**. Windows PowerShell 5.1 reads a
  BOM-less ``.ps1`` as ANSI, so a single em dash decodes to mojibake that
  contains a double quote, which terminates a string and breaks the parse. That
  shipped broken once and no macOS check caught it, which is why it is here.
* **Argument parsers** — a probe for the ``--flag`` as the final argument case,
  which makes ``shift 2`` fail under ``set -e`` and exit 1 with no output at all.
* **Cross-file references** — paths named in documentation that do not exist.
  This is the check that catches the most common defect, and it is mechanical.

Then it installs (or refreshes) a pre-commit hook that patch-bumps
``.claude-plugin/plugin.json`` so a version bump cannot be forgotten.

Why a script for this
---------------------
Every one of these is a rule that has already been learned by getting it wrong.
Writing them down in a README means they get read once; running them means they
get enforced every commit.

Usage
-----
    python3 scripts/check.py                     # everything, from the repo root
    python3 scripts/check.py --skip-hook         # check only, do not install the hook
    python3 scripts/check.py --root .            # explicit plugin root
    python3 scripts/check.py --no-install-hook   # alias for --skip-hook

Exit codes: 0 everything passed, 1 findings, 2 bad input.

Provenance
----------
Reconstructed from the "Lint gate" and "Gotchas" sections of this skill's
SKILL.md, which name ``check.py``, the ASCII rule, the ``shift 2`` probe, and the
pre-commit hook. The manifests walked, the frontmatter rules, and the hook
implementation are this file's own.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# .claude-plugin/plugin.json is the one file here with a fixed contract. VERSION
# is the four-part stamp; this is the three-part translation npm and CI see.
PLUGIN_MANIFEST = Path(".claude-plugin") / "plugin.json"
VERSION_FILES = ("VERSION", Path(".claude-plugin") / "marketplace.json")

HOOK_PATH = Path(".git") / "hooks" / "pre-commit"
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "target", ".pytest_cache", ".mypy_cache", ".tox",
}
SOURCE_SUFFIXES = {".sh", ".ps1", ".py", ".js", ".ts", ".json", ".md", ".yaml", ".yml"}
MAX_BYTES = 4 * 1024 * 1024

REQUIRED_PLUGIN_KEYS = {
    "name": str,
    "version": str,
    "description": str,
}
# The arg-parser bug: `$# -lt 2` is missing, so a trailing --flag makes shift 2
# fail and set -e exits with no output.
SHIFT_GUARD = re.compile(
    r"\[\s*\$\#\s*-ge\s*\d+\s*\]|\[\s*\$\#\s*-lt\s*\d+\s*\]"
    r"|\$\(\(\s*\$\#\s*[-<>]=?\s*\d+\s*\)\)"
)


class Report:
    """Findings, with the file and line they belong to."""

    def __init__(self) -> None:
        self.errors: list[tuple[str, int, str]] = []
        self.warnings: list[tuple[str, int, str]] = []
        self.notes: list[str] = []

    def error(self, path: str, line: int, message: str) -> None:
        self.errors.append((path, line, message))

    def warn(self, path: str, line: int, message: str) -> None:
        self.warnings.append((path, line, message))

    def note(self, message: str) -> None:
        self.notes.append(message)

    @property
    def failed(self) -> bool:
        return bool(self.errors)


def iter_files(root: Path, suffixes: set[str] | None = None):
    """Every candidate file under the root, bounded, skipping build trees."""
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        yield path


# ------------------------------------------------------------------ checks --


def check_json(root: Path, report: Report) -> None:
    """Every JSON parses. A manifest that does not parse is not a manifest."""
    for path in iter_files(root, {".json"}):
        relative = str(path.relative_to(root))
        try:
            if path.stat().st_size > MAX_BYTES:
                report.warn(relative, 0, f"larger than {MAX_BYTES} bytes; not parsed")
                continue
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            report.error(relative, getattr(exc, "lineno", 0) or 0, f"invalid JSON: {exc}")


def check_plugin_manifest(root: Path, report: Report) -> None:
    """The plugin manifest has the required keys, and the version is consistent."""
    path = root / PLUGIN_MANIFEST
    if not path.is_file():
        report.note(f"no {PLUGIN_MANIFEST} found; skipping the plugin manifest check")
        return
    relative = str(PLUGIN_MANIFEST)

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(relative, exc.lineno, f"invalid JSON: {exc}")
        return
    if not isinstance(document, dict):
        report.error(relative, 0, "the manifest must be a JSON object")
        return

    for key, expected in REQUIRED_PLUGIN_KEYS.items():
        if key not in document:
            report.error(relative, 0, f"missing required key {key!r}")
        elif not isinstance(document[key], expected):
            report.error(
                relative, 0,
                f"{key!r} should be {expected.__name__}, got {type(document[key]).__name__}",
            )
        elif expected is str and not document[key].strip():
            report.error(relative, 0, f"{key!r} is empty")

    version = document.get("version")
    if isinstance(version, str) and version and not re.fullmatch(r"\d+\.\d+\.\d+", version):
        report.error(
            relative, 0,
            f"version {version!r} is not three-part semver. The four-part VERSION stamp "
            "translates to this form; see the patch-bump hook.",
        )


def frontmatter_of(path: Path) -> tuple[dict, int] | None:
    """Parse a leading ``---`` block. Returns (fields, body_start_line) or None."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            return fields, index + 1
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip().strip("'\"")
    return None


def check_frontmatter(root: Path, report: Report) -> None:
    """Every SKILL.md and command has a name, and every SKILL.md has a description."""
    for path in iter_files(root, {".md"}):
        relative = str(path.relative_to(root))
        is_skill = path.name == "SKILL.md"
        is_command = path.parent.name == "commands"
        if not (is_skill or is_command):
            continue

        parsed = frontmatter_of(path)
        if parsed is None:
            report.error(
                relative, 1,
                "no frontmatter block. The harness reads name and description from it, "
                "so a file without one is invisible.",
            )
            continue
        fields, _body = parsed

        if "name" not in fields or not fields["name"]:
            report.error(relative, 1, "frontmatter has no name")
        if is_skill:
            if "description" not in fields or not fields["description"]:
                report.error(
                    relative, 1,
                    "frontmatter has no description. Selection is matched against the "
                    "description, so a skill without one is never chosen.",
                )
            elif len(fields["description"]) > 1024:
                report.error(
                    relative, 1,
                    f"description is {len(fields['description'])} characters, over the "
                    "1024 limit",
                )
            name = fields.get("name", "")
            if name and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
                report.error(relative, 1, f"name {name!r} should be kebab-case")
            if name and name != path.parent.name:
                report.warn(
                    relative, 1,
                    f"name {name!r} does not match the directory {path.parent.name!r}. "
                    "Some loaders key on the directory.",
                )


def check_powershell_ascii(root: Path, report: Report) -> None:
    """``.ps1`` files must be pure ASCII. This is not a style rule.

    Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI. A single em dash then
    decodes to mojibake containing a double quote, which terminates a string and
    breaks the parse — on Windows only, where nothing in a macOS run can see it.
    """
    for path in iter_files(root, {".ps1"}):
        relative = str(path.relative_to(root))
        try:
            raw = path.read_bytes()
        except OSError as exc:
            report.error(relative, 0, f"unreadable: {exc}")
            continue
        for number, line in enumerate(raw.split(b"\n"), start=1):
            try:
                line.decode("ascii")
            except UnicodeDecodeError:
                offenders = sorted({
                    f"U+{byte:04X}" for byte in line if byte > 127
                })
                try:
                    text = line.decode("utf-8", errors="replace")
                    excerpt = text.strip()[:60]
                except Exception:
                    excerpt = ""
                report.error(
                    relative, number,
                    f"non-ASCII byte(s) {', '.join(offenders)} in a .ps1. Windows PowerShell "
                    f"5.1 reads this file as ANSI and the resulting mojibake breaks the "
                    f"parse. Line: {excerpt!r}",
                )


def check_shell_syntax(root: Path, report: Report) -> None:
    """``bash -n`` on every .sh.

    The Bash tool runs zsh. A script that parses under zsh can still be invalid
    bash — ``shopt`` builtins, different glob semantics — so the parse has to
    happen under bash explicitly.
    """
    bash = shutil.which("bash")
    if not bash:
        report.note("bash is not on PATH; skipping the shell syntax check")
        return

    for path in iter_files(root, {".sh"}):
        relative = str(path.relative_to(root))
        try:
            completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
                [bash, "-n", str(path)], capture_output=True, timeout=20, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            report.error(relative, 0, f"could not run bash -n: {exc}")
            continue
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            report.error(relative, 0, f"bash -n failed: {message[:300]}")


def check_arg_parsers(root: Path, report: Report) -> None:
    """Look for the ``--flag`` as the final argument failure.

    A handler that does ``shift 2`` without checking ``$#`` exits 1 under
    ``set -e`` with no output at all, which an admin reads as a broken script
    rather than as a missing argument. The fix is a ``[ $# -ge 2 ]`` guard.
    """
    for path in iter_files(root, {".sh", ".ps1"}):
        relative = str(path.relative_to(root))
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        # A shift guarded only by a case that cannot match a bare --flag.
        for number, line in enumerate(lines, start=1):
            shift = re.search(r"\b(?:shift|Shift)\s+(-?\d+)", line)
            if not shift:
                continue
            amount = abs(int(shift.group(1)))
            window = "\n".join(lines[max(0, number - 6): number])
            if SHIFT_GUARD.search(window):
                continue
            # A shift inside a case branch is fine as long as the branch matched
            # an option, which implies two arguments existed. Only flag the ones
            # with no argument-count check anywhere in the function body.
            report.warn(
                relative, number,
                f"'{line.strip()}' has no [ $# -ge {amount} ] guard within six lines. A "
                f"bare --flag as the final argument makes this shift fail, and under "
                f"set -e the script exits 1 with no output at all.",
            )


def check_referenced_paths(root: Path, report: Report) -> None:
    """Backticked paths inside documentation must exist.

    Mechanical, and it catches the most common defect in a plugin: a SKILL.md
    that names a script which was never written. The reference is confident, the
    path is wrong, and a reader follows it and finds nothing.
    """
    reference = re.compile(r"`((?:\.?[\w.-]+/)*[\w.-]+\.(?:sh|ps1|py|json|md|ts|js))`")

    for path in iter_files(root, {".md"}):
        relative = str(path.relative_to(root))
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith(("#", "//", "*")) and "`" not in line:
                continue
            for match in reference.finditer(line):
                target = match.group(1)
                if target.startswith(("http://", "https://")):
                    continue
                # Only check a path that is relative to this document or to the
                # plugin root; a bare filename in prose is a name, not a path.
                if "/" not in target:
                    continue
                candidates = [
                    path.parent / target,
                    root / target,
                    root / "scripts" / target,
                ]
                if any(candidate.exists() for candidate in candidates):
                    continue
                report.error(
                    relative, number,
                    f"references {target!r}, which does not exist. A confident reference "
                    "to a missing file is worse than no reference.",
                )


# -------------------------------------------------------------------- hook --

HOOK_SCRIPT = """#!/usr/bin/env bash
# Installed by scripts/check.py. Patch-bumps .claude-plugin/plugin.json.
#
# The four-part VERSION stamp is authoritative; the manifest carries the
# three-part translation npm and CI read. This hook keeps the two in step so a
# release cannot ship a manifest that says one thing and a VERSION that says
# another.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
MANIFEST="$ROOT/.claude-plugin/plugin.json"
VERSION_FILE="$ROOT/VERSION"

[ -f "$VERSION_FILE" ] || exit 0
[ -f "$MANIFEST" ] || exit 0

# Only touch this when the manifest is actually part of the staged change.
if ! git diff --cached --name-only | grep -qx '.claude-plugin/plugin.json'; then
  exit 0
fi

STAGED="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("version",""))' "$MANIFEST")"
python3 - "$VERSION_FILE" "$MANIFEST" "$STAGED" <<'PY'
import json
import sys

version_path, manifest_path, staged = sys.argv[1], sys.argv[2], sys.argv[3]
four = open(version_path, encoding="utf-8").read().strip()
if not four:
    sys.exit(0)

parts = four.split(".")
if len(parts) == 4:
    three = ".".join(parts[:3])
elif len(parts) == 3:
    three = four
else:
    print(f"warning: VERSION {four!r} is neither 3- nor 4-part; leaving the manifest alone")
    sys.exit(0)

if three == staged:
    sys.exit(0)

with open(manifest_path, encoding="utf-8") as handle:
    document = json.load(handle)
document["version"] = three
with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(document, handle, indent=2)
    handle.write("\\n")
print(f"plugin.json: {staged or '(unset)'} -> {three}, from VERSION {four}")
PY

git add "$MANIFEST"
"""


def install_hook(root: Path, report: Report, force: bool) -> None:
    """Write (or refresh) the pre-commit hook, and make it executable."""
    hooks_dir = root / ".git" / "hooks"
    if not (root / ".git").exists():
        report.note("not a git repository; skipping the pre-commit hook")
        return

    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        report.warn(".git/hooks", 0, f"could not create the hooks directory: {exc}")
        return

    if HOOK_PATH.exists() and not force:
        existing = HOOK_PATH.read_text(encoding="utf-8", errors="replace")
        if "Installed by scripts/check.py" in existing:
            report.note("pre-commit hook already installed by check.py; left alone")
            return
        if existing.strip() and not existing.startswith("#!"):
            report.warn(
                str(HOOK_PATH), 0,
                "a pre-commit hook is already installed and was not written by check.py. "
                "Left alone. Merge the version bump in by hand, or move that hook aside.",
            )
            return
        if existing.strip():
            report.warn(
                str(HOOK_PATH), 0,
                "a pre-commit hook is already installed and was not written by check.py. "
                "Refusing to overwrite it; --force does not override this either.",
            )
            return

    try:
        HOOK_PATH.write_text(HOOK_SCRIPT, encoding="utf-8")
        HOOK_PATH.chmod(0o755)
    except OSError as exc:
        report.warn(str(HOOK_PATH), 0, f"could not install the hook: {exc}")
        return
    report.note(f"installed {HOOK_PATH}")


# ------------------------------------------------------------------ report --


def render(report: Report, root: Path) -> str:
    lines = [
        f"plugin root: {root}",
        f"errors: {len(report.errors)}   warnings: {len(report.warnings)}",
        "",
    ]
    for path, line, message in report.errors:
        where = f"{path}:{line}" if line else path
        lines.append(f"error: {where}: {message}")
    for path, line, message in report.warnings:
        where = f"{path}:{line}" if line else path
        lines.append(f"warning: {where}: {message}")
    for message in report.notes:
        lines.append(f"note: {message}")
    if not report.errors:
        lines += [
            "",
            "This gate checks shape, encoding, and cross-references. It does not prove "
            "any script works: drive the scripts against a fake $HOME, snapshot-diff the "
            "storage tree around a destructive run, and run the .ps1 scripts on a real "
            "Windows host with PowerShell 5.1. A .ps1 verified only on macOS is "
            "unverified.",
        ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lint manifests, check shell and PowerShell scripts, install the version hook.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--root", default=None,
                        help="plugin root; default is the first parent of scripts/ holding "
                             ".claude-plugin, falling back to the working directory")
    parser.add_argument("--skip-hook", action="store_true", help="do not install the pre-commit hook")
    parser.add_argument("--no-install-hook", action="store_true", help="alias for --skip-hook")
    parser.add_argument("--force-hook", action="store_true",
                        help="rewrite a hook that check.py installed")
    return parser


def find_root(explicit: str | None) -> Path:
    """The plugin root, discovered rather than assumed.

    Run from the repository root per the SKILL.md, so the working directory is
    the answer; if that does not hold, walk up from this file looking for
    .claude-plugin.
    """
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_dir():
            raise SystemExit(f"error: --root is not a directory: {explicit}")
        return path

    candidates = [Path.cwd().resolve()]
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    for candidate in candidates:
        if (candidate / ".claude-plugin").is_dir():
            return candidate
    return candidates[0]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = find_root(args.root)
    report = Report()

    if not any(root.iterdir()):
        raise SystemExit(f"error: {root} is empty; run this from the repository root")

    check_json(root, report)
    check_plugin_manifest(root, report)
    check_frontmatter(root, report)
    check_powershell_ascii(root, report)
    check_shell_syntax(root, report)
    check_arg_parsers(root, report)
    check_referenced_paths(root, report)

    if not (args.skip_hook or args.no_install_hook):
        install_hook(root, report, args.force_hook)

    print(render(report, root), end="")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
