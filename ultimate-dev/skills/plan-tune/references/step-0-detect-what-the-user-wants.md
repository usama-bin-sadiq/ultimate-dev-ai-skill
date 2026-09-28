<!-- Moved verbatim from plan-tune/SKILL.md, the
     'step-0-detect-what-the-user-wants' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0: Detect what the user wants

Read the user's message. Route based on plain-English intent, not keywords.

**Implicit gates run first** (before user-intent routing). These exist so first-time
users see the consent prompt, so explicit opt-ins eventually run the 5-Q setup,
and so accumulated free-text answers get dream-cycled into actionable proposals.
Each gate is guarded by a marker so the user is prompted at most once per choice.

1. **Consent gate.** If `question_tuning` is `false` AND
   `~/.gstack/.question-tuning-prompted` is missing → run `Consent + opt-in`
   below. Honor the answer with a marker write either way; do not re-prompt.
2. **Setup gate.** If `question_tuning` is `true` AND
   `~/.gstack/developer-profile.json`'s `declared` object is empty AND
   `~/.gstack/.declared-setup-prompted` is missing → run `5-Q setup` below.
   Touch the marker after setup completes OR is declined.
3. **Dream-cycle gate (Layer 8 / cathedral T10/T11).** If
   `~/.gstack/projects/<slug>/distillation-proposals.json` exists AND has
   `applied_at` missing on any proposal → run `Dream cycle review` below.
   Marker: each proposal carries its own `applied_at` so re-firing this
   gate naturally skips already-handled items.

When no implicit gate fires, route by user intent:

4. **"Show my profile" / "what do you know about me" / "show my vibe"** →
   run `Inspect profile`.
5. **"Review questions" / "what have I been asked" / "show recent"** →
   run `Review question log`.
6. **"Stop asking me about X" / "never ask about Y" / "tune: ..."** →
   run `Set a preference`.
7. **"Update my profile" / "I'm more boil-the-ocean than that" / "I've changed
   my mind"** → run `Edit declared profile` (confirm before writing).
8. **"Show the gap" / "how far off is my profile"** → run `Show gap`.
9. **"Dream cycle" / "distill" / "what have I been free-texting"** →
   run `Dream cycle distill` below (triggers `gstack-distill-free-text`).
10. **"Turn it off" / "disable"** → `~/.claude/skills/gstack/bin/gstack-config set question_tuning false`
11. **"Turn it on" / "enable"** → `~/.claude/skills/gstack/bin/gstack-config set question_tuning true && touch ~/.gstack/.question-tuning-prompted`
12. **Clear ambiguity** — if you can't tell what the user wants, ask plainly:
    "Do you want to (a) see your profile, (b) review recent questions, (c) set
    a preference, (d) update your declared profile, (e) run the dream cycle,
    or (f) turn it off?"

Power-user shortcuts (one-word invocations) — handle these too:
`profile`, `vibe`, `gap`, `stats`, `review`, `enable`, `disable`, `setup`,
`distill`, `dream`, `audit`.

---
