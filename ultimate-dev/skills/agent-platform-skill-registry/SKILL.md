---
name: agent-platform-skill-registry
metadata:
  version: "1.0.0"
  category: AiAndMachineLearning
description: >
  Interact with the Gemini Enterprise Agent Platform Skill Registry to create
  and search for available skills. Use this skill to enable agents to register
  functionality or discover new capabilities.
neutralised: tool-specific paths and single-runtime invocations replaced
---

# Skill Registry

This skill provides instructions for interacting with the **Skill Registry** on
the Gemini Enterprise Agent Platform.

## Core Capabilities

-   **Skill Discovery** - Query the registry to easily search, list, get
    specific skills, and inspect revision histories.
-   **Skill Lifecycle Management** - Upload, update, or permanently delete
    skills.
-   **Operation Monitoring** - Utility to check the completion status of
    long-running state changes (LROs).
-   **Generate Skill** - Automate the initial scaffolding of new agent skills
    locally.

## Core Directives

-   **Mandatory Validation**: ALWAYS execute the environment validation check
    before performing any operations.

    Before any operation, you **must** validate the core environment.

    ```bash
    # Execute the validation script
    python3 scripts/validate_env.py
    ```

## Prerequisites & Authentication

### Library & Authentication

Ensure you have the latest Google Cloud credentials and libraries installed.

```bash
# Install required libraries
pip install google-auth requests

# Authenticate with Google Cloud
gcloud auth application-default login
```

### Environment Variables

The following variables are required for operations:

-   `GCP_PROJECT_ID`: Your Google Cloud Project ID.
-   `GCP_LOCATION`: The region (e.g., `us-central1`).

--------------------------------------------------------------------------------

## Quickstart

Quickly search for available skills in the registry:

```bash
python3 scripts/skill_registry_ops.py search \
  --query "test skill" \
  --top-k 5
```

--------------------------------------------------------------------------------

## Operations

-   **Skill Discovery**: [query-skills.md](references/query-skills.md)
-   **Skill Lifecycle**: [manage-skills.md](references/manage-skills.md)
-   **Monitor Operations**:
    [monitor-operations.md](references/monitor-operations.md)
-   **Generate Skill**: [generate-skill.md](references/generate-skill.md)

## Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **pip** — means. One tool's way of doing a step a different runtime may do another way.
- **cloud-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.
