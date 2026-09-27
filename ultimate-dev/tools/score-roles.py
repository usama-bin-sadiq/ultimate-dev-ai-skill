#!/usr/bin/env python3
"""Score agent roles for substance, using a mechanical proxy.

A public survey of four role repositories found that the separator between
genuine expertise and persona cosplay is whether a file names a specific failure
mode with its exception conditions. The test offered for it was semantic --
substitute "plumber" for the role name and see whether the rules survive. That
cannot be automated. This is the mechanical proxy, and it is a proxy: it counts
checkable markers, and a role can score well by listing numbers it never uses.

It exists because the kernel's own roles had never been measured against it. The
project's recurring defect is structure satisfied while contents are wrong, and
"a role file exists, is over 40 lines, and is named in SKILL.md" is exactly that
shape of claim. This scores the contents.

Markers counted, and why each is a marker rather than decoration:

  numbers      a threshold, budget, or limit -- an unfalsifiable role states no
               quantities, because a quantity can be wrong
  negatives    explicit prohibitions -- a role that cannot say what it must not
               do has not decided what it is for
  commands     runnable or named-tool references -- the work is anchored to
               something outside the prompt
  standards    named external systems, IDs, or formalisms -- the role cites
               authority rather than asserting taste
  outputs      explicit output field names -- a deliverable with no named shape
               cannot be checked by the caller
  failures     named concrete failure modes -- the single strongest signal in
               the survey, weighted highest

Usage:
    python3 tools/score-roles.py            # score ultimate-dev/agents
    python3 tools/score-roles.py --json     # machine-readable
    python3 tools/score-roles.py --min N    # exit 1 if any role scores below N
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = SKILL_ROOT / "agents"

# A number that is part of an identifier or a version string is not a threshold.
_NUMBER = re.compile(
    r"(?<![\w.])\d+(?:\.\d+)?\s*(?:%|ms|s\b|sec|seconds?|minutes?|min|hours?|"
    r"days?|kb|mb|gb|lines?|chars?|items?|times|attempts?|retries|x\b)?",
    re.IGNORECASE,
)
_NUMBER_NOISE = re.compile(r"\b(19|20)\d{2}-\d{2}-\d{2}\b|^\d+$")
_NEGATIVE = re.compile(
    r"\b(never|do not|don't|must not|no\b|refuse|prohibit\w*|forbidden|"
    r"not allowed|may not|without)\b",
    re.IGNORECASE,
)
_COMMAND = re.compile(
    r"`[^`]*?(?:\-\-[a-z\-]{2,}|\b(?:python3?|npm|npx|git|gh|curl|jq|make|"
    r"pytest|rg|grep|sed|awk|bash|sh|go|cargo|docker|kubectl)\b)[^`]*?`",
    re.IGNORECASE,
)
_STANDARD = re.compile(
    r"\b(?:RFC\s?\d+|CWE-?\d+|OWASP|MITRE|ATT&CK|ISO\s?\d+|NIST|"
    r"SLO|SLI|error budget|p95|p99|burn rate|C0[1-7]|R[0-4]|L[0-7]|"
    r"STRIDE|Obs-n|SPEC\s?\d+)\b",
    re.IGNORECASE,
)
_OUTPUT_FIELD = re.compile(
    # Two accepted shapes, because the first version of this pattern required a
    # colon and therefore scored every role in this repository as having no
    # output contract. The roles use an all-caps label followed by a space run;
    # other contracts use a colon. A scorer that under-counts is worse than no
    # scorer, so both shapes are accepted.
    r"^\s*`?[A-Z][A-Z0-9_]{2,}`?\s*(?:::|\s{2,})\S",
    re.MULTILINE,
)
_FAILURE = re.compile(
    r"\b(failure mode|fails? when|bug|defect|regression|drift|"
    r"silent(?:ly)?\s+\w+|corrupt\w*|hallucinat\w+|fabricat\w+|"
    r"wrong|breaks?|broken|trap|footgun|anti-pattern)\b",
    re.IGNORECASE,
)

# Persona markers: the phrases that make a role cosplay rather than a procedure.
_PERSONA = re.compile(
    r"\byou are (?:an?|the)\b[^.\n]{0,60}?"
    r"\b(?:expert|specialist|senior|staff|principal|elite|world-class|"
    r"veteran|seasoned|renowned|master)\b|"
    r"\bwith (?:over |more than )?\d+ years\b|"
    r"\bpassionate about\b|\bcutting-edge\b|\bstate-of-the-art\b|"
    r"\bleverage your\b|\bbest practices\b",
    re.IGNORECASE,
)

WEIGHTS = {
    "failures": 3,
    "negatives": 2,
    "outputs": 2,
    "numbers": 1,
    "commands": 1,
    "standards": 1,
}
# A role at or above this is carrying a procedure. Below it, the file is
# asserting authority rather than encoding judgement.
SUBSTANTIVE_AT = 12
PERSONA_PENALTY = 4


def _count(pattern: re.Pattern[str], text: str) -> int:
    if pattern is _NUMBER:
        hits = 0
        for m in _NUMBER.finditer(text):
            token = m.group(0).strip()
            if not token or _NUMBER_NOISE.search(token):
                continue
            if token.isdigit() and len(token) < 2:
                continue
            hits += 1
        return hits
    return len(pattern.findall(text))


def score_role(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    # Frontmatter describes the role; it is not the role's procedure.
    body = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    marks = {name: _count(pat, body) for name, pat in (
        ("numbers", _NUMBER),
        ("negatives", _NEGATIVE),
        ("commands", _COMMAND),
        ("standards", _STANDARD),
        ("outputs", _OUTPUT_FIELD),
        ("failures", _FAILURE),
    )}
    raw = sum(WEIGHTS[k] * v for k, v in marks.items())
    persona = len(_PERSONA.findall(body))
    total = max(0, raw - PERSONA_PENALTY * persona)
    return {
        "role": path.stem,
        "score": total,
        "persona_markers": persona,
        "substantive": total >= SUBSTANTIVE_AT,
        "markers": marks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--min", type=int, default=None, metavar="N",
                    help=f"exit 1 if any role scores below N "
                         f"(substantive threshold is {SUBSTANTIVE_AT})")
    ap.add_argument("--agents", type=Path, default=AGENTS_DIR, metavar="DIR",
                    help="directory of role files to score (default: agents/ "
                         "beside this script). Exists so the scorer can be run "
                         "against a candidate catalogue, including a synthetic "
                         "persona file, to confirm it actually separates them.")
    args = ap.parse_args()

    agents_dir = args.agents
    if not agents_dir.is_dir():
        print(f"error: {agents_dir} not found", file=sys.stderr)
        return 2
    roles = sorted(p for p in agents_dir.glob("*.md") if p.stem.islower())
    if not roles:
        print(f"error: {agents_dir} contains no role definitions", file=sys.stderr)
        return 2

    results = [score_role(p) for p in roles]
    results.sort(key=lambda r: r["score"])

    if args.json:
        print(json.dumps({
            "proxy_disclaimer": (
                "Counts checkable markers. A role can score well by listing "
                "numbers it never uses; this is not a quality judgement."
            ),
            "substantive_at": SUBSTANTIVE_AT,
            "roles": results,
        }, indent=2))
    else:
        width = max(len(r["role"]) for r in results)
        print(f"{'role'.ljust(width)}  score  persona  "
              f"{'neg':>4} {'out':>4} {'fail':>5} {'num':>4} {'cmd':>4} {'std':>4}")
        for r in results:
            m = r["markers"]
            flag = " " if r["substantive"] else "<"
            print(f"{r['role'].ljust(width)}  {r['score']:5}  "
                  f"{r['persona_markers']:7}  "
                  f"{m['negatives']:4} {m['outputs']:4} {m['failures']:5} "
                  f"{m['numbers']:4} {m['commands']:4} {m['standards']:4} {flag}")
        weak = [r["role"] for r in results if not r["substantive"]]
        print()
        print(f"{len(results) - len(weak)}/{len(results)} at or above "
              f"{SUBSTANTIVE_AT} (proxy, not a quality verdict)")
        if weak:
            print(f"below threshold: {', '.join(weak)}")
        print("< marks a role the proxy could not distinguish from persona. "
              "Read it before concluding it is empty -- the proxy counts "
              "markers, and a short sharp rule can be excellent.")

    if args.min is not None:
        below = [r for r in results if r["score"] < args.min]
        if below:
            print(f"error: {len(below)} role(s) below {args.min}: "
                  f"{', '.join(r['role'] for r in below)}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
