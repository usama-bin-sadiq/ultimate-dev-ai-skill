<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Consent + opt-in

**When this fires.** Step 0's consent gate: `question_tuning` is `false` AND
`~/.gstack/.question-tuning-prompted` is missing. The user has never been
asked.

**Privacy note.** gstack defaults `question_tuning` to `false` for every user.
There is no auto-flip for any cohort. The consent prompt is the only path to
enabling, and the answer is honored with a marker file so the user is never
re-asked. Contributors are not auto-enrolled. If the user is a contributor
(`gstack_contributor: true`), the
prompt can mention it as additional context, but the decision is still
explicit.

**Flow:**

1. Detect contributor state (for prompt framing only, not for auto-action):
   ```bash
   _QT=$(~/.claude/skills/gstack/bin/gstack-config get question_tuning 2>/dev/null || echo "false")
   _CONTRIB=$(~/.claude/skills/gstack/bin/gstack-config get gstack_contributor 2>/dev/null || echo "false")
   echo "QUESTION_TUNING: $_QT"
   echo "CONTRIBUTOR: $_CONTRIB"
   ```

2. AskUserQuestion (use the contributor-specific framing only if `_CONTRIB=true`,
   otherwise use the general framing):

   **General framing:**
   > Question tuning is off. gstack can learn which of its prompts you find
   > valuable vs noisy — so over time, gstack stops asking questions you've
   > already answered the same way. It takes about 2 minutes to set up your
   > initial profile. v1 is observational: gstack tracks your preferences
   > and shows you a profile, but doesn't silently change skill behavior yet.
   > Logs stay local (`~/.gstack/projects/<slug>/question-log.jsonl`).
   >
   > RECOMMENDATION: Enable and set up your profile. Completeness: A=9/10.
   >
   > A) Enable + set up (recommended, ~2 min)
   > B) Enable but skip setup (I'll fill it in later)
   > C) Cancel — I'm not ready

   **Contributor framing (only if `_CONTRIB=true`):**
   > You're a gstack contributor. Question tuning isn't on by default for
   > anyone, but contributors are the cohort whose data most helps v2 work
   > (skills adapting to your steering style). Enabling logs every
   > AskUserQuestion outcome locally to
   > `~/.gstack/projects/<slug>/question-log.jsonl` — nothing leaves your
   > machine. v1 is observational only.
   >
   > RECOMMENDATION: Enable and set up your profile. Completeness: A=9/10.
   >
   > A) Enable + set up (recommended for contributors, ~2 min)
   > B) Enable but skip setup (I'll fill it in later)
   > C) Cancel — I'm not ready

3. ALWAYS touch the marker, regardless of choice:
   ```bash
   touch ~/.gstack/.question-tuning-prompted
   ```

4. If A or B: enable:
   ```bash
   ~/.claude/skills/gstack/bin/gstack-config set question_tuning true
   ```

5. If C: do nothing else. Tell the user: "Question tuning stays off. Re-enable
   any time with `/plan-tune enable` or `gstack-config set question_tuning true`."
