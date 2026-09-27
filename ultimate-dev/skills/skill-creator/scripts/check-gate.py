#!/usr/bin/env python3
"""The promotion gate, executable.

`skills/skill-creator/SKILL.md` specifies a lifecycle whose middle steps were
prose: specify, security-review, test, then promote. Nothing in the repository
could check any of it, so a capability could be written, shipped, named in the
kernel, and routed to from a dispatch table while having never been specified,
attacked, or promoted by a decision. That is the project's recurring defect
applied to its own capability engine, and it is why four roles were recommended
and never shipped while the suite reported them as present.

This enforces the steps the engine already claims to require. It is deliberately
strict: a gate that passes things the engine's own text rejects is worse than no
gate, because it converts an unexamined capability into a certified one.

What it requires, and where the requirement comes from:

  specification   Step 1 -- name, purpose, inputs, outputs, constraints,
                  security boundaries, verification criteria, failure modes
  security        Step 3 -- what authority does this widen, stated as an answer
  behavioural     Step 4.1 -- a case that must work
  adversarial     Step 4.2 -- a case designed to make it do the wrong thing
  interaction     Step 4.3 -- a case against an existing capability
  negative        Step 4, the forgotten one -- a request inside its domain that
                  must not trigger it. Without this a capability that fires on
                  everything scores perfectly and the false-positive rate is
                  unmeasurable.
  promotion       Step 5 -- a JEv record naming the disposition and what would
                  deprecate it
  provenance      Step 6 -- version and source, so behaviour is attributable

Usage:
    python3 skills/skill-creator/scripts/check-gate.py            # report
    python3 skills/skill-creator/scripts/check-gate.py --json     # machine
    python3 skills/skill-creator/scripts/check-gate.py --require  # exit 1 on
                                                                 # any gap
    python3 skills/skill-creator/scripts/check-gate.py --only verifier

A missing requirement is reported, never inferred. `--require` is for a promotion
gate; the default report mode is for seeing the state of a catalogue.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AGENTS = SKILL_ROOT / "agents"
SKILLS = SKILL_ROOT / "skills"
SPEC_DIR = SKILL_ROOT / "skills" / "skill-creator" / "specs"

# Each requirement is a set of alternative markers. A file satisfies a
# requirement if it contains any one of them. The markers are deliberately
# loose about wording and strict about presence: this checks that a section
# exists and was answered, not that the answer is good. Judging the answer is
# the reviewer's job and no regex can do it.
REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "specification": (
        "## Specification", "## Spec", "## Purpose", "## Inputs", "## Outputs",
    ),
    "security": (
        "## Security", "security boundary", "widens", "authority",
    ),
    "behavioural test": (
        "### behavioural", "behavioural case", "behavioural test",
        "## Test case", "## Tests", "positive case",
    ),
    "adversarial test": (
        "### adversarial", "adversarial", "hostile input", "## Attack",
    ),
    "interaction test": (
        "### interaction", "interaction", "collides with", "## Overlap",
    ),
    "negative test": (
        "### negative", "must not trigger", "negative case", "## Negative",
    ),
    "promotion record": (
        "## Promotion", "PROMOTED", "disposition", "## Decision record",
    ),
    "provenance": (
        "source_repo", "source_file", "version:", "## Version",
    ),
}

# A separate spec file is as good as an inline section. Adapters and adopted
# roles that keep their specification beside the file rather than inside it are
# a legitimate shape, and a gate that cannot see that shape is a gate that
# teaches people to inline everything.
def spec_file_for(stem: str) -> Path | None:
    candidate = SPEC_DIR / f"{stem}.md"
    return candidate if candidate.is_file() else None


# Minimum substantive characters under a required heading. A heading with nothing
# under it is a gap wearing a heading's clothes, and the first version of this
# checker could not tell the difference: a spec consisting of nine empty headings
# passed every requirement. That is this repository's recurring defect -- the
# structure satisfied and the contents wrong -- appearing inside the tool written
# to catch it, on the day it was written.
MIN_SECTION_CHARS = 120


def _section_body(text: str, marker: str) -> str:
    """The prose under the first occurrence of `marker`, up to the next heading."""
    idx = text.lower().find(marker.lower())
    if idx < 0:
        return ""
    rest = text[idx + len(marker):]
    lines, current = [], []
    for line in rest.splitlines():
        if line.lstrip().startswith("#"):
            if current:
                break
            continue
        current.append(line)
    lines = current
    body = "\n".join(lines)
    # Count prose, not heading characters or bullet dashes.
    return "".join(ch for ch in body if not ch.isspace() and ch not in "-#*`|")


def satisfied(marker: str, text: str) -> bool:
    return len(_section_body(text, marker)) >= MIN_SECTION_CHARS


def check_one(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    spec = spec_file_for(path.stem)
    spec_text = spec.read_text(encoding="utf-8") if spec else ""
    combined = text + "\n" + spec_text

    missing = [
        name for name, markers in REQUIREMENTS.items()
        if not any(satisfied(m, combined) for m in markers)
    ]
    return {
        "name": path.stem,
        "path": str(path.relative_to(SKILL_ROOT)),
        "spec_file": str(spec.relative_to(SKILL_ROOT)) if spec else None,
        "lines": len(text.splitlines()),
        "missing": missing,
        "complete": not missing,
    }


def candidates() -> list[Path]:
    found: list[Path] = []
    if AGENTS.is_dir():
        found += sorted(
            p for p in AGENTS.glob("*.md")
            if p.stem.islower() and p.stem != "readme"
        )
    if SKILLS.is_dir():
        found += sorted(SKILLS.glob("*/SKILL.md"))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require", action="store_true",
                    help="exit 1 if any candidate has a gap")
    ap.add_argument("--only", metavar="NAME", help="check one candidate")
    args = ap.parse_args()

    paths = candidates()
    if args.only:
        paths = [p for p in paths if p.stem == args.only]
        if not paths:
            print(f"error: no candidate named {args.only!r}", file=sys.stderr)
            return 2
    if not paths:
        print("error: no candidates found", file=sys.stderr)
        return 2

    results = [check_one(p) for p in paths]
    results.sort(key=lambda r: (-len(r["missing"]), r["name"]))

    if args.json:
        print(json.dumps({
            "requirement_source": "skills/skill-creator/SKILL.md steps 1-6",
            "spec_dir": str(SPEC_DIR.relative_to(SKILL_ROOT)),
            "results": results,
            "complete": sum(1 for r in results if r["complete"]),
            "total": len(results),
        }, indent=2))
    else:
        reqs = list(REQUIREMENTS)
        width = max(len(r["name"]) for r in results)
        print("missing requirement per candidate "
              f"({len(reqs)} required by skill-creator steps 1-6)\n")
        header = "  " + "candidate".ljust(width) + "  " + "  ".join(
            r.split()[0][:4] for r in reqs)
        print(header)
        print("  " + "-" * (width + 2 + 5 * len(reqs)))
        cache: dict[str, str] = {}

        def body_for(r: dict) -> str:
            if r["name"] not in cache:
                t = (SKILL_ROOT / r["path"]).read_text(encoding="utf-8")
                if r["spec_file"]:
                    t += "\n" + (SKILL_ROOT / r["spec_file"]).read_text(
                        encoding="utf-8")
                cache[r["name"]] = t
            return cache[r["name"]]

        for r in results:
            body = body_for(r)
            marks = "  ".join(
                "." if any(satisfied(m, body) for m in REQUIREMENTS[k]) else "X"
                for k in reqs)
            print("  " + r["name"].ljust(width) + "  " + marks)
        done = sum(1 for r in results if r["complete"])
        print(f"\n  {done}/{len(results)} candidates satisfy every requirement.")
        if done < len(results):
            worst: dict[str, int] = {}
            for r in results:
                for m in r["missing"]:
                    worst[m] = worst.get(m, 0) + 1
            print("  most widely missing:")
            for m, n in sorted(worst.items(), key=lambda kv: -kv[1])[:6]:
                print(f"    {n:3}/{len(results)}  {m}")
            print("\n  A capability named in the kernel and routed from a dispatch")
            print("  table is not thereby a capability. It becomes one when these")
            print("  are answered, and until then the catalogue is a set of")
            print("  assertions about judgement rather than tested judgement.")

    if args.require:
        gaps = [r for r in results if not r["complete"]]
        if gaps:
            print(f"\nerror: {len(gaps)} candidate(s) below the promotion gate: "
                  f"{', '.join(r['name'] for r in gaps)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
