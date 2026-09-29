#!/usr/bin/env python3
"""Measure the cost each coordination mode imposes, from disk.

The claim under test
--------------------

`SKILL.md`, `references/coordination-modes.md` and `references/budget-system.md`
all say some version of: read "cheapest adequate" as cheapest per *call*, which
is not cheapest per unit of work, because inline is free per call and can cost
most overall -- every loaded skill stays in the conversation and is paid for
again on every turn.

Three documents assert it. Nothing measured it. `evaluation/metrics.md` records
token-level context efficiency as one of the metrics that "cannot be measured
honestly, and are reported null", and `run-pilot.py` has no token counter. The
justification for the four-mode design was therefore unfalsifiable by
construction: the only output the budget system permits is the word
"unmeasured".

What is measurable, and what is not
-----------------------------------

Not measurable here, and reported as such rather than estimated:

  * tokens, and therefore currency. The runtime does not expose usage for every
    arm in every configuration, and `references/budget-system.md` line 40 forbids
    a figure that could not be measured: "Not zero, not an estimate, not a
    plausible number."
  * cost per outcome. That needs a real-model run, which the corpus has still
    never had.

Measurable from disk, and measured here:

  * how many bytes of instruction text each capability kind puts into a context
    when it is invoked
  * whether that text persists for the rest of the run or leaves with the
    context
  * what each mode therefore implies, as an ordering rather than a number

The ordering is the part that is structural. It follows from *where the context
goes*, which is a property of the mechanism and not of a provider's pricing, so
it survives the absence of a price list. The magnitudes do not, and are not
printed.

Outputs `null` rather than 0 for anything unmeasured, following the repository's
own rule that a metric which could not be honestly measured is null, never zero.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
TOOLS = ROOT / "tools"

# Bytes of text per token, for orientation only. Used to print a rough order of
# magnitude next to a figure that is itself explicitly not a measurement, so a
# reader can see whether a difference is one turn or one career.
BYTES_PER_TOKEN = 4


def _bytes(path: pathlib.Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").encode())
    except OSError:
        return 0


def skill_costs() -> list[int]:
    out = []
    for f in sorted(SKILLS.glob("*/SKILL.md")):
        out.append(_bytes(f))
    return out


def skill_with_references_costs() -> list[int]:
    """A sub-skill plus every reference it declares as a pointer.

    Progressive disclosure means only some of those are ever loaded, so this is
    an upper bound and is reported as one. Averaging the full set would overstate
    the typical case; reporting only SKILL.md would understate the worst.

    iterdir() on a missing directory raises, and this function was the only one
    of the three that did: pointed at a tree with no skills/ it died with a
    traceback and exit 1, which is indistinguishable from the refusal below
    doing its job. The other two use glob(), which returns empty for a missing
    directory. Guarded here so that a missing tree produces the honest refusal
    rather than a crash that looks like one.
    """
    out = []
    if not SKILLS.is_dir():
        return out
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.is_file():
            continue
        total = _bytes(f)
        for r in (d / "references").glob("*.md"):
            total += _bytes(r)
        out.append(total)
    return out


def role_costs() -> list[int]:
    return [_bytes(f) for f in sorted(AGENTS.glob("*.md"))
            if f.stem != "readme" and f.stem.islower()]


def tool_costs() -> list[int]:
    return [_bytes(f) for f in sorted(TOOLS.glob("*.py"))]


def summarise(name: str, values: list[int], persists: bool, note: str) -> dict:
    if not values:
        return {"kind": name, "n": 0, "bytes": None, "persists": persists,
                "note": note}
    return {
        "kind": name,
        "n": len(values),
        "bytes_median": int(statistics.median(values)),
        "bytes_p90": int(sorted(values)[int(len(values) * 0.9)]),
        "bytes_total": sum(values),
        "persists": persists,
        "note": note,
    }


def modes(measurements: list[dict]) -> list[dict]:
    """What each mode costs, as an ordering with a mechanism, not a number."""
    by = {m["kind"]: m for m in measurements}

    def med(kind: str) -> int | None:
        return by.get(kind, {}).get("bytes_median")

    skill, full, role = med("sub-skill"), med("sub-skill+references"), med("role")
    return [
        {
            "mode": "inline",
            "loads": "a tool, or a capability read into this context",
            # Zero is a real figure and not an absence: a tool adds no
            # instruction text. It is zero for a tool and NOT zero for a
            # capability read inline, which is why the "why" is where the
            # interesting part is.
            "context_cost_median_bytes": 0,
            "context_cost_location": "this context, and it stays here for the "
                                    "rest of the run",
            "isolated": False,
            "why": "A tool costs a subprocess and no context. A capability read "
                   "inline costs whatever it weighs and it stays for the rest of "
                   "the run, which is the per-unit cost the documents describe.",
        },
        {
            # Measured, not "not measured". A delegate that reads a sub-skill
            # puts that sub-skill's bytes in the delegate's context instead of
            # this one -- the same bytes, a different address. Reporting null
            # here would be a false null: the number was measured three lines
            # above and refusing to print it would be refusing to look.
            "mode": "delegate",
            "loads": "one sub-skill, or a role answered in one result",
            "context_cost_median_bytes": skill,
            "context_cost_location": "the delegate's context, not this one",
            "isolated": True,
            "why": f"A sub-skill dispatched rather than read inline still costs "
                   f"{skill} bytes of context in the delegate, and the delegate "
                   f"returns only its answer. A role costs {role} bytes, but "
                   f"none of it comes back.",
            "sub_skill_median_bytes": skill,
            "sub_skill_with_references_upper_bound_bytes": full,
            "role_median_bytes": role,
        },
        {
            "mode": "route",
            "loads": "several sources, one merged answer",
            "context_cost_median_bytes": None,
            "context_cost_location": "sum over the sources, which is a property "
                                     "of the task rather than of the mode",
            "isolated": True,
            "why": "Several isolated reads, merged. Stateless, so a repeat "
                   "re-pays classification as well as the reads.",
        },
        {
            "mode": "handoff",
            "loads": "one party, held across stages",
            "context_cost_median_bytes": role,
            "context_cost_location": "the holder's context, held longest",
            "isolated": True,
            "why": "One isolated context held longest, so it is the mode with "
                   "the most context resident for the least of the run, and the "
                   "one whose answer is least able to be checked against this "
                   "context later.",
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable only")
    ap.add_argument("--out", type=pathlib.Path)
    args = ap.parse_args()

    measurements = [
        summarise("tool", tool_costs(), False,
                  "run as a subprocess; adds no instruction text to any context"),
        summarise("sub-skill", skill_costs(), True,
                  "read into the invoking context and stays there for the run"),
        summarise("sub-skill+references", skill_with_references_costs(), True,
                  "UPPER BOUND: a skill plus every reference it declares. "
                  "Progressive disclosure means only some are ever loaded, so "
                  "this overstates the typical case and the sub-skill row is "
                  "the floor."),
        summarise("role", role_costs(), False,
                  "read into a separate context that does not return"),
    ]

    payload = {
        "measured": measurements,
        "modes": modes(measurements),
        "not_measured": {
            "tokens": None,
            "currency": None,
            "cost_per_outcome": None,
            "why": ("The runtime does not report usage for every arm in every "
                    "configuration, and references/budget-system.md forbids a "
                    "figure that could not be measured. Reported null, never "
                    "zero and never estimated."),
        },
        "the_ordering_is_structural": (
            "The ordering of the four modes follows from where context goes, "
            "which is a property of the mechanism. It does not require a price "
            "list and does not change with one. The magnitudes do require a "
            "real-model run, which has not happened."
        ),
    }

    if args.out:
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Refuse to report if it measured nothing. summarise() returns n=0 for a
    # missing directory, and a table of nulls printed from an empty tree reads
    # as "the cost is unknown" when it should read as "this tool is pointed at
    # the wrong place" -- the same false clean the workflow-auth checker had.
    empty = [m["kind"] for m in measurements if m["n"] == 0]
    if empty:
        print(f"FAIL  measured nothing for: {', '.join(empty)}")
        print(f"      expected skills/ and agents/ under {ROOT}")
        print("      A table of nulls from an empty tree is a broken tool, not a")
        print("      measurement, and reporting one is how a cost claim survives")
        print("      having no cost behind it.")
        return 1


    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print("  measured from disk, bytes of instruction text per invocation")
    print(f"    {'kind':<24} {'n':>5} {'median':>9} {'p90':>9}  stays in context?")
    for m in measurements:
        if m["n"] == 0:
            print(f"    {m['kind']:<24} {'0':>5} {'null':>9} {'null':>9}  -")
            continue
        print(f"    {m['kind']:<24} {m['n']:>5} {m['bytes_median']:>9,} "
              f"{m['bytes_p90']:>9,}  {'yes' if m['persists'] else 'no'}")
    print()
    print("  per mode -- what the mode loads, and where that context goes")
    for m in payload["modes"]:
        cost = m.get("context_cost_median_bytes")
        if cost is None:
            shown = "task-dependent"
        elif cost == 0:
            shown = "0"
        else:
            shown = f"~{cost:,} B"
        print(f"    {m['mode']:<10} {shown:<16} isolated={str(m['isolated']):<6} "
              f"{m.get('context_cost_location', '')}")
    print()
    print("  NOT MEASURED, reported null and not estimated:")
    for k, v in payload["not_measured"].items():
        if k == "why":
            continue
        print(f"    {k:<20} {v}")
    print(f"    {payload['not_measured']['why']}")
    print()
    print(f"  orientation only, at ~{BYTES_PER_TOKEN} bytes per token: a median")
    med = next(m for m in measurements if m["kind"] == "sub-skill")["bytes_median"]
    print(f"  sub-skill is about {med // BYTES_PER_TOKEN:,} tokens, paid again on")
    print("  every turn it remains resident. That is the per-unit cost. It is not")
    print("  a currency figure and is not one.")
    if args.out:
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
