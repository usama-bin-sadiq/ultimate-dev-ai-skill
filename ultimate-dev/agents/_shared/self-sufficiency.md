# Self-Sufficiency: Handle Projects with NO Existing Skills/Tools

When this skill is used in a project with NO specialized tooling (no framework, no linter, no CI, no existing patterns), the orchestrator activates **Generic Mode**.

## Detection: When to activate

Scan for:
1. No package.json, requirements.txt, go.mod, Cargo.toml, pom.xml, or similar manifest
2. No linter configs (.eslintrc, pyproject.toml, .golangci.yml, etc.)
3. No CI/CD configs (.github/workflows, .gitlab-ci.yml, Jenkinsfile, etc.)
4. No CLAUDE.md or AGENTS.md
5. No existing test files
6. No existing agent patterns

If **3+ of these are true** → activate Generic Mode.

## Generic Mode Rules

1. **Ask the user first** — "No project configuration detected. Should I: (a) analyze the code as-is, (b) set up recommended tooling, or (c) create a CLAUDE.md?"
2. **Use language-agnostic agents** — task-triage, code-reviewer, dead-code-finder, doc-writer, stack-detection work without any framework
3. **Skip framework-specific agents** — do NOT load framework-specific agents (database-specialist, frontend-reviewer, etc.) unless the code reveals a framework
4. **Create inline analysis** — when no agent fits, do the analysis yourself using WebSearch for documentation patterns
5. **Propose tooling** — suggest (but don't install) what the project should use

## Self-Sufficient Analysis Workflow

When no agents match:

```
1. Read the code
2. Identify: language, patterns used, code quality
3. Apply universal checks (dead code, docs, secrets, errors)
4. Use WebSearch for language-specific best practices
5. Produce findings using the Output Rules format
```

## Token Efficiency in Generic Mode

- Load only task-triage (3.5k) and code-reviewer (8k) as base agents
- Add web-searcher if needed (1k)
- Do NOT load any 4k+ agents unless the code specifically matches
- Manual analysis is preferred over loading mismatched agents
