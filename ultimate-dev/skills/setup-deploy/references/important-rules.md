<!-- Moved verbatim from setup-deploy/SKILL.md, the
     'important-rules' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Important Rules

- **Never expose secrets.** Don't print full API keys, tokens, or passwords.
- **Confirm with the user.** Always show the detected config and ask for confirmation before writing.
- **<agent-instructions> is the source of truth.** All configuration lives there — not in a separate config file.
- **Idempotent.** Running /setup-deploy multiple times overwrites the previous config cleanly.
- **Platform CLIs are optional.** If `fly` or `vercel` CLI isn't installed, fall back to URL-based health checks.
