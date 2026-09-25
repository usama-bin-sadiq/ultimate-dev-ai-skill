#!/usr/bin/env python3
"""Validate an optional organization context pack without contacting systems."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("validate-company-context: PyYAML is required") from exc

REQUIRED = (
    "version", "kind", "status", "company", "effective_date", "owner", "scope",
    "terminology", "policies", "approvals", "templates", "unknowns", "last_verified",
)
SECRET_KEYS = {"api_key", "token", "password", "secret", "private_key", "credential"}
PLACEHOLDER = re.compile(r"<[^>]+>")


def _walk(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in SECRET_KEYS:
                errors.append(f"{path + '.' if path else ''}{key}: secret-like field is not allowed")
            errors.extend(_walk(child, f"{path + '.' if path else ''}{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk(child, f"{path}[{index}]"))
    elif isinstance(value, str) and ("://" in value and "@" in value.split("://", 1)[1]):
        errors.append(f"{path}: URL contains embedded credentials")
    return errors


def validate(path: Path, *, template: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return {"path": str(path), "ok": False, "errors": [str(exc)], "warnings": []}
    if not isinstance(data, dict):
        return {"path": str(path), "ok": False, "errors": ["root must be a mapping"], "warnings": []}
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing field: {key}")
    if data.get("kind") != "optional-company-context":
        errors.append("kind must be optional-company-context")
    if data.get("status") not in {"template", "draft", "active", "retired"}:
        errors.append("status must be template|draft|active|retired")
    scope = data.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be a mapping")
    else:
        for key in ("domains", "jurisdictions", "systems", "repositories"):
            if not isinstance(scope.get(key), list):
                errors.append(f"scope.{key} must be a list")
    for key in ("terminology", "policies", "approvals", "templates", "unknowns"):
        if key not in data:
            continue
        if key == "terminology" and not isinstance(data[key], dict):
            errors.append("terminology must be a mapping")
        elif key in {"policies", "approvals", "templates", "unknowns"} and not isinstance(data[key], (dict, list)):
            errors.append(f"{key} must be a mapping or list")
    for key in ("effective_date", "last_verified"):
        value = str(data.get(key) or "")
        if template and PLACEHOLDER.search(value):
            continue
        try:
            parsed = date.fromisoformat(value)
            if parsed > date.today():
                errors.append(f"{key} cannot be in the future")
        except ValueError:
            errors.append(f"{key} must be an ISO date")
    errors.extend(_walk(data))
    if not template:
        for key, value in data.items():
            if isinstance(value, str) and PLACEHOLDER.search(value):
                errors.append(f"{key}: template placeholder remains")
        if data.get("status") == "active" and not data.get("owner"):
            errors.append("active pack requires an owner")
    else:
        warnings.append("template mode: placeholders are allowed")
    return {
        "path": str(path),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "scope": scope if isinstance(scope, dict) else {},
        "status": data.get("status"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--template", action="store_true", help="allow template placeholders")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.path, template=args.template)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['path']}")
        for error in result["errors"]:
            print(f"  ERROR: {error}")
        for warning in result["warnings"]:
            print(f"  WARN: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
