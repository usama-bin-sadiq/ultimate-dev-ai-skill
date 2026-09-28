<!-- Moved verbatim from ship/SKILL.md, the
     'step-16-verification-gate' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 16: Verification Gate

**IRON LAW: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Find generation/build commands in CLAUDE.md/AGENTS.md, package scripts, and build
configuration; run them first, skipping only when none are defined. A failed build blocks push. If it changes tracked files, inspect the
changes, run affected checks from Steps 6–11, refresh release facts, and commit
under Step 15 before returning here. Reuse unchanged results and actual approvals.

Then check test evidence against the final content:

```bash
~/.claude/skills/gstack/bin/gstack-evidence check --label tests --expect-cmd '<exact tests-lane command from Step 5>' --label vitest --expect-cmd '<exact vitest-lane command from Step 5>' --max-age 24 --allow-paths CHANGELOG.md,VERSION,package.json,agents-digest/gstack-AGENTS.md
```

Use only Step 5's actual lane labels and exact commands; `vitest` is an example.
If Step 4 explicitly declined testing and no lanes exist, report that gap instead
of inventing FRESH evidence. Build verification still applies.

The allow-list covers release bookkeeping, including Step 12's package/digest
version stamps. Behavioral package.json edits still require live tests despite
the path exemption. Do not add `TODOS.md` or generated tests to the allow-list:
Step 7 tests, review fixes, and Step 14 TODOS edits intentionally make evidence STALE.

- **Every line FRESH (exit 0):** recorded runs passed on identical content except
  the listed release files. Cite label, exit, timestamp, and log path; continue.
- **Any STALE/MISSING (exit non-zero):** inspect the reason before choosing recovery:
  - **Content, command or age mismatch, or no passing live evidence:** rerun the
    affected lanes on final content, wrapped as `~/.claude/skills/gstack/bin/gstack-evidence run --label <lane> -- '<command>'`.
    Read results and recheck once. TODOS edits and generated tests are content
    changes, not ledger-only bookkeeping.
  - **Ledger read/write failure only:** if a successful live run already covers
    the unchanged final content, exact command and permitted age, cite its exit,
    timestamp and log directly. Report ledger unavailable and continue, never
    ledger FRESH. Do not rerun green suites solely because the ledger cannot save
    or read its record. If unchanged content cannot be confirmed, STOP.

A failed CHECK identifies evidence to repair; it is not a test failure. The
required live RUN must pass, except for the explicit triage waiver below.

Paste build and rerun results. Later code, test, or build-input changes return
through this gate before pushing. Step 18 owns validation of its post-push
docs-only edits; follow repository-required checks there too. Do not claim an
earlier test run covered changed inputs.

**If tests fail here:** apply Step 5's triage. A prior explicit waiver remains valid
only for the same verified pre-existing failures and approved scope; cite that
approval and actual failing counts, never FRESH or all-green evidence. New,
changed, or unwaived failures STOP publication and return to Step 5.

Claiming work is complete without verification is dishonesty, not efficiency.

---
