#!/usr/bin/env python3
"""Drive the evaluate-then-improve loop for a skill's description.

Each iteration evaluates the current description, records the result, and asks
the runtime for a better one. Held-out evals are scored but never shown to the
improver, so the reported best description is chosen on data the generator never
saw. A proposal that fails validation is rejected and the current description is
kept, so the loop cannot regress.

The loop needs a runtime to propose descriptions. ``--dry-run`` performs every
structural check and prints the plan without invoking anything, which is how the
test suite exercises this file on a host with no agent CLI installed.

Usage:
    python scripts/run_loop.py --eval-set evals/evals.json --skill-path ./my-skill \\
        --agent opencode --max-iterations 3
    python scripts/run_loop.py --eval-set evals/evals.json --skill-path ./my-skill --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import webbrowser
from pathlib import Path

if __package__ in (None, ""):  # allow `python scripts/run_loop.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import agent_runner  # noqa: E402
from scripts.improve_description import improve_description  # noqa: E402
from scripts.run_eval import run_eval  # noqa: E402
from scripts.utils import load_evals, parse_skill_md, write_json  # noqa: E402


def split_eval_set(
    eval_set: list[dict], holdout: float, seed: int = 42
) -> tuple[list[dict], list[dict]]:
    """Split evals into train and held-out sets, stratified by should_trigger."""
    if holdout <= 0 or len(eval_set) < 2:
        return list(eval_set), []

    rng = random.Random(seed)
    positives = [e for e in eval_set if e["should_trigger"]]
    negatives = [e for e in eval_set if not e["should_trigger"]]
    rng.shuffle(positives)
    rng.shuffle(negatives)

    def take(group: list[dict]) -> tuple[list[dict], list[dict]]:
        # Only hold something out when something remains to train on.
        n = min(max(1, int(len(group) * holdout)), max(0, len(group) - 1))
        return group[:n], group[n:]

    pos_test, pos_train = take(positives)
    neg_test, neg_train = take(negatives)
    return pos_train + neg_train, pos_test + neg_test


def evaluate(
    evals: list[dict],
    *,
    skill_path: Path,
    description: str,
    iteration: int,
    args: argparse.Namespace,
    results_root: Path,
    project_root: Path,
) -> dict:
    """Run one evaluation pass, overriding the description under test."""
    output = run_eval(
        evals,
        skill_path=skill_path,
        agent=args.agent,
        model=args.model,
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        extra_args=args.extra_args,
        results_root=results_root / f"iteration-{iteration}",
        config=args.config,
        include_skill=not args.no_skill,
        project_root=project_root,
        detector=args.trigger_detector,
        command=args.command,
    )
    # The description is the variable under test. Record it on the run so a
    # results directory is self-describing rather than needing side metadata.
    output["description"] = description
    output["iteration"] = iteration
    return output


def _partition(results: list[dict], train_queries: set[str]) -> tuple[list[dict], list[dict]]:
    train = [r for r in results if r["query"] in train_queries]
    test = [r for r in results if r["query"] not in train_queries]
    return train, test


def _score(results: list[dict]) -> dict:
    return {
        "passed": sum(1 for r in results if r["pass"]),
        "failed": sum(1 for r in results if not r["pass"]),
        "total": len(results),
    }


def _trigger_metrics(results: list[dict]) -> dict | None:
    """Precision/recall over trigger detection, or None when undetectable.

    Reported only when a detector actually produced verdicts, so the loop never
    presents a precision figure that was never measured.
    """
    tp = fp = fn = tn = 0
    for r in results:
        observed = r.get("trigger_observed")
        if observed is None:
            continue
        expected = bool(r["should_trigger"])
        if observed and expected:
            tp += 1
        elif observed and not expected:
            fp += 1
        elif not observed and expected:
            fn += 1
        else:
            tn += 1
    total = tp + fp + fn + tn
    if total == 0:
        return None
    return {
        "true_positive": tp, "false_positive": fp,
        "false_negative": fn, "true_negative": tn,
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else None,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else None,
        "accuracy": round((tp + tn) / total, 4),
    }


def report_iteration(label: str, results: list[dict], verbose: bool) -> None:
    if not verbose:
        return
    score = _score(results)
    metrics = _trigger_metrics(results)
    trigger_text = (
        f" precision={metrics['precision']} recall={metrics['recall']}"
        if metrics and metrics["precision"] is not None
        else " (trigger detection not configured)"
    )
    print(
        f"{label}: {score['passed']}/{score['total']} evals passed{trigger_text}",
        file=sys.stderr,
    )
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        observed = r.get("trigger_observed")
        observed_text = f"trigger={observed}/{r['runs']}" if observed is not None else "trigger=n/a"
        print(
            f"  [{status}] {observed_text} expected={r['should_trigger']}: {r['query'][:60]}",
            file=sys.stderr,
        )


def run_loop(
    *,
    evals: list[dict],
    skill_path: Path,
    description_override: str | None = None,
    args: argparse.Namespace,
    results_dir: Path | None = None,
    project_root: Path | None = None,
) -> dict:
    """Run the loop to completion and return the best description found."""
    project_root = project_root or Path.cwd()
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description

    train_set, test_set = split_eval_set(evals, args.holdout)
    train_queries = {e["query"] for e in train_set}

    history: list[dict] = []
    proposals: list[dict] = []
    exit_reason = "unknown"
    best: dict | None = None
    started = time.monotonic()

    for iteration in range(1, args.max_iterations + 1):
        if args.verbose:
            print(f"\n{'=' * 60}\nIteration {iteration}/{args.max_iterations}\n{'=' * 60}",
                  file=sys.stderr)
            print(f"Description: {current_description}", file=sys.stderr)

        # Train and held-out evals are evaluated in one batch so a runtime that
        # supports parallel work is used efficiently.
        output = evaluate(
            train_set + test_set,
            skill_path=skill_path,
            description=current_description,
            iteration=iteration,
            args=args,
            results_root=results_dir or Path("runs"),
            project_root=project_root,
        )
        all_results = output["results"]
        train_results, test_results = _partition(all_results, train_queries)
        train_score, test_score = _score(train_results), _score(test_results)

        report_iteration("Train", train_results, args.verbose)
        report_iteration("Test ", test_results, args.verbose)

        record = {
            "iteration": iteration,
            "description": current_description,
            "train": train_score,
            "test": test_score,
            "trigger_metrics": _trigger_metrics(all_results),
            "results": all_results,
        }
        history.append(record)

        if best is None or _rank(record) > _rank(best):
            best = record

        if train_score["failed"] == 0 and train_score["total"] > 0:
            exit_reason = f"all train evals passed (iteration {iteration})"
            if args.verbose:
                print(f"\nAll train evals passed on iteration {iteration}.", file=sys.stderr)
            break
        if iteration == args.max_iterations:
            exit_reason = f"max_iterations ({args.max_iterations})"
            break

        if args.verbose:
            print("\nRequesting a better description...", file=sys.stderr)

        proposal_started = time.monotonic()
        blinded = [
            {k: v for k, v in h.items() if not k.startswith("test")}
            for h in history
        ]
        new_description, report = improve_description(
            name,
            content,
            current_description,
            {"results": train_results, "summary": train_score},
            blinded,
            agent=args.agent,
            model=args.model,
            timeout=args.timeout,
            extra_args=args.extra_args,
            command=args.command,
        )
        report["iteration"] = iteration
        report["elapsed_ms"] = round((time.monotonic() - proposal_started) * 1000)
        proposals.append(report)

        if args.verbose:
            verdict = "accepted" if report.get("accepted") else "rejected"
            detail = report.get("problems") or []
            print(f"Proposal {verdict} in {report['elapsed_ms']}ms {detail}", file=sys.stderr)
            if report.get("accepted"):
                print(f"  {new_description}", file=sys.stderr)

        if not report.get("accepted") and report.get("problems", [""])[0].startswith(
            "proposal unavailable"
        ):
            exit_reason = f"proposal unavailable at iteration {iteration}"
            break

        current_description = new_description

    if best is None:  # max_iterations < 1
        exit_reason = "no iterations were run"
        best = {
            "iteration": 0, "description": current_description,
            "train": {"passed": 0, "failed": 0, "total": 0},
            "test": {"passed": 0, "failed": 0, "total": 0},
        }

    return {
        "skill_name": name,
        "skill_path": str(skill_path),
        "exit_reason": exit_reason,
        "original_description": original_description,
        "best_description": best["description"],
        "best_iteration": best["iteration"],
        "best_train": best["train"],
        "best_test": best["test"] if test_set else None,
        "final_description": current_description,
        "improved": best["description"] != original_description,
        "iterations_run": len(history),
        "holdout": args.holdout,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "history": history,
        "proposals": proposals,
    }


def _rank(record: dict) -> tuple:
    """Order two iterations. Held-out score first, then train, then earlier.

    Earlier iterations win ties, so the simplest description that performed
    equally well is preferred.
    """
    return (
        record["test"]["passed"],
        record["train"]["passed"],
        -record["iteration"],
    )


def apply_description(skill_path: Path, description: str) -> bool:
    """Rewrite the description in a SKILL.md frontmatter block.

    Returns False and changes nothing when the frontmatter cannot be located,
    so a failed apply never corrupts a skill.
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        return False
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    head, tail = text[3:end], text[end:]

    escaped = description.replace('"', '\\"')
    replaced, count = re.subn(
        r"^description:.*$", f'description: "{escaped}"', head, count=1, flags=re.MULTILINE
    )
    if count == 0:
        return False
    skill_md.write_text("---" + replaced + tail, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the eval + improve loop")
    parser.add_argument("--eval-set", required=True, help="Path to the eval set JSON")
    parser.add_argument("--skill-path", required=True, help="Skill directory to optimize")
    parser.add_argument("--description", default=None, help="Override the starting description")
    parser.add_argument("--agent", default="auto")
    parser.add_argument(
        "--command", default=os.environ.get("AGENT_COMMAND"),
        help="Command prefix for --agent custom. Also settable via AGENT_COMMAND.",
    )
    parser.add_argument("--model", default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--runs-per-query", type=int, default=1)
    parser.add_argument("--holdout", type=float, default=0.4,
                        help="Fraction of evals held out (0 disables)")
    parser.add_argument("--config", default="with_skill")
    parser.add_argument("--no-skill", action="store_true")
    parser.add_argument("--extra-args", nargs="*", default=[])
    parser.add_argument("--trigger-detector", default=None)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--report", default="none",
        help="Write the final HTML report to this path ('none' disables, the default)",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Open the report in a browser. Off by default: the loop must not "
             "require a GUI, and 'auto' used to open one on every run.",
    )
    parser.add_argument("--results-dir", default=None, help="Directory for results and run artifacts")
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the best description back into the skill's SKILL.md",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Validate the eval set, the skill and the runtime, then exit "
             "without invoking anything",
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    if not (skill_path / "SKILL.md").is_file():
        print(f"error: no SKILL.md at {skill_path}", file=sys.stderr)
        return 1

    try:
        _name, evals = load_evals(Path(args.eval_set))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not 0.0 <= args.holdout < 1.0:
        print("error: --holdout must be in [0, 1)", file=sys.stderr)
        return 1

    if args.dry_run:
        from scripts.quick_validate import validate_skill

        registry = agent_runner.load_registry()
        try:
            spec = agent_runner.resolve_adapter(
                args.agent, registry=registry, command=args.command
            )
            adapter_ok, adapter_note = True, spec.get("confidence", "unknown")
        except (ValueError, SystemExit) as exc:
            adapter_ok, adapter_note = False, str(exc)

        train, test = split_eval_set(evals, args.holdout)
        plan = {
            "skill_path": str(skill_path),
            "skill_valid": validate_skill(skill_path).as_dict(),
            "evals": {"total": len(evals), "train": len(train), "held_out": len(test)},
            "iterations": args.max_iterations,
            "runs_per_eval": args.runs_per_query,
            "max_evals_to_execute": (len(train) + len(test)) * args.max_iterations
            * args.runs_per_query,
            "agent": {"requested": args.agent, "resolves": adapter_ok, "confidence": adapter_note},
            "apply": args.apply,
        }
        print(json.dumps(plan, indent=2))
        return 0 if validate_skill(skill_path).ok and adapter_ok else 1

    results_dir = None
    if args.results_dir:
        results_dir = Path(args.results_dir) / time.strftime("%Y-%m-%d_%H-%M-%S")
        results_dir.mkdir(parents=True, exist_ok=True)

    output = run_loop(
        evals=evals,
        skill_path=skill_path,
        description_override=args.description,
        args=args,
        results_dir=results_dir,
    )

    write_json(Path(results_dir) / "results.json" if results_dir else Path("results.json"), output)

    if args.report != "none":
        from scripts.generate_report import generate_html

        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            generate_html(output, auto_refresh=False, skill_name=output["skill_name"]),
            encoding="utf-8",
        )
        if args.open:
            webbrowser.open(str(report_path.resolve()))
        print(f"Report: {report_path}", file=sys.stderr)

    if args.apply:
        applied = apply_description(skill_path, output["best_description"])
        print(
            f"{'Applied' if applied else 'Could not apply'} best description to "
            f"{skill_path / 'SKILL.md'}",
            file=sys.stderr,
        )

    print(json.dumps({k: v for k, v in output.items() if k != "history"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
