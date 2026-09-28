<!-- Moved verbatim from figma-create-design-system-rules/SKILL.md, the
     'project-specific-conventions' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Project-Specific Conventions

- [Add any unique architectural patterns]
- [Add any special import requirements]
- [Add any testing requirements]
- [Add any accessibility standards]
- [Add any performance considerations]
```

### Step 4: Save Rules to the Appropriate Rule File

Detect which AI coding agent the user is working with and save the generated rules to the corresponding file:

| Agent | Rule File | Notes |
|-------|-----------|-------|
| Claude Code | `CLAUDE.md` in project root | Markdown format. Can also use `.claude/rules/figma-design-system.md` for modular organization. |
| Codex CLI | `AGENTS.md` in project root | Markdown format. Append as a new section if file already exists. 32 KiB combined size limit. |
| Cursor | `.cursor/rules/figma-design-system.mdc` | Markdown with YAML frontmatter (`description`, `globs`, `alwaysApply`). |

If unsure which agent the user is working with, check for existing rule files in the project or ask the user.

For Cursor, wrap the rules with YAML frontmatter:

```markdown
---
description: Rules for implementing Figma designs using the Figma MCP server. Covers component organization, styling conventions, design tokens, asset handling, and the required Figma-to-code workflow.
globs: "src/components/**"
alwaysApply: false
---

[Generated rules here]
```

Customize the `globs` pattern to match the directories where Figma-derived code will live in the project (e.g., `"src/**/*.tsx"` or `["src/components/**", "src/pages/**"]`).

After saving, the rules will be automatically loaded by the agent and applied to all Figma implementation tasks.

### Step 5: Validate and Iterate

After creating rules:

1. Test with a simple Figma component implementation
2. Verify the agent follows the rules correctly
3. Refine any rules that aren't working as expected
4. Share with team members for feedback
5. Update rules as the project evolves
