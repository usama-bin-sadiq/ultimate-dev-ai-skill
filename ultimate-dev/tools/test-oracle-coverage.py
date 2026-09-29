#!/usr/bin/env python3
"""Self-test for the routing-oracle projection.

What could go wrong
-------------------

The routing oracle lives in one file, `evaluation/coordination-modes/CASES.md`,
and two labels carry it: `**Correct mode:**` for a single mode and
`**Coordination:**` for a recovery sequence. Two failure directions, and they
oppose each other, so neither a "found everything" nor a "found nothing" test
catches both.

  R1  a stated mode is dropped              coverage falls, silently
  R2  a wrong path is captured as correct   coverage reads 100% and is wrong
  R3  a sequence is flattened to one mode   a run is scored on the wrong step
  R4  a case that states nothing is scored  an unlabelled case becomes a pass or
                                           a fail rather than unscored
  R5  coverage is reported as a pass rate   4 of 128 is printed as 4/128 scored

R2 and R3 are the dangerous ones, because they make the oracle look complete. A
grader that compared a run's mode against `delegate -> route (correct recovery) ·
keep retrying delegate (wrong)` flattened to a single value would score a run
correct for ending on the mode the case says is wrong. The test asserts the
wrong path is *not* in the sequence.

R4 is the false-null class this repository keeps hitting. A case with no oracle
is unscored. It is not a pass, because nothing was compared, and it is not a fail,
because the run may well have chosen correctly.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
EVALS = ROOT / "evals" / "evals.json"
BUILDER = HERE / "build-evals.py"
CORPUS = ROOT / "evaluation" / "coordination-modes" / "CASES.md"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


proc = subprocess.run([sys.executable, str(BUILDER)], capture_output=True, text=True)
check("the builder runs", proc.returncode == 0, proc.stderr[-160:])
if proc.returncode != 0:
    print(f"\nFAIL  cannot rebuild the corpus, so nothing below is measurable")
    sys.exit(1)

cases = {c["id"]: c for c in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]}
cm = {k: v for k, v in cases.items() if k.startswith("CM-")}

# ---- R1: every single-mode case survives the projection ----
for cid, expected in (("CM-01", "inline"), ("CM-02", "route"),
                      ("CM-03", "delegate"), ("CM-04", "handoff")):
    check(f"R1 {cid} keeps its stated mode ({expected})",
          cm.get(cid, {}).get("correct_mode") == expected,
          f"got {cm.get(cid, {}).get('correct_mode')!r}")

# ---- R2/R3: the sequence is the correct path only, and is not flattened ----
seq = cm.get("CM-05", {}).get("expected_mode_sequence")
check("R2 CM-05 carries a sequence", isinstance(seq, list) and len(seq) == 2, repr(seq))
check("R2 CM-05's sequence is the correct recovery, in order",
      seq == ["delegate", "route"], repr(seq))
check("R3 CM-05's sequence ends on route, not on the repeated delegate",
      bool(seq) and seq[-1] == "route", repr(seq))
check("R2 the wrong path's trailing delegate is not captured",
      bool(seq) and seq.count("delegate") == 1, repr(seq))
check("R3 CM-05 is not given a single-mode oracle from a transition",
      cm.get("CM-05", {}).get("correct_mode") is None,
      f"got {cm.get('CM-05', {}).get('correct_mode')!r}")

# ---- R4: a case stating no mode is unscored, not scored ----
check("R4 CM-06 states no single mode (it states 'unstable')",
      cm.get("CM-06", {}).get("correct_mode") is None,
      f"got {cm.get('CM-06', {}).get('correct_mode')!r}")
check("R4 CM-06 has no sequence either",
      cm.get("CM-06", {}).get("expected_mode_sequence") is None,
      f"got {cm.get('CM-06', {}).get('expected_mode_sequence')!r}")

non_cm = {k: v for k, v in cases.items() if not k.startswith("CM-")}
asserted = [k for k, v in non_cm.items() if v.get("correct_mode")]
check("R4 no non-CM case acquired a mode label", not asserted, repr(asserted[:5]))

unlabelled = [k for k, v in cases.items() if v.get("correct_mode") is None]
check("R4 unlabelled cases are kept, not dropped", len(unlabelled) > 100,
      f"{len(unlabelled)} unlabelled of {len(cases)}")
check("R4 and every case still has an id and a query",
      all(c.get("id") and c.get("query") for c in cases.values()), "")

# ---- R5: coverage is reported as coverage ----
cov = subprocess.run([sys.executable, str(HERE / "report-oracle-coverage.py")],
                     capture_output=True, text=True)
check("R5 the coverage report runs", cov.returncode == 0, cov.stderr[-160:])
check("R5 it states the mode count as 'of'", "of 128" in cov.stdout, "")
check("R5 it does not print a pass rate",
      "accuracy" not in cov.stdout.lower() and "%" not in cov.stdout, "")
check("R5 it names the file the oracle lives in",
      "coordination-modes/CASES.md" in cov.stdout, "")
check("R5 it says the projection drops nothing",
      "drops nothing" in cov.stdout, "")
# Run the coverage report against a real empty corpus, not a grep of its source.
# A check that reads the script and asserts a string is present tests the string,
# not the behaviour: it would pass on a report that printed "holds no cases" and
# then reported 0 of 0 anyway.
import shutil
import tempfile

empty = pathlib.Path(tempfile.mkdtemp())
try:
    copy = empty / "tools"
    copy.mkdir()
    for name in ("report-oracle-coverage.py",):
        shutil.copy(HERE / name, copy / name)
    (empty / "evals").mkdir()
    (empty / "evals" / "evals.json").write_text('{"evals": []}', encoding="utf-8")
    empty_run = subprocess.run(
        [sys.executable, str(copy / "report-oracle-coverage.py")],
        capture_output=True, text=True)
    check("R5 an empty corpus is refused, not reported as 0 of 0",
          empty_run.returncode != 0, f"exit {empty_run.returncode}")
    check("R5 and it says the corpus holds no cases",
          "holds no cases" in (empty_run.stdout + empty_run.stderr), empty_run.stdout[:120])
    check("R5 and it prints no coverage table for an empty corpus",
          "routing oracle coverage" not in empty_run.stdout, empty_run.stdout[:120])

    # And a corpus that cannot be read at all is also refused, rather than
    # reported as full coverage of nothing.
    (empty / "evals" / "evals.json").unlink()
    missing = subprocess.run(
        [sys.executable, str(copy / "report-oracle-coverage.py")],
        capture_output=True, text=True)
    check("R5 an unreadable corpus is refused", missing.returncode != 0,
          f"exit {missing.returncode}")
finally:
    shutil.rmtree(empty, ignore_errors=True)

# ---- the corpus file itself is not hand-edited to match the projection ----
text = CORPUS.read_text(encoding="utf-8")
stated = text.count("**Correct mode:**")
check("the corpus still states its modes in the file, not in the tool",
      stated >= 4, f"{stated} occurrences")

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
