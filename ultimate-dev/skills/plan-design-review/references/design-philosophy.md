<!-- Moved verbatim from plan-design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Design Philosophy

Review for intentional UI with an opinionated, collaborative posture. Find every
gap, explain why it matters, recommend a concrete fix, and get its individual
decision before editing. Even obvious fixes need approval; DESIGN.md supplies
the recommendation, not the user's approval.

When creating the initial plan artifact, copy existing requirements and record
unapproved gaps as pending. A gap-to-token mapping is a proposed fix, not a
completed decision. Do not write those fixes into accepted implementation tasks
or raise their scores before their individual approvals.

Do NOT make any code changes. Do NOT start implementation. Your only job right now
is to review and improve the plan's design decisions with maximum rigor.

### The gstack designer — YOUR PRIMARY TOOL

Use the **gstack designer** by default to turn design briefs into real visual mockups.

**The rule is simple:** If the plan has UI and the designer is available, generate mockups.
Don't ask permission. Don't write text descriptions of what a homepage "could look like."
Show it. The only reason to skip mockups is when there is literally no UI to design
(pure backend, API-only, infrastructure).

Design reviews without visuals are just opinion. Mockups ARE the plan for design work.
You need to see the design before you code it.

Commands: `generate` (single mockup), `variants` (multiple directions), `compare`
(side-by-side review board), `iterate` (refine with feedback), `check` (cross-model
quality gate via GPT-4o vision), `evolve` (improve from screenshot).

Setup is handled by the DESIGN SETUP section below. If `DESIGN_READY` is printed,
the designer is available and you should use it.
