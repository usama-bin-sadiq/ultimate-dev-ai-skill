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
    handoff with no target, or evidence that is prose rather than a pointer. Those are the
    four ways this file can become a decoration.
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
        ev = (d.get("evidence") or "").strip()
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

    for p in problems:
        print(f"  problem: {p}")
    if problems:
        print(f"\n  {len(problems)} problem(s). State is a claim until this passes.")
        return 1
    print(f"  run state is coherent: mode={mode.get('mode')}, "
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
    common.add_argument("--state-dir", default=None,
                        help=f"where run state lives (default {DEFAULT_DIR}/)")

    p = argparse.ArgumentParser(description=__doc__, parents=[common],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.set_defaults(state_dir=DEFAULT_DIR)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="start a run", parents=[common])
    s.add_argument("--objective", required=True)
    s.add_argument("--rung", default="R1")
    s.add_argument("--scale", default="L2")
    s.add_argument("--mode", default="inline", choices=list(MODES))
    s.add_argument("--why", default="")
    s.add_argument("--until", default="")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("show", help="print the current state", parents=[common])
    s.set_defaults(fn=cmd_show)

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
    if getattr(args, "state_dir", None) is None:
        args.state_dir = DEFAULT_DIR
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
