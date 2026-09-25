#!/usr/bin/env python3
"""Validate durable task state files so a resume never depends on chat history.

This tool is provider-free and dependency-free. It checks that a task state file
is a single parseable JSON document with the fields a resume needs. It also
catches the two failure modes seen in practice: YAML written with a `.json`
extension, and two JSON documents concatenated into one file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("task_id", "status", "updated_at")
TERMINAL_STATUSES = {"completed", "partial", "failed", "blocked", "not_run", "closed"}


def check_file(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"file": str(path), "ok": False, "errors": [], "warnings": []}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        result["errors"].append(f"unreadable: {exc}")
        return result
    if not text.strip():
        result["errors"].append("file is empty")
        return result
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        lowered = text.lstrip()
        if not lowered.startswith(("{", "[")):
            result["errors"].append(
                f"not JSON at line {exc.lineno}: content starts with "
                f"{lowered[:12]!r}; YAML or plain text was written with a .json name"
            )
        else:
            extra = text[exc.pos:].strip()
            result["errors"].append(
                f"invalid JSON at line {exc.lineno}"
                + (f"; trailing content begins {extra[:20]!r} (concatenated documents?)" if extra else "")
            )
        return result
    if not isinstance(document, dict):
        result["errors"].append("top level must be a JSON object")
        return result
    for field in REQUIRED_FIELDS:
        if field not in document:
            result["errors"].append(f"missing field: {field}")
    status = document.get("status")
    if isinstance(status, str) and status not in TERMINAL_STATUSES and "status" not in document:
        result["warnings"].append(f"non-terminal status {status!r} is fine for an in-flight task")
    if "schema_version" not in document:
        result["warnings"].append("no schema_version recorded")
    result["ok"] = not result["errors"]
    result["task_id"] = document.get("task_id")
    result["status"] = document
    result["status"] = document.get("status")
    return result


def check_tree(root: Path) -> dict[str, Any]:
    files = sorted(root.glob("*/state.json")) if root.is_dir() else [root]
    results = [check_file(path) for path in files if path.is_file()]
    return {
        "kind": "task_state_validation",
        "root": str(root),
        "total": len(results),
        "invalid": sum(1 for item in results if not item["ok"]),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="a state.json file or a tasks directory")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    if not args.target.exists():
        print(f"validate-task-state: not found: {args.target}")
        return 2
    report = check_tree(args.target)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["results"]:
            marker = "PASS" if item["ok"] else "FAIL"
            print(f"{marker} {item['file']} ({item.get('task_id') or 'unidentified'})")
            for error in item["errors"]:
                print(f"  ERROR: {error}")
            for warning in item["warnings"]:
                print(f"  WARN: {warning}")
        print(f"{report['total'] - report['invalid']}/{report['total']} task state files valid")
    return 1 if args.strict and report["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
