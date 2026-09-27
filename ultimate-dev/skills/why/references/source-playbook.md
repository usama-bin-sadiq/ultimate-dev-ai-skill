# Source playbooks

The why skill spawns one investigator per available evidence category, each reading a single source-specific playbook below. The playbooks are concrete examples for common MCPs; adapt them for a different MCP in the same category.

| Category | Example MCP it documents |
|---|---|
| Source control history | git, `gh` |
| Issue / ticket tracker | Linear (adapt for Jira, GitHub Issues, Plane, Shortcut) |
| Long-form documents | Notion (adapt for Confluence, Google Docs, Coda) |
| Real-time team chat | Slack (adapt for Discord, Microsoft Teams, Mattermost) |
| Infrastructure observability | Datadog (adapt for New Relic, Honeycomb, Grafana, Splunk) |
| Error / exception tracking | Sentry (adapt for Rollbar, Bugsnag, Airbrake) |
| Product analytics warehouse | Databricks SQL (adapt for Snowflake, BigQuery, ClickHouse, dbt) |

Cross-cutting:

- [`incident-postmortem.md`](./sources/incident-postmortem.md). Add this if the target code looks defensive (null checks, retry, timeout, rate limit, feature flag, egress guard, OOM handler).
