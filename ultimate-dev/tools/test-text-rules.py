#!/usr/bin/env python3
"""Self-tests for the output-declaration rule in tools/text_rules.py.

Why this file exists
--------------------
`declared_output_paths()` decides which paths a document is exempt from
dangling-reference reporting. A path wrongly in that set is invisible: the
check reports nothing and the error count reads zero, which is
indistinguishable from the check working. That has happened twice in this
repository -- once in the exemption rule itself, and once in
link-orphan-references.py, whose comment records 16 files exempted by the word
"Configuration" and 21 more by the word "reference".

So the rule is pinned here in both directions:

  * a genuine declaration must still exempt its path (a false positive stops a
    commit, and a rule that never exempts anything would be "safe" and useless)
  * a read must not inherit a neighbouring declaration (a false negative hides
    a broken reference)

Every assertion below names the failure it prevents. Run:

    python3 tools/test-text-rules.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("text_rules", TOOLS / "text_rules.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)

FAILURES: list[str] = []
COUNT = 0


def check(label: str, got, want) -> None:
    global COUNT
    COUNT += 1
    if got != want:
        FAILURES.append(f"{label}\n     got:  {got!r}\n     want: {want!r}")


# --- the original defect: one declaration, four innocent paths -------------
# This is the real line from skills/stock-analysis/SKILL.md, the reference to
# the forensic exemplar that had not been written. Judged per line the single
# "write" cleared the two reads, so the missing file went unreported.
MIXED = (
    "Score using `references/11-scoring-rubric.md` (run `scripts/score.py` for "
    "the arithmetic), then write the report using the template in "
    "`references/12-report-template.md`. Before writing, read the worked "
    "exemplars in `examples/` to calibrate the target quality: "
    "`examples/standard-analysis-example.md` (a full Standard-mode report that "
    "passes the linter and embeds real `valuation.py` output) and "
    "`examples/forensic-analysis-example.md` (a Forensic-mode review). They are "
    "fictional by design."
)

def clause_holding(text: str, needle: str) -> str:
    """The clause of `text` that contains `needle`.

    Selecting by content rather than by index on purpose. An earlier version
    indexed clauses(MIXED)[1], which turned a real regression -- clauses()
    returning the line uncut -- into an IndexError instead of a reported
    failure. A crash still fails the gate, but it tells the next reader
    nothing about what broke.
    """
    for clause in tr.clauses(text):
        if needle in clause:
            return clause
    raise AssertionError(
        f"no clause of the mixed line contains {needle!r}; the splitter put "
        f"{len(tr.clauses(text))} clause(s) where a path-bearing one was expected"
    )


# Both exemplar paths sit in one sentence -- they are joined by "and", not a
# full stop -- so one clause is correct. The invariant that matters is that no
# clause holding an exemplar read is a declaration.
check(
    "both exemplar reads share the sentence they were written in",
    len([c for c in tr.clauses(MIXED) if "examples/" in c]),
    1,
)
check(
    "the read in the 'score using' clause is not an output",
    bool(tr.line_declares_output(clause_holding(MIXED, "11-scoring-rubric"))),
    False,
)
check(
    "the template in the 'write' clause is still an output declaration",
    bool(tr.line_declares_output(clause_holding(MIXED, "12-report-template"))),
    True,
)
check(
    "a clause holding an exemplar read is not an output declaration",
    bool(tr.line_declares_output(clause_holding(MIXED, "forensic-analysis-example"))),
    False,
)

# --- exemptions that must survive, or the rule is useless --------------------
EXEMPT = [
    ("Save as `agents/agent-name.md`.", "the plain save-as form"),
    ("Create `agents/new.md` and run it.", "create"),
    ("Write the report to `docs/report.md`.", "write"),
    ("**Output:** MP4 videos in `./videos/`", "the bolded field label"),
    ("Store the state in `.memory/run-state.json`.", "store"),
    ("The loader default is `./config.json`.", "the loader default"),
    ("Run this from `foo` -- e.g. `bar` is another path.", "e.g. in the same clause"),
    ("Save as `docs/report.md`, then run the linter.", "a path before a ', then' join"),
    ("Before writing the report, read `references/11-scoring-rubric.md`.",
     "a gerund that does have an object"),
]
for line, why in EXEMPT:
    check(f"still exempt: {why}", bool(tr.line_declares_output(line)), True)

# --- boundaries that must NOT be cut, or real files read as missing ----------
# Each contains a full stop that a naive splitter would read as a sentence end,
# and none of them is one: an initial, an abbreviation, a decimal, a file
# extension, a multiple. Cutting any of these separates a declaration from its
# own path and reports a file that exists as missing.
NOT_SPLIT = [
    ("Signed by J. Smith, per the AR.", "an initial"),
    ("Compare e.g. `a` with `b`.", "e.g."),
    ("See fig. 3 and note No. 4.", "fig. and No."),
    ("ROCE 18.4% and net debt/EBITDA 1.18x, own 5y range 0.4-1.9x.",
     "decimals and multiples"),
    ("See `references/12-report-template.md`.", "a file extension at end of line"),
    ("A U.S. filer reports 12.7%.", "an initialism"),
]
MUST_SPLIT = [
    ("96. The mix shifted.", "a genuine sentence end"),
    ("per the AR. Signed by J. Smith.", "a sentence end after an acronym"),
    ("`a` with `b`. Then the score.", "a sentence end after a backtick"),
    ("Read `a`, then read `b`.", "a sequencing join"),
    ("Read `a` — then read `b`.", "an em-dash separator"),
]
for line, why in NOT_SPLIT:
    check(f"not split on {why}", len(tr.clauses(line)), 1)
for line, why in MUST_SPLIT:
    check(f"split on {why}", len(tr.clauses(line)), 2)
for line, why in NOT_SPLIT:
    check(f"not split on {why}", len(tr.clauses(line)), 1)

# --- a line with no boundary is returned whole, so behaviour is unchanged ----
check("a boundary-free line yields one clause", len(tr.clauses("Just prose.")), 1)
check("an empty line yields no clauses", tr.clauses("   "), [])

# --- the negative control: a check that reports nothing must be provable -----
# If clauses() ever returned the whole line uncut, the mixed-line assertions
# above would fail. If it ever returned one clause per character, the
# not-split assertions would fail. Both directions are therefore live.
check(
    "a missing reference is NOT hidden by a neighbouring declaration",
    "examples/forensic-analysis-example.md"
    in tr.clauses(MIXED)[0],
    False,
)

# --- the rule's own guards still work after the split ------------------------
check(
    "emphasis stripping survives clause scoping",
    bool(tr.line_declares_output(tr.clauses("Save as `x/y.md`.")[0])),
    True,
)
check(
    "NOT_THIS_REPOSITORY survives clause scoping",
    bool(tr.line_declares_output(tr.clauses("It lives in the user's own repo. See `x/y.md`.")[0])),
    True,
)

if FAILURES:
    print(f"FAIL -- {len(FAILURES)} of {COUNT} assertions failed\n", file=sys.stderr)
    for f in FAILURES:
        print(f"  - {f}", file=sys.stderr)
    sys.exit(1)

print(f"PASS -- {COUNT} assertions")
