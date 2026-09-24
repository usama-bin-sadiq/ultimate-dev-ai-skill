#!/usr/bin/env python3
"""Synchronize versioned runtime configuration with the canonical VERSION file."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT.parent / "VERSION"
CONFIG_FILES = (
    ROOT / "config" / "context_budgets.yaml",
    ROOT / "config" / "models.yaml",
    ROOT / "config" / "permissions.yaml",
    ROOT / "config" / "security.yaml",
    ROOT / "config" / "workflow.yaml",
)
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
VERSION_LINE_RE = re.compile(r"^version\s*:")


class SyncVersionError(ValueError):
    """The canonical version or a managed config file is invalid."""


def read_version(path: Path = VERSION_FILE) -> str:
    if not path.is_file():
        raise SyncVersionError(f"canonical VERSION is missing: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(value):
        raise SyncVersionError(f"canonical VERSION is not semantic: {value}")
    return value


def sync_text(text: str, version: str, *, label: str = "config") -> str:
    if not SEMVER_RE.fullmatch(version):
        raise SyncVersionError(f"version is not semantic: {version}")
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if VERSION_LINE_RE.match(line)]
    if len(matches) != 1:
        raise SyncVersionError(f"{label}: expected exactly one top-level version line")
    index = matches[0]
    line = lines[index]
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line
    comment = ""
    comment_match = re.search(r"\s+#.*$", body)
    if comment_match:
        comment = comment_match.group(0)
    lines[index] = f'version: "{version}"{comment}{newline}'
    return "".join(lines)


def sync_file(path: Path, version: str, *, check: bool = False) -> bool:
    if not path.is_file():
        raise SyncVersionError(f"managed config is missing: {path}")
    original = path.read_text(encoding="utf-8")
    updated = sync_text(original, version, label=str(path))
    changed = updated != original
    if changed and not check:
        path.write_text(updated, encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if managed config versions differ")
    args = parser.parse_args(argv)
    try:
        version = read_version()
        changed = [str(path) for path in CONFIG_FILES if sync_file(path, version, check=args.check)]
    except (OSError, SyncVersionError) as exc:
        print(f"sync-version: {exc}", file=sys.stderr)
        return 1
    if args.check and changed:
        for path in changed:
            print(f"sync-version: out of sync: {path} (expected {version})", file=sys.stderr)
        return 1
    if changed:
        print(f"sync-version: synchronized {len(changed)} config file(s) to {version}")
    else:
        print(f"sync-version: already synchronized to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
