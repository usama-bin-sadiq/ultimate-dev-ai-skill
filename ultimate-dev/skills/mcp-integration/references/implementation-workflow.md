<!-- Moved verbatim from mcp-integration/SKILL.md, the
     'implementation-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Implementation Workflow

To add MCP integration to a plugin:

1. Choose MCP server type (stdio, SSE, HTTP, ws)
2. Create `.mcp.json` at plugin root with configuration
3. Use ${CLAUDE_PLUGIN_ROOT} for all file references
4. Document required environment variables in README
5. Test locally with `/mcp` command
6. Pre-allow MCP tools in relevant commands
7. Handle authentication (OAuth or tokens)
8. Test error cases (connection failures, auth errors)
9. Document MCP integration in plugin README

Focus on stdio for custom/local servers, SSE for hosted services with OAuth.

Each file below is loaded on demand, not at triage. 15 file(s):

- `references/additional-resources.md` — Additional Resources. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/authentication-patterns.md` — Authentication Patterns. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/debugging.md` — Debugging. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/environment-variable-expansion.md` — Environment Variable Expansion. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/error-handling.md` — Error Handling. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/implementation-workflow.md` — Implementation Workflow. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/integration-patterns.md` — Integration Patterns. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/lifecycle-management.md` — Lifecycle Management. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/mcp-server-configuration-methods.md` — MCP Server Configuration Methods. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/mcp-server-types.md` — MCP Server Types. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/mcp-tool-naming.md` — MCP Tool Naming. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/performance-considerations.md` — Performance Considerations. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/quick-reference.md` — Quick Reference. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/security-best-practices.md` — Security Best Practices. <!-- Moved verbatim from mcp-integration/SKILL.md, the
- `references/testing-mcp-integration.md` — Testing MCP Integration. <!-- Moved verbatim from mcp-integration/SKILL.md, the
