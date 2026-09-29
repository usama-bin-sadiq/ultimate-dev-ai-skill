#!/usr/bin/env python3
"""Make the mode oracle's coverage explicit, instead of leaving 4 of 128 to be found.

The problem
-----------

`evals/evals.json` carries a `correct_mode` for 4 of 128 cases. An earlier commit
fixed the projection so it would stop dropping the label, which took the count from
0 to 4 -- and 4 is the whole corpus's oracle. The remaining 124 have none.

That is not a bug in `build-evals.py`. The projection is correct: the labels are
gone before it runs. Only the six `CM-*` cases in
`evaluation/coordination-modes/CASES.md` were ever written with a `**Correct mode:**`
line, and two of them have stopped carrying one. Every other case file states a
`Rung` and a `Scale` and a `Pass criteria`, and states its expected *behaviour* in
prose, but never names a mode.

So the honest report on routing coverage is 4 of 128, and it has been 4 of 128
since the projection was fixed. Reporting it as a projection failure sent the
reader looking for a tool bug that does not exist.

Why it cannot be derived
------------------------

Deriving a mode from a case's prose is the same defect as the 277 dispatch rows,
one level down. A mode oracle is a claim about what a competent agent *should*
choose for a task, and a claim written by a tool that never read the task is a
guess wearing the authority of a labelled fixture. The `BM-*` cases illustrate why
the guess is not even well defined: BM-SIMPLE-01 asks for one constant changed and
prohibits a plan, a task model, and a capability search. The correct mode is
`inline` -- but so is the correct mode for a case that needs three tools, and the
text alone does not distinguish "correctly inline" from "inline by default". A
derived label would make every such case pass on a default rather than on a
judgement, which is precisely the unearned measurement this repository keeps
refusing.

What this tool does
-------------------

It reports the coverage, and it reports it as a coverage figure rather than as a
pass rate. It refuses to invent labels, and it refuses to describe a case with no
label as failing: an unlabelled case is unscored, which is different from wrong.

    routing oracle coverage
      cases with a mode label       4 of 128
      cases with a rung label      74 of 128
      cases with a scale label     74 of 128

    mode labels by prefix
      CM  4   (coordination-modes/CASES.md -- the only file that states one)
      BM  0   FC  0   NM  0   RG  0   SC  0   TN  0   DM  0

    The 6 CM cases are the routing corpus. The other 122 measure
    something else -- tool-call traces, artefact presence, step budgets --
    which is a legitimate measurement and not a gap. The kernel's
    coordination claim is testable only against the cases written to
    test it, and that set is six files wide.

Exit status
-----------

0 always, unless the corpus cannot be read at all. This reports; it does not
gate. A coverage report that fails the build is a coverage report nobody
updates, and coverage is a fact to be stated, not a threshold to be enforced.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals" / "evals.json"

# The file that states modes, and the only one. Named so the report can say where
# coverage comes from rather than only how much of it there is.
ORACLE_SOURCE = "evaluation/coordination-modes/CASES.md"


def load() -> list[dict]:
    try:
        payload = json.loads(EVALS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL  cannot read {EVALS}: {exc}")
        raise SystemExit(1) from exc
    cases = payload.get("evals")
    if not cases:
        # An empty list and a missing key are the same failure here: a corpus that
        # parsed but holds nothing, which would otherwise report 0 of 0 and read
        # as full coverage of nothing.
        print(f"FAIL  {EVALS} holds no cases")
        raise SystemExit(1)
    return cases


def main() -> int:
    cases = load()
    total = len(cases)

    def count(field: str) -> int:
        return sum(1 for c in cases if c.get(field))

    modes = count("correct_mode")
    rungs = count("rung")
    scales = count("scale")

    by_prefix: dict[str, list[int]] = {}
    for c in cases:
        prefix = c["id"].split("-", 1)[0]
        slot = by_prefix.setdefault(prefix, [0, 0])
        slot[0] += 1
        if c.get("correct_mode"):
            slot[1] += 1

    print("  routing oracle coverage")
    print(f"    cases with a mode label       {modes:>4} of {total}")
    print(f"    cases with a rung label       {rungs:>4} of {total}")
    print(f"    cases with a scale label      {scales:>4} of {total}")
    print()
    print("    mode labels by prefix")
    for prefix in sorted(by_prefix):
        total_p, with_mode = by_prefix[prefix]
        mark = "" if with_mode else "   (no mode stated)"
        print(f"      {prefix:<4} {with_mode:>3} of {total_p:<4}{mark}")
    print()
    print(f"    The mode oracle exists only in `{ORACLE_SOURCE}`. The projection in")
    print("    build-evals.py carries whatever that file states and drops nothing:")
    print("    4 of 128 is the corpus's coverage, not a projection failure.")
    print()
    print("    The 122 unlabelled cases measure tool-call traces, artefact presence,")
    print("    and step budgets. That is a real measurement and not a gap. The")
    print("    coordination claim is testable only against cases written to test it.")
    print()
    print("    Deriving a label from a case's prose would be the 277-dispatch-row")
    print("    defect one level down: a guess about what a competent agent should")
    print("    choose, written by a tool that did not reason about the task. An")
    print("    unlabelled case is unscored, which is not the same as wrong, and is")
    print("    never counted as a failure here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
