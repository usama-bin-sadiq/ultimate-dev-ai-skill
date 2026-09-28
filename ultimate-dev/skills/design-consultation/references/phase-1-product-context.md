<!-- Moved verbatim from design-consultation/SKILL.md, the
     'phase-1-product-context' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 1: Product Context

Confirm product context in Q1, pre-filled from the codebase; then ask the memorable-thing question.

**AskUserQuestion Q1 — include ALL of these:**
1. Confirm what the product is, who it's for, what space/industry
2. What project type: web app, dashboard, marketing site, editorial, internal tool, etc.
3. "Want me to research what top products in your space are doing for design, or should I work from my design knowledge?"
4. **Explicitly say:** "At any point you can just drop into chat and we'll talk through anything — this isn't a rigid form, it's a conversation."

Pre-fill context from README or office-hours output, then confirm it and the research preference in Q1.

**Memorable-thing forcing question.** Before moving on, ask the user: *"What's the one
thing you want someone to remember after they see this product for the first time?"*

Record the one-sentence answer: a feeling, visual, claim, or posture. Every subsequent design decision must serve it.

### Taste profile (if this user has prior sessions)

Read this project's taste profile:

```bash
eval "$("~/<agent-config-dir>/gstack/bin/gstack-slug" 2>/dev/null)"
[ -n "${SLUG:-}" ] || { echo "NO_TASTE_PROFILE"; exit 0; }
_TASTE_PROFILE=~/.gstack/projects/$SLUG/taste-profile.json
if [ -f "$_TASTE_PROFILE" ]; then
  # Schema v1: { dimensions: { fonts, colors, layouts, aesthetics }, sessions: [] }
  # Each dimension has approved[] and rejected[] entries with
  # { value, confidence, approved_count, rejected_count, last_seen }
  # Confidence decays 5% per week of inactivity — computed at read time.
  cat "$_TASTE_PROFILE" 2>/dev/null
  echo "TASTE_PROFILE_FOUND"
else
  echo "NO_TASTE_PROFILE"
fi
```

**If TASTE_PROFILE_FOUND:** Parse the full JSON; malformed/unreadable uses the legacy fallback. After decay, rank each dimension by confidence * approved_count (or rejected_count); take three per kind. Count retained sessions (at most 50, not lifetime). Include in the Phase 1 product brief (later shared unchanged with both independent voices):

"Based on [number of retained sessions] recorded sessions, this user's taste leans toward:
fonts [top-3], colors [top-3], layouts [top-3], aesthetics [top-3]. Bias
generation toward these unless the user explicitly requests a different direction.
Also avoid their strong rejections: [top-3 rejected per dimension]."

**Legacy fallback:** Glob `~/.gstack/projects/$SLUG/designs/**/approved.json`; Read the five newest. Use explicit feedback only, never infer fonts/colors from variant letters. No usable files: continue without a taste profile.

**Conflict handling:** If the current user request contradicts a strong persistent
signal (e.g., "make it playful" when taste profile strongly prefers minimal), flag
it: "Note: your taste profile strongly prefers minimal. You're asking for playful
this time — I'll proceed, but want me to update the taste profile, or treat this
as a one-off?"

**Decay:** Multiply stored confidence by 0.95 raised to elapsed weeks since last_seen (minimum zero weeks). Skip invalid dates/confidence; do not rewrite the file while reading.

**Schema migration:** If the file has no `version` field or `version: 0`, it's
the legacy approved.json aggregate — `~/<agent-config-dir>/gstack/bin/gstack-taste-update`
will migrate it to schema v1 on the next write.

Before Phase 3, assemble one **product brief** with the confirmed product and users, project type and use scene, existing constraints, the memorable-thing answer, a taste summary, and Phase 2 findings with source URLs or an explicit declined/unavailable status. For a v1 taste profile, count its retained `sessions` entries (at most 50), not lifetime approvals; with no usable sessions, do not invent a count. Use the same facts for your draft and both independent voices; keep your proposed direction out of their prompts. Taste is a preference, not a constraint; justify departures through the memorable-thing answer.

---
