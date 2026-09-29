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
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
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
    "schema_version": 3, "run_id": "T", "started": "now", "objective": "o",
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
               "at": "now", "closed_at": "now"}],
    "context": {"loaded": [], "dropped": []},
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
    st["decisions"] = [{"question": "q", "selected": "s", "rejected": "r",
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

d, sp = write_state({**BASE, "decisions": [{"question": "q", "selected": "s",
                                           "rejected": "", "recovery": ""}]})
code, out = cli("--state-dir", d, "check")
check("S12 a decision with no rejected and no recovery still fails", code == 1,
      f"exit {code}")

# A well-formed state must pass, or every assertion above is vacuous.
d, sp = write_state({
    **BASE, "rung": "R2",
    "rung_triggers": {"escalate_on": "a tool disagrees",
                      "de_escalate_on": "the first attempt worked"},
    "decisions": [{"question": "q", "selected": "s", "rejected": "r",
                   "recovery": "v", "evidence": ["OBS-1"]}],
    "observations": [{"id": "OBS-1", "text": "t"}],
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
      'DEFAULT_DIR = ".memory"' in _src, "DEFAULT_DIR is not .memory")
check("S23 and the legacy directory is still recognised for migration",
      'LEGACY_DIR = ".ultimate-dev"' in _src, "LEGACY_DIR missing")

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
