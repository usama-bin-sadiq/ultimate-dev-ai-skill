#!/usr/bin/env python3
"""Score each skill against a 4-point quality rubric.

Checks (1 point each):
  1. trigger clause      (use when | triggers | invoke | activate)
  2. exclusion clause    (not for | do not | don't | never | n.b.)
  3. exact usage         (fenced code block or `command` token)
  4. failure handling    (fail | error | fallback | recover | edge case | gotcha)

Writes reports/skill-quality.md. Exits 1 if the repo mean drops below a floor
(--mean-floor, default 2.0) so CI can gate quality drift.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
OUT = ROOT.parent / "reports" / "skill-quality.md"

TRIGGER = re.compile(r"use when|triggers?|invoke|activate", re.I)
EXCLUDE = re.compile(r"not for|do not|don't|never|n\.?b\.?|exclude", re.I)
USAGE   = re.compile(r"```|`python |`bash |`curl |`npm |`pip |python3 |bash ", re.I)
FAILURE = re.compile(r"fail|error|fallback|recover|edge case|gotcha|retry|handles", re.I)

def score_body(text: str) -> int:
    return sum(bool(p.search(text)) for p in (TRIGGER, EXCLUDE, USAGE, FAILURE))

def main():
    floor = float(sys.argv[sys.argv.index("--mean-floor") + 1]) if "--mean-floor" in sys.argv else 2.0
    rows = []
    for md in sorted(SKILLS.glob("*/SKILL.md")):
        rows.append((md.parent.name, score_body(md.read_text(encoding="utf-8", errors="replace"))))
    mean = sum(s for _, s in rows) / max(len(rows), 1)
    worst = sorted(rows, key=lambda r: r[1])[:20]
    lines = [f"# Skill quality rubric", f"", f"- skills scored: {len(rows)}", f"- mean score: {mean:.2f} / 4", f""]
    lines.append("## Lowest scoring (needs work)")
    for name, s in worst:
        lines.append(f"- **{s}/4** — `{name}`")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"scored {len(rows)} skills; mean {mean:.2f}/4; report at {OUT.relative_to(ROOT.parent)}")
    if mean < floor:
        print(f"FAIL: mean {mean:.2f} below floor {floor}")
        sys.exit(1)

if __name__ == "__main__":
    main()
