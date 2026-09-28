<!-- Moved verbatim from command-development/SKILL.md, the
     'reference-files' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [`references/advanced-workflows.md`](references/advanced-workflows.md)
- [`references/documentation-patterns.md`](references/documentation-patterns.md)
- [`references/interactive-commands.md`](references/interactive-commands.md)
- [`references/marketplace-considerations.md`](references/marketplace-considerations.md)
- [
Each file below is loaded on demand, not at triage. 15 file(s):

- `references/bash-execution-in-commands.md` — Bash Execution in Commands. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/best-practices.md` — Best Practices. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/command-basics.md` — Command Basics. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/command-organization.md` — Command Organization. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/common-patterns.md` — Common Patterns. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/dynamic-arguments.md` — Dynamic Arguments. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/file-format.md` — File Format. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/file-references.md` — File References. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/integration-with-plugin-components.md` — Integration with Plugin Components. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/overview.md` — Overview. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/plugin-specific-features.md` — Plugin-Specific Features. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/reference-files.md` — Reference files. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/troubleshooting.md` — Troubleshooting. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/validation-patterns.md` — Validation Patterns. <!-- Moved verbatim from command-development/SKILL.md, the
- `references/yaml-frontmatter-fields.md` — YAML Frontmatter Fields. <!-- Moved verbatim from command-development/SKILL.md, the

`references/testing-strategies.md`](references/testing-strategies.md)

### Bash Commands

1. **Limit scope:** Use `Bash(git:*)` not `Bash(*)`
2. **Safe commands:** Avoid destructive operations
3. **Handle errors:** Consider command failures
4. **Keep fast:** Long-running commands slow invocation

### Documentation

1. **Add comments:** Explain complex logic
2. **Provide examples:** Show usage in comments
3. **List requirements:** Document dependencies
4. **Version commands:** Note breaking changes

```markdown
---
description: Deploy application to environment
argument-hint: [environment] [version]
---

<!--
Usage: /deploy [staging|production] [version]
Requires: AWS credentials configured
Example: /deploy staging v1.2.3
-->

Deploy application to $1 environment using version $2...
```
