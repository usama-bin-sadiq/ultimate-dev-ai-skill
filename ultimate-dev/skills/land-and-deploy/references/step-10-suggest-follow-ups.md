<!-- Moved verbatim from land-and-deploy/SKILL.md, the 'Step 10: Suggest follow-ups' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 10: Suggest follow-ups

State the verdict in plain English. Verified: changes are live. Unverified/degraded:
name the missing evidence/issues and the exact workflow/status command or `/canary <url>`
to check next. No deploy needed: merged, verification skipped for the stated reason.
Staging-only: production remains unverified, not necessarily undeployed. Rollback
pending: identify who must resolve conflicts, merge the revert PR, or verify its deploy.
REVERTED: cite rollback evidence; do not claim the original branch survived cleanup.
Offer `/canary <url>` for extended monitoring, `/benchmark <url>` when performance
matters, and `/document-release` when docs need updating.

---
