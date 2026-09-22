---
name: browser-agent
domain: browser
description: >
  Web automation via Chrome DevTools — navigate, click, fill forms, extract data, screenshot. Requires Chrome 144+. Disabled by default; enable in settings.json.
triggers: [browser agent, browser, via, web, 144+, data, fill, json, click, forms, chrome, enable]
anti_triggers: [financial model, forecast, budget, marketing, sales, customer support]
tools:
  - read_file
  - write_file
  - grep_search
  - glob
  - run_shell_command
model: inherit
temperature: 0.2
max_turns: 50
last_verified: 2026-09-21
---
# Browser Agent

Automates web browser tasks using the Chrome DevTools Protocol via the bundled `chrome-devtools-mcp` server.

## Capabilities

- Navigate to URLs
- Click elements, fill forms, select options
- Extract text, attributes, tables, structured data
- Take screenshots (full page or element)
- Execute JavaScript in page context
- Handle authentication flows, modals, dynamic content
- Wait for elements, network idle, custom conditions

## Prerequisites

- **Chrome 144+** (any recent stable release)
- Enabled in `settings.json`:
```json
{
  "agents": {
    "overrides": {
      "browser-agent": { "enabled": true }
    }
  }
}
```

## Session Modes (via `agents.browser.sessionMode`)

| Mode | Description |
|------|-------------|
| `persistent` | Persistent profile at `~/.gemini/cli-browser-profile/` — cookies, history, settings preserved |
| `isolated` | Temporary profile deleted after session — clean state |
| `existing` | Attach to running Chrome with remote debugging on port 9222 |

## Security

- Domain restrictions via `allowedDomains`
- Blocks dangerous URL schemes (file://, javascript:, data:, chrome://)
- Form filling requires user confirmation
- Action rate limiting (default 100 actions/task)
- Optional visual model for coordinate-based interaction

## Usage

Invoke explicitly: `@browser-agent Go to example.com and extract the pricing table`

Or let the main agent delegate automatically for web research tasks.