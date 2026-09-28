<!-- Moved verbatim from plan-tune/SKILL.md, the
     '5-q-setup-post-consent-or-via-setup-gate' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## 5-Q setup (post-consent, or via Setup gate)

**When this fires.** Two paths:
- Right after the consent prompt above accepts option A.
- Standalone via Step 0's setup gate: `question_tuning` is already `true`
  (user opted in via gstack-config or earlier `/plan-tune enable`) AND
  `declared` is empty AND `~/.gstack/.declared-setup-prompted` is missing.
  This catches users who set `question_tuning: true` directly without
  running the wizard.

**Flow:**

1. Ask FIVE one-per-dimension declaration questions via individual
   AskUserQuestion calls (one at a time). Use plain English, no jargon:

   **Q1 — scope_appetite:** "When you're planning a feature, do you lean toward
   shipping the smallest useful version fast, or building the complete, edge-
   case-covered version?"
   Options: A) Ship small, iterate (low scope_appetite ≈ 0.25) /
   B) Balanced / C) Boil the ocean — ship the complete version (high ≈ 0.85)

   **Q2 — risk_tolerance:** "Would you rather move fast and fix bugs later, or
   check things carefully before acting?"
   Options: A) Check carefully (low ≈ 0.25) / B) Balanced / C) Move fast (high ≈ 0.85)

   **Q3 — detail_preference:** "Do you want terse, 'just do it' answers or
   verbose explanations with tradeoffs and reasoning?"
   Options: A) Terse, just do it (low ≈ 0.25) / B) Balanced /
   C) Verbose with reasoning (high ≈ 0.85)

   **Q4 — autonomy:** "Do you want to be consulted on every significant
   decision, or delegate and let the agent pick for you?"
   Options: A) Consult me (low ≈ 0.25) / B) Balanced /
   C) Delegate, trust the agent (high ≈ 0.85)

   **Q5 — architecture_care:** "When there's a tradeoff between 'ship now'
   and 'get the design right', which side do you usually fall on?"
   Options: A) Ship now (low ≈ 0.25) / B) Balanced /
   C) Get the design right (high ≈ 0.85)

   After each answer, map A/B/C to the numeric value and save the declared
   dimension. Write each declaration directly into
   `~/.gstack/developer-profile.json` under `declared.{dimension}`:

   ```bash
   # Ensure profile exists
   ~/.claude/skills/gstack/bin/gstack-developer-profile --read >/dev/null
   # Update declared dimensions atomically
   eval "$(~/.claude/skills/gstack/bin/gstack-paths)"
   _PROFILE="$GSTACK_STATE_ROOT/developer-profile.json"
   bun -e "
     const fs = require('fs');
     const p = JSON.parse(fs.readFileSync('$_PROFILE','utf-8'));
     p.declared = p.declared || {};
     p.declared.scope_appetite = <Q1_VALUE>;
     p.declared.risk_tolerance = <Q2_VALUE>;
     p.declared.detail_preference = <Q3_VALUE>;
     p.declared.autonomy = <Q4_VALUE>;
     p.declared.architecture_care = <Q5_VALUE>;
     p.declared_at = new Date().toISOString();
     const tmp = '$_PROFILE.tmp';
     fs.writeFileSync(tmp, JSON.stringify(p, null, 2));
     fs.renameSync(tmp, '$_PROFILE');
   "
   ```

2. Touch the marker so the Setup gate doesn't re-fire:
   ```bash
   touch ~/.gstack/.declared-setup-prompted
   ```
   Touch it even if the user bails out partway — they were asked; they chose
   not to complete. The Setup gate respects that. They can rerun the 5-Q
   anytime with `/plan-tune setup` (Step 0 power-user shortcut).

3. Tell the user: "Profile set. Question tuning is on. Use `/plan-tune`
   again any time to inspect, adjust, or turn it off."

4. Show the profile inline as a confirmation (see `Inspect profile` below).

---
