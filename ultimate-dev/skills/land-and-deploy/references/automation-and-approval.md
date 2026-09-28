<!-- Moved verbatim from land-and-deploy/SKILL.md, the
     'automation-and-approval' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Automation and approval

Automate read-only detection and polling. First-run setup confirmation (Step 1.5)
and pre-merge approval (Step 3.5) are mandatory when applicable. Stop on missing
access, unknown target/state, failing required CI, conflicts, or failing tests.
After any merge error, read server state before deciding whether to stop.
Failures, timeouts, staging choices, rollback, and optional cleanup use the explicit
decisions below; no approval overrides a blocker or authorizes a different revision.
