#!/usr/bin/env python3
"""Route-accuracy benchmark over real tasks, with the accuracy gate in front.

What this measures, and what it deliberately does not:

  MEASURED   how often the kernel chose the coordination mode and the effort
             rung that a human declared correct for the task, on real tasks
             drawn from real work. Cost per task when the runtime reports it.

  REFUSED    any single accuracy figure until the judge has been shown
             consistent with itself (see measure-judge.py). Agreement with a
             judge whose own repeat-to-repeat variance is unknown is not
             evidence, and the literature on this is unambiguous: LLM-judge
             inter-rater reliability has been observed swinging 0.167 to 1.00
             across runs differing only in seed.

The two axes are kept apart on purpose, because conflating them is how the
existing harness ended up with a `publishable` flag guarding the
false-trigger rate while nothing guarded quality:

  process    did it pick the right architecture   <- what this file scores
  quality    was the answer right                 <- not scored here; there is
                                                      no answer oracle for most
                                                      tasks, and inventing one
                                                      is the failure this
                                                      repository keeps finding

Task format, one JSON per task in tasks/:

  {
    "id": "RT-01",
    "title": "...",
    "repo": "path or name the task was drawn from",
    "split": "dev" | "heldout",
    "query": "the task as it would be put to the kernel",
    "expected_mode": "inline|delegate|route|handoff",
    "expected_rung": "R0".."R4",
    "oracle": "why that is the right answer -- the reasoning a reviewer can
               disagree with, which is the point"
  }

A task with no `expected_mode` is scored on nothing rather than scored as a
pass. An unscoreable task is the most common outcome and is reported as such.

Exit 0 on a completed run whatever the accuracy, because this is a reporting
harness. Exit 1 only when the run could not happen or the gate was demanded
and unmet -- `run-pilot.py` has the same property and it is why a run in which
every case failed was a passing invocation.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TASKS = HERE / "tasks"
VERDICT = HERE / "judge-verdict.json"
SCORES = ("wrong", "over", "under")


def load_tasks(split: str | None) -> list[dict]:
    out = []
    for path in sorted(TASKS.glob("*.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        task["_file"] = path.name
        if split and task.get("split") != split:
            continue
        out.append(task)
    return out


def gate() -> dict:
    """The judge verdict, or an explicit refusal."""
    if not VERDICT.is_file():
        return {"accuracy_may_be_quoted": False,
                "reason": "judge-verdict.json absent; run measure-judge.py"}
    return json.loads(VERDICT.read_text(encoding="utf-8"))


def grade_rung(observed: str | None, expected: str | None) -> str | None:
    """wrong | over | under | None. Over-effort is the failure that matters.

    Carrying R3 reasoning on an R0 task is invisible: nothing breaks, the user
    just waits longer and reads more than they needed. Under-effort breaks
    loudly. Both are errors, and they are counted apart, because a benchmark
    that collapses them to a single miss rate cannot tell you which one you
    have.
    """
    if not observed or not expected:
        return None
    o, e = _code(observed), _code(expected)
    if o not in RUNGS or e not in RUNGS:
        return None
    if o == e:
        return "correct"
    return "over" if RUNGS.index(o) > RUNGS.index(e) else "under"


def _code(value: str) -> str:
    return str(value or "").strip().split(" ", 1)[0].upper()


RUNGS = ("R0", "R1", "R2", "R3", "R4")


def summarise(rows: list[dict]) -> dict:
    mode_total = [r for r in rows if r.get("expected_mode")]
    mode_hit = [r for r in mode_total if r.get("mode_match") is True]
    rung_total = [r for r in rows if r.get("expected_rung")]
    rung = {"correct": 0, "over": 0, "under": 0, "undecided": 0}
    for r in rung_total:
        v = r.get("rung_grade")
        rung[v if v in rung else "undecided"] += 1
    costs = [r["cost"] for r in rows if r.get("cost") is not None]
    return {
        "tasks": len(rows),
        "mode": {
            "scored": len(mode_total),
            "correct": len(mode_hit),
            "undecided": len(rows) - len(mode_total),
            "accuracy": (len(mode_hit) / len(mode_total)) if mode_total else None,
        },
        "rung": {
            "scored": len(rung_total),
            **rung,
            "accuracy": ((rung["correct"] / len(rung_total)) if rung_total else None),
        },
        "cost": {
            "reported": len(costs),
            "unreported": len(rows) - len(costs),
            "mean": statistics.fmean(costs) if costs else None,
        },
    }


def coverage_gaps(rows: list[dict]) -> list[str]:
    """Which rungs and modes have no task at all."""
    gaps = []
    have_r = {_code(r.get("expected_rung")) for r in rows}
    have_m = {r.get("expected_mode") for r in rows}
    missing_r = [r for r in RUNGS if r not in have_r]
    missing_m = [m for m in ("inline", "delegate", "route", "handoff") if m not in have_m]
    if missing_r:
        gaps.append(f"rungs {', '.join(missing_r)} -- {len(RUNGS) - len(missing_r)}"
                    f" of {len(RUNGS)} represented")
    if missing_m:
        gaps.append(f"modes {', '.join(missing_m)} -- "
                    f"{4 - len(missing_m)} of 4 represented")
    return gaps


def render(rows: list[dict], g: dict, may_quote: bool) -> None:
    s = summarise(rows)
    print(f"  tasks run           {s['tasks']}")
    print(f"  mode   scored       {s['mode']['scored']}  "
          f"correct {s['mode']['correct']}  undecided {s['mode']['undecided']}")
    print(f"  rung   scored       {s['rung']['scored']}  "
          f"correct {s['rung']['correct']}  over {s['rung']['over']}  "
          f"under {s['rung']['under']}  undecided {s['rung']['undecided']}")
    print(f"  cost   reported     {s['cost']['reported']} of {s['tasks']}  "
          f"mean {s['cost']['mean']}")
    print()
    # Coverage before accuracy. A rate over a skewed sample reads as a property
    # of the router when it is a property of the sample. The first 12 tasks here
    # are drawn from real work on one repository, which is 10 inline and 2
    # delegate -- no route, no handoff, no R0, no R4 -- so a high score on them
    # says the router handles inline well and nothing else. Stating the gap is
    # cheaper than being quoted a number without it.
    # `gap`, not `g`: `g` is the judge-gate parameter, and a coverage loop
    # rebinding it makes the gate read as a string a few lines later. A
    # shadowed name fails far from its cause.
    gaps = coverage_gaps(rows)
    if gaps:
        print("  COVERAGE GAP -- the sample does not exercise:")
        for gap in gaps:
            print(f"    {gap}")
        print("    A rate below is a rate over the tasks present, not over the")
        print("    decision space. Untested rungs are not passing rungs.")
        print()
    if may_quote:
        for label, block in (("mode", s["mode"]), ("rung", s["rung"])):
            acc = block["accuracy"]
            print(f"  {label} accuracy: "
                  + (f"{acc:.0%} ({block['correct']}/{block['scored']})"
                     if acc is not None else "null -- nothing was decidable"))
    else:
        print("  NO ACCURACY FIGURE REPORTED.")
        print(f"    {g.get('reason') or 'the judge has not been shown consistent'}")
        print("    Per-task rows are below, so the raw outcomes are inspectable; the")
        print("    rate is withheld because a rate over an unvalidated judge is a")
        print("    number, not a measurement.")
    print()
    for r in rows:
        flags = []
        if r.get("expected_mode") and r.get("mode_match") is False:
            flags.append(f"mode: chose {r.get('observed_mode')!r}, "
                         f"expected {r['expected_mode']!r}")
        if r.get("expected_rung") and r.get("rung_grade") not in (None, "correct"):
            flags.append(f"rung: chose {r.get('observed_rung')!r}, "
                         f"expected {r['expected_rung']!r} ({r['rung_grade']})")
        if r.get("expected_mode") and r.get("mode_match") is None:
            flags.append("mode: no run-state record, undecided")
        if r.get("expected_rung") and r.get("rung_grade") is None:
            flags.append("rung: no run-state record, undecided")
        # Undecided is not a failure. A run that recorded nothing has not been
        # shown to choose wrongly; it has been shown to choose nothing, which is
        # a gap in the instrument rather than a defect in the work. Marking those
        # rows FAIL is the same conflation the existing harness makes between a
        # process check and a quality check, and it would put a number in the
        # summary that means "not measured" while looking like "measured bad".
        undecided = (r.get("mode_match") is None and r.get("expected_mode")) or \
                    (r.get("rung_grade") is None and r.get("expected_rung"))
        wrong = (r.get("mode_match") is False) or \
                (r.get("rung_grade") in ("over", "under"))
        mark = "FAIL" if wrong else ("skip" if undecided else "ok  ")
        print(f"    {mark} {r['id']:<7} {r['title'][:52]}")
        for f in flags:
            print(f"           {f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["dev", "heldout"],
                    help="score only one split. The heldout split is the only "
                         "number quoted outside this repository; the dev split "
                         "is what a change is tuned against, and reporting both "
                         "as if they were one thing is how a benchmark stops "
                         "predicting anything.")
    ap.add_argument("--from-results", type=pathlib.Path,
                    help="grade a results file produced elsewhere instead of "
                         "running anything")
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--require-gate", action="store_true",
                    help="exit 1 if the judge gate is unmet")
    args = ap.parse_args()

    if not TASKS.is_dir():
        print(f"  no {TASKS}; nothing to run")
        return 1

    g = gate()
    may_quote = bool(g.get("accuracy_may_be_quoted"))

    if args.from_results:
        payload = json.loads(args.from_results.read_text(encoding="utf-8"))
        # Either a bare list of rows or the object this script writes.
        rows = payload if isinstance(payload, list) else payload.get("rows", [])
    else:
        tasks = load_tasks(args.split)
        if not tasks:
            print(f"  no tasks for split={args.split}")
            return 1
        print(f"  {len(tasks)} task(s) for split={args.split or 'all'}")
        print("  NOTE: this file grades results. It does not invoke a model.")
        print("        Produce rows with --from-results; see README.md for how.")
        if args.require_gate and not may_quote:
            return 1
        return 0

    render(rows, g, may_quote)
    if args.out:
        args.out.write_text(json.dumps(
            {"summary": summarise(rows), "rows": rows,
             "gate": g, "accuracy_quoted": may_quote}, indent=2) + "\n",
            encoding="utf-8")
        print(f"  wrote {args.out}")
    if args.require_gate and not may_quote:
        print("  --require-gate: the judge verdict does not permit an accuracy figure")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
