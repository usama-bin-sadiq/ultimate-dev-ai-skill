<!-- Moved verbatim from plan-devex-review/SKILL.md, the 'Auto-Detect Product Type + Applicability Gate' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Auto-Detect Product Type + Applicability Gate

Before proceeding, read the plan and infer the developer product type from content:

- Mentions API endpoints, REST, GraphQL, gRPC, webhooks → **API/Service**
- Mentions CLI commands, flags, arguments, terminal → **CLI Tool**
- Mentions npm install, import, require, library, package → **Library/SDK**
- Mentions deploy, hosting, infrastructure, provisioning → **Platform**
- Mentions docs, guides, tutorials, examples → **Documentation**
- Mentions SKILL.md, skill template, Claude Code, AI agent, MCP → **Claude Code Skill**

If NONE of the above: the plan has no developer-facing surface. Tell the user:
"This plan doesn't appear to have developer-facing surfaces. /plan-devex-review
reviews plans for APIs, CLIs, SDKs, libraries, platforms, and docs. Consider
/plan-eng-review or /plan-design-review instead." Exit gracefully.

If detected: State your classification and ask for confirmation. Do not ask from
scratch. "I'm reading this as a CLI Tool plan. Correct?"

**STOP. Ask for product-type confirmation before deeper branch research.**
After the answer, carry the confirmed type into Step 0A; do not treat an
unanswered guess as persona approval.

A product can be multiple types. Identify the primary type for the initial assessment.
Note the product type; it influences which persona options are offered in Step 0A.

---
