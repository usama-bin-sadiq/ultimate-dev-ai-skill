#!/usr/bin/env python3
"""Generate a small, evidence-based project-context recipe.

The generator is provider-free and read-only by default. It reports detected
files and candidate commands as unverified until a human or host actually runs
them. Use ``--output`` only when writing the recipe is explicitly intended.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECT = ROOT.parent
MANIFEST_FILES = (
    "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "gradle.properties", "gradlew", "Gemfile", "composer.json", "Makefile",
)
PATH_CANDIDATES = ("src", "app", "lib", "packages", "services", "tests", "test", "docs", "infra")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _simple_make_targets(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    targets: list[str] = []
    for line in lines:
        match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if match and match.group(1) not in targets:
            targets.append(match.group(1))
    return targets


def _candidate_commands(project: Path) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    package = project / "package.json"
    if package.is_file():
        scripts = _read_json(package).get("scripts")
        if isinstance(scripts, dict):
            for name in ("build", "test", "lint", "start", "dev"):
                if isinstance(scripts.get(name), str) and scripts[name].strip():
                    commands.append({
                        "name": name,
                        "command": f"npm run {name}",
                        "status": "not_run",
                        "source": "package.json",
                    })
    pyproject = project / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace").lower()
        if "pytest" in text:
            commands.append({"name": "test", "command": "pytest", "status": "not_run", "source": "pyproject.toml"})
    if (project / "Cargo.toml").is_file():
        commands.append({"name": "build", "command": "cargo check", "status": "not_run", "source": "Cargo.toml"})
        commands.append({"name": "test", "command": "cargo test", "status": "not_run", "source": "Cargo.toml"})
    if (project / "go.mod").is_file():
        commands.append({"name": "test", "command": "go test ./...", "status": "not_run", "source": "go.mod"})
    makefile = project / "Makefile"
    if makefile.is_file():
        for target in _simple_make_targets(makefile):
            if target in {"build", "test", "lint", "run", "check"}:
                commands.append({"name": target, "command": f"make {target}", "status": "not_run", "source": "Makefile"})
    if (project / "gradlew").is_file():
        commands.extend([
            {"name": "build", "command": "./gradlew build", "status": "not_run", "source": "gradlew"},
            {"name": "test", "command": "./gradlew test", "status": "not_run", "source": "gradlew"},
        ])
    return commands


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {{}}")
            elif isinstance(item, list):
                if item:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_yaml_lines(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: []")
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _path_rules(project: Path) -> list[str]:
    rules: list[str] = []
    package = _read_json(project / "package.json") if (project / "package.json").is_file() else {}
    workspaces = package.get("workspaces")
    if isinstance(workspaces, list):
        for workspace in workspaces:
            if isinstance(workspace, str):
                rules.append(f"{workspace}: workspace/package boundary; inspect before editing")
    if (project / "tsconfig.json").is_file():
        rules.append("src/**: TypeScript/JavaScript source governed by tsconfig.json")
    if (project / "pyproject.toml").is_file():
        rules.append("src/**: Python package boundary declared by pyproject.toml")
    for directory, label in (
        ("platform", "platform modules"),
        ("community", "community edition code"),
        ("plugins", "plugin modules"),
        ("gradle", "Gradle build configuration"),
    ):
        if (project / directory).is_dir() and not any(item.startswith(f"{directory}/") for item in rules):
            rules.append(f"{directory}/**: {label}; inspect build and ownership rules")
    for directory, label in (
        ("src", "application source"),
        ("app", "application entrypoints"),
        ("services", "service boundaries"),
        ("tests", "test/verification scope"),
        ("docs", "documentation scope"),
        ("infra", "infrastructure changes"),
    ):
        if (project / directory).is_dir() and not any(item.startswith(f"{directory}/") for item in rules):
            rules.append(f"{directory}/**: {label}; verify before changing")
    return rules


def build_recipe(project: Path) -> dict[str, Any]:
    project = project.expanduser().resolve()
    manifests = [name for name in MANIFEST_FILES if (project / name).is_file()]
    stack: list[str] = []
    if (project / "package.json").is_file():
        package = _read_json(project / "package.json")
        dependencies = package.get("dependencies")
        if isinstance(dependencies, dict):
            for name in ("react", "vue", "next", "express", "typescript"):
                if name in dependencies:
                    stack.append(name)
        if "typescript" in str(dependencies).lower() or (project / "tsconfig.json").is_file():
            stack.append("typescript")
    if (project / "pyproject.toml").is_file() or (project / "requirements.txt").is_file():
        stack.append("python")
    if (project / "Cargo.toml").is_file():
        stack.append("rust")
    if (project / "go.mod").is_file():
        stack.append("go")
    gradle_manifests = ("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
    if any((project / name).is_file() for name in gradle_manifests):
        stack.extend(["java", "kotlin"])
    important_paths = [name for name in PATH_CANDIDATES if (project / name).exists()]
    readme = project / "README.md"
    purpose = "Not extracted; verify from README and project instructions." if not readme.is_file() else "See README.md; summarize purpose after review."
    return {
        "version": "1.0",
        "project": project.name,
        "project_root": str(project),
        "purpose": purpose,
        "stack": sorted(set(stack)),
        "manifests": manifests,
        "entrypoints": [],
        "important_paths": important_paths,
        "path_rules": _path_rules(project),
        "commands": _candidate_commands(project),
        "conventions": [],
        "constraints": [],
        "verification": ["All generated commands are candidates and remain not_run until executed."],
        "provenance": {
            "generator": "scripts/generate-project-context.py",
            "sources_inspected": manifests + (["README.md"] if readme.is_file() else []),
            "command_status": "not_run",
        },
        "unknowns": ["Purpose, entrypoints, conventions, and approved commands require project review."],
        "last_verified": date.today().isoformat(),
    }


def render(recipe: dict[str, Any]) -> str:
    return "\n".join(_yaml_lines(recipe)) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--output", type=Path, help="write the generated recipe explicitly")
    parser.add_argument("--check", action="store_true", help="fail when --output is stale")
    args = parser.parse_args(argv)
    recipe = build_recipe(args.project)
    rendered = render(recipe)
    if args.output:
        if args.check:
            if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
                print(f"project context is stale: {args.output}", file=sys.stderr)
                return 1
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
