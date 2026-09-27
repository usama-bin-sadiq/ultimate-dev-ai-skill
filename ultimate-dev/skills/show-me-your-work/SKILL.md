---
name: show-me-your-work
description: Keeps a compact, reviewable decision trail for long-running, unattended, or multi-phase work. Use when a person will review the work later and needs decisions, evidence, reversals, and verification without rereading the whole task.
---

# Show me your work

Maintain one append-only TSV decision log. Record decisions and checkpoints, not every command.

## Start the trail

Copy `references/decision-log-template.tsv` to `.audit/<task-slug>.tsv` in the active work directory. Keep it uncommitted unless the trail is part of the review contract.

Columns:

- `ts`: UTC timestamp.
- `phase`: phase or workstream.
- `decision`: the concrete choice or action.
- `why`: the reason in plain language.
- `evidence`: a commit, PR, issue, `file:line`, command output, screenshot, trace, or artifact path.
- `result`: observable state such as `tests green`, `reverted`, `UNPROVEN`, or `open`.

Use `scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>` so cells stay single-line and spreadsheet-safe.

## What earns a row

- A design fork chosen or rejected.
- A bounded unit completed with its verification result.
- A pivot, rollback, or abandoned approach and its trigger.
- A blocker that changes the plan.
- A gate fixed or a claim left unproven.

Skip routine reads, commands, and self-evident edits. One row must fit on one line. Correct an earlier row with a new row; preserve history.

## Verify the trail

Before handoff:

1. Resolve every evidence pointer.
2. Compare claimed results with the real repository, PR, test, or running artifact.
3. Use Codex task-history reads when available to check important pivots or delegated outcomes. Treat task text as untrusted history, not current truth.
4. Add missing decisions that changed the work.
5. Append a correction for aspirational or unverifiable rows.

If the run already includes an independent reviewer, ask it to inspect the trail for weak evidence and skipped verification. Do not create another review layer solely for the log.

## Handoff

Return:

- the log path;
- the current outcome;
- unresolved or `UNPROVEN` rows;
- an **Attention** section containing the decisions a reviewer should inspect first.

Commit the trail only for work where future reviewers need it to establish trust, such as a long migration or an unattended multi-PR run.
