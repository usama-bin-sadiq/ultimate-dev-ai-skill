<!-- Moved verbatim from autoplan/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Pre-Gate Verification

Check the plan and conversation for every applicable deliverable:

| Phase | Required outputs |
|---|---|
| CEO | Named premise challenges; findings or explicit examination/no-findings for every applicable section; Error & Rescue and Failure Modes registries (or N/A with reason); NOT in scope; What already exists; dream state delta; Completion Summary; consensus table. |
| Design, if UI | Scores for all 7 dimensions; identified and decided issues; litmus scorecard. |
| DX, if developer-facing | Scores for all 8 dimensions; developer journey map; empathy narrative; TTHW assessment and target; DX Implementation Checklist; consensus table. |
| Eng, always last | Scope challenge grounded in code; architecture ASCII diagram; codepath-to-test diagram; test plan on disk at ~/.gstack/projects/$SLUG/; NOT in scope; What already exists; failure modes registry with critical gaps; Completion Summary; consensus table. |

For each phase, verify native and outside voice results or explicit
unavailable/skipped status. Verify cross-phase themes and at least one Decision
Audit Trail row per auto-decision. Produce missing outputs before the gate; after
at most 2 repair attempts, warn at the gate with each still-incomplete item.

---
