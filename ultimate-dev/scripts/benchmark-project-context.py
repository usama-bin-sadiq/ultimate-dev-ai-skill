#!/usr/bin/env python3
"""Benchmark project-context generation on a local checkout without installing dependencies."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("benchmark-project-context: PyYAML is required") from exc

SKILL_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = SKILL_ROOT / "scripts" / "generate-project-context.py"
REQUIRED = {
    "version", "project", "project_root", "purpose", "stack", "manifests",
    "entrypoints", "important_paths", "path_rules", "commands", "conventions",
    "constraints", "verification", "provenance", "unknowns", "last_verified",
}


def benchmark(project: Path) -> dict[str, Any]:
    project = project.expanduser().resolve()
    if not project.is_dir():
        raise RuntimeError(f"project directory not found: {project}")
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-project-benchmark-") as directory:
        recipe_path = Path(directory) / "context.yaml"
        completed = subprocess.run(
            [sys.executable, str(GENERATOR), "--project", str(project), "--output", str(recipe_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout + completed.stderr)
        recipe = yaml.safe_load(recipe_path.read_text(encoding="utf-8")) or {}
    missing = sorted(REQUIRED - set(recipe))
    commands = recipe.get("commands") if isinstance(recipe.get("commands"), list) else []
    command_statuses = [str(item.get("status")) for item in commands if isinstance(item, dict)]
    checks = {
        "required_fields_present": not missing,
        "all_candidate_commands_not_run": all(status == "not_run" for status in command_statuses),
        "provenance_present": isinstance(recipe.get("provenance"), dict),
        "unknowns_explicit": isinstance(recipe.get("unknowns"), list) and bool(recipe["unknowns"]),
        "dependencies_installed": False,
    }
    errors = []
    if missing:
        errors.append(f"missing recipe fields: {', '.join(missing)}")
    if not checks["all_candidate_commands_not_run"]:
        errors.append("candidate command status must be not_run")
    if not checks["provenance_present"]:
        errors.append("recipe provenance is missing")
    if not checks["unknowns_explicit"]:
        errors.append("recipe must retain explicit unknowns")
    return {
        "project": str(project),
        "skill": str(SKILL_ROOT),
        "status": "fail" if errors else "pass",
        "checks": checks,
        "metrics": {
            "manifests_detected": len(recipe.get("manifests") or []),
            "stack_signals": len(recipe.get("stack") or []),
            "important_paths": len(recipe.get("important_paths") or []),
            "path_rules": len(recipe.get("path_rules") or []),
            "candidate_commands": len(commands),
            "unknowns": len(recipe.get("unknowns") or []),
        },
        "errors": errors,
        "limitations": [
            "This is project-context extraction only; it does not build, test, or execute the target project.",
            "Detected commands remain not_run until a host or user verifies them.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = benchmark(args.project)
    except RuntimeError as exc:
        print(f"benchmark-project-context: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"project: {result['project']}")
        print(f"metrics: {result['metrics']}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 1 if args.strict and result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
