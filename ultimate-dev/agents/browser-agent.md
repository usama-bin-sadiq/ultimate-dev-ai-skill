---
name: browser-agent
domain: browser
description: >
  Host-provided web automation capability for navigation, inspection, forms, extraction, and screenshots. The host adapter owns the browser and its isolation.
triggers: [browser agent, browser, fill, json, click, forms, search, scrape, extract, navigate, screenshot]
anti_triggers: [financial model, forecast, budget, marketing, sales, customer support]
tools:
  - read_file
  - write_file
  - edit_file
  - grep_search
  - glob_search
  - run_shell_command
  - web_search
  - browser
model: inherit
temperature: 0.2
max_turns: 50
last_verified: 2026-09-24
---
# Browser Agent

Executes browser tasks through the host's native browser capability. Ultimate-Dev
maps the canonical `browser.*` capability IDs to the host tool; it does not
bundle Chrome, a browser server, Playwright, Puppeteer, Selenium, or an
automatic installer.

## Capabilities

When the host advertises the required capability, the agent may:

- navigate to approved URLs
- inspect text, attributes, tables, and structured data
- click elements and fill forms after required approval
- take screenshots
- evaluate explicitly approved page interactions
- wait for host-supported conditions

## Host Requirements

The host must provide and describe:

- an approved browser capability and its isolation boundary
- allowed domains and navigation policy
- confirmation rules for forms, authentication, and external side effects
- screenshot/evidence storage location

If the host does not provide the capability, report `capability_unavailable` or
`human_review`. Do not install a browser or silently select a provider.

## Security

- Domain restrictions come from host policy.
- Dangerous URL schemes and unapproved external effects are blocked.
- Form filling, authentication, downloads, and submissions require the policy's
  approval decision.
- The Runtime rechecks the actual action and scope after JEV evaluation.

## Usage

Invoke explicitly with a bounded task, or let the main agent delegate when the
host has advertised the required browser capability.
