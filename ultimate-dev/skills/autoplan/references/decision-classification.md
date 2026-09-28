<!-- Moved verbatim from autoplan/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Decision Classification

Every auto-decision is classified:

**Mechanical** — one clearly right answer. Auto-decide silently.
Examples: run the outside reviewer when enabled (always yes), run evals (always yes), reduce scope on a complete plan (always no).

**Taste** — reasonable people could disagree. Auto-decide with recommendation, but surface at the final gate. Three natural sources:
1. **Close approaches** — top two are both viable with different tradeoffs.
2. **Borderline scope** — in blast radius but 3-5 files, or ambiguous radius.
3. **Codex disagreements** — the outside reviewer recommends differently and has a valid point.

**User Challenge** — Claude and Codex both recommend changing the
user's stated direction: merge, split, add or remove features/skills/workflows.
NEVER auto-decide these. At the final approval gate, give:
the original direction, proposed change, reasoning, blind spots and cost of being
wrong, using the Phase 4 template. Flag agreed security/feasibility risks explicitly.
The user's original direction stands unless they approve the change.

---
