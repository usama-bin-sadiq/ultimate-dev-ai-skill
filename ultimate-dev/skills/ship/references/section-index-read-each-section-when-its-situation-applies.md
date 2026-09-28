<!-- Moved verbatim from ship/SKILL.md, the 'Section index — Read each section when its situation applies' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Section index — Read each section when its situation applies

This skill is a decision-tree skeleton. The steps below point to on-demand
sections. Read a section in full before doing its step; do not work from memory.

| When | Read this section |
|------|-------------------|
| the ship target is an Apple platform app (.xcodeproj, .xcworkspace, or an app-product Swift package) — read BEFORE Step 1's branch gate and any preflight; store distribution never routes through the branch/PR ceremony | `sections/apple-release.md` |
| running the test suites and (if prompt files changed) the eval suites (Steps 4-6) | `sections/tests.md` |
| auditing test coverage of the diff (Step 7) | `sections/test-coverage.md` |
| auditing plan completion, verification, and scope drift (Step 8) | `sections/plan-completion.md` |
| the pre-landing review and specialist dispatch (Step 9) | `sections/review-army.md` |
| addressing Greptile review comments when a PR exists (Step 10) | `sections/greptile.md` |
| the adversarial review and learnings capture (Step 11) | `sections/adversarial.md` |
| writing the CHANGELOG entry (Step 13) | `sections/changelog.md` |
| dispatching the /document-release subagent to sync docs (Step 18) and then creating or updating the PR/MR (Step 19) | `sections/pr-body.md` |

---
