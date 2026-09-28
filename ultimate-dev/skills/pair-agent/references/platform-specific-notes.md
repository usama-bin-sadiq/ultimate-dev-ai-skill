<!-- Moved verbatim from pair-agent/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Platform-specific notes

### OpenClaw / AlphaClaw

OpenClaw agents use the `exec` tool instead of `Bash`. The instruction block uses
`exec curl` syntax which OpenClaw understands natively. When using `--local openclaw`,
credentials are written to `~/.openclaw/skills/gstack/browse-remote.json`.


### Codex

Codex agents can execute shell commands via `codex exec`. The instruction block's
curl commands work directly. When using `--local codex`, credentials are written
to `~/<agent-config-dir>/skills/gstack/browse-remote.json`.

### Cursor

Cursor's AI can run terminal commands. The instruction block works as-is.
When using `--local cursor`, credentials are written to
`<agent-config-dir>/skills/gstack/browse-remote.json`.
