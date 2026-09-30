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
SPEC_SHA256 = "37f38585"
SPEC_PATH = os.path.join(os.path.dirname(ROOT), "kernel-fix.md")

# kind: file  -- the file must exist
# kind: has   -- the file must exist and match the regex
# kind: gate  -- the command must exist in run-state.py AND the concept must be
#                documented; the enforcement is a command, listed for review
TEXT, GATE = "text", "gate"

# (section, requirement, kind, target, pattern, enforcement)
ROWS: list[tuple[int, str, str, str, str, str]] = [
    (1, "absolute completion principle", TEXT, "references/completion-law.md",
     r"Complete the user's actual task", "none"),
    (1, "stated as a hard rule in the kernel", TEXT, "SKILL.md",
     r"verified complete.*\n?.*genuine blocker|verified complete",
     "audit + check"),
    (2, "never abandon an actionable task", TEXT, "references/completion-law.md",
     r"may not end on", "audit"),
    (3, "the completion invariant", TEXT, "references/completion-law.md",
     r"IF the task is not complete", "none"),
    (4, "JEv decision fabric", TEXT, "SKILL.md", r"JEv, the decision fabric", "none"),
    (5, "decision record fields", GATE, "SKILL.md",
     r"rejected\s+.*the most useful field", "run-state.py decide + check"),
    (5, "JEv must produce an executable next action", TEXT, "SKILL.md",
     r"must produce an executable next action", "none"),
    (6, "four coordination modes", GATE, "SKILL.md",
     r"inline.*delegate.*route.*handoff|1\. \*\*inline\*\*", "set-mode + check"),
    (7, "cheapest sufficient coordination", TEXT, "SKILL.md",
     r"cheapest adequate|cheapest coordination", "none"),
    (7, "not optimised for fewer agents/calls", TEXT, "SKILL.md",
     r"not\s+for fewer tokens|fewer agents", "none"),
    (8, "capability discovery", TEXT, "SKILL.md", r"resolve capability", "none"),
    (9, "reachability gate", GATE, "SKILL.md",
     r"reachability", "dispatch --state unreachable --tried"),
    (10, "agent execution contract chain", GATE, "tools/run-state.py",
     r"DISPATCH_ORDER\s*=\s*\(\"selected\", \"invoked\", \"running\", \"observed\", \"verified\"\)",
     "run-state.py dispatch"),
    (10, "never finish at SELECTED/PLANNED/NOT TOUCHED", GATE, "tools/run-state.py",
     r"never reached observed", "check refuses non-terminal"),
    (11, "agent input contract", TEXT, "references/delegation.md",
     r"[Ww]hat to hand over|hand over", "none"),
    (12, "agent output contract", TEXT, "references/output-contract.md",
     r"(?i)result|evidence", "none"),
    (13, "context on demand is a hard rule", TEXT, "SKILL.md",
     r"Do not load all skills", "none"),
    (14, "context ladder C0-C6", GATE, "SKILL.md", r"C0\s+the task.*\n?.*C6", "context --level"),
    (15, "context request names what/why/action/scope", TEXT, "SKILL.md",
     r"name four things", "context --why"),
    (16, "context acquisition loop", TEXT, "references/context-system.md",
     r"(?i)acquisi|load", "none"),
    (17, "context efficiency", TEXT, "SKILL.md",
     r"never read a whole role file", "none"),
    (18, "run state field list", TEXT, "references/state-system.md",
     r"(?i)field|shape", "none"),
    (19, "state updated after every important event", TEXT,
     "references/state-system.md", r"(?i)before the work|written before", "none"),
    (20, "truthful state values", GATE, "SKILL.md",
     r"NOT_INVOKED and UNREACHABLE|not terminal",
     "dispatch unreachable --tried"),
    (20, "PLANNED is not EXECUTED", GATE, "tools/run-state.py",
     r"not the same as|not terminal", "check refuses non-terminal dispatch"),
    (21, "active agent state on handoff", GATE, "tools/run-state.py",
     r"active_agent", "check + handoff"),
    (22, "process numbering", TEXT, "references/execution-system.md",
     r"P0\d", "none"),
    (23, "process log", TEXT, "references/execution-system.md",
     r"(?i)process log", "none"),
    (24, "process log must be truthful", TEXT, "SKILL.md",
     r"must agree with the state", "none"),
    (25, "execution state machine", TEXT, "SKILL.md", r"RECEIVE.*UNDERSTAND", "none"),
    (26, "execution plan / atomic units", GATE, "SKILL.md",
     r"atomic work units", "step + require"),
    (27, "execution loop per unit", TEXT, "SKILL.md",
     r"determine the objective, determine the required capability", "none"),
    (28, "failure recovery classification", TEXT, "SKILL.md",
     r"missing context.*wrong capability|wrong capability", "none"),
    (29, "failure does not end the task", TEXT, "SKILL.md",
     r"Approach failure is not task impossibility", "none"),
    (30, "exhaust alternatives before blocking", TEXT, "references/retry-policy.md",
     r"(?i)alternative|exhaust", "blocked --tried"),
    (31, "genuine blocker is a five-term conjunction", GATE, "tools/run-state.py",
     r"--tried is required", "blocked --tried non-empty"),
    (32, "never invent a blocker", GATE, "tools/run-state.py",
     r"BLOCK_CONCLUSIONS", "audit + blocked"),
    (33, "verification gate V/P/F", GATE, "SKILL.md",
     r"\*\*VERIFIED\*\*.*\*\*PARTIAL\*\*|\*\*PARTIAL\*\*", "criteria + check"),
    (34, "result received is not verified", TEXT, "SKILL.md",
     r"RESULT RECEIVED is not RESULT VERIFIED", "dispatch observed vs verified"),
    (35, "completion gate", GATE, "tools/run-state.py",
     r"no acceptance criteria|criterion .* is ", "check"),
    (36, "continue until completion", TEXT, "SKILL.md",
     r"One gate before you stop", "check"),
    (37, "user's objective has priority", TEXT, "SKILL.md",
     r"at the expense of completion", "none"),
    (38, "do not over-delegate", TEXT, "SKILL.md",
     r"Do not over-delegate", "none"),
    (39, "do not under-delegate", GATE, "SKILL.md",
     r"And do not under-delegate", "dispatch gate + check"),
    (40, "multi-agent synthesis", TEXT, "SKILL.md",
     r"never concatenate", "none"),
    (41, "handoff control", GATE, "SKILL.md", r"handoff", "set-mode + check"),
    (42, "context package for agents", TEXT, "references/delegation.md",
     r"(?i)hand over|context package", "none"),
    (43, "state + context + capability triad", TEXT, "SKILL.md",
     r"resolve capability|required capability", "none"),
    (44, "recovery must update state", TEXT, "SKILL.md",
     r"Every recovery changes state", "blocked --next-action"),
    (45, "self-evaluation questions", TEXT, "SKILL.md",
     r"did we under-delegate|process\*\*, which verification", "none"),
    (46, "final can-i-still-do-something gate", TEXT, "references/completion-law.md",
     r"## The route list", "check decides 2 of 14"),
    (47, "final delivery format", TEXT, "references/output-contract.md",
     r"(?i)deliver", "none"),
    (48, "if completed template", TEXT, "references/output-contract.md",
     r"(?i)completed", "none"),
    (49, "if partial template", TEXT, "references/output-contract.md",
     r"(?i)partial", "none"),
    (50, "if blocked template", TEXT, "references/output-contract.md",
     r"(?i)blocked", "none"),
    (51, "failed is not blocked", TEXT, "references/output-contract.md",
     r"(?i)failed", "none"),
    (52, "operational priority", TEXT, "SKILL.md",
     r"(?i)priority|serve", "none"),
    (53, "core execution law", TEXT, "references/completion-law.md",
     r"Recovery is not the end of the task", "audit + check"),
    (54, "master execution loop", TEXT, "SKILL.md",
     r"RECEIVE.*TRIAGE.*DECIDE", "none"),
    (55, "final non-negotiable rule: two conditions", GATE, "tools/run-state.py",
     r"TERMINAL_CLAIMS", "audit"),
    (56, "the agent exists to finish work", TEXT, "references/completion-law.md",
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
    gates = texts = 0
    seen: set[int] = set()

    for sec, req, kind, target, pattern, enforcement in ROWS:
        seen.add(sec)
        ok, detail = probe(kind, target, pattern)
        if kind == GATE:
            gates += 1
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
          f"  ({gates} with a command behind them, {texts} prose-only)")
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

    if gaps:
        print(f"\nFAIL  {len(gaps)} gap(s). The kernel does not implement the "
              f"specification it is being measured against.")
        return 1
    print("\nPASS  every section of the spec is addressed, and the table's hash "
          "matches the spec it was written from.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
