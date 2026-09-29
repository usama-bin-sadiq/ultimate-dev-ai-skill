#!/usr/bin/env python3
"""Run state: create, read, update, and check it.

`references/state-system.md` has specified this structure for the whole life of the
repository and nothing has ever read or written it. Every claim the architecture makes
about resumption, about work outliving a context window, and about the L4+ rows of the
scale ladder depends on a file existing -- and none did. That is the gap this closes.

State is a single JSON file, one per run, under `--state-dir` (default `.ultimate-dev/`).
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
import sys

DEFAULT_DIR = ".ultimate-dev"
STATE_FILE = "run-state.json"
SCHEMA_VERSION = 2

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
    print(f"  run       {state.get('run_id')}   rung {state.get('rung')} "
          f"scale {state.get('scale')}")
    print(f"  objective {state.get('objective')}")
    print(f"  mode      {mode.get('mode')}  — {mode.get('why')}")
    print(f"  until     {mode.get('until')}")
    print(f"  active    {state.get('active_agent') or '(none)'}  "
          f"authority={state.get('authority')}")
    print(f"  decisions {len(state.get('decisions', []))}   "
          f"observations {len(state.get('observations', []))}")
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

    s = sub.add_parser("show", help="print the current state", parents=[common])
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

    s = sub.add_parser("list", help="list runs in the state directory", parents=[common])
    s.set_defaults(fn=cmd_list)

    args = p.parse_args()
    if not getattr(args, "state_dir", None):
        args.state_dir = DEFAULT_DIR
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
