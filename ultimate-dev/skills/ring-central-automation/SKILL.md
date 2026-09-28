---
name: ring-central-automation
description: "RingCentral automation via Rube MCP -- toolkit not currently available in Composio; no RING_CENTRAL_ tools found"
requires:
  mcp:
    - rube
---

# RingCentral Automation

> **Status: Toolkit Not Available** -- RUBE_SEARCH_TOOLS returned no `ring_central`-specific tools. The RingCentral toolkit is not currently available in Composio's tool catalog. Searches returned tools from unrelated toolkits (ClickSend, Telnyx, Slack) instead.

**Toolkit docs:** [composio.dev/toolkits/ring_central](https://composio.dev/toolkits/ring_central)

---

## Setup

1. Add the Rube MCP server to your environment: `https://rube.app/mcp`
2. Check availability by calling `RUBE_SEARCH_TOOLS` with RingCentral-related queries
3. If `RING_CENTRAL_*` tools appear in the future, connect via `RUBE_MANAGE_CONNECTIONS` with toolkit `ring_central`

---

## Current Status

As of the last tool discovery scan, no `RING_CENTRAL_*` tool slugs were returned by RUBE_SEARCH_TOOLS. Queries for RingCentral messaging, call logs, fax, and extension management all returned tools from other toolkits:

- SMS/messaging queries returned **ClickSend** tools (`CLICKSEND_CREATE_SMS_SEND`, etc.)
- Call management queries returned **Pipedrive** call log tools
- Telephony/VoIP queries returned **Telnyx** notification tools
- Fax queries returned **ClickSend** fax automation tools

This indicates the `ring_central` toolkit either has no tools registered or is not yet integrated into the Composio platform.

---

## Alternatives

If you need telephony, SMS, or communication automation, consider these available toolkits:

| Need | Alternative Toolkit | Example Tool |
|------|-------------------|--------------|
| SMS messaging | ClickSend | `CLICKSEND_CREATE_SMS_SEND` |
| VoIP/telephony | Telnyx | `TELNYX_CREATE_NOTIFICATION_CHANNEL` |
| Team messaging | Slack / Webex | `SLACK_SEND_MESSAGE` / `WEBEX_MESSAGING_CREATE_MESSAGE` |

---

## When Tools Become Available

Once RingCentral tools are added to Composio, this skill should be updated with real tool slugs, schemas, and pitfalls following the same pattern as other automation skills in this collection.

---

*Powered by [Composio](https://composio.dev)*

## Prerequisites

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Rube MCP must be connected (RUBE_SEARCH_TOOLS available)
- Active RingCentral connection via `RUBE_MANAGE_CONNECTIONS` with toolkit `ring_central`
- Always call `RUBE_SEARCH_TOOLS` first to get current tool schemas

## Tool Discovery

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always discover available tools before executing workflows:

```
RUBE_SEARCH_TOOLS: queries=[{"use_case": "calls, messages, meetings, and unified communications", "known_fields": ""}]
```

This returns:
- Available tool slugs for RingCentral
- Recommended execution plan steps
- Known pitfalls and edge cases
- Input schemas for each tool

## Search Before Action

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always search for existing resources before creating new ones to avoid duplicates.

## Pagination

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Many list operations support pagination. Check responses for `next_cursor` or `page_token` and continue fetching until exhausted.

## Error Handling

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Check tool responses for errors before proceeding
- If a tool fails, verify the connection is still ACTIVE
- Re-authenticate via `RUBE_MANAGE_CONNECTIONS` if connection expired

## Batch Operations

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

For bulk operations, use `RUBE_REMOTE_WORKBENCH` with `run_composio_tool()` in a loop with `ThreadPoolExecutor` for parallel execution.

## Common Patterns

<!-- Carried from the underscore-named ring_central-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

