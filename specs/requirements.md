# Requirements — "10/10" for the ultimate-dev package

A 10/10 package is not a prettier README. It is one where a reader can answer
three questions with evidence, not vibes:

1. **Does it route correctly?** For a given user request, the right skill/agent
   is selected from the 2,372-entry pool as often as a strong retriever should.
2. **Do the skills actually help?** Running a task with the skill beats running
   it without, on a deterministic verifier, on more than one domain.
3. **Is every skill worth its context?** No duplicates, no placeholder bodies,
   every skill states its trigger *and* its exclusions.

## Functional requirements

- R1. The routing index (`skills/_routing-index.json`) must be regenerable and
  current; a stale index is a CI failure.
- R2. A routing eval: ≥50 hand-labeled (query → expected skill) pairs,
  run mechanically, reporting Hit@1, MRR@10, Recall@5.
- R3. Overlap lint: the pair-Jaccard report must not exceed the 11 known
  template duplicates; new true duplicates fail CI.
- R4. Skill-quality rubric: every skill body must state (a) when to use,
  (b) when NOT to use, (c) exact command/example usage, (d) failure mode.
  Measured per skill, exported as a score, top-violators listed.
- R5. A minimal with-skills vs without-skills task harness on ≥5 tasks across
  distinct domains, with deterministic verifiers.
- R6. The Composio stub cluster (611 skills with identical one-line bodies)
  must be either merged, pruned, or marked as an explicit "external template"
  family and excluded from routing metrics.

## Non-functional requirements

- N1. No change may break `validate-skills.py` PASS.
- N2. Every new tool must be stdlib-only, runnable on bare Python 3.10+, and
  documented in `tools/README.md`.
- N3. Nothing commits; the branch keeps all changes staged for review.
- N4. Docs (README/CONTRIBUTING/INSTALL) must match the tree after each ticket.
