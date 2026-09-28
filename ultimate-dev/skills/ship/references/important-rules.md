<!-- Moved verbatim from ship/SKILL.md, the
     'important-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Important Rules

- **Never skip tests.** If tests fail, stop.
- **Never skip the pre-landing review.** If checklist.md is unreadable, stop.
- **Never force push.** Use regular `git push` only.
- **Never ask for trivial confirmations** (e.g., "ready to push?", "create PR?"). DO stop for: version bumps (MINOR/MAJOR), pre-landing review findings (ASK items), and Codex structured review [P1] findings (large diffs only).
- **Always use the 4-digit version format** from the VERSION file.
- **Date format in CHANGELOG:** `YYYY-MM-DD`
- **Split commits for bisectability** — each commit = one logical change.
- **TODOS.md completion detection must be conservative.** Only mark items as completed when the diff clearly shows the work is done.
- **Use Greptile reply templates from greptile-triage.md.** Every reply includes evidence (inline diff, code references, re-rank suggestion). Never post vague replies.
- **Never push without fresh verification evidence.** If code changed after Step 5 tests, re-run before pushing.
- **Step 7 generates coverage tests.** They must pass before committing. Never commit failing tests.
- **The goal is: user says `/ship`, next thing they see is the review + PR URL + auto-synced docs.**

Each file below is loaded on demand, not at triage. 37 file(s):

- `references/artifacts-sync-skill-start.md` — Artifacts Sync (skill start). <!-- Moved verbatim from ship/SKILL.md, the
- `references/askuserquestion-format.md` — AskUserQuestion Format. <!-- Moved verbatim from ship/SKILL.md, the
- `references/claimed-limitations-need-evidence.md` — Claimed Limitations Need Evidence. <!-- Moved verbatim from ship/SKILL.md, the
- `references/completeness-principle-boil-the-ocean.md` — Completeness Principle — Boil the Ocean. <!-- Moved verbatim from ship/SKILL.md, the
- `references/completion-status-protocol.md` — Completion Status Protocol. <!-- Moved verbatim from ship/SKILL.md, the
- `references/confusion-protocol.md` — Confusion Protocol. <!-- Moved verbatim from ship/SKILL.md, the
- `references/context-health-soft-directive.md` — Context Health (soft directive). <!-- Moved verbatim from ship/SKILL.md, the
- `references/context-recovery.md` — Context Recovery. <!-- Moved verbatim from ship/SKILL.md, the
- `references/important-rules.md` — Important Rules. <!-- Moved verbatim from ship/SKILL.md, the
- `references/model-specific-behavioral-patch-claude.md` — Model-Specific Behavioral Patch (claude). <!-- Moved verbatim from ship/SKILL.md, the
- `references/operational-self-improvement.md` — Operational Self-Improvement. <!-- Moved verbatim from ship/SKILL.md, the
- `references/plan-mode-safe-operations.md` — Plan Mode Safe Operations. <!-- Moved verbatim from ship/SKILL.md, the
- `references/plan-status-footer.md` — Plan Status Footer. <!-- Moved verbatim from ship/SKILL.md, the
- `references/preamble-run-first.md` — Preamble (run first). <!-- Moved verbatim from ship/SKILL.md, the
- `references/question-tuning-skip-entirely-if-question-tuning-false.md` — Question Tuning (skip entirely if `QUESTION_TUNING: false`). <!-- Moved verbatim from ship/SKILL.md, the
- `references/repo-ownership-see-something-say-something.md` — Repo Ownership — See Something, Say Something. <!-- Moved verbatim from ship/SKILL.md, the
- `references/review-readiness-dashboard.md` — Review Readiness Dashboard. <!-- Moved verbatim from ship/SKILL.md, the
- `references/search-before-building.md` — Search Before Building. <!-- Moved verbatim from ship/SKILL.md, the
- `references/section-index-read-each-section-when-its-situation-applies.md` — Section index — Read each section when its situation applies. <!-- Moved verbatim from ship/SKILL.md, the
- `references/section-self-check-before-you-finish.md` — Section self-check (before you finish). <!-- Moved verbatim from ship/SKILL.md, the
- `references/skill-invocation-during-plan-mode.md` — Skill Invocation During Plan Mode. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-0-9-apple-target-detection.md` — Step 0.9: Apple target detection. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-0-detect-platform-and-base-branch.md` — Step 0: Detect platform and base branch. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-1-pre-flight.md` — Step 1: Pre-flight. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-12-version-bump-auto-decide.md` — Step 12: Version bump (auto-decide). <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-14-todos-md-auto-update.md` — prose
- `references/step-15-commit-bisectable-chunks.md` — Step 15: Commit (bisectable chunks). <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-16-verification-gate.md` — Step 16: Verification Gate. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-17-push.md` — Step 17: Push. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-2-distribution-pipeline-check.md` — Step 2: Distribution Pipeline Check. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-20-persist-ship-metrics.md` — Step 20: Persist ship metrics. <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-21-plan-tune-discoverability-nudge-first-successful-ship-only.md` — Step 21: Plan-tune discoverability nudge (first-successful-ship only). <!-- Moved verbatim from ship/SKILL.md, the
- `references/step-3-merge-the-base-branch-before-tests.md` — Step 3: Merge the base branch (BEFORE tests). <!-- Moved verbatim from ship/SKILL.md, the
- `references/telemetry-run-last.md` — Telemetry (run last). <!-- Moved verbatim from ship/SKILL.md, the
- `references/third-party-web-actions.md` — Third-Party Web Actions. <!-- Moved verbatim from ship/SKILL.md, the
- `references/voice.md` — Voice. <!-- Moved verbatim from ship/SKILL.md, the
- `references/writing-style-skip-entirely-if-explain-level-terse-appears-in-the-preamble-echo-or-the-user-s-current-message-explicitly-requests-terse-no-explanations-output.md` — prose
