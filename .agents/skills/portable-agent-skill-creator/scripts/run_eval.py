#!/usr/bin/env python3
"""Evaluate a skill's behavior across a runtime, with and without the skill.

Each eval runs N times in an isolated directory seeded with the eval's fixture
files. Every run is graded against that eval's assertions by ``grade.py`` and
recorded under a stable layout that ``aggregate_benchmark.py`` consumes::

    <results-root>/eval-<id>/<config>/run-<n>/{run.json,stdout.txt,grading.json}

Trigger detection is deliberately separate from task performance and is never
inferred from provider-specific tool names. Without a detector the result
records ``trigger_observed: null``; supply ``--trigger-detector`` to plug in a
runtime-specific discovery hook.

Usage:
    python scripts/run_eval.py --eval-set evals/evals.json \\
        --skill-path ./my-skill --agent opencode --results-root runs/with_skill
    python scripts/run_eval.py ... --config without_skill --no-skill
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/run_eval.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import agent_runner  # noqa: E402
from scripts.grade import grade_run  # noqa: E402
from scripts.utils import load_evals, write_json  # noqa: E402

# `--trigger-detector` command templates get these substitutions.
_DETECTOR_FIELDS = ("run_dir", "skill_path", "query", "config", "eval_id")


def resolve_detector(command: str, context: dict[str, str]) -> bool | None:
    """Run a user-supplied trigger detector and interpret its verdict.

    Returns True/False for a decisive answer and None for anything else, so an
    unanswerable probe is recorded as unknown rather than guessed.
    """
    cmd = command
    for field in _DETECTOR_FIELDS:
        cmd = cmd.replace("{" + field + "}", str(context.get(field, "")))
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=60, cwd=context.get("run_dir") or ".",
        )
    except Exception:  # noqa: BLE001 - an unusable detector is not a failure
        return None
    if proc.returncode != 0:
        return None
    verdict = (proc.stdout or "").strip().lower()
    if verdict in ("1", "true", "yes", "y", "triggered", "used"):
        return True
    if verdict in ("0", "false", "no", "n", "not_triggered", "unused"):
        return False
    return None


def materialize_files(
    eval_item: dict, base: Path, skill_path: Path, project_root: Path
) -> list[str]:
    """Copy an eval's fixture files into the run directory.

    Relative paths are resolved against the skill directory, then the project
    root, then the caller's working directory, so a fixture path can be written
    the way a human would write it in a task description.
    """
    base.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    sources = [Path(f) for f in eval_item.get("files", [])]
    if not sources:
        return copied
    for source in sources:
        if not source.is_absolute():
            for candidate in (
                skill_path / source,
                project_root / source,
                base / source,
                Path.cwd() / source,
            ):
                if candidate.exists():
                    source = candidate
                    break
        if not source.exists():
            copied.append(f"MISSING:{source}")
            continue
        destination = base / source.name
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)
        copied.append(str(destination))
    return copied


def run_single(
    eval_item: dict,
    *,
    run_dir: Path,
    skill_path: Path,
    agent: str,
    model: str | None,
    timeout: int,
    extra_args: list[str],
    include_skill: bool,
    project_root: Path,
    detector: str | None,
    command: str | None = None,
) -> dict:
    """Execute one prompt in its own directory and grade the result."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    fixture_status = materialize_files(eval_item, run_dir, skill_path, project_root)

    prompt = eval_item["query"]
    if include_skill:
        prompt += (
            "\n\nThe skill under test is at:\n"
            f"{skill_path.resolve()}\n"
            "Read and follow its SKILL.md for this task. If this runtime has a native "
            "skill mechanism, use that instead of treating the path as task data."
        )

    registry = agent_runner.load_registry()
    try:
        spec = agent_runner.resolve_adapter(agent, registry=registry, command=command)
    except (ValueError, SystemExit) as exc:
        record = {
            "exit_code": None, "stdout": "", "stderr": str(exc),
            "duration_ms": None, "error": "AdapterError", "agent": agent,
        }
    else:
        argv = agent_runner.build_command(
            agent, prompt, model, extra_args, command, registry
        )
        executable = spec.get("executable")
        if executable and not shutil.which(executable):
            record = {
                "exit_code": None, "stdout": "",
                "stderr": f"executable not found on PATH: {executable}",
                "duration_ms": None, "error": "ExecutableNotFound", "agent": agent,
            }
        else:
            # The runtime runs INSIDE the run directory. The directory is
            # seeded with the eval's fixture files and every artifact the run
            # produces lands there, which is also where the assertions look.
            # Running in the caller's cwd instead would scatter artifacts
            # outside the sandbox and make every file assertion vacuously fail.
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    argv, cwd=run_dir, capture_output=True, text=True,
                    timeout=timeout, env=agent_runner.build_env(spec),
                )
                record = {
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout or "",
                    "stderr": proc.stderr or "",
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "error": None,
                    "agent": agent,
                }
            except subprocess.TimeoutExpired as exc:
                record = {
                    "exit_code": None,
                    "stdout": _text(exc.stdout), "stderr": _text(exc.stderr),
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "error": "Timeout", "agent": agent,
                }
            except Exception as exc:  # noqa: BLE001
                record = {
                    "exit_code": None, "stdout": "", "stderr": str(exc),
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "error": type(exc).__name__, "agent": agent,
                }

    usage = agent_runner.extract_usage(record.get("stdout") or "")
    record["total_tokens"] = usage.get("total_tokens")

    # Grade against the eval's assertions, in the run directory.
    grading = grade_run(
        eval_item.get("assertions") or [],
        base=run_dir,
        stdout=record.get("stdout", ""),
        stderr=record.get("stderr", ""),
        exit_code=record.get("exit_code"),
    )

    # Task success: the runtime completed, and no decided assertion failed.
    # A run with no assertions is judged on exit status alone, which is a real
    # signal and is labelled as such in the record.
    summary = grading["summary"]
    assertions_decided = summary["total"] > 0
    task_ok = record.get("exit_code") == 0 and summary["failed"] == 0
    record["task_success"] = task_ok
    record["assertions_decided"] = assertions_decided
    # Recorded on the run itself so a run directory is self-describing: the
    # reviewer and the aggregator do not need the parent eval set to interpret it.
    record["query"] = eval_item["query"]
    record["eval_id"] = eval_item.get("id")
    record["should_trigger"] = eval_item["should_trigger"]
    record["expected_output"] = eval_item.get("expected_output", "")
    record["assertions"] = eval_item.get("assertions") or []
    record["trigger_observed"] = (
        resolve_detector(detector, {
            "run_dir": str(run_dir), "skill_path": str(skill_path.resolve()),
            "query": eval_item["query"], "config": run_dir.parent.name,
            "eval_id": str(eval_item.get("id")),
        })
        if detector else None
    )
    record["trigger_detection"] = "user-detector" if detector else "none"
    record["fixture_status"] = fixture_status

    # Persist the run.
    (run_dir / "stdout.txt").write_text(record.get("stdout") or "", encoding="utf-8")
    (run_dir / "stderr.txt").write_text(record.get("stderr") or "", encoding="utf-8")
    write_json(run_dir / "grading.json", grading)
    write_json(run_dir / "run.json", record)
    return record


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_eval(
    evals: list[dict],
    *,
    skill_path: Path,
    agent: str = "auto",
    model: str | None = None,
    num_workers: int = 4,
    timeout: int = 300,
    runs_per_query: int = 1,
    extra_args: list[str] | None = None,
    results_root: Path = Path("runs"),
    config: str = "with_skill",
    include_skill: bool = True,
    project_root: Path | None = None,
    detector: str | None = None,
    command: str | None = None,
) -> dict:
    """Run every eval ``runs_per_query`` times and summarize per eval."""
    skill_path = Path(skill_path).resolve()
    results_root = Path(results_root)
    project_root = Path(project_root or Path.cwd()).resolve()
    extra_args = list(extra_args or [])

    jobs: list[tuple[dict, int, Path]] = []
    for eval_item in evals:
        for n in range(1, max(1, runs_per_query) + 1):
            jobs.append((
                eval_item, n,
                results_root / f"eval-{eval_item['id']}" / config / f"run-{n}",
            ))

    records: dict[int, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=max(1, num_workers)) as pool:
        futures = {
            pool.submit(
                run_single,
                eval_item,
                run_dir=run_dir,
                skill_path=skill_path,
                agent=agent,
                model=model,
                timeout=timeout,
                extra_args=extra_args,
                include_skill=include_skill,
                project_root=project_root,
                detector=detector,
                command=command,
            ): eval_item["id"]
            for eval_item, _n, run_dir in jobs
        }
        for future in as_completed(futures):
            eval_id = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # noqa: BLE001 - a worker crash is data
                record = {
                    "exit_code": None, "stdout": "", "stderr": repr(exc),
                    "duration_ms": None, "error": type(exc).__name__,
                    "task_success": False, "assertions_decided": False,
                    "trigger_observed": None, "trigger_detection": "none",
                }
            records.setdefault(eval_id, []).append(record)

    # Aggregate per eval.
    summaries: list[dict] = []
    for eval_item in evals:
        runs = records.get(eval_item["id"], [])
        successes = sum(1 for r in runs if r.get("task_success"))
        triggers = [r.get("trigger_observed") for r in runs]
        decided_triggers = [t for t in triggers if t is not None]
        durations = [r["duration_ms"] for r in runs if r.get("duration_ms") is not None]
        tokens = [r["total_tokens"] for r in runs if r.get("total_tokens") is not None]
        assertion_rates = [
            r for r in runs
            if r.get("assertions_decided")
        ]
        summaries.append({
            "id": eval_item["id"],
            "query": eval_item["query"],
            "should_trigger": eval_item["should_trigger"],
            "runs": len(runs),
            "successful_runs": successes,
            # `pass` stays the summary verdict used by the improve loop.
            "pass": bool(runs) and successes >= max(1, len(runs) // 2),
            "trigger_observed": (
                sum(1 for t in decided_triggers if t) if decided_triggers else None
            ),
            "trigger_detection": runs[0]["trigger_detection"] if runs else "none",
            "duration_ms": sum(durations) if durations else None,
            "total_tokens": sum(tokens) if tokens else None,
            "assertions_decided": bool(assertion_rates),
            "runs_detail": runs,
        })

    write_json(results_root / "eval_results.json", {
        "skill_path": str(skill_path),
        "agent": agent,
        "model": model,
        "config": config,
        "include_skill": include_skill,
        "runs_per_query": runs_per_query,
        "command": command,
        "results": summaries,
        "summary": {
            "total": len(summaries),
            "passed": sum(1 for s in summaries if s["pass"]),
            "failed": sum(1 for s in summaries if not s["pass"]),
        },
    })
    return {
        "skill_path": str(skill_path),
        "agent": agent,
        "model": model,
        "config": config,
        "command": command,
        "results": summaries,
        "summary": {
            "total": len(summaries),
            "passed": sum(1 for s in summaries if s["pass"]),
            "failed": sum(1 for s in summaries if not s["pass"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a skill across a runtime")
    parser.add_argument("--eval-set", required=True, help="Path to the eval set JSON")
    parser.add_argument("--skill-path", required=True, help="Skill directory under test")
    parser.add_argument("--agent", default=os.environ.get("AGENT_TOOL", "auto"))
    parser.add_argument(
        "--command", default=os.environ.get("AGENT_COMMAND"),
        help="Command prefix for --agent custom. Also settable via AGENT_COMMAND.",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--runs-per-query", type=int, default=1)
    parser.add_argument("--extra-args", nargs="*", default=[])
    parser.add_argument("--results-root", default="runs", help="Directory for run artifacts")
    parser.add_argument("--config", default="with_skill", help="Configuration label")
    parser.add_argument(
        "--no-skill", action="store_true",
        help="Baseline run: do not point the runtime at the skill",
    )
    parser.add_argument(
        "--project-root", default=None,
        help="Working directory for the runtime (default: current directory)",
    )
    parser.add_argument(
        "--trigger-detector", default=None,
        help="Shell command that decides whether the skill was triggered. "
             "Placeholders: {run_dir} {skill_path} {query} {config} {eval_id}. "
             "Print 1/0 to decide; anything else records unknown.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    try:
        _skill_name, evals = load_evals(Path(args.eval_set))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = run_eval(
        evals,
        skill_path=Path(args.skill_path),
        agent=args.agent,
        model=args.model,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        extra_args=args.extra_args,
        results_root=Path(args.results_root),
        config=args.config,
        include_skill=not args.no_skill,
        project_root=Path(args.project_root) if args.project_root else None,
        detector=args.trigger_detector,
        command=args.command,
    )

    for item in output["results"]:
        status = "PASS" if item["pass"] else "FAIL"
        trigger = (
            f"trigger={item['trigger_observed']}/{item['runs']}"
            if item["trigger_observed"] is not None
            else "trigger=n/a"
        )
        print(
            f"[{status}] {item['id']} {trigger} "
            f"success={item['successful_runs']}/{item['runs']} "
            f"expected_trigger={item['should_trigger']}: {item['query'][:64]}",
            file=sys.stderr if args.verbose else sys.stdout,
        )
    print(json.dumps(output["summary"], indent=2))
    return 0 if output["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
