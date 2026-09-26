#!/usr/bin/env python3
"""Aggregate benchmark run results into summary statistics.

Reads ``grading.json`` and ``run.json`` from each run directory and produces
``benchmark.json`` plus a human-readable ``benchmark.md``.

Supported layouts, both produced by ``run_eval.py``::

    <benchmark_dir>/eval-<id>/<config>/run-<n>/     (run_eval.py)
    <benchmark_dir>/runs/eval-<id>/<config>/run-<n>/ (legacy)

Configuration directories are discovered, not hardcoded, so ``with_skill`` /
``without_skill`` / ``old_skill`` / ``new_skill`` all work.

A metric that was never measured stays missing rather than becoming ``0.0``. A
mean over zero samples is reported as ``null`` with ``measured: 0``, so an
unmeasured metric can never be read as a perfect or failing score.

Usage:
    python scripts/aggregate_benchmark.py runs --skill-name my-skill
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/aggregate_benchmark.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import read_json  # noqa: E402


def calculate_stats(values: list) -> dict:
    """Mean/stddev/min/max over the values that were actually measured.

    ``None`` entries are dropped. When nothing was measured, ``mean`` is
    ``None`` and ``measured`` is 0 rather than a misleading 0.0.
    """
    measured = [float(v) for v in values if v is not None]
    if not measured:
        return {"mean": None, "stddev": None, "min": None, "max": None, "measured": 0}

    n = len(measured)
    mean = sum(measured) / n
    if n > 1:
        stddev = math.sqrt(sum((x - mean) ** 2 for x in measured) / (n - 1))
    else:
        stddev = 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(measured), 4),
        "max": round(max(measured), 4),
        "measured": n,
    }


def find_run_dirs(benchmark_dir: Path) -> list[Path]:
    """Locate every ``eval-*/<config>/run-*`` directory, tolerating both layouts."""
    runs_dir = benchmark_dir / "runs"
    search_dir = runs_dir if runs_dir.is_dir() else benchmark_dir
    return sorted(
        d for d in search_dir.glob("eval-*/*/run-*") if d.is_dir()
    )


def load_run_results(benchmark_dir: Path) -> dict:
    """Load every run, grouped by configuration label."""
    results: dict[str, list[dict]] = {}

    for run_dir in find_run_dirs(benchmark_dir):
        config = run_dir.parent.name
        grading = read_json(run_dir / "grading.json")
        run = read_json(run_dir / "run.json", default={}) or {}

        if grading is None:
            print(f"warning: no grading.json in {run_dir}; skipping", file=sys.stderr)
            continue

        summary = grading.get("summary", {}) or {}
        duration_ms = run.get("duration_ms")
        try:
            eval_id: object = int(run_dir.parent.parent.name.split("-", 1)[1])
        except (IndexError, ValueError):
            eval_id = run_dir.parent.parent.name
        try:
            run_number = int(run_dir.name.split("-", 1)[1])
        except (IndexError, ValueError):
            run_number = run_dir.name

        results.setdefault(config, []).append({
            "eval_id": eval_id,
            "run_number": run_number,
            # Null means no assertion was decided mechanically for this run.
            "pass_rate": summary.get("pass_rate"),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "total": summary.get("total", 0),
            "manual": summary.get("manual", 0),
            "time_seconds": (
                round(duration_ms / 1000, 3) if isinstance(duration_ms, (int, float)) else None
            ),
            "tokens": run.get("total_tokens"),
            "exit_code": run.get("exit_code"),
            "error": run.get("error"),
            "task_success": run.get("task_success"),
            "trigger_observed": run.get("trigger_observed"),
            "trigger_detection": run.get("trigger_detection"),
            "expectations": grading.get("expectations", []),
            "notes": (run.get("stderr") or "")[:500],
            "path": str(run_dir),
        })

    return results


def aggregate_results(results: dict) -> dict:
    """Summarize each configuration and the delta between the first two."""
    run_summary: dict[str, dict] = {}
    configs = list(results)

    for config in configs:
        runs = results[config]
        if not runs:
            run_summary[config] = {
                "pass_rate": calculate_stats([]),
                "time_seconds": calculate_stats([]),
                "tokens": calculate_stats([]),
            }
            continue
        run_summary[config] = {
            "pass_rate": calculate_stats([r["pass_rate"] for r in runs]),
            "time_seconds": calculate_stats([r["time_seconds"] for r in runs]),
            "tokens": calculate_stats([r["tokens"] for r in runs]),
            "runs": len(runs),
            "evals": len({r["eval_id"] for r in runs}),
        }

    delta: dict[str, object] = {}
    if len(configs) >= 2:
        primary = run_summary.get(configs[0], {}).get("pass_rate", {})
        baseline = run_summary.get(configs[1], {}).get("pass_rate", {})
        pm, bm = primary.get("mean"), baseline.get("mean")
        delta["configs"] = [configs[1], configs[0]]
        delta["pass_rate"] = (
            f"{pm - bm:+.2f}" if pm is not None and bm is not None else None
        )
        delta["pass_rate_note"] = (
            None if pm is not None and bm is not None
            else "delta unavailable: at least one side has no measured pass rate"
        )
    elif configs:
        delta["configs"] = []
        delta["pass_rate"] = None
        delta["pass_rate_note"] = "delta needs at least two configurations"

    run_summary["delta"] = delta
    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "") -> dict:
    """Build the full benchmark.json payload."""
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results)

    # Prefer real model/agent metadata when the run recorded it.
    eval_results = read_json(benchmark_dir / "eval_results.json", default={}) or {}

    runs = []
    for config, config_runs in results.items():
        for result in sorted(config_runs, key=lambda r: (str(r["eval_id"]), r["run_number"])):
            runs.append({
                "eval_id": result["eval_id"],
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "manual": result["manual"],
                    "time_seconds": result["time_seconds"],
                    "tokens": result["tokens"],
                    "exit_code": result["exit_code"],
                    "task_success": result["task_success"],
                    "trigger_observed": result["trigger_observed"],
                },
                "expectations": result["expectations"],
                "notes": [result["notes"]] if result["notes"] else [],
            })

    evals_run = sorted({str(r["eval_id"]) for r in runs}, key=lambda s: (len(s), s))
    per_config = [len(v) for v in results.values()]

    return {
        "metadata": {
            "skill_name": skill_name or eval_results.get("skill_name") or "<skill-name>",
            "skill_path": skill_path or eval_results.get("skill_path") or "<path/to/skill>",
            "agent": eval_results.get("agent"),
            "executor_model": eval_results.get("model"),
            "configurations": list(results),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": evals_run,
            "runs_per_configuration": max(per_config) if per_config else 0,
            "trigger_detection": next(
                (
                    r["trigger_detection"]
                    for v in results.values() for r in v
                    if r.get("trigger_detection")
                ),
                "none",
            ),
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }


def _fmt(value, scale: float = 1.0, suffix: str = "", digits: int = 2) -> str:
    """Format a possibly-missing metric. Missing never renders as a number."""
    if value is None:
        return "n/a"
    return f"{value * scale:.{digits}f}{suffix}"


def generate_markdown(benchmark: dict) -> str:
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    delta = run_summary.get("delta", {})

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"- **Path**: `{metadata['skill_path']}`",
        f"- **Agent**: {metadata.get('agent') or 'n/a'}",
        f"- **Model**: {metadata.get('executor_model') or 'not recorded'}",
        f"- **Date**: {metadata['timestamp']}",
        f"- **Evals**: {', '.join(metadata['evals_run']) or 'none'}"
        f" ({metadata['runs_per_configuration']} runs per configuration)",
        f"- **Trigger detection**: {metadata.get('trigger_detection', 'none')}",
        "",
    ]

    if len(configs) >= 2:
        header = " | ".join(c.replace("_", " ") for c in configs)
        sep = "|".join(["---"] * (len(configs) + 1))
        lines += [f"| Metric | {header} |", f"|{sep}|"]
        for label, key, scale, suffix, digits in (
            ("Pass rate", "pass_rate", 100, "%", 0),
            ("Time (s)", "time_seconds", 1, "", 1),
            ("Tokens", "tokens", 1, "", 0),
        ):
            cells = []
            for config in configs:
                stats = run_summary.get(config, {}).get(key, {})
                mean, sd = stats.get("mean"), stats.get("stddev")
                if mean is None:
                    cells.append("n/a")
                elif sd:
                    cells.append(f"{_fmt(mean, scale, suffix, digits)} ± {_fmt(sd, scale, suffix, digits)}")
                else:
                    cells.append(_fmt(mean, scale, suffix, digits))
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
        lines += [
            "",
            f"**Delta ({delta.get('configs', ['baseline', 'candidate'])[0]}"
            f" → {delta.get('configs', ['baseline', 'candidate'])[-1]})**: "
            f"pass rate {delta.get('pass_rate') or 'n/a'}"
            + (f" — {delta['pass_rate_note']}" if delta.get("pass_rate_note") else ""),
        ]
    elif configs:
        stats = run_summary[configs[0]].get("pass_rate", {})
        lines.append(
            f"Single configuration `{configs[0]}`: pass rate "
            f"{_fmt(stats.get('mean'), 100, '%', 0)} over {stats.get('measured', 0)} measured runs. "
            "A delta needs a second configuration."
        )
    else:
        lines.append("No runs found.")

    manual = sum(
        e.get("manual") for r in benchmark["runs"] for e in [r.get("result", {})]
    )
    if manual:
        lines += [
            "",
            f"> {manual} assertion(s) were deferred to manual review and are excluded "
            "from every pass rate above.",
        ]

    if benchmark.get("notes"):
        lines += ["", "## Notes", ""] + [f"- {n}" for n in benchmark["notes"]]

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate benchmark run results into summary statistics"
    )
    parser.add_argument("benchmark_dir", type=Path, help="Path to the benchmark directory")
    parser.add_argument("--skill-name", default="")
    parser.add_argument("--skill-path", default="")
    parser.add_argument("--output", "-o", type=Path, help="Output path for benchmark.json")
    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"error: directory not found: {args.benchmark_dir}", file=sys.stderr)
        return 1

    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path)
    if not benchmark["runs"]:
        print(
            f"error: no graded runs under {args.benchmark_dir} "
            "(expected eval-*/<config>/run-*/grading.json)",
            file=sys.stderr,
        )
        return 1

    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")
    output_md = output_json.with_suffix(".md")
    output_md.write_text(generate_markdown(benchmark), encoding="utf-8")

    print(f"Generated: {output_json}")
    print(f"Generated: {output_md}")
    run_summary = benchmark["run_summary"]
    for config in (k for k in run_summary if k != "delta"):
        stats = run_summary[config]["pass_rate"]
        mean = stats.get("mean")
        print(
            f"  {config}: "
            + (f"{mean * 100:.1f}% pass rate over {stats['measured']} measured runs"
               if mean is not None else "pass rate not measured")
        )
    delta = run_summary.get("delta", {})
    if delta.get("pass_rate") is not None:
        print(f"  delta: {delta['pass_rate']}")
    elif delta.get("pass_rate_note"):
        print(f"  delta: n/a ({delta['pass_rate_note']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
