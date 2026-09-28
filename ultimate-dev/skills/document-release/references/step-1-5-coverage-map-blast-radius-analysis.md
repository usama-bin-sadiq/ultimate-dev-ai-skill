<!-- Moved verbatim from document-release/SKILL.md, the
     'step-1-5-coverage-map-blast-radius-analysis' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1.5: Coverage Map (Blast-Radius Analysis)

Before touching any documentation file, build a **coverage map** of what shipped vs what's
documented. This is inspired by the Diataxis framework (tutorial / how-to / reference / explanation)
— but applied as an audit lens, not a generation tool.

1. **Extract public surface changes from the diff.** Scan `git diff <diff-base> HEAD` for:
   - New exported functions, classes, commands, CLI flags, config options, API endpoints
   - New skills, workflows, or user-facing capabilities
   - Renamed or removed public surface (modules, commands, features)
   - New environment variables, feature flags, or configuration knobs

2. **For each new/changed public surface item, assess documentation coverage:**

```
Coverage map:
  [entity]         [reference?] [how-to?] [tutorial?] [explanation?]
  /new-skill       ✅ <agent-instructions>  ❌        ❌          ❌
  --new-flag       ✅ README     ✅ README  ❌          ❌
  FooProcessor     ❌            ❌        ❌          ❌
```

Use these definitions:
- **Reference** — factual description of what it is, its API, its options (README tables, <agent-instructions> skill lists, API docs)
- **How-to** — task-oriented: "how to do X with this" (README examples, CONTRIBUTING workflows)
- **Tutorial** — learning-oriented: step-by-step walkthrough for newcomers (getting started guides)
- **Explanation** — understanding-oriented: "why this works this way" (ARCHITECTURE decisions, design rationale)

3. **Output the coverage map.** Items with zero coverage are **critical gaps** — flag them for
   Step 3. Items with reference-only coverage are **common gaps** — note them for the PR body.

4. **Architecture diagram drift detection.** If ARCHITECTURE.md (or any doc) contains ASCII
   diagrams or Mermaid blocks, extract entity names (modules, services, data flows) from the
   diagrams. Cross-reference against the diff. Flag any diagram entities that were renamed,
   split, removed, or moved in the code.

The coverage map feeds into Steps 2-3 (what to audit and fix) and Step 9 (documentation debt
summary in the PR body). Do NOT auto-generate missing documentation pages — flag gaps only.
When significant gaps are found, suggest running `/document-generate` to fill them.

---

> **STOP.** Before auditing each doc file and applying updates, polishing CHANGELOG voice, checking cross-doc consistency, cleaning up TODOS, the VERSION bump, and committing (Steps 2-9, after the coverage map in Step 1.5), Read `~/<agent-config-dir>/gstack/document-release/sections/release-body.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

---
