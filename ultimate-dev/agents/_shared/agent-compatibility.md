# Agent Compatibility — Works With Any Agentic Tool

This skill is designed to work with ANY AI coding agent, not just Claude. The instructions, workflows, and agent prompts are plain English and tool-agnostic. Below is how to install and use this skill with each supported tool.

## Supported Tools

| Tool | Config Location | Skill Discovery | How to Activate |
|------|----------------|-----------------|-----------------|
| Claude Code | `.claude/skills/` or `~/.claude/skills/` | Auto-discovers SKILL.md | "Use the ultimate-developer skill" or match triggers |
| Cursor | `.cursor/rules/*.md` or project rules | Reads .md rule files | Add as a rule or paste workflow |
| Windsurf | `.windsurfrules` or project rules | Reads .md rule files | Add as a rule or paste workflow |
| Cline | `.clinerules` or project rules | Reads .md rule files | Add as a rule or paste workflow |
| GitHub Copilot | `.github/copilot-instructions.md` | Reads instruction files | Add workflow to instructions |
| Aider | `.aider.conf.yml` or project rules | Reads project rules | Add workflow to rules |
| Any future tool | Any .md rule file | Reads markdown rules | Paste workflow or link to SKILL.md |

## Installation per Tool

### Claude Code
```
your-project/
└── .claude/
    └── skills/
        └── ultimate-developer/    ← copy this folder
```

### Cursor
Copy the contents of `SKILL.md` into `.cursor/rules/ultimate-developer.md` or add to your project rules.

### Windsurf
Copy the contents of `SKILL.md` into `.windsurfrules` or add to your project rules.

### Cline
Copy the contents of `SKILL.md` into `.clinerules` or add to your project rules.

### GitHub Copilot
Copy the key workflow sections into `.github/copilot-instructions.md`.

### Aider
Add the workflow to your `.aider.conf.yml` or project rules file.

### Generic / Future Tools
Copy the `ultimate-developer/` folder anywhere the tool reads rules from. The skill is plain English markdown — any tool that reads .md files can use it.

## Agent Dispatch Adaptation

Use `agents/_shared/capability-bridge.md` as the authoritative runtime dispatch contract. This file only describes host-specific installation/adaptation.

The kernel must first discover the host's real subagent, skill, tool, plugin, and parallel-execution capabilities. Then map each agent's frontmatter requirements to those capabilities.

This skill references "dispatching agents" as separate prompts. How this maps to each tool:

| Tool | Agent Dispatch Method |
|------|----------------------|
| Claude Code | Native sub-agent support via its current task/subagent mechanism |
| Cursor | Use Composer chat with focused prompts from each agent .md file |
| Windsurf | Use Cascade chat with focused prompts from each agent .md file |
| Cline | Use chat with focused prompts from each agent .md file |
| GitHub Copilot | Use chat with focused prompts from each agent .md file |
| Aider | Use chat with focused prompts from each agent .md file |

**For tools without native sub-agent support**: Read the relevant agent's .md file and use its prompt as a focused chat message. The agent files are self-contained — each one works as a standalone prompt.

## Runtime fallback contract

A host may expose the markdown skill but not native subagents. In that case:
- run selected agent prompts serially in the current context;
- preserve the agent's requested tools where the host provides semantic equivalents;
- mark the execution `fallback`, never `native`;
- do not claim parallelism that did not occur.

A host may expose tools with different names. Resolve them semantically at runtime; do not hardcode assumptions about tool names.

## Key Adaptation Rules

1. **The workflows are universal.** Phase 0-7 works the same regardless of tool.
2. **The agent prompts are standalone.** Each agents/*.md file is a self-contained prompt that works in any chat.
3. **The shared rules are universal.** stack-detection, output-format, never-commits, tldr-output apply everywhere.
4. **The frontmatter is advisory.** Fields like `model:` and `color:` are hints for tools that support them. Tools that don't ignore them.
5. **Tool-specific config files are detected.** The stack-detection system already reads CLAUDE.md, AGENTS.md, .cursorrules, .windsurfrules, .clinerules, .github/copilot-instructions.md — it adapts to whatever exists.

## Using Individual Agents

Even if your tool doesn't support the full orchestrated workflow, you can use individual agents standalone:

1. Pick the agent that matches your task from the Agent Roster in SKILL.md
2. Read the agent's .md file
3. Paste its content as a system prompt or chat message
4. The agent will execute its workflow independently

Example: To review code in Cursor, paste the contents of `agents/code-reviewer.md` into a Composer chat with your diff.

## Rules Files This Skill Detects

The skill auto-detects project rules from ALL major agentic tools:
- `CLAUDE.md` — Claude Code
- `AGENTS.md` — Generic agent instructions
- `.cursorrules` — Cursor
- `.cursor/rules/*.md` — Cursor rules
- `.windsurfrules` — Windsurf
- `.clinerules` — Cline
- `.github/copilot-instructions.md` — GitHub Copilot
- `.claude/rules/*.md` — Claude Code rules
- `CONTRIBUTING.md` — Generic
- `STYLEGUIDE.md` — Generic
- `ARCHITECTURE.md` — Generic

Whichever tool you use, the skill finds and applies the relevant rules.
