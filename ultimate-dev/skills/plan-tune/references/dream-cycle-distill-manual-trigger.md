<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Dream cycle distill (manual trigger)

**When this fires.** The user invokes `/plan-tune distill` / `dream` /
`distill` / `dream cycle`. Auto-triggered version lives in Step 0 gate #3.

**Flow:**

1. Run distill:
   ```bash
   ~/.claude/skills/gstack/bin/gstack-distill-free-text
   ```

2. If `RATE_CAPPED`: tell the user "You've hit today's 3 distills/day cap.
   Run again tomorrow, or `/plan-tune stats` for run history."
3. If `NO_FREE_TEXT`: tell the user "No free-text answers since the last
   distill. Keep using gstack — `Other` responses on AskUserQuestion feed
   this loop."
4. If success: print the proposals count + estimated cost, then route into
   `Dream cycle review` above for the user to approve each.

For background mode (e.g., the user wants to keep working):
```bash
~/.claude/skills/gstack/bin/gstack-distill-free-text --background
```

---
