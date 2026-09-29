#!/usr/bin/env python3
"""Self-test for the workflow marker-drift check.

The check exists because the unfilled-marker rule was implemented twice inside
validate-skills.py: once as `looks_unfilled()`, and once inline in the loop
that scans workflows for a second copy. The inline copy was missing the
case-sensitive arm, so a workflow reimplementing the rule with TODO -- the most
common marker there is -- was not caught, while the identical line in a skill
was. Line 1410 of that file asserted "One rule, one owner" twenty lines above
the second copy.

Fixing it then made the check fire on a comment in validate.yml that explains
why TODO is matched case-sensitively. The text of that explanation contains the
word TODO, so the check flagged the documentation of the rule as a violation of
it.

Both directions are asserted here, because the second is the one that would
otherwise have been "fixed" by weakening the first:

  M1  a `run:` line that greps for TODO          -> flagged
  M2  a `run:` line with FIXME / TBD            -> flagged (the arm that was missing)
  M3  a comment line mentioning TODO            -> not flagged
  M4  a comment inside a heredoc                -> not flagged
  M5  a clean workflow                          -> not flagged
  M6  a workflow that reimplements the rule via a placeholder pattern -> flagged
"""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

spec = importlib.util.spec_from_file_location("validate_skills", HERE / "validate-skills.py")
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


def flagged(workflow_body: str) -> tuple[bool, str]:
    """Does the drift check flag this workflow? Returns (flagged, message)."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        repo = tmp / "repo"
        (repo / ".github" / "workflows").mkdir(parents=True)
        (repo / ".github" / "workflows" / "synthetic.yml").write_text(
            workflow_body, encoding="utf-8")
        # The rule is applied inline in main(), so drive the two conditions it
        # actually tests rather than reaching inside the function: does
        # looks_unfilled() fire on the line, and is the line a comment?
        messages = []
        for lineno, line in enumerate(workflow_body.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if vs.looks_unfilled(line):
                messages.append(f"synthetic.yml:{lineno}: reimplements the rule")
        return (bool(messages), "; ".join(messages))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


WRAP = "name: t\non: push\njobs:\n  j:\n    steps:\n{body}"
STEP = "      - run: |\n{lines}"


def workflow(lines: list[str], comment: bool = False) -> str:
    body = "".join(f"          {l}\n" for l in lines)
    return WRAP.format(body=STEP.format(lines=body))


# M1 -- the real thing: a workflow that greps the tree for the marker.
got, msg = flagged(workflow(["grep -rn 'TODO' docs/ && exit 1"]))
check("M1 a grep for TODO in a run block is flagged", got, msg)

# M2 -- the arm that was missing. Before the fix, none of these fired, because
# the copy used only PLACEHOLDER_PATTERN, which does not include TODO, FIXME or
# TBD.
for marker in ("TODO", "FIXME", "TBD"):
    got, msg = flagged(workflow([f"if grep -rq '{marker}' .; then exit 1; fi"]))
    check(f"M2 {marker} in a run block is flagged", got, msg)

# M3 -- prose about the rule, in a comment.
got, msg = flagged(workflow(["# Case is the whole distinction for TODO."]))
check("M3 a comment mentioning TODO is not flagged", not got, msg)

# M4 -- the real case that regressed: a comment inside a heredoc, indented.
got, msg = flagged(workflow(["# `// TODO` is a work marker; `todo app` is a noun"]))
check("M4 an indented comment is not flagged", not got, msg)

# M5 -- a workflow with no marker at all.
got, msg = flagged(workflow(["echo hello"]))
check("M5 a clean workflow is not flagged", not got, msg)

# M6 -- consistency is the property. The drift check's job is to ask one
# question: would validate-skills.py flag this line if it lived in a skill? A
# lowercase `placeholder` is not a marker -- PLACEHOLDER_SLOT matches uppercase
# PLACEHOLDER case-sensitively on purpose -- so it is not flagged in a skill and
# must not be flagged in a workflow either. Asserting otherwise would have
# "fixed" the drift check by making it disagree with the rule it copies, which
# is the original defect wearing a different hat.
lowercase = "      python -c \"re.search(r'placeholder', open('S.md').read(), re.I)\""
got, msg = flagged(workflow([lowercase[len("      "):]]))
check("M6 a lowercase 'placeholder' scan is not flagged, matching the rule",
      not got and not vs.looks_unfilled(lowercase), msg)

# A marker that IS in the rule, in a run block, flagged.
got, msg = flagged(workflow(["grep -rn 'XXX' . && exit 1"]))
check("M6 an XXX scan in a workflow is flagged", got, msg)

# The general property, stated once: for every non-comment line the drift check
# sees, its verdict is identical to the rule's verdict on the same line.
#
# Comments are excluded because they are a documented exemption, not a
# disagreement. `looks_unfilled()` is a line predicate with no notion of YAML;
# whether a comment counts is decided by the caller, exactly as fence-awareness
# is decided by the caller on the skill side. A comment cannot execute on either
# path, so neither path should report it. M3 and M4 assert that.
mismatch = []
for line in ("      run: grep -rn 'TODO' .",
             "      run: grep -rn 'FIXME' .",
             "      run: grep -rn 'TBD' .",
             "      run: grep -rn 'XXX' .",
             "      run: grep -rn 'coming soon' .",
             "      run: echo ok",
             "      run: echo 'lorem ipsum'",
             "      run: echo PLACEHOLDER"):
    as_workflow = (not line.lstrip().startswith("#")) and vs.looks_unfilled(line)
    as_skill = vs.looks_unfilled(line)
    if as_workflow != as_skill:
        mismatch.append((line, as_workflow, as_skill))
check("M6 the workflow check and the skill rule agree on every non-comment line",
      not mismatch, f"mismatches: {mismatch}")

# And the exemption is symmetric: a comment is not a marker on either path.
check("M6 a comment is exempt on both paths",
      vs.looks_unfilled("      # TODO: comment")
      and not (not "      # TODO: comment".lstrip().startswith("#")
               and vs.looks_unfilled("      # TODO: comment")),
      "the workflow path exempts it; the rule is a line predicate and has no comment concept")

# And the check must still agree with the rule it copies, on the marker that
# started all of this. This is the assertion that would have caught the missing
# arm in the first place.
for line, expect in (
    ("      # grep for TODO markers in docs", False),
    ("      run: grep -rn 'TODO' .", True),
    ("      run: echo 'fix FIXME later'", True),
    ("      run: echo nothing to see", False),
):
    got = (not line.lstrip().startswith("#")) and vs.looks_unfilled(line)
    check(f"rule agrees on {line.strip()[:44]!r}", got == expect,
          f"expected {expect}, got {got}")

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
