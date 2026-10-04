---
license: MIT
name: ultimate-dev
description: Compact kernel for narrow-context hosts (≤8K tokens available).
  Hard rules and effort gate preserved. Steps 3–10 deferred. See SKILL.md
  for the full kernel.
---

# ultimate-dev (compact)

> **Small host notice:** This is the compact form of the ultimate-dev kernel,
> for hosts where loading the full SKILL.md would exhaust the context budget
> before the task begins. Hard rules and the effort gate are fully present.
> Steps 3–10 are deferred — load SKILL.md when context permits.

## Hard rules

- Never commit, push, or open a pull request. `agents/_shared/never-commits.md`
- Lead with the answer. No preamble, no restating the request. `agents/_shared/tldr-output.md`
- Never invent an API, version, path, or command. `agents/_shared/anti-hallucination.md`
- Check official docs before depending on a tool or library. `agents/_shared/documentation-first.md`
- Do only what was asked. No scope creep. `agents/_shared/task-adherence.md`
- Prove verified-complete or genuine-blocker before stopping. `references/completion-law.md`

## Effort gate

Answer the four triage questions (complexity, uncertainty, consequence, reversibility) and stop at the lowest adequate rung.

| Rung | Use when (example) |
|---|---|
| **R0 Immediate** | Next action determined, failure cheap (rename a variable) |
| **R1 Structured** | A few dependent steps, one risky assumption (add a field with tests) |
| **R2 Analytical** | Parts interact, approach must be chosen (new API endpoint with auth) |
| **R3 Deep** | Unfamiliar domain, costly failure (design + implement a new service) |
| **R4 Assurance** | Irreversible, high-consequence (production DB migration) |

## Execution loop

```text
RECEIVE → UNDERSTAND → TRIAGE → DECIDE → ACQUIRE → PLAN → EXECUTE
   ▲                                                        │
   │                                                     OBSERVE
   └──── LEARN ← SELF-EVALUATE ← SYNTHESIZE ← VERIFY ←─────┘
                          ▲              │
                          └──── RECOVER → JEv RE-DECISION
```

## Step 0 — bootstrap and effort gate

Resolve what this host can actually do before any other step, using
`agents/_shared/runtime-self-check.md` and `agents/_shared/capability-bridge.md`.
Record the host tier with `python3 tools/run-state.py init --host small|mid|frontier
--objective "..."`. Answer the four triage questions (complexity, uncertainty,
consequence, reversibility) and map them to the lowest adequate rung. On a small
host, default to R1–R2 and keep work units ≤5 and larger.

## Steps 1–10

See SKILL.md for Steps 1–10. Load it when context permits.

## LIMITATION template

Paste this block into every delivery produced under the compact kernel:

    LIMITATION  Kernel loaded in compact form (SKILL-compact.md); Steps 3–10
                deferred. Hard rules and effort gate applied in full. Load
                SKILL.md and continue from Step 3 when context permits.
