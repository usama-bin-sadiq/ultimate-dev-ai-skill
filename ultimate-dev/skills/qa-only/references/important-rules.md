<!-- Moved verbatim from qa-only/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

1. **Repro is everything.** Every issue needs at least one screenshot. No exceptions.
2. **Verify before documenting.** Retry the issue once to confirm it's reproducible, not a fluke.
3. **Never include credentials.** You never type them — the user signs in inside Aside. Write `[REDACTED]` if a repro step has to mention one.
4. **Write incrementally.** Append each issue to the report as you find it. Don't batch.
5. **Never read source code.** Test as a user, not a developer.
6. **Check console after every interaction.** JS errors that don't surface visually are still bugs.
7. **Test like a user.** Use realistic data. Walk through complete workflows end-to-end.
8. **Depth over breadth.** 5-10 well-documented issues with evidence > 20 vague descriptions.
9. **Never delete output files.** Screenshots and reports accumulate — that's intentional.
10. **Use `annotatedScreenshot(pg)` when the tree misses a clickable element.** Ref labels drawn on the page find clickable divs the accessibility tree skips; then click by ref or CSS selector.
11. **Show screenshots to the user.** After every script that saves a screenshot, `cp` it out of the printed `ASIDE_DIR` into `$REPORT_DIR/screenshots/` and use the Read tool on the copied file so the user can see it inline. This is critical — without it, screenshots are invisible to the user.
12. **Never refuse to use the browser.** When the user invokes /qa or /qa-only, they are requesting browser-based testing in Aside. Never suggest evals, unit tests, curl, or other alternatives as a substitute. Even if the diff appears to have no UI changes, backend changes affect app behavior — always open the app in the browser and test.
13. **Mutating actions on a non-local target need consent.** Submitting, creating, deleting, purchasing, or changing settings on anything that is not LOCAL follows the "Invocation is consent to LOOK, not to ACT" rule in BROWSER SETUP — one AskUserQuestion per run, before the first such action.

---
