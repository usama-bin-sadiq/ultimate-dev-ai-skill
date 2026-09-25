#!/usr/bin/env python3
"""Measure a real staged Ultimate-Dev installation without external services."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "scripts" / "install.sh"
PROTECTED = (
    "runtime/core/browser/automation.py",
    "runtime/core/sandbox/runner.py",
    "runtime/core/jev/bridge.py",
)
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache"}


def _directory_sizes(target: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for child in sorted(target.iterdir(), key=lambda item: item.name):
        if child.is_dir():
            try:
                result[child.name] = int(subprocess.run(
                    ["du", "-sk", str(child)], capture_output=True, text=True, check=True
                ).stdout.split()[0])
            except (OSError, ValueError, IndexError, subprocess.CalledProcessError):
                result[child.name] = 0
    return result


def measure() -> dict[str, Any]:
    if not INSTALLER.is_file():
        raise RuntimeError(f"installer not found: {INSTALLER}")
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-install-measure-") as directory:
        project = Path(directory)
        completed = subprocess.run(
            [str(INSTALLER), "--generic", "--project", str(project), "--yes"],
            cwd=ROOT.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        target = project / ".agents" / "skills" / "ultimate-dev"
        if completed.returncode != 0 or not target.is_dir():
            raise RuntimeError(completed.stdout + completed.stderr)
        files = [path for path in target.rglob("*") if path.is_file()]
        logical_bytes = sum(path.stat().st_size for path in files)
        du = shutil.which("du")
        allocated_kib = 0
        if du:
            result = subprocess.run([du, "-sk", str(target)], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                try:
                    allocated_kib = int(result.stdout.split()[0])
                except (ValueError, IndexError):
                    allocated_kib = 0
        cache_dirs = sorted(
            str(path.relative_to(target))
            for path in target.rglob("*")
            if path.is_dir() and path.name in CACHE_DIRS
        )
        symlinks = [str(path.relative_to(target)) for path in target.rglob("*") if path.is_symlink()]
        protected = [relative for relative in PROTECTED if (target / relative).exists()]
        return {
            "version": (target / "VERSION").read_text(encoding="utf-8").strip(),
            "allocated_kib": allocated_kib,
            "logical_bytes": logical_bytes,
            "file_count": len(files),
            "cache_directories": cache_dirs,
            "symlinks": symlinks,
            "protected_files": protected,
            "directory_kib": _directory_sizes(target),
            "installer_output": completed.stdout,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="fail if cache, symlink, or protected files remain")
    args = parser.parse_args(argv)
    result = measure()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"version: {result['version']}")
        print(f"payload: {result['allocated_kib']} KiB / {result['logical_bytes']} bytes")
        print(f"files: {result['file_count']}")
        print(f"cache directories: {len(result['cache_directories'])}")
        print(f"symlinks: {len(result['symlinks'])}")
        print(f"protected files: {len(result['protected_files'])}")
    if args.strict and (result["cache_directories"] or result["symlinks"] or result["protected_files"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
