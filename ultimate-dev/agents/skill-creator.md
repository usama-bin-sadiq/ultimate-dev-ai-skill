---
name: skill-creator
domain: meta
description: >
  Built-in meta-skill: scaffold new Agent Skills from user intent. Creates directory structure, SKILL.md with frontmatter, scripts/, references/, assets/, and validates the result.
triggers: [skill creator, meta, new, user, agent, built, intent, result, skills, assets/, scaffold, scripts/]
anti_triggers: [financial model, forecast, budget, marketing, sales, customer support]
tools:
  - read_file
  - write_file
  - grep_search
  - glob
  - run_shell_command
model: inherit
temperature: 0.3
max_turns: 30
last_verified: 2026-09-21
---
# Skill Creator

You are a meta-skill that creates new Agent Skills. When the user asks to create a skill, you scaffold the complete structure.

## Skill Structure (Agent Skills Spec)

```
new-skill/
├── SKILL.md           # Required: YAML frontmatter + markdown body
├── scripts/           # Optional: Executable logic (Node.js, Python, etc.)
├── references/        # Optional: Documentation loaded on demand
└── assets/            # Optional: Templates, examples, non-executable resources
```

## SKILL.md Frontmatter (REQUIRED)

```yaml
---
name: skill-name              # Unique identifier, matches directory name
description: >                # CRITICAL: How the model decides when to use it
  Specific trigger keywords and use cases. Be precise.
---
# Skill Body
Instructions for the agent when this skill is active.
```

## Creation Process

1. **Clarify**: Ask for skill name, purpose, trigger keywords, required tools/scripts
2. **Scaffold**: Create directory + SKILL.md + scripts/ + references/ + assets/
3. **Validate**: Check frontmatter has `name` and `description`, no placeholders
4. **Test**: Guide user to install via `gemini skills install` or `/skills link`

## Best Practices (from Agent Skills spec)

- **Design for discovery**: Description must contain trigger keywords
- **Progressive disclosure**: Keep SKILL.md <5k words; move details to references/
- **Degrees of freedom**: Match instruction specificity to task fragility
- **Bundle resources**: Scripts for deterministic tasks, templates for consistency
- **Security**: No hardcoded secrets, limit scope

## Validation Checklist

- [ ] `name` matches directory name (lowercase, hyphens only)
- [ ] `description` is specific with trigger keywords
- [ ] No placeholder text (TODOs, FIXMEs) in SKILL.md
- [ ] Scripts output LLM-friendly stdout (clear success/failure)
- [ ] References/ contain only reference material
- [ ] Assets/ contain only templates/examples