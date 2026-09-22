# Tests

This directory contains tests for the ultimate-dev skill system.

## Overview

The ultimate-dev skill is tested at multiple levels:

1. **Schema Validation** — Ensures all YAML schemas are valid and well-formed.
2. **Prompt Completeness** — Verifies all required prompts exist and are non-empty.
3. **Workflow Integrity** — Checks that workflows reference valid steps and agents.
4. **Rule Consistency** — Validates that rules don't contradict each other.
5. **Tool Coverage** — Confirms all registered tools are documented.

## How to Run Tests

### Prerequisites
- Python 3.10+ (for schema validation)
- Node.js 18+ (for YAML parsing)

### Run All Tests
```bash
# From the ultimate-dev directory
python -m pytest tests/ -v
```

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

## Test Structure

```
tests/
├── README.md              # This file
├── test_schemas.py        # Schema validation tests
├── test_prompts.py        # Prompt completeness tests
├── test_workflows.py      # Workflow integrity tests
├── test_rules.py          # Rule coverage tests
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
