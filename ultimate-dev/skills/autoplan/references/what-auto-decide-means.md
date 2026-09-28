<!-- Moved verbatim from autoplan/SKILL.md, the
     'what-auto-decide-means' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## What "Auto-Decide" Means

Auto-decide replaces the USER'S answer, not ANALYSIS. Run each loaded section at
full interactive depth; answer AskUserQuestion using the 6 principles.

**Default resolution: the recommended option.** Take `(recommended)` or the mode's
context default. Use the 6 principles for missing recommendations/ties. On principle
disagreement, take the recommendation and surface the disagreement as Taste at the final gate.

**Never auto-decide User Challenges:** both models agree to change the user's
direction/settled decisions, or a premise is clearly wrong. Use Decision
Classification; ask once at Final Approval Gate, never mid-run. The user has
context models lack.

Read referenced code/diffs/files; decide every issue. Produce all required
diagrams, tables, registries and artifacts on disk or in the plan. LOG decisions,
record ALL accepted obligations below and run `amend-input` before continuing.
Missing deliverables make the review incomplete.

No summary substitutes or one-line sections; fewer than 3 sentences likely means
compression. "No issues found" needs 1-2 sentences stating what was examined and why nothing was flagged.
Explain inapplicability with evidence; skip only under Phase 0's list. Never abort
or redirect to interactive review: the user chose /autoplan.

**Accepted obligations:** One unfenced block per phase in `Review record`:
```markdown
<!-- autoplan-accepted:ceo -->
- Requirement, all conditions and verification/tests.
<!-- /autoplan-accepted:ceo -->
```
Phase: `ceo|design|dx|eng`. Record accepted requirements here;
no analysis/severity/verdict/consensus. No accepted requirements: `None: reason`.
On a rerun, carry forward unchanged accepted requirements; do not replace them with None.
`amend` checks exact retention atomically; full readback; None unchanged.
Baseline edits: `create`'s `baselineEdits`. Prior blocks immutable;
state replacements in current block. Reconcile all decisions with readback.
Transport ≠ approval/complete enumeration/correctness.

---
