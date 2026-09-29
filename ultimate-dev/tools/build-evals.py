#!/usr/bin/env python3
"""Build ``evals/evals.json`` from the Markdown evaluation corpus.

The corpus in ``evaluation/`` is the authoritative source: it is richer than any
JSON schema — pass criteria, fail criteria, and a required trap per case. The
standard agent-skill tooling consumes a flat JSON array instead. This script is
the bridge, so the two cannot drift.

It is deliberately one-directional. JSON is generated from Markdown; Markdown is
never generated from JSON. The corpus is the thing humans read and argue about,
and a machine-readable view of it is a projection.

Why this exists
---------------
Without it, the evaluation suite is documentation. An eval corpus that no harness
can execute is a checklist, and a checklist does not tell you whether the kernel
triggers, passes, or regresses. With it, the same cases run under any runtime the
harness supports, and a regression becomes a measured event rather than an opinion.

Usage
-----
    python tools/build-evals.py            # write evals/evals.json
    python tools/build-evals.py --check    # verify it is current, write nothing
    python tools/build-evals.py --strict   # fail if any case was unparseable

Exit status is 0 unless ``--strict`` is given and a case could not be parsed, or
``--check`` is given and the file on disk differs from what would be written.

Case classes and the trigger flag
---------------------------------
``should_trigger`` answers "should the kernel be selected for this request", which
is a different question from "did the run pass". The two must not be conflated: a
run can pass without the kernel, which is the baseline's result rather than an
improvement.

    TN  trigger negative     false   must NOT select the kernel
    NM  trigger near-miss    false   shares the trigger vocabulary, must NOT fire
    BM  benchmark            true    must select
    DM  domain               true    must select
    SC  security             true    must select, and refuse correctly
    FC  failure case         true    the failure must occur and be classified
    RG  regression           true    must not regress
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = SKILL_ROOT / "evaluation"
OUTPUT = SKILL_ROOT / "evals" / "evals.json"

# Class prefix -> (should_trigger, class label)
CLASS_MAP = {
    "TN": (False, "simple (must not trigger)"),
    "NM": (False, "near-miss (must not trigger)"),
    "BM": (True, "benchmark"),
    "DM": (True, "domain"),
    "SC": (True, "security"),
    "FC": (True, "failure-prone"),
    # Coordination-mode cases: the nineteenth JEv boundary. Registered rather
    # than dropped, because a prefix the builder does not know is a case the
    # builder cannot score, and an unscored case is indistinguishable from a
    # case that does not exist.
    "CM": (True, "coordination"),
    "RG": (True, "regression"),
}

# prd.md section 23 names ten task classes. They are a different axis from the
# corpus families above, and conflating them is what made the specification
# untraceable to cases: `class` said "benchmark" where the spec says
# "long-context", so there was no way to ask "show me the high-assurance cases".
#
# Both are kept. `family` is where the case file lives and how it is graded;
# `task_class` is the specification's taxonomy. A case can be a security family
# and a high-assurance task class at once, and collapsing them loses that.
SPEC_CLASS_MAP = {
    "SIMPLE": "simple",
    "MEDIUM": "medium",
    "COMPLEX": "complex",
    "AMBIGUOUS": "ambiguous",
    "LCTX": "long-context",
    "MSTEP": "multi-step",
    "XDOM": "cross-domain",
    "HA": "high-assurance",
    "NOVEL": "novel-domain",
}

# Families that have no section 23 equivalent, mapped deliberately rather than
# left blank. An unmapped class is information: it says the corpus covers
# something the specification did not ask for.
EXTRA_CLASS_MAP = {
    "TN": "trigger-negative",
    "NM": "near-miss",
    "DM": "cross-domain",
    "SC": "security",
    "FC": "failure-prone",
    "CM": "coordination",
    "RG": "regression",
}

# The identifier group is greedy on purpose. A reluctant group stops at the first
# hyphen, which turns "BM-AMBIGUOUS-02" into the id "BM-AMBIGUOUS" and silently
# collides every case in the file. A greedy group takes the whole identifier and
# leaves the title to the final group.
CASE_HEADER = re.compile(
    r"^##\s+([A-Z]{2,4})-([A-Za-z0-9-]+)\s*(?:—|--|-)\s*(.+?)\s*$",
    re.MULTILINE,
)

# Field extraction. A field runs until the next bold-label field or a heading,
# so a multi-line prompt or criteria list is captured whole.
# Match a bold label through to its closing '**'. A lazy character class here
# matches a single letter ('P' for 'Prompt'), so the label must be delimited by
# the closing marker rather than by a reluctant run of word characters.
FIELD = re.compile(
    r"^\*\*(?P<label>[^*\n]+?)\*\*\s*:?\s*(?P<value>.*)$",
    re.MULTILINE,
)

STOP_LABELS = {
    "class", "domain", "primary metric", "score rule", "vector", "artefact",
    "correct handling", "compromised output", "prompt", "expected behaviour",
    "expected output", "pass criteria", "fail criteria", "trap", "naive trigger",
    "why it must not trigger", "fixture", "fixture required",
    "self-contained because", "must not", "steps",
    # The routing oracle. These four were the strongest labels in the corpus --
    # a stated, per-case, human-readable correct answer for which coordination
    # mode and which rung the task warrants -- and none of them survived
    # projection. An unrecognised label hits `current = None` and is dropped, so
    # all 128 cases reached the grader carrying no mode and no rung. The corpus
    # could state which architecture a task warrants and then threw the answer
    # away on the way to the machine.
    #
    # The set is named STOP_LABELS because these are the points at which field
    # capture restarts, not because the fields are discarded. That misnomer has
    # already cost this rule once.
    "correct mode", "rung", "scale", "coordination",
}


def strip_quote_block(text: str) -> str:
    """Normalise a prompt to plain text.

    A prompt may be written three ways across the corpus: as a ``>`` block
    quote, inline after the label, or inline and wrapped in typographic quotes.
    All three are equivalent; only the first needs its markers removed.
    """
    body = text.strip()
    if not body.lstrip().startswith(">"):
        # Inline form. Keep it, but drop one layer of wrapping quotes if present.
        if len(body) >= 2 and body[0] == body[-1] and body[0] in "\u201c\u201d\"'":
            return body[1:-1].strip()
        return body

    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(">"):
            lines.append(stripped[1:].lstrip())
        elif lines and not stripped.strip():
            lines.append("")
        elif lines:
            # A continuation of the previous quoted line.
            lines[-1] = (lines[-1] + " " + stripped).strip()
    return "\n".join(lines).strip()


def parse_case(body: str) -> dict[str, str]:
    """Extract the labelled fields from one case body."""
    fields: dict[str, list[str]] = {}
    current: str | None = None

    for line in body.splitlines():
        heading = re.match(r"^#{2,3}\s+", line)
        if heading and current:
            current = None
            continue

        match = FIELD.match(line)
        if match:
            # The bold marker sits around "Label:" in some files and "Label" in
            # others, so normalise before comparing against the known set.
            label = match.group("label").strip().rstrip(":").strip().lower()
            value = match.group("value").strip()
            if label in STOP_LABELS:
                current = label
                fields.setdefault(current, [])
                if value:
                    fields[current].append(value)
                continue
            # A bolded line whose label is not a known field is a boundary, not
            # content. Without this it falls through and is appended to whichever
            # field was open, which silently corrupts that field -- a "**Fixture
            # note:**" line appended to the end of the fixture value is how this
            # was found. Absorbing unrecognised lines into a field is the same
            # defect as a hand-written count: the structure looks right and the
            # contents are wrong.
            current = None
            continue
        if current and line.strip():
            fields[current].append(line.rstrip())

    out: dict[str, str] = {}
    for label, parts in fields.items():
        joined = "\n".join(parts).strip()
        if label in {"prompt", "expected behaviour", "expected output"}:
            out[label] = strip_quote_block(joined) if label == "prompt" else joined
        else:
            out[label] = joined
    return out


def collect_cases() -> tuple[list[dict], list[dict]]:
    """Return (parsed cases, problems). Never silently drops a case."""
    cases: list[dict] = []
    problems: list[dict] = []

    for path in sorted(CORPUS_DIR.rglob("*.md")):
        if path.name in {"README.md", "methodology.md", "metrics.md"}:
            continue

        text = path.read_text(encoding="utf-8")
        matches = list(CASE_HEADER.finditer(text))
        if not matches:
            continue

        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[start:end]
            case_id = f"{match.group(1)}-{match.group(2)}"
            fields = parse_case(body)

            prompt = fields.get("prompt", "").strip()
            if not prompt:
                problems.append({
                    "id": case_id, "file": str(path.relative_to(SKILL_ROOT)),
                    "reason": "no extractable Prompt",
                })
                continue

            prefix = match.group(1)
            segment = match.group(2)
            should_trigger, class_label = CLASS_MAP.get(prefix, (True, "uncategorised"))
            # The identifier group is greedy, so for "BM-SIMPLE-01" it captures
            # "SIMPLE-01". The class is its first token.
            variant = segment.split("-")[0].upper()
            task_class = (SPEC_CLASS_MAP.get(variant)
                          or EXTRA_CLASS_MAP.get(prefix)
                          or "unclassified")
            if prefix not in CLASS_MAP:
                problems.append({
                    "id": case_id, "file": str(path.relative_to(SKILL_ROOT)),
                    "reason": f"unknown class prefix {prefix!r}; assumed should_trigger=true",
                })

            expected = (
                fields.get("expected behaviour")
                or fields.get("expected output")
                or fields.get("pass criteria")
                or ""
            ).strip()

            cases.append({
                "id": case_id,
                "title": match.group(3).strip(),
                "query": prompt,
                "expected_output": expected or "See the case file for full criteria.",
                "should_trigger": should_trigger,
                # "fixture" is a prose description of the workspace and is left as
                # authored. Whether one is required is a separate, unambiguous field.
                "fixture": fields.get("fixture", "").strip(),
                "fixture_required": fields.get("fixture required", "yes").strip().lower(),
                "class": class_label,
                "family": prefix,
                "task_class": task_class,
                "domain": fields.get("domain", "").strip(),
                "pass_criteria": fields.get("pass criteria", "").strip(),
                "fail_criteria": fields.get("fail criteria", "").strip(),
                "trap": fields.get("trap", "").strip(),
                # Kept as null when a case states none, so "this case has no
                # routing oracle" stays distinguishable from "the kernel chose
                # the right one".
                # Backticks stripped: the corpus writes them as Markdown, and a
                # grader comparing "`inline`" to "inline" would report a miss on
                # a correct answer.
                "correct_mode": (fields.get("correct mode", "").strip()
                                 .strip("`").strip() or None),
                "rung": fields.get("rung", "").strip() or None,
                "scale": fields.get("scale", "").strip() or None,
                "primary_metric": fields.get("primary metric", "").strip() or None,
                "source": str(path.relative_to(SKILL_ROOT)),
            })

    return cases, problems


def build() -> dict:
    cases, problems = collect_cases()

    # Duplicate ids silently break every downstream consumer: grading, the pilot
    # sampler, and any diff of two runs. Colliding ids are a parsing bug, so they
    # are reported rather than disambiguated here.
    seen: dict[str, int] = {}
    for case in cases:
        seen[case["id"]] = seen.get(case["id"], 0) + 1
    for case_id, count in sorted(seen.items()):
        if count > 1:
            problems.append({
                "id": case_id,
                "file": next(c["source"] for c in cases if c["id"] == case_id),
                "reason": f"id appears {count} times; case headers must be unique",
            })

    cases.sort(key=lambda c: (not c["should_trigger"], c["id"]))
    for index, case in enumerate(cases, 1):
        case["n"] = index
    return {
        "skill_name": "ultimate-dev",
        "generated_by": "tools/build-evals.py",
        "source_of_truth": "evaluation/ (Markdown). This file is generated; do not edit it.",
        "note": (
            "pass_criteria, fail_criteria, and trap are carried through for the "
            "human grader. The bundled harness in most agent-skill tooling grades "
            "on run success only, so these fields are for a grader that reads them, "
            "not for an automatic pass/fail."
        ),
        "evals": cases,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="verify the file on disk is current; write nothing")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if any case could not be parsed")
    args = parser.parse_args(argv)

    payload = build()
    serialised = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUTPUT.is_file():
            print(f"{OUTPUT} does not exist; run without --check", file=sys.stderr)
            return 1
        current = OUTPUT.read_text(encoding="utf-8")
        if current != serialised:
            print(f"{OUTPUT} is stale; run tools/build-evals.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT} is current ({len(payload['evals'])} cases)")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialised, encoding="utf-8")

    triggered = sum(1 for c in payload["evals"] if c["should_trigger"])
    negatives = len(payload["evals"]) - triggered
    print(f"wrote {OUTPUT.relative_to(SKILL_ROOT)}")
    print(f"  cases:     {len(payload['evals'])}")
    print(f"  must fire: {triggered}")
    print(f"  must not:  {negatives}")
    if payload["problems"]:
        print(f"  problems:  {len(payload['problems'])}")
        for problem in payload["problems"][:10]:
            print(f"    {problem['id']} ({problem['file']}): {problem['reason']}")
    else:
        print("  problems:  none")

    if args.strict and payload["problems"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
