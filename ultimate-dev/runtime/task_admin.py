"""Safe task lifecycle, routing, and retention administration CLI."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

from .core.engine import Runtime
from .core.retention import RetentionPolicy, TaskRetentionManager
from .core.memory import MemoryStore
from .core.memory_retention import MemoryRetentionManager, MemoryRetentionPolicy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Administer Ultimate-Dev durable tasks")
    parser.add_argument("--project-root", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="show task state")
    status.add_argument("task_id")
    health = sub.add_parser("health", help="show task and operation health")
    health.add_argument("task_id")

    for name in ("pause", "interrupt", "resume", "abandon"):
        command = sub.add_parser(name, help=f"{name} a task")
        command.add_argument("task_id")
        command.add_argument("--reason", default=None)

    cleanup = sub.add_parser("cleanup", help="plan/archive/delete old tasks")
    cleanup.add_argument("--retention", default="30d")
    cleanup.add_argument("--dry-run", action="store_true", help="print the plan without changing storage")
    cleanup.add_argument("--archive", action="store_true", help="archive eligible tasks without deleting them")
    cleanup.add_argument("--delete", action="store_true", help="delete after an exact dry-run confirmation")
    cleanup.add_argument("--confirmation-token")

    restore = sub.add_parser("restore", help="restore an archived task")
    restore.add_argument("archive_path")
    restore.add_argument("--task-id")

    memory_cleanup = sub.add_parser("memory-cleanup", help="plan or confirm memory retention cleanup")
    memory_cleanup.add_argument("--retention", default="30d")
    memory_cleanup.add_argument("--dry-run", action="store_true")
    memory_cleanup.add_argument("--delete", action="store_true")
    memory_cleanup.add_argument("--confirmation-token")

    route = sub.add_parser("route", help="classify a new user message")
    route.add_argument("text")
    route.add_argument("--task-id")
    return parser


def _duration_seconds(value: str) -> float:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhd])\s*", value, re.IGNORECASE)
    if not match:
        raise ValueError("retention must look like 30d, 12h, 30m, or 30s")
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2).lower()]
    return float(match.group(1)) * multiplier


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return _main_impl(argv)
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "code": "task_admin_error",
            "error": str(exc),
            "retryable": False,
        }, ensure_ascii=False), file=sys.stderr)
        return 2


def _main_impl(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    runtime = Runtime(args.project_root, require_jev_decision=False)
    if args.command == "status":
        result = runtime.store.load(args.task_id)
    elif args.command == "health":
        result = runtime.task_health(args.task_id)
    elif args.command in {"pause", "interrupt", "resume", "abandon"}:
        result = getattr(runtime, f"{args.command}_task")(args.task_id, reason=args.reason)
    elif args.command == "cleanup":
        policy = RetentionPolicy(max_age=args.retention)
        manager = TaskRetentionManager(args.project_root, policy=policy)
        if args.dry_run:
            # Dry-run is the first mode gate: no combination of flags may
            # archive or delete a task while the user requested a plan.
            result = manager.cleanup(dry_run=True, delete=bool(args.delete))
        elif args.delete:
            if not args.confirmation_token:
                raise SystemExit("--delete requires --dry-run first and then --confirmation-token")
            result = manager.delete_tasks(args.confirmation_token)
        elif args.archive:
            result = manager.archive_tasks()
        else:
            result = manager.cleanup(dry_run=True, delete=False)
    elif args.command == "memory-cleanup":
        manager = MemoryRetentionManager(
            MemoryStore(args.project_root),
            policy=MemoryRetentionPolicy(max_age_seconds=_duration_seconds(args.retention)),
        )
        if args.dry_run or not args.delete:
            result = manager.plan()
        else:
            if not args.confirmation_token:
                raise SystemExit("--delete requires a prior --dry-run confirmation token")
            result = manager.apply(args.confirmation_token)
    elif args.command == "restore":
        manager = TaskRetentionManager(args.project_root)
        result = manager.restore(args.archive_path, task_id=args.task_id)
    elif args.command == "route":
        current = runtime.store.load(args.task_id) if args.task_id else None
        result = runtime.route_user_message(args.text, current).to_dict()
    else:  # pragma: no cover - argparse enforces the command set
        raise SystemExit(f"unsupported command: {args.command}")
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
