#!/usr/bin/env python3
"""Run state: create, read, update, and check it.

`references/state-system.md` has specified this structure for the whole life of the
repository and nothing has ever read or written it. Every claim the architecture makes
about resumption, about work outliving a context window, and about the L4+ rows of the
scale ladder depends on a file existing -- and none did. That is the gap this closes.

State is a single JSON file, one per run, under `--state-dir` (default `.memory/`).
That directory is the agent's private, disposable, gitignored working memory and
is never where a deliverable goes; `deliver` refuses a path inside it.
It is small on purpose: `state-system.md` asks for size discipline, and a state file that
grows without bound is a context problem wearing a different hat.

    python3 tools/run-state.py init      --objective "..."  [--rung R2] [--scale L3]
    python3 tools/run-state.py show
    python3 tools/run-state.py set-mode  --mode route --why "three sources" \
                                         --until "single-source follow-up"
    python3 tools/run-state.py handoff   --to <role> --authority delegated
    python3 tools/run-state.py record    --observation "..." 
    python3 tools/run-state.py decide    --question "..." --selected "..." \
                                         --rejected "..." --rationale "..." \
                                         --confidence "high in X" --evidence OBS-1
    python3 tools/run-state.py check
    python3 tools/run-state.py list

COORDINATION MODE is the field revision 2 added. It is one of inline, delegate, route,
handoff, and it carries the condition that would change it -- so a mode that turns out to
be wrong is a recorded fact rather than an invisible one.

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

    tools/test-run-state.py asserts every clause of this list in both
    directions, and found the last two of those three.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import sys

# Working memory, not deliverables. `.memory/` was already in .gitignore as
# "Local agent state" while the tool wrote to `.ultimate-dev/`, so the
# convention was declared and the implementation ignored it -- and two names for
# one thing meant a run started by one version could not be read by the other.
DEFAULT_DIR = ".memory"
# Where earlier versions wrote. Read once, on load, and migrated rather than
# silently ignored: a state file the tool cannot find is indistinguishable from
# a run that never recorded anything, and the second is a finding about the
# agent while the first is a finding about the tool.
LEGACY_DIR = ".ultimate-dev"
STATE_FILE = "run-state.json"
SCHEMA_VERSION = 3

# The capability dispatch contract, from the kernel's "no silent degradation"
# section. The chain matters in one direction: a capability that was chosen and
# never observed is a delegation described rather than performed, which is the
# under-doing failure wearing a different hat.
DISPATCH_ORDER = ("selected", "invoked", "running", "observed", "verified")
# `unreachable` and `skipped` are terminal verdicts, not stages of the chain --
# a capability the host does not expose, or one deliberately passed over.
DISPATCH_TERMINAL = ("unreachable", "skipped")
DISPATCH_STATES = DISPATCH_ORDER + DISPATCH_TERMINAL


MODES = ("inline", "delegate", "route", "handoff")

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
        "context": {"loaded": [], "dropped": []},
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
    elif steps:
        last = steps[-1]
        print(f"  ○ no open step   last was {last.get('n')}: "
              f"{last.get('doing')} → {last.get('outcome')}")
    else:
        print("  ○ no step recorded; the run has not said what it is doing")

    print(f"  run       {state.get('run_id')}   rung {state.get('rung')} "
          f"scale {state.get('scale')}")
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

    current = _open_step(state)
    if current is not None:
        current["outcome"] = "superseded"
        current["closed_at"] = now()

    state.setdefault("steps", []).append({
        "n": len(state.get("steps") or []) + 1,
        "doing": doing,
        "precondition": args.precondition,
        "expect": args.expect,
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
    if _is_inside(out, DEFAULT_DIR) or _is_inside(out, LEGACY_DIR):
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
        "next_action": (args.next_action or "").strip() or None,
        "declared_at": now(),
    })
    save(args, state)
    print(f"  block {len(blocks)} recorded on {what!r}; "
          f"{len(tried)} route(s) tried")
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

    changes = mode.get("changed") or []
    if len(changes) >= 3:
        problems.append(
            f"coordination mode changed {len(changes)} times; that is a signal the "
            f"first choice was wrong, not that the task is hard")

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
    rung = state.get("rung")
    if rung is not None and str(rung).split(" ", 1)[0].upper() not in RUNGS:
        problems.append(
            f"rung {rung!r} is not one of {', '.join(RUNGS)}; the effort gate "
            f"produces a rung, so an unrecognised one means the gate was skipped")

    scale = state.get("scale")
    if scale is not None and str(scale).strip().upper() not in SCALES:
        problems.append(
            f"scale {scale!r} is not one of {', '.join(SCALES)}")

    # A rung with no trigger cannot be revised by evidence, which is the
    # difference between a decision and a label. Reported for R2 and above,
    # where the kernel's own rule is that the effort gate is recorded; R0 and
    # R1 are exempt because recording anything at those rungs is itself called
    # ceremony by references/decision-ledger.md.
    rung_code = str(rung or "").split(" ", 1)[0].upper()
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
        if p and (_is_inside(p, DEFAULT_DIR) or _is_inside(p, LEGACY_DIR)):
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
                        help=f"where run state lives (default {DEFAULT_DIR}/)")

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
    s.add_argument("--why", default="")
    s.add_argument("--until", default="")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

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
    s.add_argument("--close", action="store_true",
                   help="close the open step instead of opening a new one")
    s.add_argument("--outcome", default="",
                   help="how the open step actually ended (with --close)")
    s.add_argument("--list", action="store_true", help="list every step")
    s.set_defaults(fn=cmd_step)

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
    s.set_defaults(fn=cmd_context)

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
                   help="a route already walked; repeatable, and required")
    s.add_argument("--next-action", default="",
                   help="what will be executed next; required to continue a block")
    s.set_defaults(fn=cmd_blocked)

    s = sub.add_parser("dispatch", help="record how far a chosen capability got",
                       parents=[common])
    s.add_argument("--for", dest="what", required=True,
                   help="the capability, named as the host exposes it")
    s.add_argument("--state", required=True,
                   help="|".join(DISPATCH_STATES))
    s.add_argument("--evidence", default="", help="OBS-n; required at `verified`")
    s.add_argument("--tried", action="append", default=[],
                   help="a route looked for; repeatable, required at `unreachable`")
    s.add_argument("--why", default="", help="the reason; required at `skipped`")
    s.set_defaults(fn=cmd_dispatch)

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
