<!-- Moved verbatim from design-html/SKILL.md, the 'Step 5: Save & Next Steps' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5: Save & Next Steps

### Design Token Extraction

If no `DESIGN.md` exists in the repo root, offer to create one from the generated HTML:

Extract from the HTML:
- CSS custom properties (colors, spacing, font sizes)
- Font families and weights used
- Color palette (primary, secondary, accent, neutral)
- Spacing scale
- Border radius values
- Shadow values

Use AskUserQuestion:
> No DESIGN.md found. I can extract the design tokens from the HTML we just built
> and create a DESIGN.md for your project. This means future /design-shotgun and
> /design-html runs will be style-consistent automatically.
> A) Create DESIGN.md from these tokens
> B) Skip — I'll handle the design system later

If A: write `DESIGN.md` in the open DESIGN.md format (/design-consultation Phase 6 template): extracted values in the front matter's five token groups, line 2 `# gstack: design-md-format=spec`, rationale in the canonical sections. An existing file keeps its persisted format choice; never offer a conversion here.

### Save Metadata

Write `finalized.json` alongside the HTML:
```json
{
  "source_mockup": "<approved variant PNG path or null>",
  "source_plan": "<CEO plan path or null>",
  "mode": "<approved-mockup|plan-driven|freeform|evolve>",
  "html_file": "<path to finalized.html or component file>",
  "pretext_tier": "<selected tier>",
  "framework": "<vanilla|react|svelte|vue>",
  "iterations": <number of refinement iterations>,
  "date": "<ISO 8601>",
  "screen": "<screen name>",
  "branch": "<current branch>"
}
```

### Next Steps

Use AskUserQuestion:
> Design finalized with Pretext-native layout. What's next?
> A) Copy to project — copy the HTML/component into your codebase
> B) Iterate more — keep refining
> C) Done — I'll use this as a reference

---
