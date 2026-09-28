<!-- Moved verbatim from plan-tune/SKILL.md, the
     'dream-cycle-review' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Dream cycle review

**When this fires.** Step 0's dream-cycle gate: `distillation-proposals.json`
has at least one proposal with `applied_at` missing. Or the user explicitly
invokes via `/plan-tune distill` / `dream`.

**Flow:**

1. Show the proposals:
   ```bash
   ~/.claude/skills/gstack/bin/gstack-distill-apply --list
   ```

2. For each unapplied proposal, present it as a numbered item and use
   AskUserQuestion (one per call, per skill convention). Show:
   - Kind (`preference` / `declared-nudge` / `memory-nugget`)
   - Confidence + rationale
   - The source quotes verbatim (proves user-origin)
   - What applying does (which file/key/dim changes)

3. **On accept** (Y): apply via the bin. The skill also publishes the
   nugget to gbrain when configured.

   For `memory-nugget`:
   ```bash
   # If gbrain is configured, mirror via MCP first.
   # (Pseudo — actual gbrain call happens at the agent layer via
   # mcp__gbrain__put_page; the bin records the published flag.)
   ~/.claude/skills/gstack/bin/gstack-distill-apply --proposal N --gbrain-published true|false
   ```

   For `preference`:
   ```bash
   ~/.claude/skills/gstack/bin/gstack-distill-apply --proposal N
   ```

   For `declared-nudge`:
   ```bash
   # Same bin; updates developer-profile.json declared dim with the
   # clamped delta.
   ~/.claude/skills/gstack/bin/gstack-distill-apply --proposal N
   ```

4. **On decline**: skip without marking. User can re-decide later (the
   proposal stays in the file). To dismiss permanently, manually clear:
   `gstack-distill-apply --proposal N --dismiss` (not implemented in T11;
   for now, regenerate via next distill run with corrected free-text).

5. **gbrain integration.** When `mcp__gbrain__*` tools are available in
   this session:
   - On `memory-nugget` apply: `mcp__gbrain__put_page` with the nugget +
     `mcp__gbrain__extract_facts` + `mcp__gbrain__add_tag` per the cathedral
     plan D9 routing. Then pass `--gbrain-published true` to the bin so
     the proposals file records the mirror.
   - When gbrain isn't configured (no MCP tools), the bin's local file
     write is the durable source-of-truth and the PreToolUse hook reads it
     via Layer 8 memory injection.

---
