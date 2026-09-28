<!-- Moved verbatim from hook-development/SKILL.md, the
     'implementation-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Implementation Workflow

To implement hooks in a plugin:

1. Identify events to hook into (PreToolUse, Stop, SessionStart, etc.)
2. Decide between prompt-based (flexible) or command (deterministic) hooks
3. Write hook configuration in `hooks/hooks.json`
4. For command hooks, create hook scripts
5. Use ${CLAUDE_PLUGIN_ROOT} for all file references
6. Validate configuration with `scripts/validate-hook-schema.sh hooks/hooks.json`
7. Test hooks with `scripts/test-hook.sh` before deployment
8. Test in Claude Code with `claude --debug`
9. Document hooks in plugin README

Focus on prompt-based hooks for most use cases. Reserve command hooks for performance-critical or deterministic checks.

Each file below is loaded on demand, not at triage. 15 file(s):

- `references/additional-resources.md` — Additional Resources. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/debugging-hooks.md` — Debugging Hooks. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/environment-variables.md` — Environment Variables. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/hook-configuration-formats.md` — Hook Configuration Formats. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/hook-input-format.md` — Hook Input Format. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/hook-lifecycle-and-limitations.md` — Hook Lifecycle and Limitations. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/hook-output-format.md` — Hook Output Format. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/hook-types.md` — Hook Types. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/implementation-workflow.md` — Implementation Workflow. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/matchers.md` — Matchers. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/performance-considerations.md` — Performance Considerations. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/plugin-hook-configuration.md` — Plugin Hook Configuration. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/quick-reference.md` — Quick Reference. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/security-best-practices.md` — Security Best Practices. <!-- Moved verbatim from hook-development/SKILL.md, the
- `references/temporarily-active-hooks.md` — Temporarily Active Hooks. <!-- Moved verbatim from hook-development/SKILL.md, the
