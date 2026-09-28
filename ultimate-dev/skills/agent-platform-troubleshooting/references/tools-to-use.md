<!-- Moved verbatim from agent-platform-troubleshooting/SKILL.md, the
     'tools-to-use' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Tools to use

The skill assumes the agent has access to:

-   **`run_gcloud_command (via the host's MCP layer)`** (or **`default_api:run_command`**
    running raw `gcloud` CLI) — for `gcloud` invocations (registry listing,
    authz-extensions describe, IAM, project lookup).
-   **`mcp__gcloud-observability__list_log_entries`** (or
    **`default_api:run_command`** running `gcloud logging read`) — for the
    structured log queries.
-   **`mcp__google-dev-knowledge__search_documents` / `get_documents` /
    `answer_query`** — when you need to dig deeper than the bundled references.
-   **`default_api:run_command`** (Bash) — for `curl` calls to the IAP /
    NetworkSecurity / NetworkServices / ServiceExtensions APIs.

Run independent log queries in parallel if supported.
