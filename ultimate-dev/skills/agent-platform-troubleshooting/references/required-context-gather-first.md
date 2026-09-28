<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'required-context-gather-first' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Required context (gather first)

Before doing anything else, pin down the basics. If the user hasn't supplied
them, ask. Don't guess.

| Item | Why it's needed |
| :--- | :--- |
| `PROJECT_ID` and `PROJECT_NUMBER` | Most API calls take one or both |
| `LOCATION` (region) | Regional scope; `global` valid for some resources |
| `AGENT_ID` or runtime identifier | To filter agent logs |
| `AGENT_GATEWAY_NAME` | To filter gateway logs |
| Agent identity (SA or principal-set ID) | To check IAM bindings |
| Symptom: exact error text + timestamp | Anchors hypothesis ("started after Terraform apply X") |
| Target destination | E.g. `aiplatform`, `discoveryengine`, MCP server, peer agent |

If only some are known, proceed but call out unknowns in the report. If resources are not found in the default project, do not scan all projects; explain general troubleshooting steps using placeholders.
