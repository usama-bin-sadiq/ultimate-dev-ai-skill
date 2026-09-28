<!-- Moved verbatim from design-review/SKILL.md, the
     'phase-6-compile-report' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 6: Compile Report

### Output Locations

**Local:** `.gstack/design-reports/design-audit-{domain}-{YYYY-MM-DD}.md`

**Project-scoped:**
```bash
eval "$(~/.claude/skills/gstack/bin/gstack-slug 2>/dev/null)" && mkdir -p ~/.gstack/projects/$SLUG
```
Write to: `~/.gstack/projects/{slug}/{user}-{branch}-design-audit-{datetime}.md`

**Baseline:** Write `design-baseline.json` for regression mode (temp file then `mv`, and a per-run copy `design-baseline.<runId>.json` beside it):
```json
{
  "schemaVersion": 2,
  "date": "YYYY-MM-DD",
  "runId": "<run id from Setup>",
  "url": "<target>",
  "designScore": "B",
  "aiSlopScore": "C",
  "categoryGrades": { "hierarchy": "A", "typography": "B", ... },
  "findings": [{ "id": "FINDING-001", "title": "...", "impact": "high", "category": "typography" }],
  "detector": {
    "mode": "dom | source | none",
    "engine": "<engineVersion from the scan JSON; never a path>",
    "base": "<base commit, source mode only>",
    "targetSet": "<sha256 of the sorted target set: source mode = repo-relative paths scanned; DOM mode = the {page} slugs dumped (never the dated dump paths, which change every run)>",
    "total": 14,
    "byRule": { "kicker-above-heading": 2 },
    "byPage": { "home": { "kicker-above-heading": 2 } }
  }
}
```
`mode: "none"` when the detector did not run.

### Scoring System

**Dual headline scores:**
- **Design Score: {A-F}** — weighted average of all 10 categories
- **AI Slop Score: {A-F}** — standalone grade with pithy verdict

**Per-category grades:**
- **A:** Intentional, polished, delightful. Shows design thinking.
- **B:** Solid fundamentals, minor inconsistencies. Looks professional.
- **C:** Functional but generic. No major problems, no design point of view.
- **D:** Noticeable problems. Feels unfinished or careless.
- **F:** Actively hurting user experience. Needs significant rework.

**Grade computation:** Each category starts at A. Each High-impact finding drops one letter grade. Each Medium-impact finding drops half a letter grade. Polish findings are noted but do not affect grade. Minimum is F.

**Category weights for Design Score:**
| Category | Weight |
|----------|--------|
| Visual Hierarchy | 15% |
| Typography | 15% |
| Spacing & Layout | 15% |
| Color & Contrast | 10% |
| Interaction States | 10% |
| Responsive | 10% |
| Content Quality | 10% |
| AI Slop | 5% |
| Motion | 5% |
| Performance Feel | 5% |

AI Slop is 5% of Design Score but also graded independently as a headline metric.

### Regression Output

When previous `design-baseline.json` exists or `--regression` flag is used:
- Previous baseline = the newest readable `design-baseline*.json` under `$GSTACK_STATE_ROOT/projects/$SLUG/designs/design-audit-*/` older than this run; unreadable → "previous baseline unreadable (first scan)"
- Load baseline grades; compare per-category deltas, new findings, resolved findings
- Detector delta only when `detector.mode` and `targetSet` both match: ids appeared, ids disappeared, totals, per page (`+ kicker-above-heading (2)  - gradient-text (1)  total 14 → 9`). Otherwise say "detector modes differ, no delta" or "target set changed, no delta"; a different `engine` prints the delta with `engine changed X → Y; rule set may differ`; no `detector` field → "no detector baseline (first scan)", never `+N`. Live pages jitter, so counts are advisory and id appear/disappear is the signal
- Append regression table to report

---
