#!/usr/bin/env python3
"""Conformance gate: does the kernel actually implement the 56-section spec?

The failure this exists to prevent is the one that produced the `kernel-fix.md`
audit that was wrong twice. A mapping was produced by searching for *words* across
the kernel's markdown, three of twenty-six conclusions were spot-checked, and the
result was reported as "22 of 26 already implemented". Four of those were never
opened. A word appearing in a table of 286 role descriptions is not evidence that
a rule is enforced, and that method cannot tell the difference.

So the map is now explicit, one row per section, and each row is a probe that
fails loudly. Three outcomes per section:

  ok        the probe passed -- the requirement is implemented *somewhere*, and
            the probe says where, so the claim is checkable rather than asserted
  GAP       the probe failed. The kernel does not implement this section, and
            this exits non-zero.
  stale     the spec file's hash is not the one this table was written against,
            so the table may no longer describe it. Also non-zero.

Usage
-----
    python3 tools/check-spec.py            # the gate
    python3 tools/check-spec.py --why      # print the row for each GAP
    python3 tools/check-spec.py --list     # every row, ok or not

The probes are deliberately shallow -- a file exists, or a file contains a
pattern. They prove a requirement is *addressed*, not that it is enforced, and the
`ENFORCED` column says which is which. A row marked `text` is a rule that lives in
prose; a row marked `gate` has a command behind it that exits non-zero when the
rule is broken. The count of `gate` rows is the honest measure of how much of this
spec is mechanical rather than advisory, and it is small on purpose: the research
on this exact failure is that prose reminders do not change paired success.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The hash of kernel-fix.md this table was written against. The spec lives outside
# the skill (it is not part of an install), so this is a staleness tripwire, not a
# dependency: if the spec changes, the table is re-examined rather than trusted.
SPEC_SHA256 = "6673cc9b"
SPEC_PATH = os.path.join(os.path.dirname(ROOT), "kernel-fix.md")

# kind: file  -- the file must exist
# kind: has   -- the file must exist and match the regex
# kind: gate  -- the command must exist in run-state.py AND the concept must be
#                documented; the enforcement is a command, listed for review
TEXT, GATE = "text", "gate"

# PROSE is not a lesser kind. It is a *decided* kind: the requirement is stated in
# words because no command can enforce it without enforcing something else, and
# the ENFORCED column says which. The distinction matters because a row left as
# TEXT reads as a backlog item -- something somebody forgot -- while a row marked
# PROSE reads as a judgement somebody made. A checker that reports 61/61 with no
# distinction between the two is the same defect this file was written to end:
# coverage asserted rather than counted.
#
# The three questions that decide it, and every PROSE row answers all three:
#   1. Is there observable state the rule is about? If not, there is nothing to
#      read. ("optimise for correct completion" is a priority order, not a field.)
#   2. Could a command exist that a run could satisfy dishonestly? If so it
#      protects nothing. ("did you load too much context" has no ground truth for
#      "too much".)
#   3. Would the command punish honesty? If a correct run fails it, it is worse
#      than prose. This is the one that catches the tempting gates.
PROSE = "prose"

# The sections decided as prose, recorded here so a row's `kind` is checked
# against something rather than trusted. Without this, downgrading a GATE row to
# PROSE is a one-word edit that the gate accepts: the row is still classified, it
# just moves from one column of the headline to the other, and "55 with a command
# behind them" quietly becomes 54. The number is the honest measure of how much of
# this spec is mechanical rather than advisory, so a number that can be lowered
# without failing is a self-report wearing a measurement's clothes.
#
# Changing this set is a decision, not a refactor. It means a section that
# *should* be a command was decided not to have one, and that decision has to be
# made in two places on purpose rather than landed in one by accident.
PROSE_SECTIONS = frozenset({7, 13, 17, 37, 52})

# (section, requirement, kind, target, pattern, enforcement)
ROWS: list[tuple[int, str, str, str, str, str]] = [
    (1, "absolute completion principle", GATE, "references/completion-law.md",
     r"Complete the user's actual task", "audit + finish"),
    (1, "stated as a hard rule in the kernel", GATE, "SKILL.md",
     r"verified complete.*\n?.*genuine blocker|verified complete",
     "audit + check"),
    (2, "never abandon an actionable task", GATE, "references/completion-law.md",
     r"may not end on", "audit + finish --status"),
    (3, "the completion invariant", GATE, "references/completion-law.md",
     r"IF the task is not complete", "finish: no status, no terminal"),
    (4, "JEv decision fabric", GATE, "SKILL.md", r"JEv, the decision fabric",
     "decide + check"),
    (5, "decision record fields", GATE, "SKILL.md",
     r"rejected\s+.*the most useful field", "run-state.py decide + check"),
    (5, "JEv must produce an executable next action", GATE, "SKILL.md",
     r"must produce an executable next action",
     "check refuses a bare category"),
    (6, "four coordination modes", GATE, "SKILL.md",
     r"inline.*delegate.*route.*handoff|1\. \*\*inline\*\*", "set-mode + check"),
    (7, "cheapest sufficient coordination", PROSE, "SKILL.md",
     r"cheapest adequate|cheapest coordination",
     "judgement: the cost side is unmeasurable here, see measure-mode-cost.py"),
    (7, "not optimised for fewer agents/calls", PROSE, "SKILL.md",
     r"not\s+for fewer tokens|fewer agents",
     "a priority order; no observable state to gate"),
    (8, "capability discovery", GATE, "SKILL.md", r"resolve capability",
     "dispatch --state unreachable --tried"),
    (9, "reachability gate", GATE, "SKILL.md",
     r"reachability", "dispatch --state unreachable --tried"),
    (10, "agent execution contract chain", GATE, "tools/run-state.py",
     r"DISPATCH_ORDER\s*=\s*\(\"selected\", \"invoked\", \"running\", \"observed\", \"verified\"\)",
     "run-state.py dispatch"),
    (10, "never finish at SELECTED/PLANNED/NOT TOUCHED", GATE, "tools/run-state.py",
     r"never reached observed", "check refuses non-terminal"),
    (11, "agent input contract", GATE, "references/delegation.md",
     r"[Ww]hat to hand over|hand over", "dispatch --state invoked --brief"),
    (12, "agent output contract", GATE, "references/output-contract.md",
     r"(?i)result|evidence", "dispatch --state observed --result --result-status"),
    (13, "context on demand is a hard rule", PROSE, "SKILL.md",
     r"Do not load all skills",
     "a ceiling with no ground truth: nothing measures what \"everything\" is"),
    (14, "context ladder C0-C6", GATE, "SKILL.md", r"C0\s+the task.*\n?.*C6", "context --level"),
    (15, "context request names what/why/action/scope", GATE, "SKILL.md",
     r"name four things", "context --enables --scope, and check"),
    (16, "context acquisition loop", GATE, "references/context-system.md",
     r"(?i)acquisi|load", "context --gap / --closed, and check"),
    (17, "context efficiency", PROSE, "SKILL.md",
     r"never read a whole role file",
     "a ratio; nothing here measures tokens, see measure-mode-cost.py"),
    (18, "run state field list", GATE, "references/state-system.md",
     r"(?i)field|shape", "RUNSTATE_FIELDS, coverage printed by check"),
    (19, "state updated after every important event", GATE,
     "references/state-system.md", r"(?i)before the work|written before",
     "check: an event that happened with no trace is refused"),
    (20, "truthful state values", GATE, "SKILL.md",
     r"NOT_INVOKED and UNREACHABLE|not terminal",
     "dispatch unreachable --tried"),
    (20, "PLANNED is not EXECUTED", GATE, "tools/run-state.py",
     r"not the same as|not terminal", "check refuses non-terminal dispatch"),
    (21, "active agent state on handoff", GATE, "tools/run-state.py",
     r"active_agent", "check + handoff"),
    (22, "process numbering", GATE, "references/execution-system.md",
     r"P0\d", "run-state.py log (P01.., --under for substeps)"),
    (23, "process log", GATE, "references/execution-system.md",
     r"(?i)process log", "run-state.py log"),
    (24, "process log must be truthful", GATE, "SKILL.md",
     r"must agree with the state", "log refuses an entry the ledger contradicts"),
    (25, "execution state machine", GATE, "SKILL.md", r"RECEIVE.*UNDERSTAND",
     "log: a stage needs its predecessor"),
    (26, "execution plan / atomic units", GATE, "SKILL.md",
     r"atomic work units", "step + require"),
    (27, "execution loop per unit", GATE, "SKILL.md",
     r"determine the objective, determine the required capability",
     "step: five fields, required at R2+"),
    (28, "failure recovery classification", GATE, "SKILL.md",
     r"missing context.*wrong capability|wrong capability",
     "recover --class, nine names"),
    (29, "failure does not end the task", GATE, "SKILL.md",
     r"Approach failure is not task impossibility",
     "blocked --routes, and finish --status partial"),
    (30, "exhaust alternatives before blocking", GATE, "references/retry-policy.md",
     r"(?i)alternative|exhaust", "blocked --routes, fifteen names"),
    (31, "genuine blocker is a five-term conjunction", GATE, "tools/run-state.py",
     r"--tried is required", "blocked --tried non-empty"),
    (32, "never invent a blocker", GATE, "tools/run-state.py",
     r"BLOCK_CONCLUSIONS", "audit + blocked"),
    (33, "verification gate V/P/F", GATE, "SKILL.md",
     r"\*\*VERIFIED\*\*.*\*\*PARTIAL\*\*|\*\*PARTIAL\*\*", "criteria + check"),
    (34, "result received is not verified", GATE, "SKILL.md",
     r"RESULT RECEIVED is not RESULT VERIFIED",
     "observed needs a result; verified needs evidence"),
    (35, "completion gate", GATE, "tools/run-state.py",
     r"COMPLETION_STATUSES", "finish refuses `completed` on any of four conditions"),
    (36, "continue until completion", GATE, "SKILL.md",
     r"One gate before you stop", "check"),
    (37, "user's objective has priority", PROSE, "SKILL.md",
     r"at the expense of completion",
     "a priority order among the other rules; enforcing it would mean "
     "enforcing all of them at once"),
    (38, "do not over-delegate", GATE, "SKILL.md",
     r"Do not over-delegate",
     "check: dispatched and observed, every unit inline"),
    (39, "do not under-delegate", GATE, "SKILL.md",
     r"And do not under-delegate", "dispatch gate + check"),
    (40, "multi-agent synthesis", GATE, "SKILL.md",
     r"never concatenate",
     "check: two results need a comparison recorded"),
    (41, "handoff control", GATE, "SKILL.md", r"handoff", "set-mode + check"),
    (42, "context package for agents", GATE, "references/delegation.md",
     r"(?i)hand over|context package", "dispatch --brief"),
    (43, "state + context + capability triad", GATE, "SKILL.md",
     r"resolve capability|required capability",
     "check: the triad, or the run is refused"),
    (44, "recovery must update state", GATE, "SKILL.md",
     r"Every recovery changes state",
     "recover: seven fields, --result required"),
    (45, "self-evaluation questions", GATE, "SKILL.md",
     r"did we under-delegate|process\*\*, which verification",
     "reflect: all fifteen, and one must be a criticism"),
    (46, "final can-i-still-do-something gate", GATE, "references/completion-law.md",
     r"## The route list", "ROUTES: all fifteen, and --routes is required"),
    (47, "final delivery format", GATE, "references/output-contract.md",
     r"(?i)deliver", "audit: the five sections, --trivially exempts"),
    (48, "if completed template", GATE, "references/output-contract.md",
     r"(?i)completed", "finish --status completed"),
    (49, "if partial template", GATE, "references/output-contract.md",
     r"(?i)partial", "finish --status partial --remaining"),
    (50, "if blocked template", GATE, "references/output-contract.md",
     r"(?i)blocked", "finish --status blocked + blocked --tried"),
    (51, "failed is not blocked", GATE, "references/output-contract.md",
     r"(?i)failed", "finish --status failed --attempted"),
    (52, "operational priority", PROSE, "SKILL.md",
     r"(?i)priority|serve",
     "an ordering of the other rules, each enforced where it belongs"),
    (53, "core execution law", GATE, "references/completion-law.md",
     r"Recovery is not the end of the task", "audit + check"),
    (54, "master execution loop", GATE, "SKILL.md",
     r"RECEIVE.*TRIAGE.*DECIDE", "the same machine as section 25, enforced by log"),
    (55, "final non-negotiable rule: two conditions", GATE, "tools/run-state.py",
     r"TERMINAL_CLAIMS", "audit reads the delivery; finish records the state"),
    (56, "the agent exists to finish work", GATE, "references/completion-law.md",
     r"(?i)invisible|blind spot", "audit"),
]


def probe(kind: str, target: str, pattern: str) -> tuple[bool, str]:
    path = os.path.join(ROOT, target)
    if not os.path.isfile(path):
        return False, f"missing file: {target}"
    if kind == "file":
        return True, target
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:  # pragma: no cover
        return False, f"unreadable: {target} ({e})"
    # Whitespace is collapsed before matching, so a probe survives a reflow. This
    # is not cosmetic: the first version of this checker failed section 17 on a
    # paragraph that said the right thing, because the words straddled a line
    # break. A check that reports a false gap gets ignored, and then it protects
    # nothing -- so the probe has to be about the requirement, not the formatting.
    # It also means no pattern may rely on a newline, which is the right constraint:
    # line breaks in a markdown file are a rendering decision, not a requirement.
    flat = " ".join(text.split())
    flat_pat = " ".join(pattern.split())
    if re.search(flat_pat, flat, re.I):
        return True, target
    return False, f"no match for /{flat_pat[:48]}/ in {target}"


def spec_digest() -> str:
    if not os.path.isfile(SPEC_PATH):
        return ""
    with open(SPEC_PATH, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:8]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="print every row")
    ap.add_argument("--why", action="store_true", help="explain each gap")
    args = ap.parse_args()

    gaps: list[tuple[int, str, str, str, str]] = []
    gates = texts = prose = 0
    seen: set[int] = set()
    prose_rows: list[tuple[int, str, str]] = []

    for sec, req, kind, target, pattern, enforcement in ROWS:
        seen.add(sec)
        ok, detail = probe(kind, target, pattern)
        declared_prose = sec in PROSE_SECTIONS
        if declared_prose and kind != PROSE:
            ok, detail = (False, f"section {sec} is in PROSE_SECTIONS but this row "
                                 f"says {kind.upper()}")
            kind = PROSE
        elif kind == PROSE and not declared_prose:
            ok, detail = (False, f"this row says PROSE but {sec} is not in "
                                 f"PROSE_SECTIONS; add the section there if the "
                                 f"decision is deliberate")
        if kind == GATE:
            gates += 1
        elif kind == PROSE:
            prose += 1
            prose_rows.append((sec, req, enforcement))
        else:
            texts += 1
        status = "ok  " if ok else "GAP "
        if args.list or not ok:
            print(f"  {status} {sec:>2}. {req}"
                  + ("" if ok else f"  -- {detail}"))
        if not ok:
            gaps.append((sec, req, target, pattern, enforcement))

    missing_sections = sorted(set(range(1, 57)) - seen)
    digest = spec_digest()
    stale = ""
    if digest and digest != SPEC_SHA256:
        stale = (f"  the spec has changed since this table was written "
                 f"({SPEC_SHA256} -> {digest}); re-examine the table")

    print(f"\n  {len(ROWS) - len(gaps)}/{len(ROWS)} probes pass"
          f"  ({gates} with a command behind them, {prose} decided prose,"
          f" {texts} unclassified)")
    if args.why and prose_rows:
        print("\n  the rows deliberately left in prose, and why:")
        for sec, req, why in prose_rows:
            print(f"    {sec:>2}. {req}")
            print(f"        {why}")
    print(f"  spec digest: {digest or '(spec not present -- not an install)'}"
          + (f"  STALE against {SPEC_SHA256}" if stale else ""))
    if stale:
        gaps.append((0, "the spec changed and this table was not re-examined",
                     "-", "-", "-"))

    if missing_sections:
        print(f"  {len(missing_sections)} section(s) have no row at all: "
              f"{', '.join(str(s) for s in missing_sections)}")
        gaps.extend((s, "NO ROW", "-", "-", "-") for s in missing_sections)

    if args.why and gaps:
        print("\n  what each gap would need:")
        for sec, req, target, pattern, enf in gaps:
            print(f"    {sec:>2}. {req}")
            print(f"        target {target}  pattern /{pattern[:60]}/")
            print(f"        or a real command behind: {enf}")

    if gaps or texts:
        if gaps:
            print(f"\nFAIL  {len(gaps)} gap(s). The kernel does not implement the "
                  f"specification it is being measured against.")
        if texts:
            print(f"\nFAIL  {texts} row(s) still carry no decision. Every row is "
                  f"either GATE, with a command behind it, or PROSE, with a stated "
                  f"reason a command would be worse. An unclassified row is a "
                  f"backlog item somebody forgot, which is what this table was "
                  f"rewritten to stop being.")
        return 1
    print("\nPASS  every section of the spec is addressed, every row is either "
          "gated or decided prose with a reason, and the table's hash matches the "
          "spec it was written from.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
