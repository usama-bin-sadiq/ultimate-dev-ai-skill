# Developer Guide

## Quick Start

### Installation
```bash
# Project-specific (recommended)
./scripts/install.sh --project . --yes

# Global (all projects)
./scripts/install.sh --global
```

### Invocation
```bash
# Any task - skill auto-detects pattern
@ultimate-dev "Build a React login form with tests"
@ultimate-dev "Deploy to production with zero-downtime"
@ultimate-dev "Audit codebase for security vulnerabilities"
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout main && git pull
git checkout -b feature/your-feature-name
```

### 2. Make Changes
Follow the [Architecture Guide](../architecture/ARCHITECTURE.md):
- Use smallest sufficient pattern
- Write verification evidence
- Persist state to `.memory/ultimate-dev/tasks/`

### 3. Run Validation
```bash
cd ultimate-dev
python scripts/validate.py
python -m pytest tests/ -q
./scripts/verify.sh
python scripts/agent_quality/quality_gate.py agents
```

### 4. Create PR
- Title follows conventional commits: `feat(scope): description`
- Fill out PR template completely
- Add appropriate labels (`feature`, `bug`, `release:*`)

### 5. Merge & Release
- PR to `main` with `release:*` label triggers auto-release
- Version bump, tag, changelog, GitHub Release created automatically

## Adding New Agents

### 1. Create Agent File
```
ultimate-dev/agents/<domain>/<agent-name>.md
```

### 2. Required Frontmatter
```yaml
---
name: agent-name
domain: your-domain
description: >
  Specializes in X, Y, Z. Use for A, B, C.
triggers: [keyword1, keyword2, keyword3]
anti_triggers: [exclude1, exclude2]
tools:
  - read_file
  - write_file
  - grep_search
model: inherit
temperature: 0.2
max_turns: 50
last_verified: 2026-01-01
---
```

### 3. Agent Body Structure
```markdown
# Agent Name

## Overview
What this agent does and when to use it.

## Capabilities
- Capability 1
- Capability 2

## Usage
When and how to invoke this agent.

## Examples
### Example 1
Input: "task description"
Output: Expected behavior
```

### 4. Run Quality Gate
```bash
python scripts/agent_quality/quality_gate.py agents
```

## Running Tests

### All Tests
```bash
cd ultimate-dev
python -m pytest tests/ -v
```

### Specific Test Categories
```bash
# Schema validation
python -m pytest tests/test_schemas.py -v

# Workflow integrity
python -m pytest tests/test_workflows.py -v

# Agent validation
python -m pytest tests/test_agents.py -v

# Model adapter
python -m pytest tests/test_model_adapter.py -v

# 9.5+ Evidence tests
python -m pytest tests/test_95_evidence.py -v
```

### Validate Structure
```bash
python scripts/validate.py
./scripts/verify.sh
```

## Adding New Skills

1. Create `ultimate-dev/skills/<skill-name>/SKILL.md`
2. Add to `skill-manifest.yaml` (auto-generated via `python scripts/generate-manifest.py`)
3. Test with `python scripts/validate.py`

## Adding New Modules

1. Create `ultimate-dev/modules/<module-name>.md` or directory
2. Reference from relevant agents/skills
3. No manifest update needed (modules are internal)

## Debugging

### Runtime Debugging
```python
from runtime.core.engine import Runtime
runtime = Runtime(".")
state = runtime.start({"goal": "debug test"})
print(runtime.store.load(state["task_id"]))
```

### State Inspection
```bash
# View task state
cat .memory/ultimate-dev/tasks/<task-id>/state.json

# View evidence
ls .memory/ultimate-dev/tasks/<task-id>/evidence/
```

### Debug Logs
```bash
# Enable verbose logging
export ULTIMATE_DEV_DEBUG=1
```

## CI/CD Pipeline

### Branch Protection (main)
- Require PR + 1 approval
- Require status checks:
  - Validate Skill Structure
  - Verify Package Integrity
  - Auto-generate Manifest
  - Sync Documentation
  - Test Installation
  - PR Quality Check

### Release Workflow
1. PR merged with `release:patch|minor|major` label
2. Auto-release workflow triggers
3. Version bumped, manifest synced, docs synced
4. Changelog updated, tag created, pushed
5. GitHub Release created with notes

### Manual Release
```bash
gh workflow run release.yml -f version_type=patch
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Commit message conventions
- PR requirements
- Issue reporting

---

*See also: [Architecture Guide](../architecture/ARCHITECTURE.md) | [User Guide](../user/USER_GUIDE.md)*