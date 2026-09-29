#!/usr/bin/env python3
"""Self-test for the routing assertions.

`coordination_mode` is the first assertion in this repository that grades a
decision rather than an artefact, and it is the answer to a question that was
previously unmeasurable: did the kernel pick the right architecture for this
task?

It is also the assertion most likely to be quietly useless, for the same reason
the previous grader was. Every way it can degenerate produces a *pass*:

  * if it read the transcript instead of the state file, a run that narrated
    "I would use inline" would score correct without having chosen anything
  * if it accepted a missing state file, a run that recorded nothing would
    score correct -- and a kernel that never records anything would score 100%
  * if it compared loosely, `route` and `handoff` would match

So all three failure directions are asserted here, and the third -- no record is
null, not pass -- is the one that would be invisible in a passing suite.

  R1  a run that recorded the correct mode            -> pass
  R2  a run that recorded a wrong mode                -> fail, naming both
  R3  a run that recorded nothing                     -> null, NOT pass
  R4  a run-state file that is corrupt                -> null, not a crash
  R5  narration alone, with no state file             -> null (not `inline`)
  R6  mode_changes_at_most: 1 change passes, 3 fails
  R7  every CM case in assertions.json has an assertion the grader recognises
  R8  the grader is reachable: an unknown type is still refused
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

spec = importlib.util.spec_from_file_location("run_pilot", HERE / "run-pilot.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def sandbox_with(mode: str | None, changes: int = 0, corrupt: bool = False) -> str:
    d = pathlib.Path(tempfile.mkdtemp())
    (d / ".ultimate-dev").mkdir()
    path = d / ".ultimate-dev" / "run-state.json"
    if corrupt:
        path.write_text("{not json", encoding="utf-8")
    elif mode is not None:
        state = {
            "schema_version": 1,
            "objective": "t",
            "rung": "R1",
            "scale": "L1",
            "coordination": {
                "mode": mode,
                "why": "test",
                "until": "test",
                "changed": [{"from": "a", "to": "b"} for _ in range(changes)],
            },
            "decisions": [], "observations": [],
        }
        path.write_text(json.dumps(state), encoding="utf-8")
    return str(d)


def run(sandbox: str, assertions: list[dict]) -> dict:
    spec_ = {"assertions": assertions}
    return rp.apply_assertions("T-01", spec_, {"observed": []}, {}, {}, sandbox)


tmpdirs: list[str] = []


def keep(s: str) -> str:
    tmpdirs.append(s)
    return s


try:
    # R1 -- the correct choice, recorded.
    sb = keep(sandbox_with("inline"))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    a = out["detail"][0]
    check("R1 correct recorded mode passes", a["passed"] is True, json.dumps(a))

    # R2 -- a wrong choice. The kernel reached for a specialist where the case
    # says inline would do, and produced a good answer. This is the case the
    # whole assertion exists to catch, and the previous grader could not see it.
    sb = keep(sandbox_with("handoff"))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    a = out["detail"][0]
    check("R2 wrong mode fails", a["passed"] is False, json.dumps(a))
    check("R2 it names both the expected and the observed",
          a.get("expected") == "inline" and a.get("observed") == "handoff", json.dumps(a))

    # R3 -- no record at all. This is the one that would pass silently.
    sb = keep(sandbox_with(None))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    a = out["detail"][0]
    check("R3 no record is null, not pass", a["passed"] is None, json.dumps(a))
    # The case-level contract: with nothing decidable, quality is null and the
    # note says why. The first version of this test asserted an `undecidable`
    # key that apply_assertions has never returned -- the counter is internal --
    # so it was testing an interface that does not exist. The behaviour was
    # right; the assertion was aimed at the wrong thing.
    check("R3 the case quality is null, not true",
          out.get("quality") is None, json.dumps(out.get("quality")))
    check("R3 and the reason is stated",
          "no decidable objective assertion" in (out.get("note") or ""),
          str(out.get("note")))

    # And the converse, so R3 is not passing because everything is null: a
    # recorded-and-correct mode must produce a decidable verdict, and a wrong
    # one must produce a failure rather than another null. The verdict is the
    # strings "pass"/"fail", with null reserved for undecidable.
    sb = keep(sandbox_with("inline"))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    check("R3 a correct record yields a decidable verdict",
          out.get("quality") == "pass", json.dumps(out.get("quality")))
    sb = keep(sandbox_with("handoff"))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    check("R3 a wrong record yields fail, not null",
          out.get("quality") == "fail", json.dumps(out.get("quality")))

    # R4 -- a corrupt state file must not crash the grader.
    sb = keep(sandbox_with(None, corrupt=True))
    out = run(sb, [{"id": "m", "type": "coordination_mode", "mode": "inline"}])
    a = out["detail"][0]
    check("R4 corrupt state file is null, not a crash", a["passed"] is None,
          json.dumps(a))

    # R5 -- narration without a record. The harness greps tool output elsewhere;
    # if this read the transcript, a model that merely said the word would score.
    sb = keep(sandbox_with(None))
    out = rp.apply_assertions(
        "T-02", {"assertions": [{"id": "m", "type": "coordination_mode",
                                 "mode": "inline"}]},
        {"observed": ["I would use the inline mode for this task"]}, {}, {}, sb)
    a = out["detail"][0]
    check("R5 narration alone does not count as a choice", a["passed"] is None,
          json.dumps(a))

    # R6 -- the thrash bound.
    sb = keep(sandbox_with("delegate", changes=1))
    out = run(sb, [{"id": "t", "type": "mode_changes_at_most", "max": 2}])
    check("R6 one mode change passes the bound",
          out["detail"][0]["passed"] is True, json.dumps(out["detail"][0]))
    sb = keep(sandbox_with("delegate", changes=3))
    out = run(sb, [{"id": "t", "type": "mode_changes_at_most", "max": 2}])
    check("R6 three mode changes fail the bound",
          out["detail"][0]["passed"] is False, json.dumps(out["detail"][0]))
    sb = keep(sandbox_with(None))
    out = run(sb, [{"id": "t", "type": "mode_changes_at_most", "max": 2}])
    check("R6 no record is null, not pass",
          out["detail"][0]["passed"] is None, json.dumps(out["detail"][0]))

    # R7 -- every authored CM assertion is a type the grader implements. An
    # assertion type the grader does not know is refused as undecidable, which
    # is safe, but it would mean the six cases measure nothing while appearing
    # to be asserted.
    known = {"output_matches", "file_contains", "file_unchanged",
             "only_files_changed", "coordination_mode", "mode_changes_at_most"}
    data = json.loads((ROOT / "evaluation" / "assertions.json").read_text())
    unknown = [
        f"{cid}/{a.get('type')}"
        for cid, entry in data["cases"].items()
        for a in entry.get("assertions", [])
        if a.get("type") not in known
    ]
    check("R7 every authored assertion uses a type the grader implements",
          not unknown, f"unknown: {unknown}")

    cm = [c for c in data["cases"] if c.startswith("CM-")]
    check("R7 all six routing cases now carry an assertion", len(cm) == 6,
          f"{len(cm)} present: {sorted(cm)}")

    # R8 -- an unknown type is still refused rather than silently passing.
    sb = keep(sandbox_with("inline"))
    out = run(sb, [{"id": "u", "type": "no_such_assertion"}])
    check("R8 an unknown assertion type is undecidable, not a pass",
          out["detail"][0]["passed"] is None, json.dumps(out["detail"][0]))

    # The corpus and the projection must agree, or the grader is reading an
    # oracle the corpus no longer states.
    evals = json.loads((ROOT / "evals" / "evals.json").read_text())
    evals = evals if isinstance(evals, list) else evals.get("evals", evals.get("cases", []))
    carried = [c for c in evals if c.get("correct_mode")]
    check("the projection carries a routing oracle", len(carried) >= 4,
          f"{len(carried)} cases carry one")
    modes = {c["id"]: c.get("correct_mode") for c in evals if c.get("correct_mode")}
    for cid, entry in data["cases"].items():
        if cid not in modes:
            continue
        want = entry["assertions"][0].get("mode")
        check(f"{cid}: the assertion and the corpus agree",
              want == modes[cid], f"assertion={want!r} corpus={modes[cid]!r}")

finally:
    for d in tmpdirs:
        shutil.rmtree(d, ignore_errors=True)

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
