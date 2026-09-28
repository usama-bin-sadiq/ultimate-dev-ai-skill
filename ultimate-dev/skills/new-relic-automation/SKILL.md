---
name: new-relic-automation
description: "Automate New Relic observability workflows -- manage alert policies, notification channels, alert conditions, and monitor applications and browser apps via the Composio MCP integration."
requires:
  mcp:
    - rube
---

# New Relic Automation

Automate your New Relic observability workflows -- create and manage alert policies, configure notification channels (email, Slack, webhook, PagerDuty), monitor APM applications, inspect alert conditions, and integrate New Relic alerting into cross-app pipelines.

**Toolkit docs:** [composio.dev/toolkits/new_relic](https://composio.dev/toolkits/new_relic)

---

## Setup

1. Add the Composio MCP server to your client: `https://rube.app/mcp`
2. Connect your New Relic account when prompted (API key authentication)
3. Start using the workflows below

---

## Core Workflows

### 1. List Alert Policies

Use `NEW_RELIC_GET_ALERT_POLICIES` to discover existing alert policies with optional filtering.

```
Tool: NEW_RELIC_GET_ALERT_POLICIES
Inputs:
  - name: string (optional, partial match supported)
  - incident_preference: "PER_POLICY" | "PER_CONDITION" | "PER_CONDITION_AND_TARGET"
  - page: integer (1-indexed pagination)
```

### 2. Create an Alert Policy

Use `NEW_RELIC_CREATE_ALERT_POLICY` to set up a new policy container for alert conditions.

```
Tool: NEW_RELIC_CREATE_ALERT_POLICY
Inputs:
  - name: string (required) -- must be unique within the account
  - incident_preference: "PER_POLICY" | "PER_CONDITION" | "PER_CONDITION_AND_TARGET" (default: PER_POLICY)
```

**Incident preferences explained:**
- `PER_POLICY` -- one issue per policy (recommended for most use cases)
- `PER_CONDITION` -- one issue per alert condition
- `PER_CONDITION_AND_TARGET` -- one issue per condition and signal/target

### 3. Create Alert Notification Channels

Use `NEW_RELIC_CREATE_ALERT_CHANNEL` to register notification endpoints for alert delivery.

```
Tool: NEW_RELIC_CREATE_ALERT_CHANNEL
Inputs:
  - type: "email" | "slack" | "webhook" | "pagerduty" | "opsgenie" | "victorops" (required)
  - name: string (required) -- human-readable channel name
  - configuration: object (required) -- varies by type:
    Email:     { recipients: "devops@example.com,oncall@example.com" }
    Slack:     { url: "<slack_webhook_url>", channel: "alerts" }
    Webhook:   { url: "https://hooks.example.com/alerts", auth_username, auth_password }
    PagerDuty: { service_key: "<integration_key>" }
    OpsGenie:  { api_key, recipients, tags, teams }
    VictorOps: { key: "<api_key>", route_key: "<routing_key>" }
```

### 4. Get Alert Conditions for a Policy

Use `NEW_RELIC_GET_ALERT_CONDITIONS` to inspect the conditions attached to a specific policy.

```
Tool: NEW_RELIC_GET_ALERT_CONDITIONS
Inputs:
  - policy_id: integer (required)
```

### 5. Monitor Applications

Use `NEW_RELIC_GET_APPLICATIONS` and `NEW_RELIC_GET_BROWSER_APPLICATIONS` to list APM and browser-monitored apps.

```
Tool: NEW_RELIC_GET_APPLICATIONS
Inputs:
  - name: string (optional, case-insensitive partial match)
  - host: string (optional, case-insensitive partial match)
  - ids: string (optional, comma-separated list of app IDs)
  - page: integer (1-indexed)

Tool: NEW_RELIC_GET_BROWSER_APPLICATIONS
Inputs:
  - filter[name]: string (optional, case-insensitive partial match)
  - page: integer (1-indexed)
```

### 6. Manage Channels and Policies

Use `NEW_RELIC_UPDATE_ALERT_CHANNEL` to modify existing channels and `NEW_RELIC_DELETE_ALERT_POLICY` to remove policies.

```
Tool: NEW_RELIC_UPDATE_ALERT_CHANNEL
Inputs:
  - alert_channel_id: integer (required)
  - name: string (optional)
  - type: string (optional, only to change type)
  - configuration: object (optional, fields vary by type)

Tool: NEW_RELIC_DELETE_ALERT_POLICY
Inputs:
  - policy_id: string (required) -- ID of the policy to delete
```

---

## Known Pitfalls

| Pitfall | Detail |
|---------|--------|
| Unique policy names | `NEW_RELIC_CREATE_ALERT_POLICY` requires the name to be unique within the account. |
| Channel config varies by type | The `configuration` object for `NEW_RELIC_CREATE_ALERT_CHANNEL` has different required fields per channel type (e.g., `recipients` for email, `service_key` for PagerDuty). |
| Pagination required | All list endpoints return paginated results. Iterate pages until results are exhausted. |
| Policy ID type mismatch | `NEW_RELIC_GET_ALERT_CONDITIONS` expects `policy_id` as an integer, while `NEW_RELIC_DELETE_ALERT_POLICY` expects it as a string. |
| Channel-policy linking | After creating a channel, you must separately associate it with a policy for alerts to flow to that channel. |

---

## Quick Reference

| Tool Slug | Description |
|-----------|-------------|
| `NEW_RELIC_GET_ALERT_POLICIES` | List alert policies with optional filtering |
| `NEW_RELIC_CREATE_ALERT_POLICY` | Create a new alert policy |
| `NEW_RELIC_DELETE_ALERT_POLICY` | Delete an alert policy by ID |
| `NEW_RELIC_CREATE_ALERT_CHANNEL` | Create a notification channel (email, Slack, webhook, etc.) |
| `NEW_RELIC_GET_ALERT_CHANNELS` | List all configured alert channels |
| `NEW_RELIC_UPDATE_ALERT_CHANNEL` | Update an existing alert channel |
| `NEW_RELIC_GET_ALERT_CONDITIONS` | Get alert conditions for a policy |
| `NEW_RELIC_GET_APPLICATIONS` | List APM applications |
| `NEW_RELIC_GET_BROWSER_APPLICATIONS` | List browser-monitored applications |

---

*Powered by [Composio](https://composio.dev)*

## Prerequisites

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Rube MCP must be connected (RUBE_SEARCH_TOOLS available)
- Active New Relic connection via `RUBE_MANAGE_CONNECTIONS` with toolkit `new_relic`
- Always call `RUBE_SEARCH_TOOLS` first to get current tool schemas

## Tool Discovery

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always discover available tools before executing workflows:

```
RUBE_SEARCH_TOOLS: queries=[{"use_case": "APM, alerts, dashboards, NRQL queries, and infrastructure monitoring", "known_fields": ""}]
```

This returns:
- Available tool slugs for New Relic
- Recommended execution plan steps
- Known pitfalls and edge cases
- Input schemas for each tool

## Search Before Action

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always search for existing resources before creating new ones to avoid duplicates.

## Pagination

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Many list operations support pagination. Check responses for `next_cursor` or `page_token` and continue fetching until exhausted.

## Error Handling

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Check tool responses for errors before proceeding
- If a tool fails, verify the connection is still ACTIVE
- Re-authenticate via `RUBE_MANAGE_CONNECTIONS` if connection expired

## Batch Operations

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

For bulk operations, use `RUBE_REMOTE_WORKBENCH` with `run_composio_tool()` in a loop with `ThreadPoolExecutor` for parallel execution.

## Common Patterns

<!-- Carried from the underscore-named new_relic-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

