<!-- Moved verbatim from command-development/SKILL.md, the
     'bash-execution-in-commands' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Bash Execution in Commands

Commands can execute bash commands inline to dynamically gather context before Claude processes the command. This is useful for including repository state, environment information, or project-specific context.

**When to use:**

- Include dynamic context (git status, environment vars, etc.)
- Gather project/repository state
- Build context-aware workflows

**Implementation details:**
For complete syntax, examples, and best practices, see `references/plugin-features-reference.md` section on bash execution. The reference includes the exact syntax and multiple working examples to avoid execution issues
