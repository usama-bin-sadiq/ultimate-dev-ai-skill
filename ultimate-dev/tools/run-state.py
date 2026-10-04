#!/usr/bin/env python3
"""Run state: create, read, update, and check it.

`references/state-system.md` has specified this structure for the whole life of the
repository and nothing has ever read or written it. Every claim the architecture makes
about resumption, about work outliving a context window, and about the L4+ rows of the
scale ladder depends on a file existing -- and none did. That is the gap this closes.

State is a single JSON file, one per run, under `--state-dir` (default <skill_root>/.memory/ or ~/.ultimate-dev/.memory/).
That directory is the agent's private, disposable, gitignored working memory and
is never where a deliverable goes; `deliver` refuses a path inside it.
It is small on purpose: `state-system.md` asks for size discipline, and a state file that
grows without bound is a context problem wearing a different hat.

    python3 tools/run-state.py init      --objective "..."  [--rung R2] [--scale L3]
    python3 tools/run-state.py show
    python3 tools/run-state.py set-mode  --mode route --why "three sources" \
                                         --until "single-source follow-up"
    python3 tools/run-state.py handoff   --to <role> --authority delegated
    python3 tools/run-state.py step      --doing "..." --precondition "..." --expect "..." \
                                         --capability "..." --verify "..."
    python3 tools/run-state.py log       --kind execute --what "..."  [--under P03]
    python3 tools/run-state.py record    --observation "..." 
    python3 tools/run-state.py decide    --question "..." --selected "<an action>" \
                                         --rejected "..." --rationale "..." \
                                         --confidence "high in X" --evidence OBS-1
    python3 tools/run-state.py context   --ref "..." --why "..." [--enables "..." --scope "..."]
    python3 tools/run-state.py context   --gap "<what is missing>"   /  --closed "<gap>"
    python3 tools/run-state.py require   --what "..."
    python3 tools/run-state.py satisfy   --what "..." --evidence OBS-1
    python3 tools/run-state.py recover   --class <one of nine> --action "<what was done>" --result "<what it produced>"
    python3 tools/run-state.py blocked   --what "..." --reason "..." --tried "..." --routes <one of fifteen>
    python3 tools/run-state.py reflect   --answer "<question>=<answer>"   # all fifteen
    python3 tools/run-state.py finish    --status completed|partial|blocked|failed
    python3 tools/run-state.py audit     -            # or --path <file>
    python3 tools/run-state.py check
    python3 tools/run-state.py list

COORDINATION MODE is the field revision 2 added. It is one of inline, delegate, route,
handoff, and it carries the condition that would change it -- so a mode that turns out to
be wrong is a recorded fact rather than an invisible one.

THE PROCESS LOG and THE COMPLETION STATUS are revision 3. The log is numbered P01, P02,
... and never resets, including across a recovery, because a number that restarts at 1
after a failure produces a log that cannot be read to find out what had already been
tried -- which is the only reason it is numbered. Its entries that claim something about
the work are checked against the work: a line saying a specialist was invoked is refused
unless the dispatch ledger says one was, and `verify` is refused unless something was
actually verified. `finish` writes the terminal status and refuses `completed` unless all
four conditions of section 35 hold at once: every work unit closed, at least one
acceptance criterion and all of them met, and no capability in flight.

`audit` is the complement of every gate here. All of them read the state; `audit` reads
the delivery. That is the one that matters, because a run can satisfy every gate in this
file and still hand the user a report describing work it did not do -- the description
and the state are written by the same judgement and share its blind spot.

Usage notes:
  * `check` is the gate. It exits non-zero on an unknown mode, a mode with no reason, a
    mode with no reversing condition, a handoff with no target, evidence that is prose
    rather than a pointer, a rung outside R0..R4, a scale outside L1..L7, an R2+ rung
    with neither trigger, and repeated mode or rung changes.

    Three of those were claimed and not implemented. `until` was written by
    set-mode and read by nothing, so the reversing condition the kernel is told
    to record was never required. The rung and scale were not read at all, so the
    numbers the effort gate exists to produce were neither constrained nor
    verified -- `--rung` accepted the string "banana". And `check` read
    `evidence` with `.strip()`, so a decision carrying the list form its own
    schema defines crashed it; a crash exits non-zero, which looks like the gate
    firing rather than the gate being broken.

    Revision 3 found the same class of gap a third time, in the one place the
    spec is most worried about. The process log and the completion status were
    both specified -- sections 22-24 name the kinds, section 35 names the four
    conditions, section 26 names five fields per work unit -- and both were
    prose. `COMPLETION_STATUSES`, `STEP_FIELDS` and `LOG_KINDS` were declared as
    constants in this file and read by nothing, which is the same defect as
    `until` wearing a different hat: a vocabulary that exists and is never
    consulted constrains nobody.

    tools/test-run-state.py asserts every clause of this list in both
    directions, and found the last two of those three.

    Revision 5 took the ratio the other way. check-spec.py measured 17 of 61 spec
    sections with a command behind them and called the remaining 44 prose; the
    request was to enforce all of them, and the honest answer turned out to be
    55 gated, 6 decided prose, and 0 undecided. Thirty-one new refusals landed:
    the executable-action rule on a decision record, the four parts of a context
    request, the open context gap, the state-shape report, the orphan checks, the
    state machine's ordering, the recovery class and its seven fields, the fifteen
    routes, the handover brief, the handback result, over-delegation, synthesis,
    the fifteen self-evaluation questions, and the delivery sections.

    Six sections stayed prose, and check-spec now fails on any row that is neither
    gated nor carries a stated reason. That is the part worth more than the
    thirty-one: an unclassified row reads as a backlog item somebody forgot, and
    the table was rewritten once already to stop being that.

    Four of the thirty-one arrived broken and were fixed by being run before their
    assertions were written, which is the rule the S36 lint exists to enforce:
    `rung_code` was read above its assignment; an empty process log accepted any
    stage; the §18 check gated on a field holding a value rather than existing,
    so a correct early run failed for being early; and two of §45's questions share
    their first eighteen characters, so one answer silently answered the wrong
    question.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import shutil
import sys

# Working memory, not deliverables. `.memory/` was already in .gitignore as
# "Local agent state" while the tool wrote to `.ultimate-dev/`, so the
# convention was declared and the implementation ignored it -- and two names for
# one thing meant a run started by one version could not be read by the other.


def _find_skill_root(start: str) -> "str | None":
    """Walk up from start looking for the directory that contains SKILL.md."""
    current = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(current, "SKILL.md")):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # reached filesystem root
            return None
        current = parent


_SKILL_ROOT = _find_skill_root(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = (
    os.path.join(_SKILL_ROOT, ".memory")
    if _SKILL_ROOT
    else os.path.expanduser("~/.ultimate-dev/.memory")
)
# Where earlier versions wrote. Read once, on load, and migrated rather than
# silently ignored: a state file the tool cannot find is indistinguishable from
# a run that never recorded anything, and the second is a finding about the
# agent while the first is a finding about the tool.
LEGACY_DIR = ".ultimate-dev"
STATE_FILE = "run-state.json"
# 4 added `log`, `completion`, `host`, `host_history` and `exceeds_ceiling` at the
# top level, and `capability` / `verify` on each step. Nothing reads this field, so
# nothing breaks on the bump -- which is exactly why it needed making: a version
# number that is allowed to drift is a version number that carries no information,
# and it was still claiming 3 after the shape had changed. Every added field is
# read with .get() or setdefault(), so a 3 state file loads unchanged.
SCHEMA_VERSION = 4

# The capability dispatch contract, from the kernel's "no silent degradation"
# section. The chain matters in one direction: a capability that was chosen and
# never observed is a delegation described rather than performed, which is the
# under-doing failure wearing a different hat.
# --- §1/§2/§32/§55: the phrasings a run may not end on ---
#
# The specification names them, which makes them a list rather than a sentiment,
# and a list can be checked. Two classes, because they fail differently:
#
#   A. A non-action paired with a block conclusion -- "I did not use the skill,
#      therefore blocked". This is a false conclusion about the world, not a
#      phrasing choice, and it is always a defect.
#   B. A named terminal justification -- "the first attempt failed". Legitimate
#      inside a recovery narrative, illegitimate as a stopping point, so it is
#      only a defect when it is what the delivery leads with.
#
# The second class is the hard one, because the same words serve both purposes.
# A check that failed on the vocabulary would be satisfied by rewording, and
# rewording is not the property under test. So class B is checked against the
# shape of a terminal claim -- a justification standing where a result should be,
# with nothing after it -- and the remedy it prints is to record which of the two
# conditions of section 55 holds, not to choose different adjectives.
BLOCK_CONCLUSIONS = (
    (re.compile(r"\b(?:did\s+not|didn't|have\s+not|haven't|never)\s+"
                r"(?:use|used|invoke|invoked|call|called|touch|touched|run|ran|"
                r"execute|executed|load|loaded|deploy|deploy)\b"
                r"[^.?!\n]{0,120}?\b(?:therefore|so|thus|hence)?\s*"
                r"\b(?:blocked|unavailable|therefore blocked|so blocked)\b", re.I),
     "a capability not used, concluded blocked or unavailable -- the capability "
     "was not looked for, which is not a finding about the host"),
    (re.compile(r"\b(?:need|needs|needed|require|requires|required)\s+(?:more\s+)?"
                r"(?:additional\s+|further\s+)?"
                r"(?:context|information|info|details?)\b"
                r"[^.?!\n]{0,60}?\b(?:therefore|so|thus)?\s*"
                r"\b(?:blocked|stopping|stopped|cannot continue)\b", re.I),
     "missing context concluded to be a stop -- context that can be acquired is "
     "route 2 of the gate before you stop, not a terminal state"),
    (re.compile(r"\b(?:the\s+)?task\s+(?:is|was)\s+complex\b"
                r"[^.?!\n]{0,40}?\b(?:therefore|so|thus)?\s*"
                r"\b(?:blocked|stopping|stopped|not\s+(?:attempted|proceed))\b", re.I),
     "complexity concluded to be a stop -- complexity is a rung, and a rung is "
     "revised by evidence rather than obeyed"),
    (re.compile(r"\b(?:first|initial|original)\s+"
                r"(?:approach|method|attempt|try|strategy)\s+failed\b"
                r"[^.?!\n]{0,60}?\b(?:therefore|so|thus)?\s*"
                r"\b(?:blocked|stopping|stopped|giving up)\b", re.I),
     "a failed first approach concluded to be a stop -- section 29: approach "
     "failure is not task impossibility"),
    (re.compile(r"\b(?:i\s+)?(?:only\s+)?(?:planned|identified|found|discovered)\b"
                r"[^.?!\n]{0,60}?\b(?:therefore|so|thus)?\s*\bblocked\b", re.I),
     "planning or discovery concluded to be a block -- candidate_found is never "
     "task_completed, and it is not blocked either"),
)

# A terminal claim: the sentence opens the delivery, or is the whole of it. A
# justification buried mid-report is a recovery narrative and is left alone.
TERMINAL_CLAIMS = (
    re.compile(r"^\W{0,3}i\s+(?:did\s+not|didn't|only\s+(?:planned|identified|"
               r"found|reviewed|analysed|analyzed))\b", re.I),
    re.compile(r"^\W{0,3}i\s+(?:wasn't|was\s+not)\s+sure\b", re.I),
    re.compile(r"^\W{0,3}(?:i\s+)?need\s+(?:more\s+)?(?:context|information)\b", re.I),
    re.compile(r"^\W{0,3}the\s+(?:task\s+was|skill\s+is|agent\s+is)\s+complex\b", re.I),
    re.compile(r"^\W{0,3}(?:the\s+)?(?:first|initial)\s+(?:attempt|approach|try)"
               r"\s+failed\b", re.I),
    re.compile(r"^\W{0,3}i\s+(?:found|identified)\s+the\s+"
               r"(?:skill|agent|specialist|capability)\b", re.I),
    re.compile(r"^\W{0,3}i\s+(?:didn't|did\s+not)\s+invoke\b", re.I),
)

# The four completion statuses (sections 35, 48-51). `completed` is the only one
# that asserts the objective was met, so it is the only one `check` refuses
# without every criterion satisfied and no block standing.
COMPLETION_STATUSES = ("completed", "partial", "blocked", "failed")

# A work unit's declared shape (section 26). `capability` and `verify` are the
# two that get skipped: a unit worked on with no named capability, and an
# expected condition with no verification method, are both a wish.
STEP_FIELDS = ("doing", "precondition", "expect", "capability", "verify")

# The process log (sections 22-24). Every entry names a kind, and the kinds are a
# closed vocabulary because the specification lists them; a list can be checked,
# and free text cannot.
#
# The value is the *dispatch state the entry claims*. A log line that says a
# specialist was invoked is refused unless the ledger says one was, which is the
# dispatch chain's own rule ("a capability at `selected` is not `observed`")
# applied to the narrative form. This is the whole of section 24: a run can
# satisfy every state gate and still write a log claiming work it did not do,
# because the log is prose and the gates are not.
#
# `None` means the entry claims nothing about the capability ledger, so it is
# always accepted. Two claims are not about a capability and are checked against
# the run instead: `verify` (satisfied by a dispatch at verified, or by a
# criterion met -- an inline run verifies without ever dispatching) and
# `complete` (satisfied by a recorded completion status).
LOG_KINDS = {
    # Section 25's stage names.
    "receive": None, "understand": None, "triage": None, "decide": None,
    "context": None, "plan": None, "execute": "running", "observe": "observed",
    "verify": "verified", "recover": None, "replan": None, "escalate": None,
    "synthesize": None, "deliver": None, "complete": None,
    # The names section 23's worked example uses, kept so a log written by
    # copying that example is accepted verbatim rather than rejected as a typo.
    "delegate": "invoked", "dispatch": "invoked", "reachability": None,
    "recovery": None, "result": "observed", "executed": "running",
    "observed": "observed", "invoked": "invoked", "verified": "verified",
    # Found by the gate refusing to log real work. `execute` claims a dispatch is
    # `running`, because §23's example uses it for the specialist's turn -- so a run
    # that did its work inline, which is most runs and the cheap-correct case, had
    # no kind that described what it did. Forcing such a run to either lie about a
    # dispatch or omit the execution from its own log is the gate punishing the
    # honest answer. `execute-inline` is the honest answer, and it is also the one
    # a reader most wants distinguished: work this kernel did, versus work it
    # bought.
    "execute-inline": None,
}

# §25's state machine, as the part of it that can be checked: what has to precede
# what. `LOG_STAGE_ENTRY` are the kinds a log may open with -- a run may begin
# work without a recorded plan, and an inline run has no dispatch to be running.
LOG_STAGE_ENTRY = frozenset({"receive", "understand", "triage", "decide", "plan",
                             "execute-inline", "reachability", "recover",
                             "recovery", "replan", "escalate"})
LOG_STAGE_PREDECESSORS = {
    "execute": frozenset({"plan", "decide", "delegate", "dispatch", "execute",
                          "execute-inline", "replan", "recover", "recovery"}),
    "executed": frozenset({"plan", "decide", "delegate", "dispatch", "execute",
                           "execute-inline", "replan", "recover", "recovery"}),
    "delegate": frozenset({"decide", "reachability", "plan", "replan"}),
    "dispatch": frozenset({"decide", "reachability", "plan", "replan"}),
    "invoked": frozenset({"decide", "reachability", "plan", "delegate",
                          "dispatch", "replan"}),
    "observe": frozenset({"execute", "executed", "execute-inline", "delegate",
                          "dispatch", "invoked"}),
    "observed": frozenset({"execute", "executed", "execute-inline", "delegate",
                           "dispatch", "invoked"}),
    "result": frozenset({"execute", "executed", "execute-inline", "delegate",
                         "dispatch", "invoked", "observe", "observed"}),
    "verify": frozenset({"observe", "observed", "result", "execute-inline",
                         "decide"}),
    "verified": frozenset({"observe", "observed", "result", "execute-inline",
                           "decide"}),
    "synthesize": frozenset({"verify", "verified", "observe", "observed",
                             "execute-inline"}),
    # `deliver` deliberately accepts almost anything before it. It is a terminal
    # act, and a short run that received, triaged and delivered is legitimate --
    # demanding an execution entry first punishes a run for being short, which is
    # the same mistake as gating a field on whether it holds a value rather than
    # whether it exists. The "a long run delivered having logged no execution at
    # all" case is real, and it is checked in `check` instead, where the rung and
    # the work-unit count are both known.
    "deliver": LOG_STAGE_ENTRY,
    "complete": frozenset({"deliver", "synthesize", "verify", "verified"}),
}

DISPATCH_ORDER = ("selected", "invoked", "running", "observed", "verified")
# `unreachable` and `skipped` are terminal verdicts, not stages of the chain --
# a capability the host does not expose, or one deliberately passed over.
DISPATCH_TERMINAL = ("unreachable", "skipped")
DISPATCH_STATES = DISPATCH_ORDER + DISPATCH_TERMINAL


MODES = ("inline", "delegate", "route", "handoff")

# The host's capability, as a term in the effort gate.
#
# The rung ladder answers "how hard is this task". It has never answered "what can
# this model actually carry", and that omission is measurable in both directions,
# which is rare for a design question.
#
# Toward dull on a strong host: this repository's own research says step-by-step
# scripts and stacked MUST/NEVER measurably degrade current-generation model
# output, and that structured-but-irrelevant context is a distinct risk class --
# a coherent procedure is worse than none when it is not the one your model needs.
# A 549-line kernel applied unchanged to a frontier model is spending its
# attention on form.
#
# Toward dull on a weak host: the same research says less-capable models fail to
# *trigger* loads, so a rule that is only reachable by looking it up is a rule that
# does not fire. And breadth is the expensive failure -- a small model given twenty
# work units produces twenty shallow ones, which reads as thorough and is nothing
# of the kind.
#
# So the ceiling is the useful maximum, and it is a ceiling on *procedure*, never on
# the hard rules. A small host may still decide to run R3 for one focused, hard call;
# it has to say why. What it may not do is get there by default.
#
# Host-derived, never a model name: the tier is read from what the host exposes, the
# same rule the capability registry already follows. A ladder that named models
# would be stale the week a model ships.
HOSTS = ("small", "mid", "frontier")
HOST_CEILING = {"small": "R2", "mid": "R3", "frontier": "R4"}
#
# There is deliberately no HOST_FLOOR. One was written here first, uniform at R0
# across all three tiers, and it could never fire -- which makes it worse than
# dead code, because a reader meets a mechanism that expresses no judgement and
# cannot tell it from one that does. The asymmetry it was reaching for is real and
# is enforced elsewhere: the under-investment gate keys on the *host being
# frontier*, not on a floor value, because that is the actual condition. See the
# frontier de-escalation check in cmd_check.

# The rung and scale vocabularies, as constrained values rather than free text.
# `--rung` was `default="R1"` with no choices=, so it accepted the string
# "banana", stored it, and `check` never read the field -- so the one number
# the effort gate is meant to produce was neither typed nor verified. Mode has
# always carried choices=; rung did not, and that asymmetry is what this removes.
RUNGS = {
    "R0": "Immediate",
    "R1": "Structured",
    "R2": "Analytical",
    "R3": "Deep",
    "R4": "Assurance",
}
SCALES = ("L1", "L2", "L3", "L4", "L5", "L6", "L7")

# Evidence must point, not narrate. "the logs showed retries" cannot be checked for
# existence, so a fabricated citation is indistinguishable from a real one. A pointer
# either resolves to a recorded observation or it does not, and that is mechanical.
EVIDENCE_POINTER = re.compile(r"^(none|OBS-\d+)$", re.IGNORECASE)

REQUIRED = ("objective", "coordination", "decisions", "observations")

# §18's RunState field list, mapped onto where this tool actually keeps each one.
#
# The mapping is the point, and it is mostly a record of what is NOT here. §18
# names 38 fields; this file had somewhere to put about half of them on its own,
# and the rest either live under a different name (`run_id` for `task_id`,
# `steps` for `current_step`) or had no home at all (`unknowns`, `dependencies`,
# `retries`, `escalations`, and a dozen more).
#
# Two ways to handle that, and only one of them is honest. The first is to add all
# 38 fields and refuse a run that leaves them empty -- which would charge every R0
# and R1 run for ceremony the kernel spends its first page criticising, and would
# be a gate that fires on bookkeeping rather than on correctness. The second is to
# name the coverage and let a reader judge it. That is this table, and `check`
# reports the ratio and fails only where a *mapped* field is actually missing.
#
# A `None` target is a field §18 asks for that this tool does not keep. Those are
# the ones to look at first when deciding what to build next, which is why they
# are enumerated rather than quietly absent.
RUNSTATE_FIELDS: tuple[tuple[str, "str | None"], ...] = (
    ("task_id", "run_id"),
    ("objective", "objective"),
    ("status", "completion"),
    # `status` and `completion_status` are the same field in §18's list, so they
    # map to the same container. The distinction the specification draws between
    # them is prose, not shape, and a gate that enforced the difference would be
    # enforcing a distinction nobody can observe.
    ("current_stage", None),              # the log's last `kind` is the stage
    ("current_step", "steps"),
    ("process_number", "log"),
    ("requirements", None),
    ("constraints", None),
    ("status", "completion"),
    ("completion_status", "completion"),
    ("success_criteria", "criteria"),
    ("assumptions", "assumptions"),
    ("unknowns", None),
    ("dependencies", None),
    ("selected_capabilities", "dispatch"),
    ("available_capabilities", None),
    ("reachable_capabilities", None),
    ("coordination_mode", "coordination.mode"),
    ("active_agent", "active_agent"),
    ("authority", "authority"),
    ("context_loaded", "context.loaded"),
    ("context_requested", "context.gaps"),
    ("context_required", "context.loaded"),
    ("context_reason", "context.why"),
    ("execution_plan", "steps"),
    ("atomic_work_units", "steps"),
    ("completed_work_units", "steps"),
    ("remaining_work_units", "steps"),
    ("delegated_tasks", "dispatch"),
    ("agent_results", None),              # DISPATCH_ORDER is the chain, not a store
    ("evidence", "observations"),
    ("verification_status", "verification.verdicts"),
    ("verification_results", "verification.verdicts"),
    ("errors", None),
    ("failures", None),
    ("recovery_attempts", "recoveries"),
    ("mode_changes", "coordination.changed"),
    ("replans", "log"),
    ("retries", None),
    ("escalations", "handoffs"),
    ("final_result", "result"),
    ("completion_status", "completion"),
    ("blocker", "blocks"),
)

# §19: state is updated after every important event. The form that can be checked
# is not "was the state updated" -- that is unobservable -- but the converse: an
# event that demonstrably happened must have left a trace. Each pair is (a
# predicate over the state that means the event happened, the path that must then
# be non-empty). An orphaned fact is the failure: something occurred, the run
# knows it, and nothing was recorded about it.
ORPHAN_CHECKS: tuple[tuple[str, "str | None"], ...] = (
    ("a capability was invoked", "dispatch.history"),
    ("a recovery was recorded", "recoveries.result"),
    ("a block was declared", "blocks.routes"),
    ("a mode change happened", "coordination.changed"),
    ("a handoff returned", "handoffs.returned_at"),
    ("a work unit was opened", "steps"),
)
# Read through _has(), so ORPHAN_CHECKS is the single list of what §19 demands a
# trace for, and the prose above can name each orphan in its own words without the
# two drifting apart.
ORPHAN_REASONS = {path: what for what, path in ORPHAN_CHECKS}



def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def state_path(args) -> str:
    return os.path.join(args.state_dir, STATE_FILE)


def load(args) -> dict:
    path = state_path(args)
    if not os.path.isfile(path):
        # A run started by an earlier version wrote to .ultimate-dev/. Migrate it
        # rather than reporting no state: "no state file" is a finding about the
        # agent, and reporting one for a run that recorded plenty would send a
        # reader looking for a missing discipline that is actually a moved path.
        legacy = os.path.join(LEGACY_DIR, STATE_FILE)
        if os.path.isfile(legacy) and not args.state_dir_explicit:
            os.makedirs(args.state_dir, exist_ok=True)
            shutil.move(legacy, path)
            print(f"  migrated {legacy} -> {path} (earlier versions wrote to "
                  f"{LEGACY_DIR}/)", file=sys.stderr)
        else:
            die(f"no run state at {path}. Start with:  run-state.py init --objective \"...\"")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(args, state: dict) -> None:
    path = state_path(args)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # A trailing newline because every other text artifact in this repository has one,
    # and a file that is the odd one out gets flagged by tools that check for it.
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=False)
        fh.write("\n")


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


# --------------------------------------------------------------------- commands

def cmd_init(args) -> int:
    args.rung = _rung_code(args.rung)   # closed vocabulary, both spellings
    if str(args.scale).strip().upper() not in SCALES:
        die(f"unknown scale {args.scale!r}. One of: {', '.join(SCALES)}")
    args.scale = str(args.scale).strip().upper()
    path = state_path(args)
    if os.path.isfile(path) and not args.force:
        die(f"{path} already exists. --force to overwrite, or resume with `show`.")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "started": now(),
        "objective": args.objective,
        "rung": args.rung,
        "scale": args.scale,
        # What this host can carry, as the second term in the effort gate. The
        # rung answers how hard the task is; this answers how much procedure the
        # model can turn into substance, which is a different question and the
        # one that decides whether a run is thorough or merely long.
        "host": getattr(args, "host", None),
        # Record the assumed tier value ("mid") when --host was not supplied, or
        # None when the host was explicitly declared. cmd_set_host clears this
        # field (sets it to None) once the host is updated, so the state file
        # reliably distinguishes "never set" from "set later".
        "host_tier_assumed": "mid" if not getattr(args, "host", None) else None,
        "exceeds_ceiling": (args.exceeds_ceiling or "").strip() or None,
        # A rung without the events that would move it cannot be revised by
        # evidence, so the triggers are stored beside it rather than left to
        # prose. Empty is allowed and reported by `check` as a finding.
        "rung_triggers": {
            "escalate_on": args.escalate_on,
            "de_escalate_on": args.de_escalate_on,
        },
        # inline is the default because it is the cheapest mode and the only one that
        # costs nothing extra. Starting higher has to be a decision, not an accident.
        "coordination": {
            "mode": args.mode,
            "why": args.why or "default: cheapest adequate",
            "until": args.until or "a cheaper mode becomes inadequate, or this one fails",
            "changed": [],
        },
        "active_agent": None,
        "authority": "inline",
        # The work units from Step 5 and the compiled context from Step 3, both
        # of which were specified in references/state-system.md for the whole
        # life of the repository and had nowhere to live. A plan held only in
        # prose cannot be resumed, and a context held only in a transcript
        # cannot be reconstructed without re-reading everything, which is the
        # cost the state file exists to remove.
        #
        # `steps` is an ordered log. At most one is open: the last one without
        # an `outcome`. That entry is what the agent is doing right now, and it
        # is the first thing `show` prints, because the question "what is this
        # agent actually doing" is the one a human supervising a run asks most
        # often and the one a transcript answers worst.
        "steps": [],
        # §18's containers, created empty rather than on first use. A state file
        # that grows keys as commands are run cannot answer "has this event
        # happened" -- the difference between an empty list and an absent key is
        # the difference between "no, and here is the run that says so" and "no,
        # and nothing knows". The full list is RUNSTATE_FIELDS at the top of
        # this file; these are the ones with somewhere to live.
        "criteria": [],
        "dispatch": [],
        "recoveries": [],
        "blocks": [],
        "handoffs": [],
        # The process log (sections 22-24), numbered and never reset. It is the
        # one narrative the user reads, so it is the one place a run can assert
        # something the ledger contradicts without a gate noticing -- every other
        # list here is a record, and a record cannot assert. `cmd_log` is what
        # makes it checkable.
        "log": [],
        # The terminal status (section 35), written only by `finish`, and only
        # once the conditions for that status actually hold.
        "completion": None,
        "context": {"loaded": [], "dropped": [], "gaps": [], "why": ""},
        # Where the user said the output goes, if they said. Recorded at init so
        # the distinction between working memory and a deliverable is decided
        # once, from the request, rather than re-guessed at the end of the run --
        # which is the point at which an agent has the least context left and the
        # strongest incentive to file its work somewhere private and convenient.
        "deliverables": {"asked_location": args.deliverables or "", "produced": []},
        "decisions": [],
        "observations": [],
        "assumptions": [],
        "verification": {"criteria": [], "verdicts": []},
        "result": None,
    }
    save(args, state)
    print(f"  wrote {path}")
    print(f"  coordination: {args.mode}  ({state['coordination']['why']})")
    return 0


def cmd_show(args) -> int:
    state = load(args)
    mode = state.get("coordination", {})

    if args.json:
        print(json.dumps(state, indent=2))
        return 0

    # The current step is printed first, before the run header, because the
    # question a human asks of a running agent is "what is it doing right now"
    # and the answer should not be the fourth line. A transcript answers that
    # question worse the longer the run gets; this does not get worse.
    current = _open_step(state)
    steps = state.get("steps") or []
    if current:
        print(f"  ▶ step {current.get('n')} of {len(steps)}   {current.get('doing')}")
        print(f"      if      {current.get('precondition')}")
        print(f"      then    {current.get('expect')}")
        if current.get("capability"):
            print(f"      using   {current.get('capability')}")
        if current.get("verify"):
            print(f"      checked {current.get('verify')}")
    elif steps:
        last = steps[-1]
        print(f"  ○ no open step   last was {last.get('n')}: "
              f"{last.get('doing')} → {last.get('outcome')}")
    else:
        print("  ○ no step recorded; the run has not said what it is doing")

    print(f"  run       {state.get('run_id')}   rung {state.get('rung')} "
          f"scale {state.get('scale')}")
    host = state.get("host")
    if host:
        ceil = HOST_CEILING.get(str(host), "?")
        note = ""
        rung_c = str(state.get("rung") or "").split(" ", 1)[0].upper()
        if rung_c in RUNGS and rung_c > ceil:
            note = "  <- above this host's ceiling; set-host --why to record why"
        print(f"  host      {host}  (procedure ceiling {ceil}){note}")
    print(f"  objective {state.get('objective')}")
    print(f"  mode      {mode.get('mode')}  — {mode.get('why')}")
    print(f"  until     {mode.get('until')}")
    print(f"  active    {state.get('active_agent') or '(none)'}  "
          f"authority={state.get('authority')}")

    disp = state.get("dispatch") or []
    inflight = [d for d in disp if isinstance(d, dict)
                and (d.get("state") or "") in ("selected", "invoked", "running")]
    if disp:
        head = (f"  dispatch  {len(disp)} recorded, {len(inflight)} in flight"
                + ("  <- check will refuse" if inflight else ""))
        print(head)
        for d in disp:
            if not isinstance(d, dict):
                continue
            mark = "▶" if d in inflight else " "
            extra = ""
            if (d.get("state") or "") == "unreachable" and d.get("tried"):
                extra = f"  tried: {len(d['tried'])}"
            print(f"    {mark} {d.get('for')}  →  {d.get('state')}{extra}")
    else:
        print("  dispatch  none recorded; a chosen capability is invisible to `check`")

    ctx = state.get("context") or {}
    loaded = ctx.get("loaded") or []
    dropped = ctx.get("dropped") or []
    print(f"  context   {len(loaded)} loaded, {len(dropped)} dropped")
    for entry in loaded[-3:]:
        lvl = f" [{entry.get('level')}]" if entry.get("level") else ""
        print(f"      + {entry.get('ref')}{lvl}")
    for entry in dropped[-3:]:
        print(f"      - {entry.get('ref')}  ({entry.get('why')})")

    print(f"  steps     {len(steps)}   decisions {len(state.get('decisions', []))}   "
          f"observations {len(state.get('observations', []))}")

    # The process log, last three lines. It is the narrative the user reads, so
    # it prints next to the state rather than only under `--json`: a log that
    # disagrees with the state is the section-24 failure, and it is invisible to
    # anyone who only ever looks at one of the two.
    plog = state.get("log") or []
    comp = state.get("completion") or {}
    if comp.get("status"):
        print(f"  finished  {str(comp.get('status')).upper()}  at {comp.get('finished_at')}")
    if plog:
        print(f"  log       {len(plog)} entr{'y' if len(plog) == 1 else 'ies'}"
              f"  (P{str(plog[0].get('n')).lstrip('P')}.."
              f"{plog[-1].get('n')})")
        for e in plog[-3:]:
            print(f"      {e.get('n'):>6}  {str(e.get('kind')).upper():<12} "
                  f"{e.get('what')}")
    else:
        print("  log       empty; the run has recorded no numbered operation")

    # Working memory and deliverables are different things, so they print
    # differently: a `>` for something a person will read, and nothing at all
    # for private notes. A reader who cannot tell which is which will assume
    # both are notes, and the one that mattered will be the one they skip.
    dl = state.get("deliverables") or {}
    produced = dl.get("produced") or []
    if dl.get("asked_location"):
        print(f"  asked for output at  {dl.get('asked_location')}")
    for entry in produced:
        print(f"  > delivered  {entry.get('path')}"
              + (f"  ({entry.get('what')})" if entry.get("what") else ""))
    if state.get("result"):
        print(f"  result    {state['result']}")
    return 0


def _rung_code(value: str) -> str:
    """Normalise "R2" or "R2 Analytical" to "R2". Die on anything else."""
    code = (value or "").strip().split(" ", 1)[0].upper()
    if code not in RUNGS:
        die(f"unknown rung {value!r}. One of: {', '.join(RUNGS)} "
            f"(optionally with its name, e.g. 'R2 Analytical')")
    return code


def cmd_set_rung(args) -> int:
    """Change the effort rung, in either direction, keeping the history.

    De-escalation had no mechanism at all. `init` was the only command that
    wrote a rung, so raising it meant `init --force`, and --force overwrites the
    whole state file: the decisions and observations recorded so far are lost.
    So the only available response to "reality is harder than expected" was to
    discard the record of what had happened, and the only available response to
    "reality is easier than expected" was to do nothing and carry the heavier
    reasoning to the end.

    SKILL.md calls de-escalation "the direction most often missing elsewhere".
    The tool implemented the opposite asymmetry: mode thrashing -- the axis
    SKILL.md does not single out -- was the only one with a gate.
    """
    state = load(args)
    code = _rung_code(args.rung)
    previous = state.get("rung")
    state["rung"] = code
    triggers = state.setdefault("rung_triggers", {"escalate_on": "", "de_escalate_on": ""})
    if args.escalate_on:
        triggers["escalate_on"] = args.escalate_on
    if args.de_escalate_on:
        triggers["de_escalate_on"] = args.de_escalate_on
    history = state.setdefault("rung_changed", [])
    history.append({
        "from": previous, "to": code, "at": now(), "why": args.why or "",
    })
    save(args, state)
    direction = "escalated" if code > (previous or code) else "de-escalated"
    print(f"  rung {previous} -> {code}  ({direction})")
    if args.why:
        print(f"  because {args.why}")
    if not triggers.get("de_escalate_on"):
        print("  note: no de-escalation trigger recorded. A rung you cannot lower")
        print("        is a label rather than a decision. Pass --de-escalate-on.")
    return 0


def cmd_set_mode(args) -> int:
    state = load(args)
    if args.mode not in MODES:
        die(f"unknown mode {args.mode!r}. One of: {', '.join(MODES)}")
    mode = state["coordination"]
    previous = mode.get("mode")
    mode["mode"] = args.mode
    mode["why"] = args.why or mode.get("why")
    if args.until:
        mode["until"] = args.until
    # The history is the point. A mode that changes three times in a run is a signal
    # the first choice was wrong, and that is only visible if the changes are kept.
    mode.setdefault("changed", []).append({
        "from": previous, "to": args.mode, "at": now(), "why": args.why or "",
    })
    if args.mode != "handoff":
        state["active_agent"] = None
        state["authority"] = "inline"
    save(args, state)
    print(f"  mode: {previous} -> {args.mode}")
    print(f"  why:  {args.why or '(unchanged)'}")
    return 0


def cmd_handoff(args) -> int:
    state = load(args)
    if state["coordination"].get("mode") != "handoff":
        # Set the mode too rather than refusing: a handoff that does not record the
        # mode it implies is exactly the invisible change the field exists to prevent.
        state["coordination"].setdefault("changed", []).append({
            "from": state["coordination"].get("mode"), "to": "handoff",
            "at": now(), "why": "handoff issued without the mode being set first",
        })
        state["coordination"]["mode"] = "handoff"
        state["coordination"]["why"] = args.why or "conversational authority moved"
    state["active_agent"] = args.to
    state["authority"] = args.authority
    save(args, state)
    print(f"  active_agent: {args.to}  authority={args.authority}")
    if args.authority == "delegated":
        print("  note: a delegated agent holds the conversation but still cannot "
              "triage, verify, or recover. JEv decides each transfer.")
    return 0


def cmd_set_host(args) -> int:
    """Record a change in what this host can carry, and keep the reason.

    Two things make this a record rather than a field. First, the rung is not
    rewritten for you: a run that has decided it can carry more than its host's
    ceiling is sometimes right -- one focused, hard call is exactly what a small
    model is good at -- and the way to be right about that is to say so. Second,
    the direction is asymmetric. Raising the host mid-run is free. Lowering it
    carries a reason, because that is the direction the evidence says goes wrong
    silently.
    """
    state = load(args)
    host = (args.host or "").strip().lower()
    if host not in HOSTS:
        print(f"set-host: --host {host!r} is not one of {', '.join(HOSTS)}. The "
              f"tier is what the host exposes, not a model name -- a ladder that "
              f"named models would be stale the week one ships.", file=sys.stderr)
        return 2
    prior = state.get("host")
    if prior == host:
        print(f"  host is already {host!r}")
        return 0
    if not (args.why or "").strip():
        print("set-host: --why is required. A change in what the host can carry "
              "changes every later rung decision, and an unexplained one cannot be "
              "reviewed by anyone including you.", file=sys.stderr)
        return 2

    state.setdefault("host_history", []).append({
        "from": prior, "to": host, "why": args.why.strip(), "at": now(),
    })
    state["host"] = host
    # Clear the assumed-tier marker: the host is now explicitly set.
    state["host_tier_assumed"] = None
    save(args, state)
    print(f"  host {prior or '(unset)'} -> {host}  "
          f"(ceiling {HOST_CEILING[host]})  {args.why}")
    return 0


def cmd_record(args) -> int:
    state = load(args)
    state.setdefault("observations", []).append({
        "id": f"OBS-{len(state.get('observations', [])) + 1}",
        "text": args.observation,
        "at": now(),
    })
    save(args, state)
    print(f"  recorded OBS-{len(state['observations'])}")
    return 0


# §28's nine failure classes, as a closed vocabulary. Named by the specification,
# which is what makes them a list rather than a sentiment, and a list can be
# checked: a recovery that does not say which kind of failure it recovered from
# cannot be evaluated, because "I fixed it" and "I changed approach" are the same
# words whether the cause was a missing capability or a bad assumption.
FAILURE_CLASSES = (
    "capability", "context", "tool", "input", "execution",
    "verification", "coordination", "dependency", "resource",
)

# §30's fifteen routes, in the order the specification lists them, plus §46's
# "genuinely no executable path remains" as the fifteenth. This is the list that
# `references/completion-law.md` calls "the route list", and until now it existed
# in two markdown files that could drift from each other with nothing to notice.
# It lives here because `blocked --tried` is the only place a run actually walks
# it, and a route that cannot be named cannot be walked.
ROUTES = (
    "retry",
    "acquire-context",
    "other-skill",
    "other-agent",
    "inline",
    "delegate",
    "route",
    "reorder",
    "decompose",
    "other-resource",
    "replan",
    "recover",
    "continue-partially",
    "reduce-scope",
    "no-path-remains",
)



def cmd_recover(args) -> int:
    """Record a recovery, and the seven fields §44 says every one must change.

    §28 asks for a classification before a response and §44 for the state to
    record what changed. Together they are the difference between a run that
    retried and a run that recovered: a retry with no recorded cause reproduces
    the failure while producing the appearance of effort, and the appearance is
    the part a reader can see.

    `--class` is a closed vocabulary for the same reason the process log's kinds
    are. `--action` is required, because "recovered" is not an action, and
    `--result` is required because a recovery with no recorded outcome has not
    been evaluated -- which is the failure the command exists to prevent.
    """
    state = load(args)
    cls = (args.cls or "").strip().lower()
    if cls not in FAILURE_CLASSES:
        print(f"recover: --class {cls!r} is not one of "
              f"{', '.join(FAILURE_CLASSES)}", file=sys.stderr)
        return 2
    action = (args.action or "").strip()
    if not _is_executable_action(action):
        print("recover: --action is required, and it has to be an action rather "
              "than a category. 'recovered' records that something happened; "
              "'invoked the reviewer and recorded what came back' records what.",
              file=sys.stderr)
        return 2
    result = (args.result or "").strip()
    if not result:
        print("recover: --result is required. A recovery with no recorded outcome "
              "has not been evaluated, and a re-plan against an unevaluated "
              "recovery is a blind retry with a longer log.", file=sys.stderr)
        return 2

    mode = state.get("coordination") or {}
    rec = {
        "n": len(state.get("recoveries") or []) + 1,
        "class": cls,
        "reason": (args.reason or "").strip() or None,
        "action": action,
        "from_mode": (args.from_mode or "").strip() or None,
        "to_mode": (args.to_mode or "").strip() or None,
        "from_capability": (args.from_capability or "").strip() or None,
        "to_capability": (args.to_capability or "").strip() or None,
        "result": result,
        "at": now(),
    }
    if mode.get("mode") and not rec["from_mode"]:
        rec["from_mode"] = mode.get("mode")
    state.setdefault("recoveries", []).append(rec)
    save(args, state)
    print(f"  recovery {rec['n']} recorded: {cls} failure -> {result}")
    return 0


def cmd_decide(args) -> int:
    state = load(args)
    state.setdefault("decisions", []).append({
        "question": args.question,
        "selected": args.selected,
        # `rejected` is the field that earns its place: a decision without a recorded
        # alternative is an assertion, and cannot be reviewed later.
        "rejected": args.rejected,
        "rationale": args.rationale,
        "confidence": args.confidence,
        "evidence": args.evidence,
        "cost": args.cost,
        "recovery": args.recovery,
        "at": now(),
    })
    save(args, state)
    print(f"  decision recorded ({len(state['decisions'])} total)")
    return 0


def _open_step(state: dict) -> dict | None:
    """The step with no outcome: what the agent is doing right now."""
    for step in reversed(state.get("steps") or []):
        if step.get("outcome") is None:
            return step
    return None


def cmd_step(args) -> int:
    """Open, close, or list the work units. One of them is current.

    Opening a step closes the previous one, because leaving two open makes
    "what is the agent doing now" have two answers and neither of them is
    checkable. A step that is superseded mid-flight is recorded as such rather
    than closed silently, because a plan that changed without saying so is
    indistinguishable from a plan that was abandoned.
    """
    state = load(args)

    if args.list:
        steps = state.get("steps") or []
        if not steps:
            print("  no steps recorded")
            return 0
        width = max(len(str(s.get("n"))) for s in steps)
        for step in steps:
            mark = "open" if step.get("outcome") is None else "done"
            print(f"  {str(step.get('n')).rjust(width)}  {mark}  {step.get('doing')}")
        return 0

    if args.close:
        current = _open_step(state)
        if current is None:
            die("no open step to close. `step --doing ...` opens one.")
        if not (args.outcome or "").strip():
            die("--outcome is required to close a step. A step that ends with no "
                "recorded outcome is the same as a step that was never run.")
        current["outcome"] = args.outcome
        current["closed_at"] = now()
        save(args, state)
        print(f"  step {current.get('n')} closed: {args.outcome}")
        return 0

    doing = (args.doing or "").strip()
    if not doing:
        die("--doing is required. A step with no description cannot be resumed.")
    if not (args.precondition or "").strip():
        die("--precondition is required. Step 5 defines a work unit as "
            "independently verifiable, and a precondition is what makes it so: "
            "it is the condition a resuming agent re-checks before repeating the work.")
    if not (args.expect or "").strip():
        die("--expect is required, for the same reason: it is the observable "
            "condition that tells the step finished.")

    # Section 26 gives every work unit five fields, and two of them are the ones
    # that get skipped: a unit worked on with no named capability, and an
    # expected condition with no verification method. Both are a wish rather than
    # a unit -- you cannot tell whether the capability was reachable, and you
    # cannot tell whether the expectation was ever checked. They are required at
    # R2 and above, and exempt below it, because at R0 and R1 a work unit is a
    # sentence and demanding five fields of it is the ceremony the kernel spends
    # its first page criticising.
    rung_code = str(state.get("rung") or "").split(" ", 1)[0].upper()
    if rung_code in {"R2", "R3", "R4"}:
        # argparse.Namespace has no .get(); getattr with a default is the only
        # safe read, and it also covers a state dir written by an older schema.
        missing = [f for f in STEP_FIELDS
                   if not (getattr(args, f, "") or "").strip()]
        if missing:
            die("--" + ", --".join(missing) + " required at " + rung_code +
                ". Section 26 gives a work unit five fields; `doing`, "
                "`precondition` and `expect` are the three everyone writes. "
                "`capability` names what does the work, and `verify` names how "
                "you will know the expectation held. Without them a unit is a "
                "wish with a precondition. R0 and R1 are exempt.")

    current = _open_step(state)
    if current is not None:
        current["outcome"] = "superseded"
        current["closed_at"] = now()

    state.setdefault("steps", []).append({
        "n": len(state.get("steps") or []) + 1,
        "doing": doing,
        "precondition": args.precondition,
        "expect": args.expect,
        "capability": (getattr(args, "capability", "") or "").strip() or None,
        "verify": (getattr(args, "verify", "") or "").strip() or None,
        "verification_kind": (getattr(args, "verification_kind", "") or "").strip() or None,
        "at": now(),
        "closed_at": None,
        "outcome": None,
    })
    save(args, state)
    step = state["steps"][-1]
    print(f"  step {step['n']} open: {doing}")
    if current is not None:
        print(f"  step {current.get('n')} superseded")
    return 0


def _at(state: dict, path: "str | None"):
    """Read a dotted path, returning None for any step that does not exist.

    A state file written by an older schema, or by hand, will not have every path
    in RUNSTATE_FIELDS. Missing is reported as missing rather than raising, because
    the caller's question is "is this field here", and an AttributeError answers a
    different question loudly enough to be mistaken for a gate firing.
    """
    if not path:
        return None
    cur = state
    for part in path.split("."):
        if isinstance(cur, list):
            if not part.lstrip("-").isdigit():
                return None
            try:
                cur = cur[int(part)]
            except IndexError:
                return None
        elif not isinstance(cur, dict) or part not in cur:
            return None
        else:
            cur = cur[part]
    return cur


def _has(state: dict, path: "str | None") -> bool:
    """Whether a dotted path EXISTS -- as distinct from whether it holds a value.

    The first version of the §18 check used `_at(...) is None`, which conflates
    "this field is absent" with "this field is legitimately empty". Those are
    different, and the second is often correct: `active_agent` is None before any
    handoff, `completion.status` is None before `finish`, and `criteria` is empty
    before the first `require`. Gating on truthiness made a correct R0 run fail
    for being early, which is the exact shape of a gate that punishes honesty.

    Presence is the property §18 actually asks for, so that is what is checked.
    """
    if not path:
        return False
    cur = state
    for part in path.split("."):
        if isinstance(cur, list):
            if not part.lstrip("-").isdigit():
                return False
            try:
                cur = cur[int(part)]
            except IndexError:
                return False
        elif not isinstance(cur, dict) or part not in cur:
            return False
        else:
            cur = cur[part]
    return True


def _is_executable_action(phrase: str) -> bool:
    """§5: a JEv record must produce an action, not a paragraph.

    Two mechanical tests, and the first is the one that matters. An empty or
    whitespace-only `selected` is not an action. A single word is not either --
    "delegate" names a category, "invoke the reviewer and record what came back"
    does something. The second test is a proxy for that distinction and it is a
    proxy, not a proof: a two-word noun phrase still passes. The cost of a false
    refusal here is a decision record that says what it will do, which is the
    record's whole purpose, so the test leans strict.
    """
    s = (phrase or "").strip()
    return bool(s) and len(s.split()) >= 2


def _dispatch_reached(state: dict) -> int:
    """How far the capability ledger actually got: an index into DISPATCH_ORDER.

    -1 when nothing has been dispatched, which is the normal state of a run that
    did all of its work inline. That is not a defect, and nothing here treats it
    as one -- the check below is only about a log that *claims* a dispatch.
    """
    best = -1
    for d in state.get("dispatch") or []:
        st = str((d.get("state") if isinstance(d, dict) else d) or "").lower()
        if st in DISPATCH_ORDER:
            best = max(best, DISPATCH_ORDER.index(st))
    return best


def _open_criteria(state: dict) -> list[dict]:
    return [i for i in (state.get("criteria") or [])
            if isinstance(i, dict) and i.get("status") != "met"]


def _in_flight(state: dict) -> list[str]:
    """Capabilities chosen but not yet terminal -- §35's "no required action remains".

    Every stage of the chain except `verified` counts as in flight. The
    first version also had a second branch listing those four stages by name,
    which the first branch already covered, so it could never run.
    """
    live = []
    for d in state.get("dispatch") or []:
        if not isinstance(d, dict):
            continue
        st = str(d.get("state") or "").lower()
        if st in DISPATCH_ORDER and st != "verified":
            live.append(f"{d.get('for')} ({st})")
    return live


def _process_seq(n: object) -> int:
    """The integer in a process number: 'P07' -> 7, 'P03.2' -> 3."""
    digits = "".join(ch for ch in str(n or "") if ch.isdigit())
    return int(digits) if digits else 0


def _next_process_number(state: dict) -> str:
    """The next top-level process number, counting from the whole run.

    Section 22 is explicit that numbering is not restarted during recovery,
    because a number that restarts at 1 after a failure produces a log that
    cannot be read to find out what had already been tried -- which is the only
    reason to have a log at all.

    Counted as the highest top-level number rather than the last entry, so a
    substep does not become the parent of the next top-level step. A log that
    runs P01, P02, P03.1, P04 is readable; one that runs P01, P02, P03.1, P03.2
    is a fragment, and the reader cannot tell which.
    """
    tops = [_process_seq(e.get("n")) for e in (state.get("log") or [])
            if isinstance(e, dict) and "." not in str(e.get("n") or "")]
    return f"P{max(tops) + 1 if tops else 1:02d}"


def cmd_log(args) -> int:
    """Record one line of the process log, numbered, and checked against the state.

    The log is the narrative the user reads, so it is the one place a run can
    assert something the ledger contradicts without any gate noticing: every
    other command in this file is a record, and a record cannot assert. So the
    entries that claim something about the work are checked against the work.

    `verify` and `complete` are the two that a run reaches for when it wants to
    stop, and they are the two the specification is most worried about -- sections
    24, 35 and 55 all describe the same failure, arriving in three costumes.
    """
    state = load(args)
    entries = state.setdefault("log", [])

    if args.list:
        if not entries:
            print("  process log is empty")
            return 0
        for e in entries:
            print(f"  {e.get('n'):>6}  {str(e.get('kind')).upper():<12}  "
                  f"{e.get('what')}")
        return 0

    if getattr(args, "summary", False):
        if not entries:
            print("  process log is empty")
            return 0
        for e in entries:
            n = str(e.get("n") or "").strip()
            what = str(e.get("what") or "").strip()
            print(f"  {n} — {what}")
        return 0

    kind = (args.kind or "").strip().lower()
    if kind not in LOG_KINDS:
        print(f"log: --kind {kind!r} is not one of "
              f"{', '.join(sorted(LOG_KINDS))}", file=sys.stderr)
        return 2
    what = (args.what or "").strip()
    if not what:
        print("log: --what is required. A log entry with no content records that "
              "a number was spent, which is the opposite of useful.", file=sys.stderr)
        return 2

    claim = LOG_KINDS[kind]

    if claim and claim != "verified":
        reached = _dispatch_reached(state)
        need = DISPATCH_ORDER.index(claim)
        if reached < need:
            if reached < 0:
                print(f"log: refusing {kind!r}. The run has dispatched nothing, so "
                      f"there is no {claim!r} to report. If the work was done "
                      f"inline, say so with a kind that claims nothing about the "
                      f"ledger.", file=sys.stderr)
            else:
                print(f"log: refusing {kind!r}. The capability ledger only reached "
                      f"{DISPATCH_ORDER[reached]!r}, so a line claiming {claim!r} "
                      f"contradicts the state. Section 24: the log and the state "
                      f"must agree.", file=sys.stderr)
            return 2

    if kind in ("verify", "verified"):
        met = [i for i in (state.get("criteria") or []) if i.get("status") == "met"]
        if _dispatch_reached(state) < DISPATCH_ORDER.index("verified") and not met:
            print("log: refusing a verification entry. Nothing was verified: no "
                  "capability reached `verified` and no acceptance criterion is "
                  "met. `RESULT RECEIVED` is not `RESULT VERIFIED`.", file=sys.stderr)
            return 2

    # §25: the state machine, as an order rather than a diagram. The claim a log
    # makes is about a stage, and a stage cannot be reached from anywhere. This is
    # the one place the log can be wrong about *when* rather than about *what* --
    # the §24 rule catches a false claim, and this catches an impossible one.
    #
    # `plan` and `execute-inline` are the two entry points, because a run may
    # legitimately begin work without a recorded plan at R0/R1, and an inline run
    # has no dispatch to be running. Everything downstream needs something before
    # it, and saying so is cheaper than a reader reconstructing the order.
    prior_kinds = {str(e.get("kind") or "").lower() for e in entries}
    if kind not in LOG_STAGE_ENTRY:
        need = LOG_STAGE_PREDECESSORS.get(kind)
        # An empty log is not a wildcard. The first version guarded this with
        # `if entries and ...`, which meant a log with nothing in it accepted any
        # stage at all -- so a run could open straight onto `deliver` and the
        # state machine was only enforced from the second entry onwards.
        if need and not (prior_kinds & need):
            print(f"log: refusing {kind!r}. It follows "
                  f"{', '.join(sorted(need))} in §25's state machine, and the log "
                  f"has none of them. A stage that cannot be reached from anywhere "
                  f"is a claim about a step that was not taken.", file=sys.stderr)
            return 2

    if kind == "complete":
        comp = state.get("completion") or {}
        if not comp.get("status"):
            print("log: refusing a `complete` entry. The run has recorded no "
                  "completion status, so the log is claiming an ending the state "
                  "does not have. Run `finish --status` first.", file=sys.stderr)
            return 2
        if comp.get("status") == "completed" and _open_criteria(state):
            print(f"log: refusing a `complete` entry. The run is recorded as "
                  f"completed while {len(_open_criteria(state))} acceptance "
                  f"criterion/criteria are still open.", file=sys.stderr)
            return 2

    parent = (args.under or "").strip().upper()
    number = _next_process_number(state)
    number = _next_process_number(state)
    if parent:
        match = [e for e in entries if str(e.get("n")).upper() == parent]
        if not match:
            print(f"log: --under {parent} does not name a logged step. Substeps "
                  f"hang off a step that exists.", file=sys.stderr)
            return 2
        kids = [e for e in entries
                if str(e.get("n")).upper().startswith(f"{parent}.")]
        number = f"{parent}.{len(kids) + 1}"

    entries.append({
        "n": number,
        "kind": kind,
        "what": what,
        "at": now(),
    })
    save(args, state)
    print(f"  {number} — {kind.upper():<12} {what}")
    return 0


def cmd_context(args) -> int:
    """Record what was loaded into context, and what was deliberately left out.

    Both halves matter and they fail in opposite directions. A record of loads
    only is a shopping list that grows without ever saying what was dropped, so
    the next agent cannot tell an intentional omission from an oversight. A
    record of drops only cannot reconstruct the working set. `references/context-system.md`
    gives a two-line reason why the omission is the more dangerous of the two:
    dropping too much is recoverable by loading more, and loading too much is
    not recoverable at all, because the context is already gone.
    """
    state = load(args)
    ctx = state.setdefault("context", {"loaded": [], "dropped": []})
    ctx.setdefault("loaded", [])
    ctx.setdefault("dropped", [])
    ctx.setdefault("gaps", [])

    # §16: the acquisition loop is gap -> request -> update -> continue. A run that
    # knows it is missing something and does not say what is missing is stuck, and
    # the stuckness is invisible because a run reporting a blocker looks exactly
    # like a run that never noticed. So a gap is recorded and stays open until
    # something closes it.
    if args.gap:
        gap = (args.gap or "").strip()
        if not gap:
            print("context: --gap is empty, so it records that something is "
                  "missing without saying what", file=sys.stderr)
            return 2
        gaps = ctx["gaps"]
        if any(isinstance(g, dict) and (g.get("what") or "").strip().lower() == gap.lower()
               for g in gaps):
            print(f"context: {gap!r} is already recorded as an open gap. A second "
                  f"declaration of the same gap is refused: close it, or say what "
                  f"is different about this one.", file=sys.stderr)
            return 2
        gaps.append({"what": gap, "opened_at": now(), "closed_at": None})
        save(args, state)
        print(f"  context gap {len(gaps)} open: {gap}")
        print("  a gap left open at R2 or above refuses `check`: context that can be "
              "acquired is route 2 of the gate before you stop, not a terminal state")
        return 0

    if args.closed:
        what = (args.closed or "").strip()
        gap = next((g for g in ctx["gaps"] if isinstance(g, dict)
                    and (g.get("what") or "").strip().lower() == what.lower()
                    and not g.get("closed_at")), None)
        if gap is None:
            print(f"context: no open gap {what!r}. Record it with `context --gap` "
                  f"first, or close the right one.", file=sys.stderr)
            return 2
        gap["closed_at"] = now()
        gap["closed_by"] = (args.why or "").strip() or None
        save(args, state)
        print(f"  context gap closed: {what}")
        return 0

    if args.drop:
        ref = (args.ref or "").strip()
        if not ref:
            die("--ref is required.")
        if not (args.why or "").strip():
            die("--why is required for a drop. A context entry removed without a "
                "reason reads as an oversight on the next pass, and gets re-loaded.")
        ctx["dropped"].append({"ref": ref, "why": args.why,
                               "level": args.level or None, "at": now()})
        save(args, state)
        print(f"  dropped {ref}  ({args.why})")
        return 0

    ref = (args.ref or "").strip()
    if not ref:
        die("--ref is required: the file, command, or observation the context came from.")
    entry = {"ref": ref, "level": args.level or None, "why": args.why or "",
             # §15's other two. Not required at write time -- R0 and R1 do not owe
             # the ceremony -- but `check` asks for them at R2+, which is where the
             # rule is load-bearing and where nobody was recording them.
             "enables": (args.enables or "").strip() or None,
             "scope": (args.scope or "").strip() or None,
             "fresh": bool(args.fresh), "at": now()}
    ctx["loaded"].append(entry)
    save(args, state)
    print(f"  loaded {ref}" + (f"  [{args.level}]" if args.level else ""))
    return 0


def _is_inside(path: str, root: str) -> bool:
    """True when `path` sits under `root`, after normalisation.

    Both sides are compared as resolved absolute paths so that `.memory/x`,
    `./.memory/x` and an absolute path to the same file all agree. A string
    prefix test would not: `.memory-backup/x` starts with `.memory` and is a
    different directory that a deliverable may legitimately live in.
    """
    try:
        p = os.path.realpath(os.path.abspath(path))
        r = os.path.realpath(os.path.abspath(root))
    except OSError:
        return False
    if p == r:
        return True
    return p.startswith(r.rstrip(os.sep) + os.sep)


def cmd_deliver(args) -> int:
    """Record a file the run produced, and refuse the ones that belong elsewhere.

    The distinction this enforces: the agent's own working memory is private,
    disposable, and gitignored; a deliverable the user asked for is none of
    those things. Filing an audit or a research document into `.memory/` makes
    it invisible to the person who asked for it, uncommittable, and silently
    lost when the directory is cleared -- and because `.memory/` is ignored,
    nothing in the repository ever notices the file existed.

    So the memory directory is refused here rather than warned about. A warning
    is advice, and advice is what the convention already was.
    """
    state = load(args)
    out = (args.path or "").strip()
    if not out:
        die("--path is required: the file this run produced.")
    if (_is_inside(out, DEFAULT_DIR) or _is_inside(out, LEGACY_DIR)
            or _is_inside(out, ".memory") or _is_inside(out, ".ultimate-dev")):
        die(
            f"refusing to record {out}: it is inside the agent's working memory, "
            f"not a deliverable. That directory is gitignored and disposable, so a "
            f"file filed there is invisible to whoever asked for it, uncommittable, "
            f"and lost when the directory is cleared. If the user asked for an audit "
            f"or research output, write it to the path they named."
        )

    state.setdefault("deliverables", {"asked_location": "", "produced": []})
    state["deliverables"].setdefault("produced", [])
    state["deliverables"]["produced"].append({
        "path": out, "what": args.what or "", "at": now()})
    save(args, state)
    print(f"  deliverable recorded: {out}")
    return 0


def cmd_require(args) -> int:
    """Register an acceptance criterion the run must satisfy before it ends.

    The step log records what the agent is *doing*. This records what must be
    *true* when it is finished, and it persists, so the list survives the context
    that wrote it.

    The distinction is the whole point. "Add retry logic" is a step; "the retry
    header is 3 attempts and the error is logged once" is a criterion, and only
    the second tells you when to stop. A run keeps steps and never writes
    criteria is a run that stops when the work *looks* finished -- which is the
    failure mode where a precise account of the unfinished work gets delivered in
    place of the work.
    """
    state = load(args)
    items = state.setdefault("criteria", [])
    what = (args.what or "").strip()
    if not what:
        print("require: --what is the criterion, stated so it can be observed",
              file=sys.stderr)
        return 2
    if any(i.get("what") == what for i in items if isinstance(i, dict)):
        print(f"require: already recorded: {what}", file=sys.stderr)
        return 2
    items.append({
        "n": len(items) + 1,
        "what": what,
        "status": "open",
        "evidence": None,
        "met_at": None,
    })
    save(args, state)
    print(f"  criterion {len(items)} open: {what}")
    return 0


def cmd_satisfy(args) -> int:
    """Mark a criterion met, with the observation that proves it.

    Evidence is mandatory and must resolve to a recorded observation, exactly as
    decision evidence does. A criterion satisfied by a restatement of the
    criterion is not satisfied; that is the whole content of "report honestly".
    """
    state = load(args)
    items = state.get("criteria") or []
    what = (args.what or "").strip()
    match = [i for i in items if isinstance(i, dict) and i.get("what") == what]
    if not match:
        print(f"satisfy: no criterion {what!r}. Record it with `require` first.",
              file=sys.stderr)
        return 2
    item = match[0]
    raw = (args.evidence or "").strip()
    obs_ids = {o.get("id") for o in state.get("observations", [])}
    if not raw:
        print("satisfy: --evidence is required; write OBS-n, or `none`", file=sys.stderr)
        return 2
    if raw.lower() != "none" and raw.upper() not in obs_ids:
        print(f"satisfy: evidence {raw!r} does not resolve to a recorded "
              f"observation", file=sys.stderr)
        return 2
    item["status"] = "met"
    item["evidence"] = raw
    item["met_at"] = now()
    save(args, state)
    print(f"  criterion {item['n']} met: {what}  [{raw}]")
    return 0


def cmd_blocked(args) -> int:
    """Declare part of the objective blocked, and pay for the declaration.

    Two rules, both structural, because the failure this exists to prevent is an
    agent quietly substituting a description of the work for the work:

    1. The routes must be named. `--tried` takes what was actually attempted; an
       empty list is refused, so "I could not find a way" cannot be written
       without a way having been looked for.
    2. The same reason cannot be blocked twice. A second `blocked` for an
       identical reason is refused unless a *different* next action is recorded,
       which turns the self-reference guard into a requirement for progress
       rather than an exhortation not to give up.

    Rule 2 is the analogue of the harness-level `stop_hook_active` guard: a run
    that has already written "this is blocked" cannot end on the same words, so
    the second attempt has to carry something new.
    """
    state = load(args)
    blocks = state.setdefault("blocks", [])
    what = (args.what or "").strip()
    reason = (args.reason or "").strip()
    if not what or not reason:
        print("blocked: --what and --reason are both required", file=sys.stderr)
        return 2
    tried = [t.strip() for t in (args.tried or []) if t and t.strip()]
    if not tried:
        print("blocked: --tried is required, and must be non-empty. A capability "
              "you did not find is a hypothesis; list the routes walked before "
              "calling it absent. See references/retry-policy.md.", file=sys.stderr)
        return 2
    # §30: the routes walked are named from a closed list, in a field of their own.
    #
    # The first version drew `--tried` itself from the vocabulary, and that was
    # wrong: `--tried` is the evidence of what was done ("searched the catalogue
    # for a local runner"), and reducing it to `other-resource` throws away the
    # only part a reader can check. So the prose stays prose and the route names
    # move beside it. Both are required, and neither substitutes for the other --
    # a block with a route and no detail asserts a category, and a block with
    # detail and no route asserts that nothing systematic was tried.
    routes = [r.strip().lower() for r in (args.routes or []) if r and r.strip()]
    unknown = [r for r in routes if r not in ROUTES]
    if unknown:
        print(f"blocked: {unknown[0]!r} is not one of the fifteen routes "
              f"({', '.join(ROUTES)}). --routes names which of §30's routes were "
              f"walked; --tried is the prose evidence for each.", file=sys.stderr)
        return 2
    if not routes:
        print("blocked: --routes is required, and must name at least one of §30's "
              "fifteen routes. --tried records what you did; --routes records that "
              "you walked the list rather than stopping at the first thing. A "
              "blocker is valid only when all five conditions hold, and 'no "
              "alternative capability' is a claim about the list.", file=sys.stderr)
        return 2
    for t in tried:
        if t.lower() == reason.lower():
            print("blocked: a route listed in --tried is the same as --reason. "
                  "The reason you are blocked on cannot also be a route you tried.",
                  file=sys.stderr)
            return 2

    prior = [b for b in blocks
             if isinstance(b, dict) and (b.get("what") or "").strip() == what]
    if prior:
        last = prior[-1]
        if (last.get("reason") or "").strip().lower() == reason.lower():
            if not (args.next_action or "").strip():
                print(f"blocked: {what!r} is already blocked for this exact reason. "
                      f"A second declaration of the same block is refused: either "
                      f"execute --next-action and report what happened, or record a "
                      f"different --reason. Declaring the same block twice is how a "
                      f"run reports a limit instead of reaching it.", file=sys.stderr)
                return 2
            last["next_action"] = args.next_action.strip()
            last["continued_at"] = now()
            save(args, state)
            print(f"  block on {what!r} continued; next action recorded: "
                  f"{last['next_action']}")
            return 0

    blocks.append({
        "n": len(blocks) + 1,
        "what": what,
        "reason": reason,
        "tried": tried,
        "routes": routes,
        "next_action": (args.next_action or "").strip() or None,
        "declared_at": now(),
    })
    save(args, state)
    print(f"  block {len(blocks)} recorded on {what!r}; "
          f"{len(tried)} thing(s) tried across {len(routes)} route(s)")
    return 0


def cmd_finish(args) -> int:
    """Record the run's terminal status, and refuse the one that is not earned.

    Section 55 allows exactly two ways to stop: verified complete, or a genuine
    blocker verified after the alternative paths. It names nine phrasings that
    are not a third option. Those nine are `audit`'s job, because they live in
    the delivery. This command is the other half: it stops the *state* from
    recording an ending it has not earned, so the delivery and the record cannot
    disagree without one of them having been written first.

    `completed` is gated on all four conditions of section 35 at once. Each is
    checkable, so each is checked:

      * every required work unit complete      -- no step left open
      * success criteria satisfied            -- at least one, all met
      * required verification passed           -- the same criteria, with evidence
      * no required action remains             -- no capability in flight

    The other three statuses each carry the field the specification says they
    carry. `partial` is only for work that genuinely happened with required work
    remaining, so it is refused on a run that never started; `blocked` is
    refused without a block whose routes were actually walked; and `failed` is
    kept separate from `blocked` because they mean opposite things -- attempted
    and lost, versus prevented -- and a run that conflates them has not decided
    which happened.
    """
    state = load(args)
    rung_code = str(state.get("rung") or "").split(" ", 1)[0].upper()

    status = (args.status or "").strip().lower()
    if status not in COMPLETION_STATUSES:
        print(f"finish: --status {status!r} is not one of "
              f"{', '.join(COMPLETION_STATUSES)}", file=sys.stderr)
        return 2

    prior = state.get("completion") or {}
    if prior.get("status") and not args.replace:
        print(f"finish: this run already finished as {prior['status']!r}. A run "
              f"does not get a second ending, and a changed verdict needs the "
              f"reason recorded: --replace --why \"...\"", file=sys.stderr)
        return 2
    if args.replace and not (args.why or "").strip():
        print("finish: --replace requires --why. Changing a recorded ending is a "
              "decision, and a decision without a reason is a retraction.",
              file=sys.stderr)
        return 2

    criteria = state.get("criteria") or []
    met = [i for i in criteria if isinstance(i, dict) and i.get("status") == "met"]
    open_c = _open_criteria(state)
    open_step = _open_step(state)
    in_flight = _in_flight(state)

    if status == "completed":
        blockers: list[str] = []
        if open_step is not None:
            blockers.append(
                f"work unit {open_step.get('n')} ({open_step.get('doing')!r}) is "
                f"still open. An unclosed unit has an unknown outcome, and an "
                f"unknown outcome is not a completed one.")
        if not criteria:
            blockers.append(
                "no acceptance criterion was ever recorded. 'Add retries' is a "
                "requirement; 'the client sees three attempts and one logged "
                "error' is the criterion that says when to stop. Without one, "
                "completion is a feeling.")
        elif open_c:
            blockers.append(
                f"{len(open_c)} acceptance criterion/criteria still open: "
                + "; ".join(str(i.get('what')) for i in open_c[:3]))
        if in_flight:
            blockers.append(
                f"capability/capabilities still in flight: {', '.join(in_flight)}. "
                f"A capability chosen and never observed is a delegation "
                f"described rather than performed.")
        if rung_code in {"R2", "R3", "R4"}:
            missing_vk = [s for s in state.get("steps", [])
                          if isinstance(s, dict)
                          and s.get("outcome") not in (None, "superseded")
                          and not (s.get("verification_kind") or "").strip()]
            if missing_vk:
                blockers.append(
                    f"{len(missing_vk)} closed work unit(s) have no verification_kind recorded: "
                    + ", ".join(
                        f"step {s.get('n')} ({s.get('doing')!r})"
                        for s in missing_vk[:3]
                    )
                    + ". At R2+, each closed unit needs a named check kind "
                      "(evidence-check | validation-check | independent-check). "
                      "Set it with `step --doing ... --verification-kind evidence-check`.")
        if rung_code in {"R2", "R3", "R4"}:
            log_entries = state.get("log") or []
            if not log_entries:
                blockers.append(
                    "No process log entries recorded. At R2+, log at least one "
                    "entry per work unit with `log --kind execute-inline --what ...`.")
        if blockers:
            print("finish: refusing `completed`.", file=sys.stderr)
            for b in blockers:
                print(f"  - {b}", file=sys.stderr)
            print("\n  Section 35 needs all four conditions, and they fail "
                  "independently. If the work really did stop short, that is "
                  "what `partial` is for -- it is not a lesser claim, it is an "
                  "accurate one.", file=sys.stderr)
            return 1

    elif status == "partial":
        if not (state.get("steps") or []):
            print("finish: `partial` is for work that genuinely happened with "
                  "required work remaining. No work unit was ever opened, so "
                  "nothing happened -- that is `failed`, or a run that should "
                  "have started.", file=sys.stderr)
            return 2
        if not (args.remaining or "").strip():
            print("finish: `partial` requires --remaining. A partial report "
                  "without the remainder is a complete one with a caveat, which "
                  "is how an unfinished run gets described as finished.",
                  file=sys.stderr)
            return 2

    elif status == "blocked":
        blocks = state.get("blocks") or []
        solid = [b for b in blocks
                 if isinstance(b, dict) and (b.get("tried") or [])]
        if not solid:
            print("finish: `blocked` requires a `blocked` record with routes "
                  "actually walked. A blocker is valid only when there is no "
                  "reachable capability, no alternative, no context path, no "
                  "recovery and no replan -- all five, and all five are records "
                  "rather than conclusions.", file=sys.stderr)
            return 2

    elif status == "failed":
        if not (args.attempted or "").strip():
            print("finish: `failed` requires --attempted. `failed` means execution "
                  "was attempted and unsuccessful, which is a different claim from "
                  "`blocked` (a dependency prevented it). Recording which one is "
                  "the point.", file=sys.stderr)
            return 2
        if not (state.get("steps") or []):
            print("finish: `failed` means execution was attempted. No work unit "
                  "was ever opened, so nothing was attempted.", file=sys.stderr)
            return 2

    state["completion"] = {
        "status": status,
        "remaining": (args.remaining or "").strip() or None,
        "attempted": (args.attempted or "").strip() or None,
        "recovery": (args.recovery or "").strip() or None,
        "next_action": (args.next_action or "").strip() or None,
        "criteria_met": len(met),
        "criteria_open": len(open_c),
        "replaced_from": prior.get("status"),
        "why": (args.why or "").strip() or None,
        "finished_at": now(),
    }
    save(args, state)

    print(f"  run finished: {status.upper()}  "
          f"({len(met)} criterion/criteria met"
          + (f", {len(open_c)} open" if open_c else "") + ")")
    if status == "completed":
        print("  condition A of section 55 holds: verified complete.")
    else:
        print("  condition B of section 55 holds: not complete, and the state "
              "records why. `audit` checks the delivery says the same thing.")
    return 0


def cmd_audit(args) -> int:
    """Check a delivery for the phrasings a run is not allowed to end on.

    This is the one gate that reads the thing the user actually receives, rather
    than the state that produced it. Every other gate in this file is satisfied
    by writing something into the state file; a run can satisfy all of them and
    still deliver a report that describes work it did not do, because the
    description and the state are written by the same judgement and share its
    blind spot. The text is the only place the failure is visible to the person
    the work was for.

    The specification supplies the list -- section 2 names seven terminations,
    section 55 names nine, section 32 names five non-actions that cannot become a
    block -- and a list can be checked, which is the whole reason this exists
    rather than another paragraph in SKILL.md saying the same thing.
    """
    if args.path == "-":
        text = sys.stdin.read()
        origin = "(stdin)"
    else:
        try:
            text = pathlib.Path(args.path).read_text(encoding="utf-8")
        except OSError as e:
            print(f"audit: cannot read {args.path}: {e}", file=sys.stderr)
            return 2
        origin = args.path

    lines = [ln for ln in text.splitlines() if ln.strip()]
    problems: list[str] = []

    # Class A -- a false conclusion about the world.
    for rx, why in BLOCK_CONCLUSIONS:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            snippet = " ".join(m.group(0).split())[:96]
            problems.append(
                f"line {line}: {snippet!r} -- {why}")

    # Class B -- a terminal justification. Only where a result should be.
    for idx, ln in enumerate(lines[:3]):
        for rx in TERMINAL_CLAIMS:
            if rx.search(ln):
                problems.append(
                    f"line {idx + 1}: the delivery opens with {ln.strip()[:72]!r}, "
                    f"which is an intermediate state. Either the objective is met "
                    f"and `satisfy` says so with evidence, or the routes are walked "
                    f"and `blocked --tried` records them. Rewording is not the "
                    f"fix; the two conditions of section 55 are.")
                break

    # --- §47: the delivery format, for a delivery big enough to carry it ---
    #
    # Skipped for a short one, and "short" is decided by the caller passing
    # --trivially rather than by counting lines: whether a report needs five
    # headings is a judgement about the run, and a line count is a bad proxy for
    # it. The default is to ask, because the section a run does not write is the
    # one a reader most needs -- "Remaining" is where the unfinished work goes,
    # and a delivery that omits the heading also omits the admission.
    if not getattr(args, "trivially", False):
        headings = {ln.lstrip("# ").strip().rstrip(":").lower() for ln in lines}
        missing_sections = [s for s in DELIVERY_SECTIONS
                            if s.lower() not in headings]
        if missing_sections:
            problems.append(
                f"the delivery has no {'/'.join(missing_sections)} section. §47 asks "
                f"for {', '.join(DELIVERY_SECTIONS)}; the ones most often missing are "
                f"the ones a reader most needs -- 'Remaining' is where unfinished work "
                f"goes, and a report without the heading does without the admission. "
                f"Pass --trivially for a delivery too short to carry them.")

    for pr in problems:
        print(f"  problem: {pr}")
    if problems:
        print(f"\n  {len(problems)} problem(s) in {origin}. A precise account of "
              f"the work you did not do is the failure this is here to catch.")
        return 1
    print(f"  delivery is clean: no terminal justification, no invented block, and "
          f"the §47 sections are present in {origin}")
    return 0


# §11 / §42: what a delegate is handed, and §12 / §34: what it hands back. The
# specification names seven fields going out and nine coming back, which makes them
# a list rather than an instruction, and a list can be required.
#
# Required at the two points where the claim changes. `--brief` at `invoked`:
# before that point nothing has been spent, so recording the handover costs
# nothing and skipping it is free. `--result` at `observed`: a capability that
# reached `observed` with nothing to show for it is indistinguishable from one
# that was never invoked, which is the whole failure `dispatch` exists to catch.
#
# The fields are the *names*, not the content. Whether a brief is any good is a
# judgement no gate can make, and a gate that tried would be enforcing
# verbosity.
BRIEF_FIELDS = ("objective", "input", "constraints", "expected output",
                "success criteria", "verification", "available context")
RESULT_FIELDS = ("status", "result", "actions", "evidence", "verification",
                 "assumptions", "remaining work", "errors")
RESULT_STATUSES = ("completed", "partial", "failed")


# §45's fifteen self-evaluation questions, as a closed list. The specification
# asks them "before delivery", which is a position in a procedure, and a position
# is not a record. Naming them here makes the set checkable: `reflect` refuses a
# partial one, and `check` refuses a run at R2+ that finished without one.
#
# The list is the whole of the requirement. Whether an answer is any good is not
# checkable and is not checked -- an answer of "no" to several of these is the
# expected output, and a gate that rewarded confident answers would be rewarding
# the one thing §45 says is worth nothing.
SELF_EVAL_QUESTIONS = (
    "did we solve the task",
    "did we execute the required work",
    "did we use the correct capabilities",
    "did we invoke selected agents",
    "did we acquire context only when needed",
    "was context sufficient",
    "was verification sufficient",
    "did we recover from failures",
    "did we unnecessarily load context",
    "did we unnecessarily delegate",
    "did we under-delegate",
    "did coordination fit the task",
    "are any required work units incomplete",
    "is the blocker genuine",
    "can anything else still be executed",
)

# §47's delivery sections. Required for a non-trivial delivery, which `audit`
# cannot tell apart from a trivial one -- so the same exemption the rung carries
# applies: a one-line answer is not asked to carry five headings.
DELIVERY_SECTIONS = ("Process", "Result", "Verification", "State", "Remaining")


def _match_question(asked: str) -> "str | None":
    """Resolve a typed question to one of §45's fifteen, or None.

    Exact match first, then a prefix, and the prefix must identify exactly one
    question. The first version compared an 18-character prefix in both
    directions with `or`, which is how "did we unnecessarily delegate" and "did we
    unnecessarily load context" collided -- they agree for 18 characters, so one of
    the two silently swallowed the other's answer and the run was told it had
    answered fourteen of fifteen when it had answered fourteen of fifteen *wrong*.

    A unique-prefix fallback keeps the ergonomics of not retyping the whole
    question while making the collision impossible: two questions sharing a
    prefix are not usable abbreviations, and the caller gets told which two.
    """
    q = (asked or "").strip().lower().rstrip("?").rstrip(".").strip()
    if not q:
        return None
    for k in SELF_EVAL_QUESTIONS:
        if k == q:
            return k
    hits = [k for k in SELF_EVAL_QUESTIONS if k.startswith(q) or q.startswith(k)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise ValueError(
            f"{asked!r} matches {len(hits)} of §45's questions "
            f"({'; '.join(hits[:3])}) -- they share a prefix, so it cannot "
            f"identify one. Type more of it, or the whole question.")
    return None


#: What counts as opening on a negation. Order matters: the list is consumed
#: first-match, and several of these are prefixes of one another -- `not` is a
#: prefix of `nothing`, `no` is a prefix of `none`, and `partly` is a prefix of
#: `partially`. Longest and most specific first, or `not sufficient: ...` gets
#: read as `no` followed by `t sufficient: ...` and the finding is mismeasured.
_NEGATION_OPENERS = (
    "did not", "does not", "was not", "were not", "is not", "are not",
    "could not", "would not", "cannot", "didn't", "doesn't", "wasn't",
    "not", "none", "n/a", "false", "no", "partially", "partly",
)


#: Openings that negate the *finding* rather than the verdict. "Nothing to
#: report" and "nobody did anything wrong" both start on a negation, and both are
#: the favourable review wearing a negative's clothes -- which is the exact shape
#: a self-review takes when it has found nothing and wants the gate to think it
#: was thorough.
_NON_FINDINGS = ("nothing", "nobody", "no issues", "no problems", "no faults",
                 "no findings", "nothing wrong", "nothing to report",
                 "nothing to add", "nothing else", "no complaints")

#: Concessions. A finding does not have to open the sentence -- it very often
#: does not, because most of what a run did was fine, and the honest shape of
#: "mostly yes, except for this" is a positive first word and a `but`.
#:
#: The floor read only the front, and that was the same defect it had just fixed
#: pointing the other way. Having concluded that a verdict is not a finding, it
#: then refused the single most common real finding there is. A gate that pushes a
#: run to write a false negative in order to satisfy it has replaced one bias
#: with another, and the substitution is harder to notice because the output
#: still looks like a self-review.
_CONCESSIONS = ("but", "however", "although", "though", "except", "except that",
                "despite", "even so", "that said", "on the other hand",
                "the problem", "the fault", "went wrong", "should not have",
                "should have", "over-", "under-")


def _names_a_finding(answer: str) -> bool:
    """Does this answer carry a finding -- a negative claim *and* something said?

    Three conditions, and each is load-bearing against a way this has been wrong.

    A verdict is not a finding. Requiring only a negation accepts fifteen bare
    "no"s, which is a review that found nothing and dressed it as fifteen
    findings.

    A finding is not necessarily at the front. Requiring the negation to open
    refuses "Yes, but the route list is in three files", which is the common
    shape of an honest self-review, because most of what a run did was fine.

    Something has to be said. Requiring only the marker accepts "Yes, but fine"
    fifteen times, which is the same fifteen bare verdicts wearing a conjunction.

    So: a finding is either a negation at the front or a concession somewhere in
    the answer, and in both cases at least eight words have to follow the marker.
    Eight sits above "no, it was not" and below "no, the route list is in three
    files and one of them does not contain it".
    """
    text = (answer or "").strip().lower()
    for phrase in _NON_FINDINGS:
        if text.startswith(phrase):
            return False
    # Openers are front-anchored, deliberately. Searching for them anywhere makes
    # "no, the count was self-reported and nothing tested it" match the "not"
    # inside "nothing", and then judge three words of remainder instead of the
    # finding sitting at the front. The first version used `find` for both lists
    # and refused its own best answer for exactly that reason.
    for opener in _NEGATION_OPENERS:
        if text.startswith(opener):
            return len(text[len(opener):].lstrip(" ,.;:-—").split()) >= 8
    for concession in _CONCESSIONS:
        m = re.search(rf"\b{re.escape(concession)}\b", text)
        if m:
            return len(text[m.end():].lstrip(" ,.;:-—").split()) >= 8
    return False


def cmd_reflect(args) -> int:
    """Record §45's self-evaluation before delivery, all fifteen or not at all.

    The kernel already had ten of these in prose in `references/self-evaluation.md`
    and none of them in the state, which is the same defect the process log had: a
    list in a document that nothing consults. The value of recording them is not
    the answers -- it is that "are any required work units incomplete" gets asked
    at all, and that the answer is next to the state it describes rather than
    somewhere in a transcript nobody re-reads.
    """
    state = load(args)

    if args.list:
        prior = state.get("self_evaluation") or {}
        if not prior:
            print("  no self-evaluation recorded")
            return 0
        print(f"  self-evaluation {prior.get('at')}")
        for q in SELF_EVAL_QUESTIONS:
            print(f"    {'y' if (q in prior) else 'n'}  {q}: {prior.get(q) or '-'}")
        return 0

    answers = (args.answer or [])
    recorded: dict[str, str] = {}
    for item in answers:
        if "=" not in item:
            print(f"reflect: {item!r} is not 'question=answer'. Every answer has to "
                  f"name the question it answers, or the list cannot be checked for "
                  f"completeness.", file=sys.stderr)
            return 2
        q, a = item.split("=", 1)
        try:
            canon = _match_question(q)
        except ValueError as e:
            print(f"reflect: {e}", file=sys.stderr)
            return 2
        if canon is None:
            print(f"reflect: {q!r} is not one of §45's fifteen questions. Use "
                  f"`reflect --list` for the vocabulary.", file=sys.stderr)
            return 2
        if canon in recorded:
            print(f"reflect: {canon!r} answered twice. §45 asks it once, and two "
                  f"answers to one question is a way of not answering it.",
                  file=sys.stderr)
            return 2
        recorded[canon] = a.strip()

    missing = [q for q in SELF_EVAL_QUESTIONS if q not in recorded]
    if missing:
        print(f"reflect: {len(missing)} of {len(SELF_EVAL_QUESTIONS)} questions are "
              f"unanswered, starting with {missing[0]!r}. §45 asks all fifteen "
              f"before delivery. An answer of 'no' to several of them is the "
              f"expected output; silence about them is the problem.", file=sys.stderr)
        return 2
    if not (args.why or "").strip():
        # Not a reason -- a floor on the *content*. A fifteen-word reflection that
        # answers every question with "yes" is the failure §45 describes as worth
        # nothing, and the only mechanical proxy for it is whether anything was
        # found wrong.
        #
        # The first version compared the whole answer against a closed list of
        # bare verdicts -- "no", "none", "n/a", "false" -- and that had it wrong
        # in both directions at once. It refused `No, and here is the fault: the
        # route list is in three files and SKILL.md points at a fourth`, which is
        # the finding the gate exists to produce, while accepting fifteen
        # consecutive answers of the single word "no", which is the failure it
        # exists to prevent: fifteen verdicts and not one finding.
        #
        # A criticism has to name something. So an answer counts when it opens on
        # a negation *and carries a finding after it* -- a bare verdict is a label
        # and labels are what a self-review produces when it has nothing.
        honest = [q for q, a in recorded.items() if _names_a_finding(a)]
        if not honest:
            print("reflect: fifteen answers and not one of them names a fault. "
                  "§45 says a favourable review of your own run is worth nothing "
                  "and that finding two or three faults is the expected output. A "
                  "bare 'no' is a verdict, not a finding, and a finding does not "
                  "have to open the sentence -- 'Yes, but the count of the gated "
                  "rows was self-reported' is one. Name the thing that was done "
                  "badly, or say which question you could not answer.",
                  file=sys.stderr)
            return 1
    state["self_evaluation"] = {**recorded, "at": now()}
    save(args, state)
    print(f"  self-evaluation recorded: {len(recorded)} answers")
    return 0


def cmd_dispatch(args) -> int:
    """Record where a chosen capability actually got to.

    The kernel already forbids *over*-delegating ("delegation is a cost, not a
    default") and had no rule at all pushing the other way, so a run could stop
    loading the capability it was built around and do the work with whatever was
    already in context -- and doing it inline always felt compliant. This is the
    mirror, and it is a record rather than a reminder for the reason the criterion
    gate is a record: a model asked whether it delegated well answers from the
    shape of its own prose, which is exactly what is in question.

    Three rules, all structural:

    1. `selected`, `invoked` and `running` are not terminal. `check` refuses a
       terminal report while any capability sits in one, so "I chose the specialist
       and then did it myself" cannot be reported as a finished run.
    2. `unreachable` needs `--tried`, and `skipped` needs `--why`. NOT_INVOKED and
       UNREACHABLE are different states: one is an action not taken, the other is
       a capability proved absent, and only the second is a finding.
    3. The chain does not run backwards. A state that un-observes itself is a
       rewrite of history, which is worse than the omission it papers over.
    """
    state = load(args)
    for_what = (args.what or "").strip()
    st = (args.state or "").strip().lower()
    if not for_what:
        print("dispatch: --for is required (it names the capability)", file=sys.stderr)
        return 2
    if st not in DISPATCH_STATES:
        print(f"dispatch: --state {st!r} is not one of "
              f"{', '.join(DISPATCH_STATES)}", file=sys.stderr)
        return 2

    tried = [t.strip() for t in (args.tried or []) if t and t.strip()]
    why = (args.why or "").strip()
    ev = (args.evidence or "").strip()

    if st == "unreachable" and not tried:
        print("dispatch: `unreachable` needs --tried, and it must be non-empty. "
              "A capability you did not look for is not a capability the host "
              "lacks; that is the under-claiming failure this state is supposed to "
              "make visible, not hide.", file=sys.stderr)
        return 2
    if st == "skipped" and not why:
        print("dispatch: `skipped` needs --why. A deliberate pass-over is a "
              "decision with a recorded reason; an unnamed one is indistinguishable "
              "from having forgotten the capability existed.", file=sys.stderr)
        return 2
    if st == "verified" and not ev:
        print("dispatch: `verified` needs --evidence OBS-n. A capability reported as "
              "checked, with nothing recording what was checked, is an assertion "
              "wearing the word for a finding.", file=sys.stderr)
        return 2

    records = state.setdefault("dispatch", [])
    prior = [d for d in records
             if isinstance(d, dict) and (d.get("for") or "") == for_what]
    last = prior[-1] if prior else None

    # §11 / §42: the handover. Required at `invoked`, which is the moment the
    # context is committed and before anything has been spent on the answer, so
    # recording it is free and skipping it only shows up later.
    brief = (args.brief or "").strip()
    if st == "invoked" and not brief:
        print("dispatch: `invoked` needs --brief, naming §11's seven fields "
              f"({', '.join(BRIEF_FIELDS)}) and §42's context package. Nothing has "
              f"been spent yet, so a missing brief is free to fix now and "
              f"unrecoverable later -- and a delegate handed three of the seven has "
              f"had its success criteria invented for it.", file=sys.stderr)
        return 2
    if brief:
        absent = [f for f in BRIEF_FIELDS if f.split()[0] not in brief.lower()]
        if absent:
            print(f"dispatch: --brief does not name {absent[0]!r}. §11 lists "
                  f"{len(BRIEF_FIELDS)} fields and a brief naming fewer is a "
                  f"paragraph about handing work over. All of them, in any order.",
                  file=sys.stderr)
            return 2

    # §12 / §34: the handback. Required at `observed` -- RESULT RECEIVED is not
    # RESULT VERIFIED, and a capability that reached `observed` carrying no status
    # and no evidence is exactly the "Done" this kernel refuses to take.
    rstatus = (args.result_status or "").strip().lower()
    result = (args.result or "").strip()
    if st in ("observed", "verified"):
        if rstatus not in RESULT_STATUSES:
            print(f"dispatch: `{st}` needs --result-status, one of "
                  f"{', '.join(RESULT_STATUSES)}. §12 asks the specialist to say "
                  f"which it is, and a run that never asks cannot tell a completed "
                  f"delegation from a partial one.", file=sys.stderr)
            return 2
        if not result:
            print(f"dispatch: `{st}` needs --result, and it needs --result-status "
                  f"beside it. §12 lists {len(RESULT_FIELDS)} fields "
                  f"({', '.join(RESULT_FIELDS)}). A capability that reached `{st}` "
                  f"with nothing to show for it is indistinguishable from one that "
                  f"was never invoked, which is the failure the whole chain exists "
                  f"to make visible.", file=sys.stderr)
            return 2
    if last is not None and (last.get("state") or "") in DISPATCH_ORDER \
            and st in DISPATCH_ORDER \
            and DISPATCH_ORDER.index(st) < DISPATCH_ORDER.index(last.get("state")):
        print(f"dispatch: {for_what!r} is {last.get('state')!r} and cannot go back to "
              f"{st!r}. If it turned out not to have run, that is a new finding and "
              f"it is recorded here rather than by quietly resetting the chain.",
              file=sys.stderr)
        return 2

    entry = last if last is not None else {
        "n": len(records) + 1, "for": for_what, "history": []}
    if last is None:
        records.append(entry)
    entry.setdefault("history", []).append(
        {"state": last.get("state") if last else None, "at": now()})
    entry["state"] = st
    entry["tried"] = tried or entry.get("tried") or []
    entry["why"] = why or entry.get("why") or ""
    entry["evidence"] = ev or entry.get("evidence") or ""
    entry["brief"] = brief or entry.get("brief") or ""
    entry["result_status"] = rstatus or entry.get("result_status") or ""
    entry["result"] = result or entry.get("result") or ""
    entry["at"] = now()
    if st in DISPATCH_TERMINAL:
        entry["terminal_reason"] = st
    save(args, state)
    print(f"  capability {for_what!r}: {st}"
          + (f" ({len(tried)} route(s) tried)" if st == "unreachable" else ""))
    return 0


def cmd_check(args) -> int:
    state = load(args)
    problems: list[str] = []

    # Normalised once, at the top, because a dozen gates below compare the rung
    # against something -- R2+ exemptions, the host ceiling, the de-escalation
    # floor. It used to be computed halfway down, which meant the gates added
    # above it raised UnboundLocalError. Reading a value once and comparing it
    # everywhere is also what stops two gates comparing a bare code against a
    # spelled-out one, which is a bug that only fires on the spelling.
    rung = state.get("rung")
    rung_code = str(rung or "").split(" ", 1)[0].upper()

    for key in REQUIRED:
        if key not in state:
            problems.append(f"missing field: {key}")

    mode = state.get("coordination") or {}
    if mode.get("mode") not in MODES:
        problems.append(
            f"coordination.mode is {mode.get('mode')!r}; must be one of "
            f"{', '.join(MODES)}")
    if not (mode.get("why") or "").strip():
        problems.append("coordination.why is empty; an unexplained mode is a default "
                        "that will not be reviewed")

    if mode.get("mode") == "handoff" and not state.get("active_agent"):
        problems.append("mode is handoff but active_agent is unset; the conversation "
                        "has no owner")
    if state.get("active_agent") and mode.get("mode") != "handoff":
        problems.append(f"active_agent is {state['active_agent']!r} but mode is "
                        f"{mode.get('mode')!r}; authority cannot sit outside a handoff")
    if state.get("authority") not in ("inline", "delegated"):
        problems.append(f"authority is {state.get('authority')!r}; "
                        f"must be inline or delegated")

    obs_ids = {o.get("id") for o in state.get("observations", [])}
    for d in state.get("decisions", []):
        # evidence may be a bare pointer or the list form the schema defines
        # (`evidence[].ref`). It was read with .strip() unconditionally, so a
        # correctly-formed list crashed check with AttributeError -- and a crash
        # exits non-zero, which reads as "the gate fired" rather than "the gate
        # is broken". The self-test found this by writing the schema's own
        # example shape.
        raw_ev = d.get("evidence")
        if isinstance(raw_ev, list):
            refs = [
                (e.get("ref") if isinstance(e, dict) else e) or ""
                for e in raw_ev
            ]
            refs = [str(r).strip() for r in refs if str(r).strip()]
        else:
            refs = [str(raw_ev or "").strip()]
        refs = [r for r in refs if r]

        if not refs:
            problems.append(
                f"decision {d.get('question')!r}: evidence is empty; write OBS-n, "
                f"or `none`")
        for ev in refs:
            if not EVIDENCE_POINTER.match(ev):
                problems.append(
                    f"decision {d.get('question')!r}: evidence {ev!r} is prose, not a "
                    f"pointer. Write OBS-n, or `none`.")
            elif ev.lower() != "none" and ev.upper() not in obs_ids:
                problems.append(
                    f"decision {d.get('question')!r}: evidence {ev} does not resolve to a "
                    f"recorded observation")
        if not (d.get("rejected") or "").strip():
            problems.append(
                f"decision {d.get('question')!r}: `rejected` is empty; a decision "
                f"without a recorded alternative is an assertion")
        if not (d.get("recovery") or "").strip():
            problems.append(
                f"decision {d.get('question')!r}: `recovery` is empty; nothing says "
                f"what would reverse this")
        # §5: JEv must produce an executable next action. A record whose `selected`
        # is empty, or is a single word, is a paragraph about deciding rather than
        # a decision -- and a paragraph cannot be executed or reviewed.
        if not _is_executable_action(d.get("selected") or ""):
            sel = (d.get("selected") or "").strip()
            problems.append(
                f"decision {d.get('question')!r}: `selected` is "
                f"{sel!r}, which is not an executable action"
                + ("; it is empty" if not sel else "; it names a category, not a "
                   "thing to do. 'delegate' is a mode; 'invoke the reviewer and "
                   "record what came back' is an action."))

    changes = mode.get("changed") or []
    if len(changes) >= 3:
        problems.append(
            f"coordination mode changed {len(changes)} times; that is a signal the "
            f"first choice was wrong, not that the task is hard")

    # --- §24: the process log and the state must agree ---
    #
    # `cmd_log` refuses a line that claims a dispatch the ledger has not reached,
    # so a hand-edited state file, or one written by an older version, is the only
    # way to get here. It is worth catching anyway, and for the same reason the
    # rest of this function exists: a state file is a claim until something reads
    # it and disagrees.
    reached = _dispatch_reached(state)
    met_criteria = [i for i in (state.get("criteria") or [])
                    if isinstance(i, dict) and i.get("status") == "met"]
    for e in state.get("log") or []:
        if not isinstance(e, dict):
            continue
        kind = str(e.get("kind") or "").lower()
        claim = LOG_KINDS.get(kind)
        if claim and claim != "verified" \
                and reached < DISPATCH_ORDER.index(claim):
            problems.append(
                f"process log {e.get('n')} says {kind!r}, but the capability ledger "
                f"only reached {DISPATCH_ORDER[reached] if reached >= 0 else 'nothing'}"
                f". The log and the state must agree; one of them is a claim.")
        if kind in ("verify", "verified") \
                and reached < DISPATCH_ORDER.index("verified") and not met_criteria:
            problems.append(
                f"process log {e.get('n')} claims verification, but nothing was "
                f"verified: no capability reached `verified` and no acceptance "
                f"criterion is met")

    comp = state.get("completion") or {}
    comp_status = str(comp.get("status") or "").strip().lower()
    if comp_status and comp_status not in COMPLETION_STATUSES:
        problems.append(
            f"completion.status is {comp_status!r}; must be one of "
            f"{', '.join(COMPLETION_STATUSES)}")

    # --- §18: the RunState field list, and how much of it this tool keeps ---
    #
    # Not every §18 field has a home here, and pretending otherwise would be the
    # same claim check-spec made before it was rewritten: coverage asserted rather
    # than counted. So only a field that IS mapped and IS missing fails -- which is
    # a defect rather than a known gap. The unmapped ones are enumerated as `None`
    # in RUNSTATE_FIELDS, and they are the list of what to build next.
    missing_mapped = [name for name, path in RUNSTATE_FIELDS
                      if path and not _has(state, path)]
    if missing_mapped:
        problems.append(
            f"state is missing {len(missing_mapped)} field(s) §18 requires and this "
            f"tool claims to keep: {', '.join(missing_mapped[:6])}"
            + (" ..." if len(missing_mapped) > 6 else ""))

    # --- §19: an event that happened must have left a trace ---
    #
    # Not "was the state updated" -- that is unobservable -- but its converse: an
    # event that demonstrably occurred must have been recorded. The orphan is a
    # dispatch that reached `invoked` with no result, a block with no named route,
    # a handoff that never came back and was never marked open.
    for d in (state.get("dispatch") or []):
        if not isinstance(d, dict):
            continue
        st = str(d.get("state") or "").lower()
        if st in ("invoked", "running", "observed", "verified") \
                and not d.get("history"):
            problems.append(
                f"capability {d.get('for')!r} is recorded at {st!r} with no history: "
                f"an invocation that left no trace is §19's orphan, and a run that "
                f"reached 'invoked' and recorded nothing is indistinguishable from "
                f"one that never invoked anything")
    for h in (state.get("handoffs") or []):
        if isinstance(h, dict) and h.get("returned_at") is None and not h.get("open"):
            problems.append(
                f"handoff to {h.get('to')!r} never came back and is not marked open; "
                f"authority is sitting with nobody")

    for r in (state.get("recoveries") or []):
        if not isinstance(r, dict):
            continue
        if not r.get("result"):
            problems.append(
                f"recovery {r.get('n')} records no result; a recovery with no "
                f"outcome has not been evaluated, which is §28's blind retry "
                f"arriving late")
        if str(r.get("class") or "") not in FAILURE_CLASSES:
            problems.append(
                f"recovery {r.get('n')} has class {r.get('class')!r}, which is not "
                f"one of {', '.join(FAILURE_CLASSES)}. A recovery that does not say "
                f"which kind of failure it recovered from cannot be evaluated.")
    for b in (state.get("blocks") or []):
        if isinstance(b, dict) and not (b.get("routes") or []):
            problems.append(
                f"block {b.get('n')} on {b.get('what')!r} names no route from §30's "
                f"fifteen ({ORPHAN_REASONS.get('blocks.routes')}). --tried records "
                f"what was looked for; a block with detail and no route asserts "
                f"that nothing systematic was tried.")

    # --- §16: an open context gap is a run that knows it is stuck and stopped ---
    # --- §15: and a context request names four things, not three ---
    if rung_code in {"R2", "R3", "R4"}:
        open_gaps = [g for g in ((state.get("context") or {}).get("gaps") or [])
                     if isinstance(g, dict) and not g.get("closed_at")]
        if open_gaps:
            problems.append(
                f"{len(open_gaps)} context gap(s) still open: "
                + "; ".join(str(g.get('what')) for g in open_gaps[:3])
                + ". Context that can be acquired is route 2 of the gate before you "
                  "stop, so an open gap and a stopped run are the same claim from "
                  "two directions. Close it with `context --closed`.")
        for c in (state.get("context") or {}).get("loaded") or []:
            if not isinstance(c, dict):
                continue
            if not (c.get("enables") or "").strip() \
                    or not (c.get("scope") or "").strip():
                problems.append(
                    f"context {c.get('ref')!r} does not say which action it enables "
                    f"or what its minimum scope was. §15 asks for four things before "
                    f"a context request, and only two of them were being recorded.")

    # --- §38: do not over-delegate, checked rather than asserted ---
    #
    # The over-delegation rule is one paragraph, and a paragraph is worth exactly
    # what a model remembers it is worth. The checkable form is narrow: a run that
    # bought a capability, watched it return, and then did every work unit inline
    # anyway paid for isolation and got nothing. That is over-delegation, and it is
    # visible in the ledger without any judgement about whether the delegation was
    # worth it in principle.
    used = [d for d in (state.get("dispatch") or [])
            if isinstance(d, dict)
            and str(d.get("state") or "") in ("observed", "verified")]
    steps_list = state.get("steps") or []
    all_inline = bool(steps_list) and all(
        str(s.get("capability") or "inline").strip().lower() in ("", "inline")
        for s in steps_list if isinstance(s, dict))
    if used and all_inline:
        problems.append(
            f"{len(used)} capabilit{'y was' if len(used) == 1 else 'ies were'} "
            f"dispatched and observed ({', '.join(str(d.get('for')) for d in used)}), "
            f"and every work unit names inline. That is §38: the run paid for "
            f"isolation and got the work done in this context anyway. Either the "
            f"work unit should name the capability, or the dispatch should be "
            f"marked `skipped --why`.")

    # --- §40: several results require a comparison, not a concatenation ---
    #
    # Two or more specialists each returning a result is not a synthesis. The
    # kernel owns the merge, and the merge is where conflicts get resolved; a run
    # that appends two outputs has skipped the only part that was the kernel's.
    # A decision record is where a comparison would be kept, and requiring one is
    # cheaper than requiring a synthesis document nobody would read.
    if len(used) >= 2:
        if not state.get("decisions"):
            problems.append(
                f"{len(used)} capabilities were observed and no decision record "
                f"exists. §40: the kernel compares, resolves conflicts, and "
                f"synthesises -- a run that concatenates specialist outputs has "
                f"skipped the only part that was its own. Record the comparison "
                f"with `decide`.")

    # --- §45: a run that finished at R2+ without asking itself anything ---
    #
    # The fifteen questions are in a reference file and, until `reflect` existed,
    # nowhere else. Ten of them are also in Step 9 of SKILL.md, which means the
    # kernel asked twice in prose and recorded nothing either time. The gate here
    # is only on the *recording*, not the quality: a fifteen-answer reflection that
    # criticises nothing is refused at write time, and a run that never recorded
    # one at all is refused here.
    if comp_status and rung_code in {"R2", "R3", "R4"} \
            and not (state.get("self_evaluation") or {}).get("at"):
        problems.append(
            f"the run is recorded {comp_status} at rung {rung_code} with no §45 "
            f"self-evaluation. `reflect --list` prints the fifteen questions. The "
            f"one that matters most here is 'are any required work units "
            f"incomplete', and it is the one a run about to declare itself finished "
            f"has least reason to ask.")

    # §25 again, from the other side: a run with real work units that reached a
    # terminal status having logged no execution at all. Short runs are exempt --
    # that is why the `log` gate lets `deliver` follow anything -- because a run
    # that did not need a log should not acquire one by being caught out.
    if comp_status and rung_code in {"R2", "R3", "R4"} \
            and (state.get("steps") or []):
        did_work = {"execute", "executed", "execute-inline", "observe",
                    "observed", "result", "verify", "verified"}
        logged = {str(e.get("kind") or "").lower() for e in (state.get("log") or [])
                  if isinstance(e, dict)}
        if not (logged & did_work):
            problems.append(
                f"the run has {len(state.get('steps') or [])} work unit(s) and is "
                f"recorded {comp_status}, but the log records no execution of any "
                f"kind. §23's log is of operations, and a run that opens work units "
                f"and delivers without ever logging having done anything has "
                f"described a run rather than recorded one.")

    if comp_status == "completed":
        # `finish` refuses this combination at write time. Re-checked here
        # because a state file can also be edited, and because the criteria can
        # be re-opened by a later `require` after the run claimed completion --
        # which is a real way to produce a contradiction, not a hypothetical.
        if _open_criteria(state):
            problems.append(
                f"run is recorded completed while "
                f"{len(_open_criteria(state))} acceptance criterion/criteria are "
                f"open. Section 35 requires the criteria satisfied and no required "
                f"action remaining, and those cannot both be true.")
        if _open_step(state) is not None:
            problems.append(
                f"run is recorded completed while work unit "
                f"{_open_step(state).get('n')} is still open")

    if state.get("log") and not str(state["log"][0].get("n") or "").startswith("P01"):
        problems.append(
            f"process log starts at {state['log'][0].get('n')!r}, not P01. Numbering "
            f"that does not start at one cannot be read to find what was already "
            f"tried, which is the only reason it is numbered")

    # --- the three things the documentation says `check` refuses, and did not ---
    #
    # SKILL.md: "run-state.py set-mode keeps the reason and the reversing
    # condition, and check refuses a state where the mode has neither." `until`
    # was written and never read. A reversing condition you are not asked for is
    # not a reversing condition.
    if not (mode.get("until") or "").strip():
        problems.append(
            f"coordination mode {mode.get('mode')!r} has no reversing condition "
            f"(`until`); set-mode --until records one and check now requires it")

    # `check` never read the rung, so the field the effort gate exists to
    # produce was neither validated nor mentioned. A rung outside the vocabulary
    # is now rejected at write time by choices=; this catches a state file
    # written by an older version, or edited by hand.
    if rung is not None and rung_code not in RUNGS:
        problems.append(
            f"rung {rung!r} is not one of {', '.join(RUNGS)}; the effort gate "
            f"produces a rung, so an unrecognised one means the gate was skipped")

    scale = state.get("scale")
    if scale is not None and str(scale).strip().upper() not in SCALES:
        problems.append(
            f"scale {scale!r} is not one of {', '.join(SCALES)}")

    # --- the host is a term in the effort gate, and the gate is asymmetric ---
    #
    # The rung ladder answers how hard the task is. It said nothing about what the
    # model can carry, so one 549-line procedure was applied unchanged to a 1B model
    # and a frontier one. This repository's own research says that is measurably
    # wrong at both ends: over-prescription degrades current-generation output, and
    # a weak host does not reliably *trigger* the rules it is given.
    host = state.get("host")
    if host is not None and str(host) not in HOSTS:
        problems.append(
            f"host {host!r} is not one of {', '.join(HOSTS)}; the host is a term in "
            f"the effort gate, so an unrecognised one means the gate was skipped")
    # P1: host tier not set — default to "mid" for ceiling purposes and warn.
    # A run that never set --host silently bypassed the ceiling gate; this
    # makes the bypass visible. Warning only, not a hard error: the model may
    # have inferred the tier correctly; we just cannot tell.
    _host_assumed = False
    if host is None or str(host) not in HOSTS:
        _host_assumed = True
        host = "mid"
        print(
            "  warning: host tier not set; defaulting to 'mid' for ceiling "
            "check. Set with:\n"
            "    run-state.py set-host --host small|mid|frontier --why '...'",
            file=sys.stderr,
        )
    ceiling = HOST_CEILING.get(str(host or ""))
    if ceiling and rung_code in RUNGS and rung_code > ceiling:
        # Deliberately exceeding the ceiling is legitimate -- one focused hard
        # call is exactly what a small model is good at, and the ceiling is a
        # default rather than a law. It has to be said at the moment the effort
        # gate is made, because afterwards the run has a result and will find a
        # reason for it, which is the wrong order.
        if not (state.get("exceeds_ceiling") or "").strip():
            problems.append(
                f"rung {rung_code} is above what a {host!r} host can carry "
                f"(ceiling {ceiling}), with nothing recorded saying why. A weak host "
                f"given more procedure produces more shallow decisions, which reads "
                f"as thorough and is not. Exceeding it deliberately is allowed -- "
                f"init --exceeds-ceiling \"<why>\".")

    # The direction the evidence says fails silently. Capability and budget sense
    # are different things (measured at r=0.35), so a capable model cannot be
    # trusted to notice it is under-investing. On a weak host, de-escalating is
    # free and often correct. On a frontier host it is the documented failure.
    if host == "frontier":
        for change in state.get("rung_changed") or []:
            if not isinstance(change, dict):
                continue
            frm = str(change.get("from") or "").split(" ", 1)[0].upper()
            to = str(change.get("to") or "").split(" ", 1)[0].upper()
            if frm in RUNGS and to in RUNGS and frm > to and frm >= "R3" \
                    and not (change.get("why") or "").strip():
                problems.append(
                    f"rung dropped {frm} -> {to} on a frontier host with no reason "
                    f"recorded. The risk here is under-investment, and a capable "
                    f"model is the one least able to notice it: capability and "
                    f"budget sense are barely correlated. `set-rung --why`.")
        # P7: frontier host at R3/R4 with no triage answers recorded.
        # The over-orchestration path is symmetric to the ceiling gate but runs in
        # the other direction: a frontier host claiming a high rung without having
        # performed triage may be inflating the ceremony. Advisory only.
        if rung_code in {"R3", "R4"}:
            has_reflect = bool((state.get("self_evaluation") or {}).get("at"))
            has_triggers = bool(
                (state.get("rung_triggers") or {}).get("escalate_on", "").strip()
                or (state.get("rung_triggers") or {}).get("de_escalate_on", "").strip()
            )
            if not has_reflect or not has_triggers:
                print(
                    f"  warning: frontier host at {rung_code} but no triage answers "
                    f"recorded. Run 'reflect' to confirm the rung is justified "
                    f"(references/triage.md)",
                    file=sys.stderr,
                )

    # P3: step-count advisory for small hosts.
    # The model-adaptation.md per-tier table says a small host should use
    # "fewer and larger — never more" work units. 5 is the advisory threshold;
    # exceeding it produces 5+ shallow results on a small model, which reads
    # thorough and is not. Warning only, not a hard error.
    # Deliberate: this gate fires only when --host small is explicitly declared.
    # An unset host falls back to "mid" (_effective_host = "mid"), not "small",
    # so runs that never declared a tier are not penalised here. There is no
    # basis for the step-count advisory without an explicit small-host declaration.
    _steps_for_count = state.get("steps") or []
    _effective_host = host if not _host_assumed else "mid"
    if _effective_host == "small" and len(_steps_for_count) > 5:
        print(
            f"  warning: small host has {len(_steps_for_count)} steps defined; "
            f"consider consolidating into \u22645 larger units "
            f"(references/model-adaptation.md)",
            file=sys.stderr,
        )

    # A rung with no trigger cannot be revised by evidence, which is the
    # difference between a decision and a label. Reported for R2 and above,
    # where the kernel's own rule is that the effort gate is recorded; R0 and
    # R1 are exempt because recording anything at those rungs is itself called
    # ceremony by references/decision-ledger.md.
    if rung_code in {"R2", "R3", "R4"}:
        triggers = state.get("rung_triggers") or {}
        if not (triggers.get("escalate_on") or "").strip():
            problems.append(
                f"rung {rung_code} records no escalation trigger; a rung that "
                f"cannot be revised by evidence is a label, not a decision")
        if not (triggers.get("de_escalate_on") or "").strip():
            problems.append(
                f"rung {rung_code} records no de-escalation trigger; SKILL.md "
                f"calls de-escalation the direction most often missing")

    # A rung that changed many times is the rung-axis analogue of mode
    # thrashing, and until now only the mode axis had a gate.
    rung_changes = state.get("rung_changed") or []
    if len(rung_changes) >= 3:
        problems.append(
            f"rung changed {len(rung_changes)} times; re-read the task rather "
            f"than oscillating")

    # --- the step log ---
    #
    # Two failure modes, and they are opposite. Zero open steps at R2+ means the
    # agent is working without saying what it is working on, which is the exact
    # case the kernel's "Stay observable" section exists for. Two or more open
    # steps means "what is the agent doing now" has more than one answer, and a
    # question with several answers gets answered by reading a transcript --
    # which is the thing this file exists to replace.
    steps = state.get("steps")
    if steps is None:
        steps = []
    open_steps = [s for s in steps if isinstance(s, dict) and s.get("outcome") is None]
    if rung_code in {"R2", "R3", "R4"} and not steps:
        problems.append(
            f"rung {rung_code} records no steps; at R2 and above the kernel "
            f"requires the current work unit, its precondition, and what is "
            f"about to happen to be stated at every boundary")
    if len(open_steps) > 1:
        problems.append(
            f"{len(open_steps)} steps are open at once (numbers "
            f"{', '.join(str(s.get('n')) for s in open_steps)}); at most one step "
            f"is current, so `show` cannot answer what the agent is doing")
    for s in steps:
        if not isinstance(s, dict):
            continue
        n = s.get("n")
        if not (s.get("doing") or "").strip():
            problems.append(f"step {n} has no description")
        if not (s.get("precondition") or "").strip():
            problems.append(
                f"step {n} has no precondition; a work unit without one cannot be "
                f"re-checked on resume, so a resuming agent repeats or skips it blind")
        if not (s.get("expect") or "").strip():
            problems.append(
                f"step {n} has no expected result; a step that does not say how it "
                f"ends is not independently verifiable")

    # A drop with no reason is the omission that gets silently re-done next pass.
    ctx = state.get("context") or {}
    for d in (ctx.get("dropped") or []):
        if not isinstance(d, dict):
            continue
        if not (d.get("why") or "").strip():
            problems.append(
                f"context entry {d.get('ref')!r} was dropped with no reason; the "
                f"next agent cannot tell an intentional omission from an oversight")

    # --- deliverables ---
    #
    # `deliver` refuses to record a path inside the memory directory, so a
    # produced file listed here is one that lives where a person can see it.
    # This re-checks that invariant rather than trusting it, because the state
    # file is editable by hand and by earlier versions of the tool.
    dl = state.get("deliverables") or {}
    for entry in (dl.get("produced") or []):
        if not isinstance(entry, dict):
            continue
        p = str(entry.get("path") or "")
        if p and (_is_inside(p, DEFAULT_DIR) or _is_inside(p, LEGACY_DIR)
                  or _is_inside(p, ".memory") or _is_inside(p, ".ultimate-dev")):
            problems.append(
                f"deliverable {p!r} is inside the agent's working memory. It is "
                f"gitignored and disposable, so the person who asked for it cannot "
                f"see it and git cannot record it. Move it to the path they named.")
    if dl.get("asked_location") and not (dl.get("produced") or []):
        # Only a problem when the user named a location: they asked for an
        # artifact at a path, and none was recorded as written there.
        problems.append(
            f"the user asked for output at {dl.get('asked_location')!r} and no "
            f"deliverable was recorded there. Either write it and `deliver "
            f"--path ...`, or record why it was not produced.")

    # --- process log enforcement at R2+ ---
    #
    # A run that has closed work units and recorded nothing in the process log has
    # described its work without logging it. At R2 this is a finding; at R3/R4
    # it is an error because the log is the record a reader cannot reconstruct.
    if rung_code in {"R2", "R3", "R4"}:
        closed_steps = [s for s in (state.get("steps") or [])
                        if isinstance(s, dict) and s.get("outcome") not in (None,)]
        log_entries = state.get("log") or []
        if closed_steps and not log_entries:
            if rung_code in {"R3", "R4"}:
                problems.append(
                    f"error: rung {rung_code} has {len(closed_steps)} closed work "
                    f"unit(s) and no process log entries. At R3/R4 the process log "
                    f"is required: log at least one entry per work unit with "
                    f"`log --kind execute-inline --what ...`.")
            else:
                problems.append(
                    f"rung {rung_code} has {len(closed_steps)} closed work unit(s) "
                    f"and no process log entries. Log at least one entry per work "
                    f"unit with `log --kind execute-inline --what ...`.")

    # --- the acceptance gate ---
    #
    # The checks above police the *shape* of a run: was the mode justified, is the
    # rung revisable, is a step open. None of them can tell whether the objective
    # was met, because nothing recorded what "met" means. This does.
    #
    # It is a mechanism, not a reminder, because the research on this exact
    # failure is unusually clear that prose does not work: an explicit "do not give
    # up" line in a system prompt does not change paired success, and a model asked
    # to judge its own completeness anchors on confident closing language and scores
    # a trajectory "completed" regardless of what happened (AUROC <= 0.65 across
    # five judge models, five prompt conditions). So the question cannot be put to
    # the model, and it cannot be left to judgement -- it has to be answered by a
    # deterministic check over state the model wrote earlier.
    #
    # R2 and above only. At R0 and R1 the run is short enough to hold the objective
    # in mind, and a rule that stops a false report would be charged as ceremony,
    # which is what the ladder exists to prevent.
    criteria = state.get("criteria") or []
    if rung_code in {"R2", "R3", "R4"}:
        if not criteria:
            problems.append(
                f"rung {rung_code} records no acceptance criteria. `require` states "
                f"what must be true when the run ends; steps without criteria are "
                f"work with no stopping condition, so they stop when the work looks "
                f"finished."
            )
        else:
            for c in criteria:
                if isinstance(c, dict) and c.get("status") != "met":
                    problems.append(
                        f"criterion {c.get('n')} is {c.get('status')!r}: "
                        f"{c.get('what')!r}. A terminal report while a criterion is "
                        f"open is a report about the work rather than the work. "
                        f"Satisfy it with `satisfy --evidence OBS-n`, or record a "
                        f"block with `blocked --tried`."
                    )

    # A continued block with no next action is a dead end by construction: it
    # declares the end of a route and leaves nothing to execute. Step 8's call to
    # escalate to the user is right once, and a loop if it becomes the answer.
    for b in state.get("blocks") or []:
        if (isinstance(b, dict) and b.get("continued_at")
                and not (b.get("next_action") or "").strip()):
            problems.append(
                f"block {b.get('n')} on {b.get('what')!r} was continued but records "
                f"no next action"
            )

    # --- the capability dispatch gate ---
    #
    # The mirror of the over-delegation rule that already existed. A run that
    # selected a specialist and then did the work inline passes every other check
    # here: its steps are closed, its criteria are met, its blocks are justified.
    # Nothing could see the missing dispatch, because nothing recorded one. This
    # records it, and refuses the report while a chosen capability is still in
    # flight.
    for d in state.get("dispatch") or []:
        if not isinstance(d, dict):
            continue
        name = d.get("for") or d.get("capability") or "?"
        st = (d.get("state") or "").strip().lower()
        if not st:
            problems.append(f"capability {name!r} is recorded with no state")
        elif st not in DISPATCH_STATES:
            problems.append(
                f"capability {name!r} is {st!r}, which is not a dispatch state "
                f"({', '.join(DISPATCH_STATES)})")
        if rung_code in {"R2", "R3", "R4"} and st in DISPATCH_ORDER \
                and st not in ("observed", "verified"):
            problems.append(
                f"capability {name!r} is {st!r} and never reached observed. A "
                f"capability that was chosen and not observed is a delegation "
                f"described rather than performed. Invoke it and record the "
                f"outcome, or record `unreachable --tried` / `skipped --why` "
                f"for a deliberate verdict.")
        if st == "unreachable" and not (d.get("tried") or []):
            problems.append(
                f"capability {name!r} is recorded unreachable with no route tried; "
                f"not-invoked and unreachable are different states, and only the "
                f"second is a finding about the host")
        if st == "skipped" and not (d.get("why") or "").strip():
            problems.append(
                f"capability {name!r} is skipped with no recorded reason")
        if st == "verified" and not (d.get("evidence") or "").strip():
            problems.append(
                f"capability {name!r} is verified with no evidence; nothing records "
                f"what was checked")

    for p in problems:
        print(f"  problem: {p}")
    if problems:
        print(f"\n  {len(problems)} problem(s). State is a claim until this passes.")
    else:
        # §18 coverage, on every clean run rather than only when asked. The number
        # is small and it is not a failure, but printing it means the gap cannot
        # quietly become larger while a reader assumes it is the same one.
        mapped = [n for n, p in RUNSTATE_FIELDS if p]
        unmapped = [n for n, p in RUNSTATE_FIELDS if not p]
        print(f"  state: {len(mapped)}/{len(RUNSTATE_FIELDS)} of §18's field list is "
              f"kept here; {len(unmapped)} have no home in this tool")
    if problems:
        return 1
    print(f"  run state is coherent: rung={state.get('rung')}, "
          f"mode={mode.get('mode')}, "
          f"{len(state.get('decisions', []))} decisions, "
          f"{len(state.get('observations', []))} observations")
    return 0


def cmd_list(args) -> int:
    d = args.state_dir
    if not os.path.isdir(d):
        print(f"  no state directory at {d}")
        return 0
    runs = sorted(f for f in os.listdir(d) if f.endswith(".json"))
    if not runs:
        print(f"  no runs in {d}")
        return 0
    for f in runs:
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            s = json.load(fh)
        mode = (s.get("coordination") or {}).get("mode", "?")
        print(f"  {s.get('run_id','?'):16} {mode:9} {str(s.get('objective'))[:60]}")
    return 0


def main() -> int:
    # --state-dir is accepted on the top-level parser AND on every subcommand, because
    # argparse would otherwise only take it before the subcommand, and that is not how
    # anyone types `run-state.py init --state-dir ...`.
    common = argparse.ArgumentParser(add_help=False)
    # SUPPRESS, not None. With default=None the subparser's own copy of this
    # argument overwrote the value given before the subcommand, so
    # `run-state.py --state-dir /tmp/x init ...` silently wrote to
    # .ultimate-dev/ instead. The comment above this parser says --state-dir is
    # accepted in both positions, and in the leading position it was accepted
    # and then discarded. SUPPRESS leaves the attribute unset unless the flag was
    # actually given, so the top-level value survives and the fallback below
    # fires only when neither position supplied one.
    common.add_argument("--state-dir", default=argparse.SUPPRESS,
                        help="where run state lives (default: <skill_root>/.memory/, or ~/.ultimate-dev/.memory/ if no skill root is found)")

    p = argparse.ArgumentParser(description=__doc__, parents=[common],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    # No set_defaults here: a real default would again be overwritten by the
    # subparser's own parse. The single fallback at the end of main() covers
    # both positions.
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="start a run", parents=[common])
    s.add_argument("--objective", required=True)
    s.add_argument("--deliverables", default="",
                   help="where the user asked any output to be written. Working "
                        "memory always goes to .memory/ and is never a deliverable.")
    # No choices= here on purpose. The case files write the rung as "R2
    # Analytical", and choices=list(RUNGS) would reject the form a reader copies
    # straight out of the corpus while accepting only the bare code. The
    # vocabulary is still closed: _rung_code() in cmd_init refuses anything
    # outside it, and it accepts both spellings. Constraining the value and
    # accepting what the corpus writes are not in tension; putting the
    # constraint in the wrong layer was.
    s.add_argument("--rung", default="R1", metavar="R0..R4",
                   help="effort rung; accepts R2 or 'R2 Analytical'")
    s.add_argument("--scale", default="L2", choices=list(SCALES))
    # The two triggers docs/architecture/kernel.md asks for: the event that
    # forces the rung up, and the one that lets it drop. "A triage without
    # triggers is a label", and a label cannot be revised by evidence.
    s.add_argument("--escalate-on", default="",
                   help="the observation that would force the rung up")
    s.add_argument("--de-escalate-on", default="",
                   help="the observation that would let the rung drop")
    s.add_argument("--mode", default="inline", choices=list(MODES))
    s.add_argument("--host", default=None, choices=list(HOSTS),
                   help="what this host can carry, as a term in the effort gate. "
                        "A term, never a model name: the tier is read from what the "
                        "host exposes, and a ladder that named models would be stale "
                        "the week one ships. See references/model-adaptation.md.")
    s.add_argument("--exceeds-ceiling", default="",
                   help="why this rung is above the host's ceiling. Required when it "
                        "is, and only then: a weak host given more procedure produces "
                        "more shallow decisions.")
    s.add_argument("--why", default="")
    s.add_argument("--until", default="")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("set-host", help="record a change in what the host can carry",
                       parents=[common])
    s.add_argument("--host", required=True, choices=list(HOSTS))
    s.add_argument("--why", required=True,
                   help="what changed. A host change moves every later rung "
                        "decision, so an unexplained one is unreviewable.")
    s.set_defaults(fn=cmd_set_host)

    s = sub.add_parser("show", help="print the current state, current step first",
                       parents=[common])
    s.add_argument("--json", action="store_true",
                   help="emit the whole state file instead of the summary")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("set-rung", help="change the effort rung, up or down",
                       parents=[common])
    s.add_argument("--rung", required=True, metavar="R0..R4",
                   help="the new rung; accepts R2 or 'R2 Analytical'")
    s.add_argument("--why", default="", help="what changed")
    s.add_argument("--escalate-on", default="", help="trigger that would force it up")
    s.add_argument("--de-escalate-on", default="", help="trigger that would let it drop")
    s.set_defaults(fn=cmd_set_rung)

    s = sub.add_parser("set-mode", help="change the coordination mode", parents=[common])
    s.add_argument("--mode", required=True, choices=list(MODES))
    s.add_argument("--why", default="")
    s.add_argument("--until", default="")
    s.set_defaults(fn=cmd_set_mode)

    s = sub.add_parser("handoff", help="move conversational authority", parents=[common])
    s.add_argument("--to", required=True, help="the role that takes the thread")
    s.add_argument("--authority", default="delegated", choices=["inline", "delegated"])
    s.add_argument("--why", default="")
    s.set_defaults(fn=cmd_handoff)

    s = sub.add_parser("step", help="open, close, or list work units",
                       parents=[common])
    s.add_argument("--doing", default="", help="what this step does")
    s.add_argument("--precondition", default="",
                   help="the condition that must hold before it is attempted")
    s.add_argument("--expect", default="",
                   help="the observable condition that means it finished")
    s.add_argument("--capability", default="",
                   help="what does the work (skill, tool, subagent, or 'inline')")
    s.add_argument("--verify", default="",
                   help="how you will know the expectation held (required at R2+)")
    s.add_argument("--verification-kind", default="",
                   help="which of the three check kinds was used: evidence-check | validation-check | independent-check")
    s.add_argument("--close", action="store_true",
                   help="close the open step instead of opening a new one")
    s.add_argument("--outcome", default="",
                   help="how the open step actually ended (with --close)")
    s.add_argument("--list", action="store_true", help="list every step")
    s.set_defaults(fn=cmd_step)

    s = sub.add_parser("log", help="append a numbered process-log line",
                       parents=[common])
    s.add_argument("--kind", default="",
                   help="the operation: " + ", ".join(sorted(LOG_KINDS)))
    s.add_argument("--what", default="", help="what actually happened")
    s.add_argument("--under", default="",
                   help="hang this off a logged step as a substep, e.g. P03")
    s.add_argument("--list", action="store_true", help="print the whole log")
    s.add_argument("--summary", action="store_true",
                   help="print compact numbered process log for inclusion in a delivery")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("context", help="record context loaded or deliberately dropped",
                       parents=[common])
    s.add_argument("--ref", default="",
                   help="the file, command, or observation the context came from")
    s.add_argument("--level", default="", metavar="C0..C6",
                   help="the context-ladder rung it was loaded at")
    s.add_argument("--why", default="", help="why it was loaded, or why dropped")
    s.add_argument("--fresh", action="store_true",
                   help="confirm it was checked for staleness before loading")
    s.add_argument("--drop", action="store_true",
                   help="record a deliberate omission rather than a load")
    # §15 asks for four things before a context request. `--ref` and `--why` were
    # the two being recorded; these are the other two, and a rule that says "name
    # four things" while only storing two is a rule three-quarters stated.
    s.add_argument("--enables", default="",
                   help="which action this context enables")
    s.add_argument("--scope", default="",
                   help="the minimum scope that would answer it")
    s.add_argument("--gap", default="",
                   help="record a context gap: what is missing, left open until "
                        "`context --closed`. §16's loop, and the thing a run that "
                        "is stuck has most reason not to write down.")
    s.add_argument("--closed", default="",
                   help="close an open context gap, naming it")
    s.set_defaults(fn=cmd_context)

    s = sub.add_parser("recover", help="record a recovery and its failure class",
                       parents=[common])
    s.add_argument("--class", dest="cls", required=True,
                   choices=list(FAILURE_CLASSES),
                   help="which of §28's nine kinds of failure this was")
    s.add_argument("--reason", default="", help="what went wrong")
    s.add_argument("--action", required=True,
                   help="what was done about it, as an action rather than a category")
    s.add_argument("--result", default="",
                   help="what the action produced. Required, but deliberately not "
                        "required=True at the parser: a missing --result deserves "
                        "the explanation of why a recovery with no outcome has not "
                        "been evaluated, not a usage line.")
    s.add_argument("--from-mode", default="", help="the coordination mode before")
    s.add_argument("--to-mode", default="", help="the coordination mode after")
    s.add_argument("--from-capability", default="", help="the capability before")
    s.add_argument("--to-capability", default="", help="the capability after")
    s.set_defaults(fn=cmd_recover)

    s = sub.add_parser("deliver", help="record a file this run produced for the user",
                       parents=[common])
    s.add_argument("--path", required=True,
                   help="the file the user asked for; must not be inside .memory/")
    s.add_argument("--what", default="", help="one line on what it is")
    s.set_defaults(fn=cmd_deliver)

    s = sub.add_parser("record", help="record an observation and get an OBS id",
                       parents=[common])
    s.add_argument("--observation", required=True)
    s.set_defaults(fn=cmd_record)

    s = sub.add_parser("decide", help="append a decision record", parents=[common])
    s.add_argument("--question", required=True)
    s.add_argument("--selected", required=True)
    s.add_argument("--rejected", required=True)
    s.add_argument("--rationale", required=True)
    s.add_argument("--confidence", required=True)
    s.add_argument("--evidence", required=True, help="OBS-n, or `none`")
    s.add_argument("--cost", default="")
    s.add_argument("--recovery", required=True)
    s.set_defaults(fn=cmd_decide)

    s = sub.add_parser("check", help="exit non-zero if the state is incoherent",
                       parents=[common])
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("require", help="state an acceptance criterion for this run",
                       parents=[common])
    s.add_argument("--what", required=True, help="what must be true when it ends")
    s.set_defaults(fn=cmd_require)

    s = sub.add_parser("satisfy", help="mark a criterion met, with its evidence",
                       parents=[common])
    s.add_argument("--what", required=True, help="the criterion, verbatim")
    s.add_argument("--evidence", required=True,
                   help="OBS-n that proves it, or `none`")
    s.set_defaults(fn=cmd_satisfy)

    s = sub.add_parser("blocked", help="declare part of the objective blocked",
                       parents=[common])
    s.add_argument("--what", required=True, help="the part that is blocked")
    s.add_argument("--reason", required=True, help="why, in one line")
    s.add_argument("--tried", action="append", default=[],
                   help="what was already looked for; repeatable, and required")
    s.add_argument("--routes", action="append", default=[],
                   choices=list(ROUTES),
                   help="which of §30's fifteen routes these cover; repeatable, "
                        "and required. --tried is the prose evidence, --routes is "
                        "the part that can be checked.")
    s.add_argument("--next-action", default="",
                   help="what will be executed next; required to continue a block")
    s.set_defaults(fn=cmd_blocked)

    s = sub.add_parser("reflect", help="record §45's self-evaluation", parents=[common])
    s.add_argument("--answer", action="append", default=[],
                   metavar="QUESTION=ANSWER",
                   help=f"repeatable. One of §45's "
                        f"{len(SELF_EVAL_QUESTIONS)} questions; `reflect --list` "
                        f"prints the vocabulary. All of them are required.")
    s.add_argument("--list", action="store_true",
                   help="print the questions and any recorded answers")
    s.add_argument("--why", default="",
                   help="unused by the gate; kept so the flag parses if a run "
                        "wants to say why the reflection was hard")
    s.set_defaults(fn=cmd_reflect)

    s = sub.add_parser("dispatch", help="record how far a chosen capability got",
                       parents=[common])
    s.add_argument("--for", dest="what", required=True,
                   help="the capability, named as the host exposes it")
    s.add_argument("--state", required=True,
                   help="|".join(DISPATCH_STATES))
    s.add_argument("--evidence", default="", help="OBS-n; required at `verified`")
    s.add_argument("--tried", action="append", default=[],
                   help="what was actually looked for; repeatable, and required at "
                        "`unreachable` and at `blocked`")
    s.add_argument("--routes", action="append", default=[],
                   choices=list(ROUTES),
                   help="which of §30's fifteen routes this covers; repeatable. "
                        "Kept separate from --tried because the prose is the "
                        "evidence and the route name is the part that can be "
                        "checked.")
    s.add_argument("--why", default="", help="the reason; required at `skipped`")
    s.add_argument("--brief", default="",
                   help="§11's seven fields and §42's context package; required at "
                        "`invoked`. Names, not prose: the gate checks that the "
                        "fields are there, not that the brief is any good.")
    s.add_argument("--result-status", default="",
                   choices=list(RESULT_STATUSES),
                   help="§12's STATUS; required at `observed` and `verified`")
    s.add_argument("--result", default="",
                   help="§12's RESULT; required at `observed` and `verified`")
    s.set_defaults(fn=cmd_dispatch)

    s = sub.add_parser("audit", help="check a delivery for terminal justifications",
                       parents=[common])
    s.add_argument("path", help="the delivery file, or - for stdin")
    s.add_argument("--trivially", action="store_true",
                   help="the delivery is too short to carry §47's five sections")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("finish", help="record the run's terminal status",
                       parents=[common])
    s.add_argument("--status", required=True, metavar="|".join(COMPLETION_STATUSES),
                   help="completed | partial | blocked | failed")
    s.add_argument("--remaining", default="",
                   help="what is still outstanding (required for `partial`)")
    s.add_argument("--attempted", default="",
                   help="what execution was attempted and lost (required for "
                        "`failed`)")
    s.add_argument("--recovery", default="",
                   help="what recovery was attempted, for partial or failed")
    s.add_argument("--next-action", default="",
                   help="the next executable action, for partial or failed")
    s.add_argument("--replace", action="store_true",
                   help="change a recorded ending; requires --why")
    s.add_argument("--why", default="", help="why the recorded ending changed")
    s.set_defaults(fn=cmd_finish)

    s = sub.add_parser("list", help="list runs in the state directory", parents=[common])
    s.set_defaults(fn=cmd_list)

    args = p.parse_args()
    # Whether the caller named a location, or is taking the default. The legacy
    # migration only applies to the default: moving a file out of a directory
    # someone explicitly pointed at would be the tool editing a location it was
    # not given.
    args.state_dir_explicit = bool(getattr(args, "state_dir", None))
    if not args.state_dir_explicit:
        args.state_dir = DEFAULT_DIR
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
