<!-- Moved verbatim from codex/SKILL.md, the
     'synthesis-recommendation-required-all-modes' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Synthesis recommendation (REQUIRED) — all modes

Every mode ends by emitting ONE synthesis recommendation line after presenting
Codex's verbatim output, in the canonical format the AskUserQuestion judge grades:

```
Recommendation: <action> because <one-line reason that names the most actionable finding>
```

The reason must engage with a specific Codex finding or insight and compare
against an alternative (another finding, fix-vs-ship, fix order, or status-quo).
Boilerplate reasons ("because it's better", "because adversarial review found
things") fail the format. The recommendation is the ONE line a user reads when
they don't have time for the verbatim output. **Never silently auto-decide;
always emit the line.** Each mode section restates this rule with mode-specific
examples.

---

> **STOP.** Before running Review mode (Step 2A) — the Step 1 dispatch chose review (`/codex review`, or the user picked "Review the diff"), Read `~/.claude/skills/gstack/codex/sections/review-mode.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before running Challenge mode (Step 2B) — the Step 1 dispatch chose adversarial challenge (`/codex challenge`, or the user picked "Challenge the diff"), Read `~/.claude/skills/gstack/codex/sections/challenge-mode.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

> **STOP.** Before running Consult mode (Step 2C) — the Step 1 dispatch chose consult (a free-form question, a plan review, or a session follow-up), Read `~/.claude/skills/gstack/codex/sections/consult-mode.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.
