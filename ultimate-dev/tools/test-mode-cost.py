#!/usr/bin/env python3
"""Self-test for measure-mode-cost.py.

The cost model is the entire justification for the four coordination modes, and
it had no measurement behind it: three documents asserted it, `metrics.md`
recorded token efficiency as unmeasurable, and `run-pilot.py` had no counter. The
only output `budget-system.md` permits is the word "unmeasured", which makes the
claim unfalsifiable by construction.

So the tool that measures it has three ways to lie, and each is asserted here:

  C1  it reports a number for a capability kind it found nothing of   -> must refuse
  C2  it prints 0 where the honest answer is "not measured"            -> must print null
  C3  it reports the four modes in an order the mechanism does not
      support, which would be a more authoritative-looking lie

C1 is the same shape as the workflow-auth checker's original bug: a scanner that
examines nothing and prints a confident table. C2 is the one this repository
keeps making -- a suspiciously perfect zero read as a measurement. C3 is the
reason the mode table carries a location for every figure: a byte count with no
statement of *whose* context it lands in cannot order the modes at all.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE / "measure-mode-cost.py"

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  pass  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        FAILURES.append(label)


spec = importlib.util.spec_from_file_location("mmc", TOOL)
mmc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mmc)

# ---- C1: an empty tree must be refused, not tabulated.
empty = pathlib.Path(tempfile.mkdtemp())
try:
    (empty / "skills").mkdir()
    (empty / "agents").mkdir()
    (empty / "tools").mkdir()
    # The tool anchors ROOT to its own location -- `parent.parent` of the file --
    # so running the real one would measure the real tree no matter what cwd is.
    # Point a COPY at the empty tree instead, which is the only way to reach the
    # "measured nothing" branch.
    copied = empty / "tree" / "ultimate-dev" / "tools" / "measure-mode-cost.py"
    copied.parent.mkdir(parents=True)
    shutil.copy(TOOL, copied)
    proc = subprocess.run([sys.executable, str(copied), "--json"],
                          capture_output=True, text=True,
                          env={"PATH": "/usr/bin:/bin", "HOME": str(empty)})
    check("C1 an empty tree is refused, not tabulated",
          proc.returncode != 0, f"exit {proc.returncode}")
    # Combined, because which stream a tool uses is not part of its contract
    # and asserting on one of them makes this a test of the print statement.
    said = (proc.stdout or "") + (proc.stderr or "")
    check("C1 and it says what it expected", "measured nothing" in said,
          f"exit {proc.returncode}, said={said[:130]!r}")
finally:
    shutil.rmtree(empty, ignore_errors=True)

# ---- the real tree produces real numbers
measurements = [
    mmc.summarise("tool", mmc.tool_costs(), False, ""),
    mmc.summarise("sub-skill", mmc.skill_costs(), True, ""),
    mmc.summarise("role", mmc.role_costs(), False, ""),
]
for m in measurements:
    check(f"{m['kind']}: found capabilities", m["n"] > 0, f"n={m['n']}")
    check(f"{m['kind']}: median is positive, not zero",
          (m.get("bytes_median") or 0) > 0, str(m.get("bytes_median")))

# ---- C2: unmeasured is null, never 0
proc = subprocess.run([sys.executable, str(TOOL), "--json"],
                      capture_output=True, text=True)
check("the tool runs on the real tree", proc.returncode == 0, proc.stderr[:140])
payload = json.loads(proc.stdout)
nm = payload["not_measured"]
for key in ("tokens", "currency", "cost_per_outcome"):
    check(f"C2 {key} is null, not 0", nm[key] is None, repr(nm[key]))
check("C2 and the reason is given", len(nm["why"]) > 40, nm["why"][:80])

# ---- C3: every mode figure carries a location
for m in payload["modes"]:
    check(f"C3 {m['mode']}: a byte count is never reported without a location",
          m.get("context_cost_location") is not None, str(m)[:120])
    if m.get("context_cost_median_bytes") is not None:
        check(f"C3 {m['mode']}: isolated is stated",
              isinstance(m.get("isolated"), bool), str(m.get("isolated")))

# ---- the structural claim the whole tool exists to support
check("inline is the only mode with zero context cost",
      [m["context_cost_median_bytes"] for m in payload["modes"] if m["mode"] == "inline"] == [0])
check("every non-inline mode is isolated",
      all(m["isolated"] for m in payload["modes"] if m["mode"] != "inline"))
check("the sub-skill persists and the role does not -- the per-unit asymmetry",
      next(m for m in measurements if m["kind"] == "sub-skill")["persists"] is True
      and next(m for m in measurements if m["kind"] == "role")["persists"] is False)

# ---- the upper bound is labelled as one
ub = next(m for m in payload["measured"] if m["kind"] == "sub-skill+references")
check("the references figure is labelled an upper bound",
      "UPPER BOUND" in ub["note"], ub["note"][:80])
check("and the upper bound is at least the floor",
      ub["bytes_median"] >= next(m for m in measurements
                                 if m["kind"] == "sub-skill")["bytes_median"])

if FAILURES:
    print(f"\nFAIL  {len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nall self-tests passed")
sys.exit(0)
