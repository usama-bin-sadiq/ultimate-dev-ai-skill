# Tests

This directory contains tests for the ultimate-dev skill system.

## Overview

The ultimate-dev skill is tested at multiple levels:

1. **Schema Validation** — Ensures all YAML schemas are valid and well-formed.
2. **Prompt Completeness** — Verifies all required prompts exist and are non-empty.
3. **Workflow Integrity** — Checks that workflows reference valid steps and agents.
4. **Rule Consistency** — Validates that rules don't contradict each other.
5. **Tool Coverage** — Confirms all registered tools are documented.
6. **Task Observer Contract** — Validates the Task Observer skill/agent boundary and registration.
7. **Runtime Hardening** — Validates path containment, JEV packet binding,
   restart rehydration, operation idempotency/cancellation/fencing, trusted
   evidence, exact allowlists, redaction, state quotas, audit-journal integrity,
   policy checks, capability availability, structured executor failures, and
   evidence-gated completion.
8. **Platform Components** — Validates the typed workflow/catalog authority,
   concrete agent catalog generation, abstract workflow-role separation, the
   portable prompt audit, optional MCP seam, provenance-aware memory and memory
   retention, governed evolution lifecycle and bounded event retention,
   provider-neutral evaluation, lifecycle/session hooks, task routing, archive
   restore, task retention, and manifest/agent/skill/adapter metadata consistency.
9. **Prompt and packaging quality** — Validates universal-task fallback contracts,
   provider-free routing fixtures, project-context generation, and installation
   payload/cache hygiene.

## How to Run Tests

### Host-native JEV tests

The canonical JEV contract and reference engine have no package-manager
dependency:

```bash
# From the repository root
node --test ultimate-dev/tests/jev/engine.test.mjs
```

### Legacy Python suite

The pre-existing skill validation suite remains optional maintenance tooling.
Install the pinned development dependencies from the repository root:

```bash
python -m pip install -r ../requirements-dev.txt
```

The prompt-only skill itself needs none of these packages. Run the suite only
when its development dependencies are available:

```bash
# From the ultimate-dev directory
python -m pytest tests/ -v
```

The JEV path does not import that suite, a model provider, a sandbox, or a
browser automation package.

### Run Specific Test Categories
```bash
# Schema validation only
python -m pytest tests/test_schemas.py -v

# Prompt completeness only
python -m pytest tests/test_prompts.py -v

# Workflow integrity only
python -m pytest tests/test_workflows.py -v
```

## What's Tested

### Schema Validation (`test_schemas.py`)
- All YAML files in `schemas/` parse without errors.
- Required fields are present in each schema.
- Example data conforms to the schema definitions.
- Error codes follow the naming convention.

### Prompt Completeness (`test_prompts.py`)
- All required prompt files exist in `prompts/`.
- No prompt file is empty or contains only headers.
- Each prompt has a clear title and structure.
- Cross-references between prompts are valid.

### Workflow Integrity (`test_workflows.py`)
- All YAML files in `workflows/` parse without errors.
- Each workflow has a name, description, and steps.
- Steps have unique IDs within their workflow.
- Required fields are present in each step.
- Error handling sections are defined.

### Rule Coverage (`test_rules.py`)
- All required rule files exist in `rules/`.
- No rule file is empty.
- Rules are consistent (no contradictions between files).
- Security rules cover OWASP Top 10.

### Tool Registry (`test_tools.py`)
- `tool_registry.yaml` parses correctly.
- All tools have required fields (id, name, description, parameters).
- Tool IDs follow naming conventions.
- Restrictions are defined for each tool.

### Task Observer Contract (`test_task_observer.py`)
- Skill and agent files exist with valid frontmatter.
- The agent references the skill without duplicating its methodology.
- The manifest registers both artifacts exactly once.
- Documentation, routing surfaces, and golden cases include Task Observer.
- The artifacts remain host-native and introduce no runtime provider.

## Test Structure

```
tests/
├── README.md              # This file
├── jev/engine.test.mjs   # Host-native JEV conformance tests
├── runtime/
│   ├── test_runtime.py
│   └── test_runtime_hardening.py
├── test_task_observer.py  # Task Observer skill/agent contract tests
├── test_schemas.py        # Schema validation tests
├── test_prompts.py        # Prompt completeness tests
├── test_workflows.py      # Workflow integrity tests
├── test_rules.py          # Rule coverage tests
├── test_consistency.py    # Catalog, version, adapter, and workflow-role checks
└── test_tools.py          # Tool registry tests
```

## Adding New Tests

When adding new content to the skill:

1. Add corresponding test cases to the relevant test file.
2. Follow the existing test patterns (pytest with descriptive names).
3. Include both positive and negative test cases.
4. Run the full test suite before committing.

## Continuous Integration

Tests should be run:
- Before every commit.
- In CI/CD pipelines on every push.
- When reviewing changes to schemas, prompts, workflows, or rules.
