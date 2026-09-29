# Technology Adapter — Auto-Create Agents for New Tools

When this skill encounters a technology, library, or tool that has no dedicated agent, follow this process to handle it without creating a permanent agent file.

## Detection

If stack-detection finds an unknown tool/library/framework:
1. Check if an existing agent covers the domain (e.g., database-optimizer covers databases, backend-architect covers queues)
2. If an existing agent's domain matches, use it with technology-specific guidance from WebSearch
3. If no domain match exists, proceed to ad-hoc creation

## Ad-Hoc Agent Creation

For tools that need a specialist but don't warrant a permanent agent:

1. **Search for official docs** via WebSearch: "[tool name] official documentation best practices"
2. **Read the docs** via WebFetch to get actual API patterns and configuration
3. **Apply the domain pattern** from the closest existing agent (adapt its structure to the new tool)
4. **Run the task** using the ad-hoc guidance from docs
5. **Do NOT create a permanent agent file** unless the tool will be used repeatedly in this project

## When to Create a Permanent Agent

Create a new agent file only if:
1. The technology is used in 3+ features in this project
2. No existing agent covers its domain
3. The technology has non-trivial patterns that differ from other tools in the same domain

## Context-Window Rules for Auto-Generated Agents

When creating ad-hoc or permanent agents for new tools:

1. **Max 60 lines per agent file** — concise, no bloat
2. **Detection patterns: max 10 regex lines** — only the most impactful patterns
3. **Method: max 5 steps** — focused workflow
4. **No duplicate shared rules** — agent files reference `_shared/` files, never inline them
5. **Token-efficient output** — agent output max 500 tokens per invocation
6. **Never read other agent files** — agents are independent, no cross-references
7. **Model tier: haiku for simple, sonnet for complex** — never opus unless critical

## How to Create a New Agent

1. Copy the closest existing agent file
2. Update frontmatter (name, description, model tier)
3. Add technology-specific:
   - Stack detection patterns (what files/configs to look for)
   - Detection patterns (grep/regex for common issues, max 10)
   - Technology-specific patterns (the actual best practices)
   - Output format (structured findings)
4. Keep under 60 lines total
5. Add a row in SKILL.md's agent table
6. Run the audit: verify the file exists and is referenced

## Future-Proofing Rule

This skill does NOT need to anticipate new technologies. It handles them when they appear:
- stack-detection.md reads actual manifests (not hardcoded lists)
- technology-adapter.md provides the process for handling unknowns
- The orchestrator asks the user when uncertain rather than guessing
- New agents are created only when justified by actual usage

## What This Means

If a new framework, library, or tool is released tomorrow:
1. stack-detection.md will detect it via its manifest/config files
2. The orchestrator will use technology-adapter.md to find docs and apply patterns
3. If it's used enough, a permanent agent is created
4. If not, it's handled ad-hoc without permanent files

This is how the skill stays future-proof without bloating.
