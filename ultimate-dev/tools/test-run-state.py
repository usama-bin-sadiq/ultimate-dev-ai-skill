#!/usr/bin/env python3
"""Self-test for run-state.py.

Four tools in this repository have a self-test. This one did not, while its own
docstring claimed a gate:

    "check is the gate. It exits non-zero on an unknown mode, a mode with no
     reason, a handoff with no target, or evidence that is prose rather than a
     pointer. Those are the four ways this file can become a decoration."

Three of those four were real. One was not implemented at all: `until`, the
reversing condition that SKILL.md says check refuses a state without, was
written by set-mode and never read by anything.

And the fields the effort gate exists to produce were unconstrained and
unverified. `--rung` had no `choices=`, so it accepted "banana" and stored it.
`check` never read rung or scale. There was no `set-rung`, so the only way to
raise the rung was `init --force`, which overwrites the state file and discards
the decisions and observations recorded so far -- the only response available to
"reality is harder than expected" was to erase the record of it. And
de-escalation, which SKILL.md calls the direction most often missing, had no
mechanism while mode thrashing had a gate.

  S1  --rung banana is rejected at the parser
  S2  --rung "R2 Analytical" is accepted and normalised to R2
  S3  --scale is likewise constrained
  S4  set-rung escalates and keeps the history
  S5  set-rung DE-ESCALATES, and decisions and observations survive
  S6  check fails when until is empty
  S7  check fails for an out-of-vocabulary rung written into the state file
  S8  check fails for R2+ with no escalation trigger
  S9  check fails for R2+ with no de-escalation trigger
  S10 check does not demand triggers at R0/R1, where recording is called ceremony
  S11 check still fails for three mode changes
  S12 check still fails for a decision with no rejected / no recovery
  S13 check passes a well-formed state
  S14 set-mode with an unknown mode is still refused

Revision 3 found the same class of gap a third time, in the two places the
specification is most worried about. `COMPLETION_STATUSES`, `STEP_FIELDS` and
`LOG_KINDS` were declared in run-state.py and read by nothing -- a vocabulary
nobody consults constrains nobody, and the file said so by containing the
constants without running them. Section 24 (the log must agree with the state),
section 26 (five fields per work unit) and section 35 (four conditions for
`completed`) were all prose.

Wiring them broke two S25 assertions, and the breakage was the gate working:
that fixture opened an R2 work unit naming only three of the five fields, so
the step was never opened and the two `check` calls downstream failed with
"rung R2 records no steps". That is worth recording separately from the fix,
because a test that fails when a gate gets stricter is the only evidence that
the gate was ever advisory.

  S26 a plain stage is logged and numbered from P01
  S26 an unknown kind, and an entry with no content, are refused
  S26 a log claiming a delegation the ledger has not got is refused
  S26 a log claiming verification with nothing verified is refused
  S26 a log claiming completion before `finish` ran is refused
  S26 substeps number under their parent, and the top level keeps counting
  S26 the same entry is accepted once the ledger agrees
  S26 check catches a hand-edited log the write path would have refused
  S31 an R2 unit with three fields is refused, five is accepted and stored
  S31 R1 is exempt, because a unit there is a sentence
  S32 `completed` is refused for each of the four conditions independently
  S32 a second ending is refused unless --replace carries a reason
  S33 `partial` needs the remainder, and needs work to have happened
  S33 `blocked` needs routes actually walked
  S33 `failed` needs the attempt named, and is kept distinct from blocked

Revision 4 added the second term in the effort gate. The rung ladder answered how
hard the task is and never answered what the model can carry, so one procedure was
applied unchanged from a 1B model to a frontier one -- and this repository's own
research says that is measurably wrong at both ends. `references/triage.md` had
already named the gap and answered it with "re-calibrate", which is not executable.

  S34 a small host at its R2 ceiling passes
  S34 a small host at R3 is refused, and a stated reason lets it through
  S34 set-host keeps the change with its reason
  S35 a frontier host may de-escalate, but check refuses it unreasoned
  S35 the same drop on a small host is free, because it usually is right
  S35 an out-of-vocabulary host in the state file is refused
  S36 no constant in run-state.py is declared and read by nothing
"""

from __future__ import annotations


import importlib.util
import json
import pathlib
import re
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_state", HERE / "run-state.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


class ArgError(Exception):
    pass


def run(*argv: str) -> tuple[int, str]:
    """Invoke run-state.main() with argv, in a throwaway state dir."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        args = ["prog", "--state-dir", str(tmp)] + list(argv)
        import argparse
        real = sys.stderr
        buf: list[str] = []

        class Cap:
            def write(self, s: str) -> None:
                buf.append(s)

            def flush(self) -> None:
                pass

        sys.stderr = Cap()
        try:
            code = rs.main.__wrapped__(args) if hasattr(rs.main, "__wrapped__") else _main(args)
        except SystemExit as e:
            code = int(e.code or 0)
        except ArgError as e:
            code, msg = 2, str(e)
            return code, msg
        finally:
            sys.stderr = real
        return code, "".join(buf)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main(argv: list[str]) -> int:
    """main() but catching argparse's SystemExit into a return code."""
    import argparse
    parser_error: list[str] = []
    try:
        return rs.main_with_args(argv) if hasattr(rs, "main_with_args") else _dispatch(argv)
    except SystemExit:
        raise


def _dispatch(argv: list[str]) -> int:
    """Call the module's main with a patched sys.argv."""
    import argparse
    old = sys.argv
    sys.argv = argv
    try:
        return rs.main()
    finally:
        sys.argv = old


