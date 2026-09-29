#!/usr/bin/env python3
"""Run the real tasks through the kernel and record what it chose.

`run-bench.py` grades results. This produces them.

For each task in `tasks/`, in a sandbox that is a copy of the repository the task
was drawn from:

  1. prompt the kernel with the task
  2. read `.ultimate-dev/run-state.json` from the sandbox
  3. record the mode and rung it actually chose, next to the declared oracle

The one design decision worth stating: **the harness does not tell the kernel to
record, and does not fall back to reading the transcript.** The kernel's own
SKILL.md tells it to use `run-state.py`, so a run that produces no state file
either did not choose, or chose without recording. Both are findings about the
kernel and both are recorded as `undecided` — which is not a pass and not a
failure, and is reported as such by the grader.

Reading the transcript instead would be the tempting shortcut, and it is the one
that cannot be taken here. An agent that narrates "I would use the inline mode
for this" and an agent that calls `set-mode --mode inline` produce the same
sentence, and only one of them chose. The distinction is exactly what the
measurement is for.

Cost: the adapter is a hardcoded path into a `~` directory, copied from
`run-pilot.py`, which means this cannot run from a clone. That is recorded here
rather than fixed, because the fix belongs in the adapter and not in two callers.

Nothing here is a gate. Exit 0 on a completed run whatever the accuracy; exit 1
only when the run could not happen. A harness in which a wrong answer is a
passing invocation is the defect this whole directory is about.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
TASKS = HERE / "tasks"
OUT = HERE / "results"

# Outside REPO. See IGNORED below for why that is not a detail.
WORK_ROOT = pathlib.Path(tempfile.gettempdir()) / "ultimate-dev-testbed"

# Which runtime to invoke is configuration, resolved in one place. It was
# hardcoded here and separately in run-pilot.py, so the two harnesses could not
# be pointed at the same agent without editing both -- and a measurement that
# needs a source edit to run is a measurement nobody runs.
sys.path.insert(0, str(REPO / "ultimate-dev" / "tools"))
from agent_invocation import (  # noqa: E402
    Invocation,
    InvocationUnconfigured,
    classify_environment_failure,
)

SKILL = REPO / "ultimate-dev"

# The sandbox must not be created inside the tree it copies. The first version
# put it under testbed/results/work/<id>/repo, and copytree then copied the
# partially-built destination into itself until the path length blew up:
# "File name too long", with the path repeating results/work/RT-01/repo seven
# times. `results` is ignored below as well, so a stale run directory cannot
# cause it even if the destination moves back inside the tree.
IGNORED = shutil.ignore_patterns(".git", "__pycache__", "dist", "node_modules",
                                 ".ultimate-dev", "runs", "results", "*.pyc")

# A run that produced no answer is not a wrong answer. It is an absent one.
MIN_ANSWER = 120

# The environment-failure classifier is the shared implementation, not a second
# copy of it. The comment that used to sit above the local copy of this table --
# "a second copy of a list of provider error strings is a second list that
# drifts" -- was written directly above the second copy, which is the clearest
# statement of the defect this repository keeps making that has yet to be made.
#
# Why the classification matters at all: the first version of this runner
# reported every run as "the run either made no choice or did not record one",
# which is a claim about the KERNEL. The runs had not happened -- the adapter
# failed in under four seconds with a quota error. Attributing an environment
# failure to the skill's decision-making is the worst form of the false null,
# because it looks exactly like a routing measurement.


def sandbox_for(task: dict, dest: pathlib.Path) -> pathlib.Path:
    """A copy of the tree the task was drawn from.

    Copied rather than used in place so that a run which edits something cannot
    damage the tree the next task is copied from.
    """
    dest.mkdir(parents=True, exist_ok=True)
    root = dest / "repo"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(REPO, root, symlinks=True, ignore=IGNORED)
    return root


def read_state(root: pathlib.Path) -> dict | None:
    path = root / ".ultimate-dev" / "run-state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def prompt_for(task: dict) -> str:
    """The task as it would actually be put, with nothing added.

    No hint that a rung or a mode is being scored. The measurement is whether
    the kernel picks the right architecture unprompted; telling it there is a
    right architecture turns the benchmark into a reading comprehension test.
    """
    return task["query"]


def run_one(task: dict, target: Invocation, timeout: int, keep: pathlib.Path) -> dict:
    root = sandbox_for(task, keep)
    row = {
        "id": task["id"],
        "title": task["title"],
        "split": task.get("split"),
        "expected_mode": task.get("expected_mode"),
        "expected_rung": task.get("expected_rung"),
        "observed_mode": None,
        "observed_rung": None,
        "mode_match": None,
        "rung_grade": None,
        "scored": False,
        "cost": None,
        "answer_chars": 0,
        "environment_failure": None,
        "note": "",
    }

    command = target.command(prompt_for(task), timeout=timeout, cwd=root)

    started = time.monotonic()
    try:
        proc = subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout + 30)
    except subprocess.TimeoutExpired:
        row["note"] = f"timeout after {timeout}s"
        row["elapsed_s"] = round(time.monotonic() - started, 1)
        return row
    except FileNotFoundError as exc:
        row["note"] = f"adapter not runnable: {exc}"
        return row

    row["elapsed_s"] = round(time.monotonic() - started, 1)
    out = proc.stdout or ""
    row["answer_chars"] = len(out)
    if proc.returncode != 0:
        row["note"] = f"adapter exit {proc.returncode}: {(proc.stderr or '')[-200:]}"

    combined = out + (proc.stderr or "")
    env = classify_environment_failure(combined) if proc.returncode != 0 else None
    if env:
        # The run did not happen. Record it as absent, with the reason, and
        # leave every routing field null so the grader counts it as undecided
        # rather than as a mode the kernel chose wrongly.
        row["environment_failure"] = env
        row["note"] = (f"environment failure: {env}. The run did not happen, so "
                      f"nothing is known about what the kernel would have "
                      f"chosen. This is not a routing result.")
        row["elapsed_s"] = round(time.monotonic() - started, 1)
        return row

    state = read_state(root)
    if state is None:
        row["note"] = (row["note"] + " " if row["note"] else "") + (
            "no run-state record; the run either made no choice or did not "
            "record one. Undecided, which is neither a pass nor a failure.")
    else:
        row["observed_mode"] = (state.get("coordination") or {}).get("mode")
        row["observed_rung"] = state.get("rung")

    # Grading, repeated here so a results file is self-describing.
    if row["expected_mode"]:
        row["mode_match"] = (row["observed_mode"] == row["expected_mode"]
                             if row["observed_mode"] else None)
    if row["expected_rung"]:
        if not row["observed_rung"]:
            row["rung_grade"] = None
        else:
            o = str(row["observed_rung"]).split(" ", 1)[0].upper()
            e = str(row["expected_rung"]).split(" ", 1)[0].upper()
            order = ("R0", "R1", "R2", "R3", "R4")
            row["rung_grade"] = ("correct" if o == e else
                                 "over" if order.index(o) > order.index(e)
                                 else "under" if o in order and e in order
                                 else None)
    row["scored"] = row["mode_match"] is not None
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["dev", "heldout"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--agent", default=None,
        help="Agent runtime to invoke. No default: a harness that falls back to "
             "one vendor measures that vendor and reports it as a property of "
             "the kernel. Falls back to ULTIMATE_DEV_AGENT.")
    ap.add_argument(
        "--runner", default=None,
        help="Path to the agent adapter script. Falls back to "
             "ULTIMATE_DEV_AGENT_RUNNER. Was a hardcoded path into a home "
             "directory, which is why this could not run from a clone.")
    ap.add_argument(
        "--agent-arg", action="append", default=None, metavar="FLAG",
        help="Agent-specific flag, repeatable. Use the = form "
             "(--agent-arg=--auto); the value starts with a dash, so the "
             "spaced form is read as another option. Falls back to "
             "ULTIMATE_DEV_AGENT_ARGS. See tools/agent_invocation.py RECIPES "
             "for a configuration that was found to be necessary.")
    ap.add_argument("--model", default=None,
                    help="Model to request, or unset for the runtime's default.")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", type=pathlib.Path, default=OUT / "rows.json")
    ap.add_argument("--work", type=pathlib.Path,
                    help="where sandboxes are built. Defaults to a directory "
                         "OUTSIDE the repository being copied; putting it "
                         "inside makes copytree copy its own destination.")
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would run and exit; no model is called")
    args = ap.parse_args()

    tasks = []
    for path in sorted(TASKS.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        if args.split and t.get("split") != args.split:
            continue
        tasks.append(t)
    if args.limit:
        tasks = tasks[:args.limit]

    if not tasks:
        print(f"  no tasks for split={args.split}")
        return 1

    target = Invocation.resolve(runner=args.runner, agent=args.agent,
                                model=args.model, agent_args=args.agent_arg)

    if args.dry_run:
        print(f"  {len(tasks)} task(s); would invoke the adapter for each.")
        for t in tasks:
            print(f"    {t['id']:<7} {t['split']:<8} expects "
                  f"{t.get('expected_mode')} / {t.get('expected_rung')}  "
                  f"{t['title'][:44]}")
        print()
        print("  invocation")
        for key, value in target.describe().items():
            if key != "missing":
                print(f"    {key:<12} {value}")
        for gap in target.missing():
            print(f"    WOULD REFUSE: {gap}")
        return 0

    gaps = target.missing()
    if gaps:
        for gap in gaps:
            print(f"FAIL  {gap}")
        print("      An unrun benchmark is a checklist, so this refuses rather")
        print("      than defaulting to a vendor and reporting the result as a")
        print("      property of the kernel.")
        return 1

    rows = []
    for i, task in enumerate(tasks, 1):
        print(f"  [{i}/{len(tasks)}] {task['id']}  {task['title'][:48]}")
        keep = (args.work or WORK_ROOT) / task["id"]
        row = run_one(task, target, args.timeout, keep)
        rows.append(row)
        if row.get("environment_failure"):
            status = f"ENVIRONMENT: {row['environment_failure']}"
        elif row["scored"]:
            status = "scored"
        else:
            status = "undecided"
        print(f"        mode={row['observed_mode']} rung={row['observed_rung']} "
              f"-> {status}  ({row.get('elapsed_s', 0)}s)")
        if row["note"]:
            print(f"        note: {row['note'][:100]}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Provenance travels with the rows. A results file that does not say
        # which agent and model produced it cannot be attributed, and a rate
        # computed from it is a statement about that agent rather than about
        # the kernel.
        args.out.write_text(
            json.dumps({"runtime": target.describe(), "rows": rows}, indent=2)
            + "\n", encoding="utf-8")

    print()
    print(f"  wrote {args.out}")
    print("  grade it with:  python3 run-bench.py --from-results "
          f"{args.out.name}")
    print("  Note that run-bench.py will withhold any accuracy figure until")
    print("  measure-judge.py has been run on repeated judgements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
