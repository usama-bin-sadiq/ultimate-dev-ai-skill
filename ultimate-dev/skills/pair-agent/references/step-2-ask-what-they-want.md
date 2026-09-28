<!-- Moved verbatim from pair-agent/SKILL.md, the
     'step-2-ask-what-they-want' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Ask what they want

Use AskUserQuestion:

> Which agent do you want to pair with your browser? This determines the
> instructions format and where credentials get written.

Options:
- A) OpenClaw (local or remote)
- B) Codex / OpenAI Agents (local)
- C) Cursor (local)
- D) Another Claude Code session (local or remote)
- E) Something else (generic HTTP instructions — use this for Hermes)

Based on the answer, set `TARGET_HOST`:
- A → `openclaw`
- B → `codex`
- C → `cursor`
- D → `claude`
- E → generic (no host-specific config)
