---
name: wave-accounting-automation
description: "Wave Accounting toolkit is not currently available as a native integration. No Wave-specific tools were found in the Composio platform. This skill is a placeholder pending future integration."
category: accounting
requires:
  mcp:
    - rube
---

# Wave Accounting Automation

> **Note:** The Wave Accounting toolkit (`wave_accounting`) does not currently have native tools available in the Composio platform. Searches for Wave Accounting-specific tools return results from other accounting/invoicing platforms (Stripe, Zoho Invoice) instead.

**Toolkit docs:** [composio.dev/toolkits/wave_accounting](https://composio.dev/toolkits/wave_accounting)

---

## Status

This integration is **not yet available** with native Wave Accounting tools. When Wave Accounting tools become available in Composio, this skill file will be updated with real tool slugs, workflows, and pitfalls.

For accounting and invoicing automation needs, consider these alternatives that are available today:
- **Stripe** -- Payment processing, invoicing, and subscription management
- **Zoho Invoice** -- Invoice creation, payment tracking, and contact management
- **QuickBooks** -- Full accounting suite with invoicing and expense tracking
- **FreshBooks** -- Cloud accounting with time tracking and invoicing

---

## Setup

1. Add the Composio MCP server to your client configuration:
   ```
   https://rube.app/mcp
   ```
2. Check back for Wave Accounting integration availability.

---

*Powered by [Composio](https://composio.dev)*

## Prerequisites

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Rube MCP must be connected (RUBE_SEARCH_TOOLS available)
- Active Wave Accounting connection via `RUBE_MANAGE_CONNECTIONS` with toolkit `wave_accounting`
- Always call `RUBE_SEARCH_TOOLS` first to get current tool schemas

## Tool Discovery

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always discover available tools before executing workflows:

```
RUBE_SEARCH_TOOLS: queries=[{"use_case": "invoices, customers, payments, and small business accounting", "known_fields": ""}]
```

This returns:
- Available tool slugs for Wave Accounting
- Recommended execution plan steps
- Known pitfalls and edge cases
- Input schemas for each tool

## Search Before Action

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always search for existing resources before creating new ones to avoid duplicates.

## Pagination

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Many list operations support pagination. Check responses for `next_cursor` or `page_token` and continue fetching until exhausted.

## Error Handling

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Check tool responses for errors before proceeding
- If a tool fails, verify the connection is still ACTIVE
- Re-authenticate via `RUBE_MANAGE_CONNECTIONS` if connection expired

## Batch Operations

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

For bulk operations, use `RUBE_REMOTE_WORKBENCH` with `run_composio_tool()` in a loop with `ThreadPoolExecutor` for parallel execution.

## Common Patterns

<!-- Carried from the underscore-named wave_accounting-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

