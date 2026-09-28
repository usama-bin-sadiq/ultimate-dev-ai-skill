<!-- Moved verbatim from plan-design-review/SKILL.md, the
     'step-0-design-scope-assessment' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0: Design Scope Assessment

### 0A. Initial Design Rating
Rate the plan's overall design completeness 0-10.
- "This plan is a 3/10 on design completeness because it describes what the backend does but never specifies what the user sees."
- "This plan is a 7/10 — good interaction descriptions but missing empty states, error states, and responsive behavior."

Explain what a 10 looks like for THIS plan.

### 0B. DESIGN.md Status
- If DESIGN.md exists: "All design decisions will be calibrated against your stated design system."
- If no DESIGN.md: "No design system found. Recommend running /design-consultation first. Proceeding with universal design principles."

### 0C. Existing Design Leverage
What existing UI patterns, components, or design decisions in the codebase should this plan reuse? Don't reinvent what already works.

### 0D. Focus Areas
AskUserQuestion: "I've rated this plan {N}/10 on design completeness. The biggest gaps are {X, Y, Z}. I'll generate visual mockups next, then review all 7 dimensions. Want me to focus on specific areas instead of all 7?"

**STOP.** Do NOT proceed until user responds.
