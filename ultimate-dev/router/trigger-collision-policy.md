# Trigger Collision Policy

Broad words are discovery hints, never routing decisions. The router must
combine:

```text
intent + deliverable + material domain + repository/task context + risk
```

## High-risk generic tokens

Treat these as weak hints and require a compound signal:

- `design`, `analysis`, `data`, `code`, `systems`, `patterns`
- `new`, `web`, `auto`, `agents`, `backend`, `frontend`, `devops`
- `security`, `architecture`, `specialized`, `general`, `task`

A candidate should be selected only when its description, anti-triggers, and
context agree. If two candidates remain plausible, prefer the common skill,
then ask one focused clarification question, then use `universal-task` for a
bounded unknown result.

## Metadata maintenance

- Prefer phrases such as `unmatched database technology` over `new`.
- Prefer technology/domain compounds such as `PostgreSQL query tuning` over
  `backend` or `data`.
- Keep generic tokens only when the agent is intentionally a catch-all.
- Do not add a new catch-all trigger to solve a one-off routing problem.
- Re-run `audit-prompt-suite.py` and the 154-case provider-free benchmark after
  metadata changes.

The audit currently reports zero broad collisions. It will report future
collisions as warnings because the prompt contract forbids keyword-only routing.
Behavioral false-activation measurements are still required before claiming
that model-level routing precision is solved.