# argparse raises SystemExit(2) on a bad choice, which is what we want to observe.
def cli(*argv: str) -> tuple[int, str]:
    tmp = tempfile.mkdtemp()
    try:
        import io
        import contextlib
        old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
        buf = io.StringIO()
        sys.argv = ["run-state.py", "--state-dir", tmp] + list(argv)
        sys.stderr = sys.stdout = buf
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
        finally:
            sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
        return code, buf.getvalue()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_state(state: dict) -> tuple[str, str]:
    """A state dir holding exactly this state, and its path."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "run-state.json").write_text(json.dumps(state), encoding="utf-8")
    return str(tmp), str(tmp / "run-state.json")


def state_of(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


BASE = {
    "schema_version": 4, "run_id": "T", "started": "now", "objective": "o",
    "rung": "R1", "scale": "L1",
    "rung_triggers": {"escalate_on": "", "de_escalate_on": ""},
    "coordination": {"mode": "inline", "why": "w", "until": "u", "changed": []},
    "active_agent": None, "authority": "inline",
    # A closed step, not an open one: S13 asserts a well-formed R2 state passes,
    # and R2 now requires a step log. Leaving `steps` out of BASE would have made
    # that case fail for a reason unrelated to what it is testing -- and the easy
    # fix, exempting R2 from its own new rule, would have deleted the check.
    "steps": [{"n": 1, "doing": "the work", "precondition": "it can start",
               "expect": "it is done", "outcome": "done",
               "capability": "inline", "verify": "read it back",
               "at": "now", "closed_at": "now"}],
    "log": [],
    "completion": None,
    "host": "mid", "exceeds_ceiling": None, "host_history": [],
    "criteria": [], "dispatch": [], "recoveries": [], "blocks": [],
    "handoffs": [],
    "context": {"loaded": [], "dropped": [], "gaps": [], "why": ""},
    "deliverables": {"asked_location": "", "produced": []},
    "decisions": [], "observations": [], "assumptions": [],
    "verification": {"criteria": [], "verdicts": []}, "result": None,
}

# ---- S1/S2/S3: the vocabularies are constrained at the parser
code, out = cli("init", "--objective", "o", "--rung", "banana")
check("S1 --rung banana is rejected", code != 0, f"exit {code}")
check("S1 and the message names the vocabulary",
      "invalid choice" in out or "R0" in out, out[:120])

code, out = cli("init", "--objective", "o", "--rung", "R2 Analytical")
check("S2 --rung 'R2 Analytical' is accepted", code == 0, f"exit {code}: {out[:120]}")

code, out = cli("init", "--objective", "o", "--scale", "L9")
check("S3 --scale L9 is rejected", code != 0, f"exit {code}")

# ---- S4/S5: escalation and de-escalation, neither of which had a path
tmp = pathlib.Path(tempfile.mkdtemp())
try:
    base = ["--state-dir", str(tmp), "init", "--objective", "o",
            "--rung", "R1", "--escalate-on", "a tool disagrees",
            "--de-escalate-on", "the first attempt worked"]
    import io, contextlib
    def call(*argv):
        old_argv, old_out = sys.argv, sys.stdout
        buf = io.StringIO(); sys.argv = ["run-state.py"] + list(argv); sys.stdout = buf
        try:
            return rs.main()
        except SystemExit as e:
            return int(e.code or 0)
        finally:
            sys.argv, sys.stdout = old_argv, old_out
    call(*base)
    sp = tmp / "run-state.json"
    st = state_of(str(sp))
    # put a decision and an observation in, so S5 can prove they survive
    st["decisions"] = [{"question": "q", "selected": "invoke the reviewer subagent", "rejected": "r",
                        "recovery": "v"}]
    st["observations"] = [{"id": "OBS-1", "text": "t"}]
    sp.write_text(json.dumps(st), encoding="utf-8")

    code = call("--state-dir", str(tmp), "set-rung", "--rung", "R3", "--why", "unknown dependency")
    st = state_of(str(sp))
    check("S4 set-rung escalates", st["rung"] == "R3", st.get("rung"))
    check("S4 and keeps the history",
          len(st.get("rung_changed", [])) == 1, str(st.get("rung_changed")))

    code = call("--state-dir", str(tmp), "set-rung", "--rung", "R1",
                "--why", "the first attempt worked")
    st = state_of(str(sp))
    check("S5 set-rung de-escalates", st["rung"] == "R1", st.get("rung"))
    check("S5 and the decisions survive -- the bug `init --force` had",
          len(st["decisions"]) == 1 and st["decisions"][0]["question"] == "q",
          str(st.get("decisions"))[:110])
    check("S5 and the observations survive",
          len(st["observations"]) == 1 and st["observations"][0]["id"] == "OBS-1",
          str(st.get("observations"))[:110])
    check("S5 and both rung changes are in the history",
          len(st.get("rung_changed", [])) == 2, str(len(st.get("rung_changed", []))))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- S6: `until` is now read
d, sp = write_state({**BASE, "coordination": {"mode": "inline", "why": "w",
                                              "until": "", "changed": []}})
code, out = cli("--state-dir", d, "check")
check("S6 check fails when until is empty", code == 1, f"exit {code}")
check("S6 and says which field", "until" in out or "reversing" in out, out[:140])

# ---- S7: an out-of-vocabulary rung in the state file
d, sp = write_state({**BASE, "rung": "banana"})
code, out = cli("--state-dir", d, "check")
check("S7 check fails for a rung outside the vocabulary", code == 1, f"exit {code}")
check("S7 and names the vocabulary", "R0" in out, out[:140])

# ---- S8/S9/S10: triggers required at R2+, not at R0/R1
d, sp = write_state({**BASE, "rung": "R2",
                     "rung_triggers": {"escalate_on": "", "de_escalate_on": "x"}})
code, out = cli("--state-dir", d, "check")
check("S8 check fails for R2 with no escalation trigger", code == 1, f"exit {code}")
check("S8 and only complains about the missing one",
      "escalation trigger" in out and "de-escalation" not in out, out[:170])

d, sp = write_state({**BASE, "rung": "R2",
                     "rung_triggers": {"escalate_on": "x", "de_escalate_on": ""}})
code, out = cli("--state-dir", d, "check")
check("S9 check fails for R2 with no de-escalation trigger", code == 1, f"exit {code}")

d, sp = write_state({**BASE, "rung": "R0",
                     "rung_triggers": {"escalate_on": "", "de_escalate_on": ""}})
code, out = cli("--state-dir", d, "check")
check("S10 check does not demand triggers at R0", code == 0, f"exit {code}: {out[:130]}")

# ---- S11/S12/S13: the existing gates must still fire
d, sp = write_state({**BASE, "coordination": {
    "mode": "inline", "why": "w", "until": "u",
    "changed": [{"from": "a", "to": "b"} for _ in range(3)]}})
code, out = cli("--state-dir", d, "check")
check("S11 three mode changes still fail", code == 1, f"exit {code}")

d, sp = write_state({**BASE, "decisions": [{"question": "q", "selected": "invoke the reviewer subagent",
                                           "rejected": "", "recovery": ""}]})
code, out = cli("--state-dir", d, "check")
check("S12 a decision with no rejected and no recovery still fails", code == 1,
      f"exit {code}")

# A well-formed state must pass, or every assertion above is vacuous.
d, sp = write_state({
    **BASE, "rung": "R2",
    "rung_triggers": {"escalate_on": "a tool disagrees",
                      "de_escalate_on": "the first attempt worked"},
    "decisions": [{"question": "q", "selected": "invoke the reviewer subagent", "rejected": "r",
                   "recovery": "v", "evidence": ["OBS-1"]}],
    "observations": [{"id": "OBS-1", "text": "t"}],
    # R2 and above need an acceptance criterion, and this fixture is a well-formed
    # R2 state, so it carries a met one. It did not when S13 was written, because
    # the gate did not exist; a fixture that predates a rule is updated, not the
    # rule relaxed.
    "criteria": [{"n": 1, "what": "the state is coherent", "status": "met",
                  "evidence": "OBS-1", "met_at": "2026-01-01T00:00:00Z"}],
})
code, out = cli("--state-dir", d, "check")
check("S13 a well-formed state passes", code == 0, f"exit {code}: {out[:200]}")
check("S13 and the passing message states the rung",
      "rung=R2" in out, out[:160])

# ---- S14: set-mode still refuses an unknown mode
d, sp = write_state(dict(BASE))
code, out = cli("--state-dir", d, "set-mode", "--mode", "teleport")
check("S14 set-mode with an unknown mode is refused", code != 0, f"exit {code}")

# ---- S15-S18: the step log, and what `show` is for
#
# The step log exists so that "what is this agent doing right now" has an
# answer which survives the run getting long. Every gate below is paired with a
# negative, because a gate that only ever passes is the failure this file has
# already caught twice.

_d = tempfile.mkdtemp()
_sdp = ["--state-dir", _d]
cli(*_sdp, "init", "--objective", "o", "--rung", "R1")
code, out = cli(*_sdp, "step", "--doing", "fix it",
                "--precondition", "it exists", "--expect", "it is fixed")
check("S15 a step opens with a precondition and an expected result",
      code == 0, f"exit {code}: {out[:120]}")

code, out = cli(*_sdp, "show")
check("S15 and `show` leads with the open step",
      "fix it" in out.splitlines()[0], out.splitlines()[0][:120] if out else "")
check("S15 and it prints the precondition and the expected result",
      "it exists" in out and "it is fixed" in out, out[:200])

# Opening a second step supersedes the first, so "current" stays singular.
cli(*_sdp, "step", "--doing", "second", "--precondition", "p", "--expect", "e")
_st = state_of(str(pathlib.Path(_d) / "run-state.json"))
_open = [s for s in _st["steps"] if s.get("outcome") is None]
check("S16 opening a second step closes the first", len(_open) == 1,
      f"{len(_open)} still open")
check("S16 and the superseded step says so, rather than vanishing",
      _st["steps"][0]["outcome"] == "superseded", str(_st["steps"][0]))

code, out = cli(*_sdp, "step", "--doing", "no precond", "--expect", "e")
check("S17 a step with no precondition is refused", code != 0, f"exit {code}")
code, out = cli(*_sdp, "step", "--doing", "no expect", "--precondition", "p")
check("S17 a step with no expected result is refused", code != 0, f"exit {code}")
code, out = cli(*_sdp, "step", "--close", "--outcome", "")
check("S17 a step cannot be closed with no outcome", code != 0, f"exit {code}")

# R2 requires a step log; R0 does not, because the kernel calls recording at R0
# ceremony, and a gate that fires there is the thing it criticises.
_d2, _ = write_state({**BASE, "rung": "R2", "steps": [],
                      "rung_triggers": {"escalate_on": "a", "de_escalate_on": "b"}})
code, out = cli("--state-dir", _d2, "check")
check("S18 an R2 state with no steps fails", code != 0, f"exit {code}")
check("S18 and it names the step log as the reason", "no steps" in out, out[:160])

_d3, _ = write_state({**BASE, "rung": "R0", "steps": []})
code, out = cli("--state-dir", _d3, "check")
check("S18 and an R0 state with no steps still passes", code == 0,
      f"exit {code}: {out[:160]}")

_d4, _ = write_state({**BASE, "steps": [
    {"n": 1, "doing": "a", "precondition": "p", "expect": "e", "outcome": None},
    {"n": 2, "doing": "b", "precondition": "p", "expect": "e", "outcome": None}]})
code, out = cli("--state-dir", _d4, "check")
check("S18 two steps open at once fails", code != 0, f"exit {code}")

# ---- S19-S21: working memory is not a deliverable
#
# `.memory/` is gitignored and disposable. An audit or research document filed
# there is invisible to whoever asked for it, lost when the directory is
# cleared, and noticed by nothing -- which is why the refusal lives in the tool
# rather than in a convention.

_d5 = tempfile.mkdtemp()
_sd5p = ["--state-dir", _d5]
cli(*_sd5p, "init", "--objective", "o", "--rung", "R1")
code, out = cli(*_sd5p, "deliver", "--path", ".memory/audit.md", "--what", "audit")
check("S19 a deliverable inside the memory directory is refused", code != 0,
      f"exit {code}")
check("S19 and the message says where it belongs",
      "path they named" in out or "where the user asked" in out, out[:200])

# `.memory-backup` begins with the string `.memory` and is a different
# directory; a prefix test would refuse a legitimate path.
code, out = cli(*_sd5p, "deliver", "--path", ".memory-backup/audit.md")
check("S19 and a sibling-prefixed path is not caught by the prefix test",
      code == 0, f"exit {code}: {out[:160]}")

code, out = cli(*_sd5p, "deliver", "--path", "docs/audit.md", "--what", "audit")
check("S20 a deliverable at the requested path is recorded", code == 0,
      f"exit {code}: {out[:120]}")
_st = state_of(str(pathlib.Path(_d5) / "run-state.json"))
check("S20 and it is in the state file",
      any(e.get("path") == "docs/audit.md"
          for e in _st["deliverables"]["produced"]), str(_st["deliverables"]))

# Hand-edited, or written by an older version: check re-derives the rule rather
# than trusting whichever tool wrote the file.
_d6, _ = write_state({**BASE, "deliverables": {
    "asked_location": "", "produced": [{"path": ".memory/x.md", "what": ""}]}})
code, out = cli("--state-dir", _d6, "check")
check("S21 a deliverable inside memory fails check even if hand-written",
      code != 0, f"exit {code}")

_d7, _ = write_state({**BASE, "deliverables": {
    "asked_location": "docs/a.md", "produced": []}})
code, out = cli("--state-dir", _d7, "check")
check("S21 and an asked-for location with nothing delivered fails", code != 0,
      f"exit {code}")

# ---- S22: a context drop with no reason
_d8, _ = write_state({**BASE, "context": {
    "loaded": [], "dropped": [{"ref": "big.md", "why": ""}]}})
code, out = cli("--state-dir", _d8, "check")
check("S22 a context drop with no reason fails", code != 0, f"exit {code}")

_d9 = tempfile.mkdtemp()
_sd9p = ["--state-dir", _d9]
cli(*_sd9p, "init", "--objective", "o", "--rung", "R1")
code, out = cli(*_sd9p, "context", "--ref", "references/x.md", "--level", "C3")
check("S22 a context load is recorded", code == 0, f"exit {code}: {out[:120]}")
code, out = cli(*_sd9p, "context", "--drop", "--ref", "big.md")
check("S22 a drop with no reason is refused at write time too", code != 0,
      f"exit {code}")

# ---- S23: the default state directory is .memory, and legacy still migrates
_src = (pathlib.Path(__file__).resolve().parent / "run-state.py").read_text(
    encoding="utf-8")
check("S23 the default state directory is .memory",
      ('DEFAULT_DIR = ".memory"' in _src or
       ('_SKILL_ROOT' in _src and '".memory"' in _src)),
      "DEFAULT_DIR does not resolve to .memory")
check("S23 and the legacy directory is still recognised for migration",
      'LEGACY_DIR = ".ultimate-dev"' in _src, "LEGACY_DIR missing")

# ---- S24: the acceptance gate, and the cost of declaring a block ----------
#
# S24 exists because of a measured failure, not a hypothetical one. One run
# concluded three separate work items by writing a precise account of why it had
# not done them -- "blocked on credits", "0 of 286 have an eval", "needs an
# owner decision" -- and each read as diligence.
#
# Prose rules against that do not work, which is why these cases exist: an
# explicit "do not give up" instruction in a system prompt does not change paired
# success, and a model asked to judge its own completeness anchors on confident
# closing language and scores a trajectory "completed" regardless of what
# actually happened (AUROC <= 0.65 across five judge models). The correction
# therefore has to be mechanical, and these cases pin the mechanics.

_s24 = pathlib.Path(tempfile.mkdtemp())


def s24(*argv: str) -> tuple[int, str]:
    """cli() against one persistent dir, so a run spans several calls."""
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s24)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s24("init", "--rung", "R2", "--objective", "gate test")
s24("set-mode", "--mode", "inline", "--why", "one tool", "--until", "done")
s24("step", "--doing", "work", "--precondition", "p", "--expect", "e")
s24("record", "--observation", "ran the gate")
s24("record", "--observation", "searched the catalogue")

code, out = s24("check")
check("S24 a terminal report is refused while no criterion exists", code != 0,
      f"exit {code}")
check("S24 and the refusal names the missing criteria",
      "no acceptance criteria" in out, out[:140])

s24("require", "--what", "the gate exits 0 only when met")
code, out = s24("check")
check("S24 an OPEN criterion still refuses the report", code != 0, f"exit {code}")
check("S24 and it names the criterion", "criterion 1 is 'open'" in out, out[:140])

code, out = s24("satisfy", "--what", "the gate exits 0 only when met",
                "--evidence", "OBS-99")
check("S24 evidence that does not resolve is refused", code != 0, f"exit {code}")

code, out = s24("satisfy", "--what", "the gate exits 0 only when met",
                "--evidence", "it works now")
check("S24 prose evidence is refused", code != 0, f"exit {code}")

code, out = s24("satisfy", "--what", "the gate exits 0 only when met",
                "--evidence", "OBS-1")
check("S24 a resolving pointer satisfies the criterion", code == 0,
      f"exit {code}: {out[:120]}")
code, out = s24("check")
check("S24 and the gate then stops complaining about it",
      "criterion 1 is" not in out, out[:140])

# The block rules -- the exact failure being corrected.
code, out = s24("blocked", "--what", "E4", "--routes", "other-agent", "--reason", "no runtime")
check("S24 a block with no --tried is refused", code != 0, f"exit {code}")
check("S24 and the refusal says an absent capability is a hypothesis",
      "hypothesis" in out, out[:140])

code, out = s24("blocked", "--what", "E4", "--routes", "other-agent", "--reason", "purchased runtime absent",
                "--tried", "checked the catalogue for a local runner")
check("S24 a block that names the routes walked is accepted", code == 0,
      f"exit {code}: {out[:120]}")

code, out = s24("blocked", "--what", "E4", "--routes", "other-agent", "--reason", "purchased runtime absent",
                "--tried", "another route")
check("S24 the SAME block cannot be declared twice for the same reason", code != 0,
      f"exit {code}")
check("S24 and the refusal demands a different reason or a next action",
      "--next-action" in out, out[:160])

code, out = s24("blocked", "--what", "E4", "--routes", "other-agent", "--reason", "purchased runtime absent",
                "--tried", "third route",
                "--next-action", "run it via a local subagent instead")
check("S24 the same block continues when a next action is recorded", code == 0,
      f"exit {code}: {out[:120]}")

code, out = s24("blocked", "--what", "E5", "--routes", "other-agent", "--reason", "same as the route",
                "--tried", "same as the route")
check("S24 a reason that is also listed as a tried route is refused", code != 0,
      f"exit {code}")

# R0/R1 are exempt: the rule must not charge ceremony at the low rungs.
_s24b = pathlib.Path(tempfile.mkdtemp())


def s24b(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s24b)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s24b("init", "--rung", "R1", "--objective", "short run")
s24b("set-mode", "--mode", "inline", "--why", "one command", "--until", "done")
code, out = s24b("check")
check("S24 R1 is exempt from the acceptance gate",
      "no acceptance criteria" not in out, out[:140])

# --- S25: the capability dispatch gate, the mirror of the over-delegation rule --
#
# Each rule gets a case that proves it fires, and one case that proves the gate
# is not simply always-on. A check that reports nothing is indistinguishable from
# a check that works.

_s25 = pathlib.Path(tempfile.mkdtemp())


def s25(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s25)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


# A well-formed R2 run, so the dispatch rules are the only thing under test.
s25("init", "--rung", "R2", "--objective", "use a specialist",
     "--escalate-on", "the capability turns out to be wrong",
     "--de-escalate-on", "one invocation is enough")
s25("set-mode", "--mode", "delegate", "--why", "the catalogue has one",
     "--until", "it returns something usable")
s25("record", "--observation", "looked the capability up in the catalogue")
# The R2 work-unit rule (§26) requires capability and verify, so this fixture
# carries them. It did not when the rule was added, and the two `check` calls
# further down started failing with "rung R2 records no steps" -- the step was
# never opened. That was the gate working, not the test breaking: the fixture
# was a run working on an R2 unit without naming what did the work.
s25("step", "--doing", "invoke it", "--precondition", "it exists",
     "--expect", "an observation back", "--capability", "stock-analysis",
     "--verify", "record what came back")
s25("require", "--what", "the specialist's output is observed")
s25("satisfy", "--what", "the specialist's output is observed",
     "--evidence", "OBS-1")

code, out = s25("dispatch", "--for", "stock-analysis", "--state", "selected")
check("S25 a capability can be recorded as selected", code == 0,
      f"exit {code}: {out[:120]}")
code, out = s25("check")
check("S25 and a capability left at `selected` refuses the report", code != 0,
      f"exit {code}")
check("S25 and the refusal says it was described, not performed",
      "described rather than performed" in out, out[:160])
check("S25 and the refusal names the capability", "stock-analysis" in out,
      out[:160])

code, out = s25("dispatch", "--for", "stock-analysis", "--state", "invoked",
     "--brief", 'objective: check the ledger; input: the state file; constraints: read only; expected output: a verdict; success criteria: one of pass or fail; verification: test-run-state S25; available context: the dispatch ledger')
check("S25 the chain advances to invoked", code == 0, f"exit {code}: {out[:120]}")
code, out = s25("check")
check("S25 `invoked` is still not terminal", code != 0, f"exit {code}")

code, out = s25("dispatch", "--for", "stock-analysis", "--state", "observed",
     "--result-status", "completed", "--result", "the ledger is coherent")
check("S25 the chain reaches observed", code == 0, f"exit {code}: {out[:120]}")
code, out = s25("check")
check("S25 and once observed the gate stops complaining about it",
      "stock-analysis" not in out, out[:160])
check("S25 -- so a well-formed run still passes", code == 0,
      f"exit {code}: {out[:160]}")

code, out = s25("dispatch", "--for", "stock-analysis", "--state", "selected")
check("S25 the chain refuses to run backwards", code != 0, f"exit {code}")
check("S25 and says so as a rewrite of history",
      "cannot go back" in out, out[:160])

# NOT_INVOKED is not UNREACHABLE: the second needs proof the first does not.
code, out = s25("dispatch", "--for", "some-skill", "--state", "unreachable")
check("S25 `unreachable` with no route tried is refused", code != 0, f"exit {code}")
check("S25 and the refusal names the under-claiming failure",
      "under-claiming" in out, out[:160])
code, out = s25("dispatch", "--for", "some-skill", "--state", "unreachable",
                "--tried", "searched the catalogue by name, then by keyword")
check("S25 `unreachable` with a route tried is accepted", code == 0,
      f"exit {code}: {out[:120]}")

code, out = s25("dispatch", "--for", "another-skill", "--state", "skipped")
check("S25 `skipped` with no reason is refused", code != 0, f"exit {code}")
code, out = s25("dispatch", "--for", "another-skill", "--state", "skipped",
                "--why", "the task needs no specialisation")
check("S25 `skipped` with a reason is accepted", code == 0,
      f"exit {code}: {out[:120]}")

code, out = s25("dispatch", "--for", "third-skill", "--state", "verified",
     "--result-status", "completed", "--result", "it holds")
check("S25 `verified` with no evidence is refused", code != 0, f"exit {code}")

code, out = s25("check")
check("S25 the three terminal verdicts all pass the gate", code == 0,
      f"exit {code}: {out[:160]}")

# The gate must be a check, not a decorator: hand-edited state, which the write
# path cannot defend against, still has to fail.
_hand = state_of(str(_s25 / "run-state.json"))
_hand["dispatch"].append({"n": 9, "for": "hand-edited", "state": "unreachable",
                          "tried": [], "history": []})
(_s25 / "run-state.json").write_text(json.dumps(_hand), encoding="utf-8")
code, out = s25("check")
check("S25 a hand-edited unreachable with no routes is still refused", code != 0,
      f"exit {code}")
check("S25 and it names the distinction",
      "not-invoked and unreachable" in out, out[:200])

# R1 is exempt, as everything else in the gate is: the ladder exists so short
# runs are not charged for ceremony.
_s25b = pathlib.Path(tempfile.mkdtemp())


def s25b(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s25b)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s25b("init", "--rung", "R1", "--objective", "one command")
s25b("set-mode", "--mode", "inline", "--why", "one command", "--until", "done")
s25b("dispatch", "--for", "a-skill", "--state", "selected")
code, out = s25b("check")
check("S25 R1 is exempt from the dispatch gate", "described rather than performed"
      not in out, out[:160])

shutil.rmtree(_s25, ignore_errors=True)
shutil.rmtree(_s25b, ignore_errors=True)

# --- S26-S30: the process log, and the rule that it must agree with the state ---
#
# The log is the one narrative the user reads. Every other structure in this file
# is a record, and a record cannot assert -- which is why the dispatch chain and
# the criterion gate could be enforced, and why a prose log claiming a delegation
# that never happened could not. Section 24 names that as the failure and
# `cmd_log` is the gate for it.
#
# The three constants that made this possible (LOG_KINDS, STEP_FIELDS,
# COMPLETION_STATUSES) were already declared in run-state.py and read by nothing.
# That is the same defect as the missing `until` check one revision earlier: a
# vocabulary nobody consults constrains nobody, and the code said so by being
# written but never run.

_s26 = pathlib.Path(tempfile.mkdtemp())


def s26(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s26)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s26("init", "--rung", "R2", "--objective", "log the work",
     "--escalate-on", "a surprise", "--de-escalate-on", "it is simpler")

code, out = s26("log", "--kind", "receive", "--what", "objective received")
check("S26 a plain stage is logged", code == 0 and "P01" in out, f"exit {code}: {out[:160]}")

code, out = s26("log", "--kind", "not-a-stage", "--what", "x")
check("S26 an unknown kind is refused", code != 0, f"exit {code}")
check("S26 and it names the vocabulary", "is not one of" in out, out[:160])

code, out = s26("log", "--kind", "receive")
check("S26 a log entry with no content is refused", code != 0, f"exit {code}")

code, out = s26("log", "--kind", "delegate", "--what", "called the reviewer")
check("S26 a log claiming a delegation the ledger has not got is refused",
      code != 0, f"exit {code}")
check("S26 and it says the two disagree", "contradicts the state" in out
      or "there is no" in out, out[:200])

code, out = s26("log", "--kind", "verify", "--what", "read it back")
check("S26 a log claiming verification with nothing verified is refused",
      code != 0, f"exit {code}")
check("S26 and it names the received-vs-verified confusion",
      "RESULT RECEIVED" in out, out[:200])

code, out = s26("log", "--kind", "complete", "--what", "finished")
check("S26 a log claiming completion before `finish` ran is refused",
      code != 0, f"exit {code}")

# Substeps hang off a logged step, and the top-level count is unaffected by them.
s26("log", "--kind", "triage", "--what", "one unit")
s26("log", "--kind", "plan", "--what", "two parts")
code, out = s26("log", "--kind", "plan", "--what", "part b", "--under", "P03")
check("S26 a substep is numbered under its parent", "P03.1" in out, out[:160])
code, out = s26("log", "--kind", "plan", "--what", "part c", "--under", "P03")
check("S26 and a second substep increments", "P03.2" in out, out[:160])
code, out = s26("log", "--kind", "deliver", "--what", "reported")
check("S26 numbering continues past a substep rather than nesting under it",
      "P04" in out, out[:160])
code, out = s26("log", "--kind", "plan", "--what", "x", "--under", "P99")
check("S26 a substep under a step that does not exist is refused", code != 0,
      f"exit {code}")

# Now the ledger catches up, and the same entry is accepted.
s26("dispatch", "--for", "stock-analysis", "--state", "selected")
code, out = s26("log", "--kind", "delegate", "--what", "invoked the reviewer")
check("S26 the same entry is accepted once the ledger agrees", code != 0,
      f"still refused at `selected`; exit {code}")  # selected != invoked
s26("dispatch", "--for", "stock-analysis", "--state", "invoked",
      "--brief", 'objective: check the ledger; input: the state file; constraints: read only; expected output: a verdict; success criteria: one of pass or fail; verification: test-run-state S25; available context: the dispatch ledger')
code, out = s26("log", "--kind", "delegate", "--what", "invoked the reviewer")
check("S26 and passes at `invoked`", code == 0, f"exit {code}: {out[:160]}")

code, out = s26("log", "--list")
check("S26 the log lists in order", "P01" in out and "P03.1" in out, out[:300])

# The log must not be able to claim more than the ledger, even hand-edited.
_st = state_of(str(_s26 / "run-state.json"))
_st["log"].append({"n": "P99", "kind": "observed", "what": "fabricated",
                   "at": "x"})
(_s26 / "run-state.json").write_text(json.dumps(_st), encoding="utf-8")
code, out = s26("check")
check("S26 check catches a hand-edited log the write path would have refused",
      code != 0 and "P99" in out, f"exit {code}: {out[:200]}")

shutil.rmtree(_s26, ignore_errors=True)

# --- S31: the five fields of a work unit at R2, and the exemption below it ---

_s31 = pathlib.Path(tempfile.mkdtemp())


def s31(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s31)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s31("init", "--rung", "R2", "--objective", "five fields",
     "--escalate-on", "a surprise", "--de-escalate-on", "simpler")
code, out = s31("step", "--doing", "edit", "--precondition", "p", "--expect", "e")
check("S31 an R2 unit with only the three usual fields is refused", code != 0,
      f"exit {code}")
check("S31 and it names the two that get skipped", "--capability, --verify" in out,
      out[:200])
code, out = s31("step", "--doing", "edit", "--precondition", "p", "--expect", "e",
                "--capability", "inline", "--verify", "read the file back")
check("S31 and is accepted with all five", code == 0, f"exit {code}: {out[:160]}")
_st = state_of(str(_s31 / "run-state.json"))
check("S31 and both fields are stored, not just accepted",
      _st["steps"][0].get("capability") == "inline"
      and _st["steps"][0].get("verify") == "read the file back",
      json.dumps(_st["steps"][0]))

_s31b = pathlib.Path(tempfile.mkdtemp())


def s31b(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s31b)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s31b("init", "--rung", "R1", "--objective", "three fields is enough here")
code, out = s31b("step", "--doing", "edit", "--precondition", "p", "--expect", "e")
check("S31 R1 is exempt, where a unit is a sentence and five fields is ceremony",
      code == 0, f"exit {code}: {out[:160]}")

shutil.rmtree(_s31, ignore_errors=True)
shutil.rmtree(_s31b, ignore_errors=True)

# --- S32-S33: the completion gate, which is the whole of section 35 ---

_s32 = pathlib.Path(tempfile.mkdtemp())


def s32(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s32)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


code, out = s32("init", "--rung", "R2", "--objective", "finish honestly",
                "--escalate-on", "a surprise", "--de-escalate-on", "simpler",
                "--why", "one unit", "--until", "it is closed")
check("S32 the fixture starts", code == 0, f"exit {code}: {out[:160]}")

code, out = s32("finish", "--status", "completed")
check("S32 `completed` is refused on a run with no criteria at all", code != 0,
      f"exit {code}")
check("S32 and it says why: a run with no criterion stops when the work looks done",
      "acceptance criterion" in out, out[:300])

s32("step", "--doing", "edit", "--precondition", "p", "--expect", "e",
     "--capability", "inline", "--verify", "read it back")
code, out = s32("finish", "--status", "completed")
check("S32 and refused while the work unit is still open", code != 0, f"exit {code}")
check("S32 naming the open unit", "still open" in out, out[:300])

s32("step", "--close", "--outcome", "wrote it")
s32("require", "--what", "the file has the new line")
s32("record", "--observation", "read the file back, 42 lines")
code, out = s32("finish", "--status", "completed")
check("S32 and refused while the criterion is open", code != 0, f"exit {code}")

s32("satisfy", "--what", "the file has the new line", "--evidence", "OBS-1")
code, out = s32("finish", "--status", "completed")
check("S32 and accepted once every condition holds", code == 0,
      f"exit {code}: {out[:200]}")
check("S32 and it names which condition of section 55 that is",
      "condition A" in out, out[:200])

s32("log", "--kind", "receive", "--what", "the objective")
s32("log", "--kind", "deliver", "--what", "delivered")
code, out = s32("log", "--kind", "complete", "--what", "delivered")
check("S32 and only then may the log claim completion", code == 0,
      f"exit {code}: {out[:200]}")

code, out = s32("finish", "--status", "failed", "--attempted", "tried it")
check("S32 a second ending is refused", code != 0, f"exit {code}")
code, out = s32("finish", "--status", "failed", "--attempted", "tried it",
                "--replace", "--why", "a criterion was reopened by a later check")
check("S32 unless the change is paid for with a reason", code == 0,
      f"exit {code}: {out[:200]}")

shutil.rmtree(_s32, ignore_errors=True)

_s33 = pathlib.Path(tempfile.mkdtemp())


def s33(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s33)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s33("init", "--rung", "R2", "--objective", "the other three statuses",
     "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u")
check("S33 the fixture starts", s33("show")[0] == 0)

code, out = s33("finish", "--status", "maybe")
check("S33 a status outside the four is refused", code != 0, f"exit {code}")

code, out = s33("finish", "--status", "partial", "--remaining", "unit 2")
check("S33 `partial` is refused when no work unit was ever opened", code != 0,
      f"exit {code}")
s33("step", "--doing", "unit 1", "--precondition", "p", "--expect", "e",
     "--capability", "inline", "--verify", "v")
code, out = s33("finish", "--status", "partial")
check("S33 `partial` without --remaining is refused", code != 0, f"exit {code}")
check("S33 and says why: a partial with no remainder is a complete one",
      "remainder" in out, out[:200])
code, out = s33("finish", "--status", "partial", "--remaining", "unit 2",
                "--next-action", "run unit 2")
check("S33 and accepted with the remainder named", code == 0,
      f"exit {code}: {out[:200]}")

_s33b = pathlib.Path(tempfile.mkdtemp())


def s33b(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s33b)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s33b("init", "--rung", "R2", "--objective", "blocked or failed",
      "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u")
s33b("step", "--doing", "unit 1", "--precondition", "p", "--expect", "e",
      "--capability", "inline", "--verify", "v")
code, out = s33b("finish", "--status", "blocked")
check("S33 `blocked` is refused without routes actually walked", code != 0,
      f"exit {code}")
check("S33 and names the five-term conjunction", "no reachable capability" in out,
      out[:300])
s33b("blocked", "--what", "the exporter", "--routes", "other-agent", "--reason", "no writer is installed",
      "--tried", "searched the catalogue", "--tried", "asked the runtime")
code, out = s33b("finish", "--status", "blocked")
check("S33 and accepted once a block with routes exists", code == 0,
      f"exit {code}: {out[:200]}")

_s33c = pathlib.Path(tempfile.mkdtemp())


def s33c(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s33c)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s33c("init", "--rung", "R2", "--objective", "failed is not blocked",
      "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u")
s33c("step", "--doing", "unit 1", "--precondition", "p", "--expect", "e",
      "--capability", "inline", "--verify", "v")
code, out = s33c("finish", "--status", "failed")
check("S33 `failed` without --attempted is refused", code != 0, f"exit {code}")
check("S33 and says why the two are different claims",
      "different claim" in out, out[:300])
code, out = s33c("finish", "--status", "failed", "--attempted", "ran it twice",
                 "--recovery", "tried the other writer", "--next-action", "port it")
check("S33 and accepted with the attempt named", code == 0,
      f"exit {code}: {out[:200]}")

shutil.rmtree(_s33, ignore_errors=True)
shutil.rmtree(_s33b, ignore_errors=True)
shutil.rmtree(_s33c, ignore_errors=True)

# --- S34-S37: the host as the second term in the effort gate ------------------
#
# The rung ladder answered how hard the task is and never answered what the model
# can carry. This repository's own research says that omission is measurable in
# both directions: over-prescription degrades current-generation output, and a weak
# host does not reliably trigger the rules it is given. `references/triage.md` named
# the gap and then said "re-calibrate", which is not something a run can execute.
#
# The gates are asymmetric on purpose. Upward past the ceiling needs a stated
# reason, because a weak host given more procedure produces more shallow
# decisions. Downward on a frontier host needs one too, because under-investment
# is the failure that arrives silently -- and a capable model is the one least
# able to notice it, since capability and budget sense are barely correlated.

_s34 = pathlib.Path(tempfile.mkdtemp())


def s34(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s34)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


def _wellformed(dir_: pathlib.Path, *extra: str) -> None:
    """A run that clears every other gate, so only the host rules are under test."""
    s34("step", "--doing", "d", "--precondition", "p", "--expect", "e",
         "--capability", "c", "--verify", "v")
    s34("step", "--close", "--outcome", "o")
    s34("require", "--what", "c1")
    s34("record", "--observation", "o")
    s34("satisfy", "--what", "c1", "--evidence", "OBS-1")


check("S34 a host is recorded at init",
      s34("init", "--rung", "R2", "--host", "small", "--objective", "o",
          "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w",
          "--until", "u")[0] == 0)
_wellformed(_s34)
code, out = s34("check")
check("S34 a small host at its ceiling passes", code == 0, f"exit {code}: {out[:200]}")

code, out = s34("init", "--rung", "R3", "--host", "small", "--objective", "o",
                "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w",
                "--until", "u", "--force")
check("S34 and R3 on a small host is accepted at the parser", code == 0,
      f"exit {code}: {out[:160]}")
_wellformed(_s34)
code, out = s34("check")
check("S34 but check refuses it, for want of a reason", code != 0, f"exit {code}")
check("S34 and it says what the failure looks like from outside",
      "shallow" in out, out[:300])

s34("init", "--rung", "R3", "--host", "small", "--exceeds-ceiling",
     "one focused hard call, which is what a small host is good at",
     "--objective", "o", "--escalate-on", "a", "--de-escalate-on", "b",
     "--why", "w", "--until", "u", "--force")
_wellformed(_s34)
code, out = s34("check")
check("S34 and a stated reason lets it through", code == 0, f"exit {code}: {out[:200]}")

code, out = s34("set-host", "--host", "mid")
check("S34 set-host without a reason is refused", code != 0, f"exit {code}")
code, out = s34("set-host", "--host", "mid",
                "--why", "the router is small, the executor is not")
check("S34 and with one is accepted", code == 0, f"exit {code}: {out[:160]}")
_st = state_of(str(_s34 / "run-state.json"))
check("S34 and the change is kept with its reason",
      _st.get("host") == "mid"
      and _st["host_history"][-1].get("why", "").startswith("the router"),
      json.dumps(_st.get("host_history")))

shutil.rmtree(_s34, ignore_errors=True)

_s35 = pathlib.Path(tempfile.mkdtemp())


def s35(*argv: str) -> tuple[int, str]:
    import io
    old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
    buf = io.StringIO()
    sys.argv = ["run-state.py", "--state-dir", str(_s35)] + list(argv)
    sys.stderr = sys.stdout = buf
    try:
        try:
            code = rs.main()
        except SystemExit as e:
            code = int(e.code or 0)
    finally:
        sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
    return code, buf.getvalue()


s35("init", "--rung", "R3", "--host", "frontier", "--objective", "o",
     "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u")
code, out = s35("set-rung", "--rung", "R1")
check("S35 de-escalating a frontier host is allowed", code == 0,
      f"exit {code}: {out[:160]}")
code, out = s35("check")
check("S35 but check refuses it with no reason recorded", code != 0, f"exit {code}")
check("S35 and it names the failure as under-investment, not over-verification",
      "under-investment" in out, out[:300])
check("S35 and it says why the capable model cannot catch it itself",
      "barely correlated" in out, out[:300])

s35("init", "--rung", "R3", "--host", "small", "--objective", "o",
     "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u",
     "--force")
s35("step", "--doing", "d", "--precondition", "p", "--expect", "e",
     "--capability", "c", "--verify", "v")
s35("step", "--close", "--outcome", "o")
s35("require", "--what", "c1")
s35("record", "--observation", "o")
s35("satisfy", "--what", "c1", "--evidence", "OBS-1")
code, out = s35("set-rung", "--rung", "R1")
check("S35 and the same drop on a small host is free", code == 0,
      f"exit {code}: {out[:160]}")
code, out = s35("check")
check("S35 because de-escalation is the direction most often missing, and on a "
      "weak host it is usually right", code == 0, f"exit {code}: {out[:240]}")

# The gate must survive a hand-edited host, the way every other one here does.
_st = state_of(str(_s35 / "run-state.json"))
_st["host"] = "banana"
(_s35 / "run-state.json").write_text(json.dumps(_st), encoding="utf-8")
code, out = s35("check")
check("S35 an out-of-vocabulary host in the state file is refused", code != 0,
      f"exit {code}")
check("S35 and it says the gate was skipped rather than that the host is odd",
      "unrecognised one means the gate was skipped" in out, out[:240])

shutil.rmtree(_s35, ignore_errors=True)

# --- S36: the defect this whole file keeps finding, aimed at this file ---------
#
# Three times now a constant has been written in run-state.py and read by
# nothing: `until`, then LOG_KINDS/STEP_FIELDS/COMPLETION_STATUSES, then
# HOST_FLOOR -- which was uniform at R0 across all three host tiers, so it could
# never fire, and is worse than dead code because a reader cannot tell a
# mechanism that expresses no judgement from one that does.
#
# A test that only covers the gates cannot catch this: a dead constant breaks
# nothing. So this one reads the module and fails on any name that is assigned a
# module-level constant and never read again. It is a lint, in a test suite,
# because that is the only place in this repository that runs on every change.

_DECLARED = re.compile(r"^([A-Z][A-Z0-9_]*)\s*(?::[^=]+)?=", re.M)


def _unused_module_constants(path: pathlib.Path) -> list[str]:
    """Module-level constants that are assigned and never read again.

    The whole file is scanned, not just the part above `__main__`. The first
    version excluded the `__main__` block on the assumption that nothing
    interesting lived there, and then failed to notice a dead constant appended
    after it -- which is to say the check for "a gate that cannot fail" could
    not fail either. A negative test on a negative test, which is the only kind
    worth having.

    `^` anchors to a line start, so an indented name inside a function does not
    match: only genuinely module-level bindings are considered.
    """
    body = path.read_text(encoding="utf-8")
    unused = []
    for name in dict.fromkeys(_DECLARED.findall(body)):
        # One hit is the assignment; anything beyond that is a read.
        if len(re.findall(rf"\b{re.escape(name)}\b", body)) < 2:
            unused.append(name)
    return unused


# Both files, not just the one the defect was found in. `check-spec.py` grew a
# constant -- PROSE_SECTIONS -- in the same session as the fix, and a lint that
# covers only the file it was written for stops covering the moment the pattern
# appears somewhere else. That is the same class of failure the lint exists to
# catch, one level up.
_LINTED = ("run-state.py", "check-spec.py")
_unused = {n: _unused_module_constants(HERE / n) for n in _LINTED}
check("S36 no constant in the enforcement tools is declared and read by nothing",
      not any(_unused.values()),
      "; ".join(f"{n}: {', '.join(u)}" for n, u in _unused.items() if u))

# --- S37-S42: the sections that were prose and are now commands --------------
#
# Thirty-seven rows of check-spec were prose-only. These are the ones where a
# command was possible without becoming a gate that fires on vocabulary: §5's
# executable action, §15/§16's context request and gap, §18/§19's state shape and
# orphans, §25's state machine, §28/§44's recovery class, §30's route list, §11/
# §12/§34/§42's handover contracts, §38's over-delegation, §40's synthesis, §45's
# self-evaluation, §47's delivery sections.
#
# Each is a refusal, not a reminder, and every refusal below was run before the
# assertion was written. That is the S36 lesson applied throughout: a test only
# watched passing has not been tested.

BRIEF_ALL = ("objective: check it; input: the state file; constraints: read only; "
             "expected output: a verdict; success criteria: pass or fail; "
             "verification: the test suite; available context: this file")


def _fresh(tag: str, rung: str = "R2", host: str = "mid", with_step: bool | None = None):
    """A throwaway state dir plus a runner for it, brought to a state `check` likes.

    One dir per case, never shared: the gates under test all mutate the same file,
    so sharing would let one case satisfy another's precondition. A step and a
    criterion are opened by default at R2+, because R2 refuses a run without them
    and every case below is about a *different* gate -- a fixture that fails an
    unrelated gate cannot tell you whether the gate under test works.
    """
    d = pathlib.Path(tempfile.mkdtemp())
    _DIRS.append(d)
    if with_step is None:
        with_step = rung in ("R2", "R3", "R4")

    def run(*argv: str) -> tuple[int, str]:
        import io
        old_argv, old_err, old_out = sys.argv, sys.stderr, sys.stdout
        buf = io.StringIO()
        sys.argv = ["run-state.py", "--state-dir", str(d)] + list(argv)
        sys.stderr = sys.stdout = buf
        try:
            try:
                code = rs.main()
            except SystemExit as e:
                code = int(e.code or 0)
        finally:
            sys.argv, sys.stderr, sys.stdout = old_argv, old_err, old_out
        return code, buf.getvalue()

    run("init", "--rung", rung, "--host", host, "--objective", tag,
        "--escalate-on", "a", "--de-escalate-on", "b", "--why", "w", "--until", "u")
    if with_step:
        run("step", "--doing", "d", "--precondition", "p", "--expect", "e",
            "--capability", "inline", "--verify", "v")
        run("step", "--close", "--outcome", "o")
        run("require", "--what", "c1")
        run("record", "--observation", "o")
        run("satisfy", "--what", "c1", "--evidence", "OBS-1")
    return d, run


_DIRS: list = []
d37, s37 = _fresh("S37")
code, out = s37("check")
check("S37 §18 a clean run reports its §18 field coverage", code == 0
      and "of §18's field list is kept here" in out, f"exit {code}: {out[:200]}")
check("S37 and the unmapped count is stated rather than implied",
      "have no home in this tool" in out, out[:200])

# §5
_, s37 = _fresh("S37 §5", rung="R1")
s37("decide", "--question", "which mode", "--selected", "delegate",
     "--rejected", "inline is free", "--rationale", "x",
     "--confidence", "high in X", "--recovery", "if Y", "--evidence", "none")
code, out = s37("check")
check("S37 §5 a one-word `selected` is refused: it names a mode, not an action",
      code != 0 and "not an executable action" in out, f"exit {code}: {out[:200]}")
_, s37 = _fresh("S37 §5b", rung="R1")
s37("decide", "--question", "which mode", "--selected", "invoke the reviewer",
     "--rejected", "inline is free", "--rationale", "x",
     "--confidence", "high in X", "--recovery", "if Y", "--evidence", "none")
check("S37 §5 and a real action passes", s37("check")[0] == 0, "refused a real action")

# §15 / §16
_, s37 = _fresh("S37 §15")
s37("context", "--ref", "references/foo.md", "--level", "C3", "--why", "needed")
code, out = s37("check")
check("S37 §15 a context record with no `enables` and no `scope` is refused",
      code != 0 and "which action it enables" in out, f"exit {code}: {out[:200]}")
_, s37 = _fresh("S37 §15b")
s37("context", "--ref", "references/foo.md", "--level", "C3", "--why", "needed",
     "--enables", "decide the delegation", "--scope", "the routing section")
check("S37 §15 and all four parts passes", s37("check")[0] == 0, "refused a full request")

_, s37 = _fresh("S37 §16")
s37("context", "--gap", "the auth module")
code, out = s37("check")
check("S37 §16 an open context gap refuses the report at R2+", code != 0
      and "context gap" in out, f"exit {code}: {out[:200]}")
s37("context", "--closed", "the auth module", "--why", "read it")
check("S37 §16 and closing it clears the gate", s37("check")[0] == 0, "still refused")
code, out = s37("context", "--closed", "a gap that was never opened")
check("S37 §16 and closing a gap that was never opened is refused", code != 0,
      f"exit {code}")

# §25: the state machine as an order
_, s37 = _fresh("S37 §25", rung="R1")
code, out = s37("log", "--kind", "deliver", "--what", "x")
check("S37 §25 a log may not open on `deliver`", code != 0
      and "state machine" in out, f"exit {code}: {out[:200]}")
s37("log", "--kind", "plan", "--what", "p")
s37("log", "--kind", "execute-inline", "--what", "e")
check("S37 §25 and plan -> execute-inline is a legal path",
      s37("log", "--kind", "deliver", "--what", "x")[0] == 0, "refused a legal path")

# §28 / §44
_, s37 = _fresh("S37 §28")
code, out = s37("recover", "--class", "vibes", "--action", "read the log",
                "--result", "it worked")
check("S37 §28 a failure class outside the nine is refused", code != 0,
      f"exit {code}")
code, out = s37("recover", "--class", "tool",
                "--action", "bound to port 0 and re-ran the suite")
check("S37 §44 a recovery with no result is refused", code != 0
      and "not been evaluated" in out, f"exit {code}: {out[:200]}")
code, out = s37("recover", "--class", "tool", "--action", "recovered", "--result", "x")
check("S37 §44 and a one-word action is refused as a category", code != 0,
      f"exit {code}")
check("S37 §28 and a real recovery is recorded",
      s37("recover", "--class", "tool", "--action", "bound to port 0 and re-ran",
          "--result", "it bound")[0] == 0, "refused a real recovery")

# §30
_, s37 = _fresh("S37 §30")
code, out = s37("blocked", "--what", "x", "--reason", "y", "--tried", "tried some things")
check("S37 §30 a block with prose and no named route is refused", code != 0
      and "--routes is required" in out, f"exit {code}: {out[:200]}")
check("S37 §30 and a block naming routes is accepted",
      s37("blocked", "--what", "x", "--reason", "y", "--tried", "searched the catalogue",
          "--routes", "other-agent")[0] == 0, "refused a named route")

# §11 / §12
_, s37 = _fresh("S37 §11")
s37("dispatch", "--for", "a-skill", "--state", "selected")
code, out = s37("dispatch", "--for", "a-skill", "--state", "invoked")
check("S37 §11 `invoked` with no brief is refused", code != 0
      and "needs --brief" in out, f"exit {code}: {out[:200]}")
code, out = s37("dispatch", "--for", "a-skill", "--state", "invoked",
                "--brief", "objective: check it; input: the file")
check("S37 §11 and a brief naming three of the seven is refused", code != 0
      and "does not name" in out, f"exit {code}: {out[:200]}")
check("S37 §11 and all seven is accepted",
      s37("dispatch", "--for", "a-skill", "--state", "invoked",
          "--brief", BRIEF_ALL)[0] == 0, "refused a full brief")
code, out = s37("dispatch", "--for", "a-skill", "--state", "observed")
check("S37 §12 `observed` with no result status is refused", code != 0
      and "--result-status" in out, f"exit {code}: {out[:200]}")
check("S37 §12 and a status with no result is refused",
      s37("dispatch", "--for", "a-skill", "--state", "observed",
          "--result-status", "completed")[0] != 0, "accepted an empty result")
check("S37 §12 and both is accepted",
      s37("dispatch", "--for", "a-skill", "--state", "observed",
          "--result-status", "completed", "--result", "the ledger is coherent")[0] == 0,
      "refused a complete result")

# §38
d38, s37 = _fresh("S37 §38", with_step=True)
s37("dispatch", "--for", "a-skill", "--state", "selected")
s37("dispatch", "--for", "a-skill", "--state", "invoked", "--brief", BRIEF_ALL)
s37("dispatch", "--for", "a-skill", "--state", "observed",
     "--result-status", "completed", "--result", "it returned")
code, out = s37("check")
check("S37 §38 a dispatched-and-observed capability with every unit inline is refused",
      code != 0 and "isolation" in out, f"exit {code}: {out[:200]}")
_st = state_of(str(d38 / "run-state.json"))
_st["steps"][0]["capability"] = "a-skill"
(d38 / "run-state.json").write_text(json.dumps(_st), encoding="utf-8")
check("S37 §38 and naming the capability on the unit clears it",
      s37("check")[0] == 0, "still refused after naming the capability")

# §45
_, s37 = _fresh("S37 §45", rung="R1")
_yes = [f"--answer={q}=yes" for q in rs.SELF_EVAL_QUESTIONS]
code, out = s37("reflect", *_yes)
check("S37 §45 fifteen answers and no criticism is refused", code != 0
      and "worth nothing" in out, f"exit {code}: {out[:200]}")
_mixed = [f"--answer={q}=yes" for q in rs.SELF_EVAL_QUESTIONS[:-1]] + \
         [f"--answer={rs.SELF_EVAL_QUESTIONS[-1]}=no, the fixtures have no builder "
          f"so validate-skills --strict cannot pass and that is pre-existing"]
# This used to assert that a bare `no` among fourteen `yes` was enough. It was
# wrong, and it was the same wrongness the predicate below used: a verdict is not
# a finding. The assertion now carries a finding, and the bare-verdict case is
# asserted separately below as a refusal.
check("S37 §45 and one answer naming a fault is accepted", s37("reflect", *_mixed)[0] == 0,
      "refused an honest reflection")
code, out = s37("reflect", "--answer=did we solve the task=yes")
check("S37 §45 and fourteen of fifteen is refused", code != 0
      and "unanswered" in out, f"exit {code}: {out[:200]}")
code, out = s37("reflect", "--answer=did we unnecessar=yes")
check("S37 §45 and a prefix shared by two questions is refused rather than guessed",
      code != 0 and "cannot" in out and "identify one" in out,
      f"exit {code}: {out[:200]}")

# §47
_, s37 = _fresh("S37 §47", rung="R1")
_good = ("## Process\nP01 -- RECEIVE\n\n## Result\nit worked\n\n"
         "## Verification\nran the tests\n\n## State\ncompleted\n\n"
         "## Remaining\nNone\n")
_good_f = pathlib.Path(tempfile.mkdtemp()) / "d.md"
_good_f.write_text(_good, encoding="utf-8")
code, out = s37("audit", str(_good_f))
check("S37 §47 a delivery carrying all five sections is clean", code == 0,
      f"exit {code}: {out[:200]}")
_bad_f = pathlib.Path(tempfile.mkdtemp()) / "d.md"
_bad_f.write_text("## Result\nit worked\n", encoding="utf-8")
code, out = s37("audit", str(_bad_f))
check("S37 §47 and one missing them all is refused", code != 0
      and "Process" in out, f"exit {code}: {out[:200]}")
check("S37 §47 and --trivially exempts a short delivery",
      s37("audit", str(_bad_f), "--trivially")[0] == 0, "--trivially did not exempt")

# The vocabulary sizes, which are the spec's own counts.
check("S37 §45 the question list is all fifteen", len(rs.SELF_EVAL_QUESTIONS) == 15,
      str(len(rs.SELF_EVAL_QUESTIONS)))
check("S37 §30 the route list is fifteen long", len(rs.ROUTES) == 15,
      str(len(rs.ROUTES)))
check("S37 §28 the failure classes are nine", len(rs.FAILURE_CLASSES) == 9,
      str(len(rs.FAILURE_CLASSES)))
check("S37 §11 the brief has seven fields", len(rs.BRIEF_FIELDS) == 7,
      str(len(rs.BRIEF_FIELDS)))
check("S37 §47 the delivery sections are five", len(rs.DELIVERY_SECTIONS) == 5,
      str(len(rs.DELIVERY_SECTIONS)))
check("S37 §18 every mapped field resolves at most one level, so _at can walk it",
      all(path is None or path.count(".") <= 1 for _, path in rs.RUNSTATE_FIELDS),
      "a deeper path would not resolve")

# The route list is written down in `references/completion-law.md` and drawn on by
# `blocked --routes`. Those are two artefacts, and the claim in both of them is
# that they cannot drift -- which is only true if something checks. This is that
# something: the prose table is parsed and held equal, name for name and in
# order. It is a text-to-constant binding, not a doc review, and it fails the
# moment somebody reorders a row for readability.
_LAW = HERE.parent / "references" / "completion-law.md"
_law_txt = _LAW.read_text(encoding="utf-8")
_law_routes = re.findall(r"^\|\s*(\d+)\s*\|\s*`([a-z-]+)`\s*\|", _law_txt, re.M)
check("S37 §30 the route table in completion-law.md is fifteen long",
      len(_law_routes) == 15, f"found {len(_law_routes)}")
check("S37 §30 the route table is numbered 1..15 without a gap",
      [int(n) for n, _ in _law_routes] == list(range(1, 16)),
      str([n for n, _ in _law_routes]))
check("S37 §30 the route table and ROUTES hold the same names in the same order",
      tuple(name for _, name in _law_routes) == tuple(rs.ROUTES),
      f"law={[n for _, n in _law_routes]} routes={list(rs.ROUTES)}")

# §45's criticism floor, as a property of the predicate rather than as one
# fifteen-answer fixture. The version this replaces compared the whole answer
# against a closed list of bare verdicts, which accepted fifteen bare "no"s --
# fifteen verdicts and not one finding, the precise failure the gate exists to
# prevent -- while refusing a real one that happened to open with "No, and here
# is the fault". Every case below is one that gate got wrong in some direction.
for _a, _want, _why in (
    ("no", False, "a bare verdict is a label, not a finding"),
    ("No.", False, "punctuation does not make it a finding"),
    ("none", False, "same"),
    ("n/a", False, "same"),
    ("false", False, "same"),
    ("not", False, "same"),
    ("NO", False, "case is not a signal"),
    ("nothing to report here at all, everything was fine", False,
     "'nothing' negates the finding, not the verdict"),
    ("nobody did anything wrong with any of the checks in this run", False,
     "same, and it is longer than any finding"),
    ("Everything was fine and I would do it the same way again", False,
     "a favourable review"),
    ("", False, "empty"),
    ("   ", False, "whitespace"),
    ("yes", False, "a positive verdict"),
    ("Yes, but fine", False, "a concession that says nothing"),
    ("Yes, but it worked", False, "same"),
    ("Yes, however", False, "a marker with nothing after it"),
    ("nothing else to add, the run was clean end to end", False,
     "'nothing else' is a favourable review, not a finding"),
    ("Yes, the outcome was nothing like what I expected and the plan was stale",
     False, "'nothing' inside a sentence is not a front non-finding"),
    ("No, the conformance table could be deflated silently and nothing tested it",
     True, "negation plus a finding, and 'nothing' does not hijack it"),
    ("Partly. The gates are real, the measure of them was not", True,
     "a partial admission is a finding"),
    # A finding need not open the sentence. These four are the shape an honest
    # self-review actually takes, because most of what a run did was fine, and the
    # floor that requires a front negation refuses every one of them.
    ("Yes, but the route list is in three files and one does not contain it", True,
     "a concession behind 'yes' is still a finding"),
    ("Yes, however the verification was insufficient because the count was self-reported",
     True, "'however' is a concession"),
    ("Yes, although it passed, the gate that failed was the one I never tested",
     True, "'although' is a concession"),
    ("Yes, I under-delegated: eight files were hand-written in a single pass", True,
     "a concession need not be a conjunction"),
    ("Yes, I re-read SKILL.md five times when one read of 597 lines was available",
     False, "a fault with no marker, and it is still not read as one"),
):
    check(f"S37 §45 criticism floor: {_why}", rs._names_a_finding(_a) is _want,
          f"{_a!r} -> {rs._names_a_finding(_a)}")

# And the end-to-end shape: fifteen bare "no"s must be refused, because that is
# what fifteen bare "no"s are. This is the assertion the old predicate passed.
_, s45 = _fresh("S37 §45 verdicts", rung="R1")
_v = [f"--answer={q}=no" for q in rs.SELF_EVAL_QUESTIONS]
check("S37 §45 fifteen bare verdicts are refused: no findings among them",
      s45("reflect", *_v)[0] != 0, "fifteen 'no' was accepted as fifteen findings")
_fault = (f"--answer={rs.SELF_EVAL_QUESTIONS[6]}=No, the conformance table could "
          f"be deflated silently and nothing tested that it could not")
_mixed = _v[:6] + [_fault] + _v[7:]
check("S37 §45 and one of them naming a fault is enough",
      s45("reflect", *_mixed)[0] == 0, "a real finding was still refused")
# The same run, with the finding written the way an honest review writes it --
# positive first, concession after -- because that is the shape the front-anchored
# rule refused, and a rule that only accepts a contrived negative is a rule that
# shapes the output rather than reading it.
_concessive = [f"--answer={q}=yes" for q in rs.SELF_EVAL_QUESTIONS[:-1]] + [
    f"--answer={rs.SELF_EVAL_QUESTIONS[-1]}=Yes, but the fixtures have no builder "
    f"so validate-skills --strict cannot pass and that is pre-existing"]
check("S37 §45 and a finding behind 'yes, but' is accepted too",
      s37("reflect", *_concessive)[0] == 0,
      "the floor only reads a front negation")

for _d in _DIRS:
    shutil.rmtree(_d, ignore_errors=True)

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
