---
name: zoho-desk-automation
description: "Zoho Desk automation via Rube MCP -- toolkit not currently available in Composio; no ZOHO_DESK_ tools found"
requires:
  mcp:
    - rube
---

# Zoho Desk Automation

> **Status: Toolkit Not Available** -- RUBE_SEARCH_TOOLS returned no `zoho_desk`-specific tools. The Zoho Desk toolkit is not currently available in Composio's tool catalog. Searches returned tools from unrelated helpdesk and CRM toolkits instead.

**Toolkit docs:** [composio.dev/toolkits/zoho_desk](https://composio.dev/toolkits/zoho_desk)

---

## Setup

1. Add the Rube MCP server to your environment: `https://rube.app/mcp`
2. Check availability by calling `RUBE_SEARCH_TOOLS` with Zoho Desk-related queries
3. If `ZOHO_DESK_*` tools appear in the future, connect via `RUBE_MANAGE_CONNECTIONS` with toolkit `zoho_desk`

---

## Current Status

As of the last tool discovery scan, no `ZOHO_DESK_*` tool slugs were returned by RUBE_SEARCH_TOOLS. Queries for Zoho Desk ticket management, contacts, agents, and departments all returned tools from other toolkits:

- Ticket creation queries returned **Freshdesk** (`FRESHDESK_CREATE_TICKET`), **HubSpot** (`HUBSPOT_CREATE_TICKET`), and **Zendesk** (`ZENDESK_CREATE_ZENDESK_TICKET`) tools
- Contact listing queries returned **Zoho Invoice** (`ZOHO_INVOICE_LIST_CONTACTS`) tools
- Agent/department queries returned **Zoho CRM** (`ZOHO_GET_ZOHO_USERS`) tools

This indicates the `zoho_desk` toolkit either has no tools registered or is not yet integrated into the Composio platform.

---

## Alternatives

If you need helpdesk and support ticket automation, consider these available toolkits:

| Need | Alternative Toolkit | Example Tools |
|------|-------------------|---------------|
| Ticket management | Freshdesk | `FRESHDESK_CREATE_TICKET`, `FRESHDESK_UPDATE_TICKET` |
| Ticket management | Zendesk | `ZENDESK_CREATE_ZENDESK_TICKET` |
| Ticket management | HubSpot | `HUBSPOT_CREATE_TICKET`, `HUBSPOT_LIST_TICKETS` |
| CRM records | Zoho CRM | `ZOHO_CREATE_ZOHO_RECORD`, `ZOHO_GET_ZOHO_USERS` |
| Contact management | Zoho Invoice | `ZOHO_INVOICE_LIST_CONTACTS` |

---

## When Tools Become Available

Once Zoho Desk tools are added to Composio, this skill should be updated with real tool slugs, schemas, and pitfalls following the same pattern as other automation skills in this collection.

---

*Powered by [Composio](https://composio.dev)*

## Prerequisites

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Rube MCP must be connected (RUBE_SEARCH_TOOLS available)
- Active Zoho Desk connection via `RUBE_MANAGE_CONNECTIONS` with toolkit `zoho_desk`
- Always call `RUBE_SEARCH_TOOLS` first to get current tool schemas

## Tool Discovery

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always discover available tools before executing workflows:

```
RUBE_SEARCH_TOOLS: queries=[{"use_case": "tickets, contacts, agents, departments, and help desk operations", "known_fields": ""}]
```

This returns:
- Available tool slugs for Zoho Desk
- Recommended execution plan steps
- Known pitfalls and edge cases
- Input schemas for each tool

## Search Before Action

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always search for existing resources before creating new ones to avoid duplicates.

## Pagination

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Many list operations support pagination. Check responses for `next_cursor` or `page_token` and continue fetching until exhausted.

## Error Handling

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Check tool responses for errors before proceeding
- If a tool fails, verify the connection is still ACTIVE
- Re-authenticate via `RUBE_MANAGE_CONNECTIONS` if connection expired

## Batch Operations

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

For bulk operations, use `RUBE_REMOTE_WORKBENCH` with `run_composio_tool()` in a loop with `ThreadPoolExecutor` for parallel execution.

## Common Patterns

<!-- Carried from the underscore-named zoho_desk-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

