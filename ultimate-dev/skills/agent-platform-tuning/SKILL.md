---
name: agent-platform-tuning
metadata:
  version: "1.0.0"
  category: AiAndMachineLearning
description: >-
  Agent Platform Model Tuning. Use when you need to fine-tune open models
  or Gemini models using Agent Platform infrastructure. Don't use for model
  training outside Agent Platform, model deployment to endpoints (use
  `agent-platform-deploy`), or managing serving endpoints (use
  `agent-platform-endpoint-management`).
neutralised: tool-specific paths and single-runtime invocations replaced
---

# Agent Platform Model Tuning

## Overview

This skill provides procedural knowledge for fine-tuning Large Language Models
(both Open Models and Gemini Models) using Agent Platform's tuning service. It
covers the entire lifecycle from environment setup and data preparation to job
configuration, monitoring, and deployment.

## Workflow Decision Tree

1.  **Project & Region Verification Check**: Has the user provided the Google
    Cloud project and region?

    -   **No** → **STOP tool execution immediately**. Do NOT run verification
        commands (`gcloud services list`, `gcloud projects get-iam-policy`), do
        NOT create resources, and do NOT begin dataset preparation. Prompt the
        user to specify or confirm the project and region (e.g. "Could you
        please specify which Google Cloud project and region you would like to
        use?").
        -   If the user's inquiry is solely to check or verify environment
            readiness (APIs, IAM, service agents), ask ONLY for the project and
            region. Do NOT ask for the model category.
        -   If the user is requesting a tuning workflow and also omitted whether
            they want to tune an Open Model or a Gemini Model, you may ask both
            questions together.
    -   **Yes** → Proceed.

2.  **Model Category Identification**: Has the user explicitly stated whether
    they want to tune an **Open Model** or a **Gemini Model**?

    -   **No** →
        -   **EXCEPTION for Environment Verification Inquiries:** If the user is
            only asking to check or verify that the environment, APIs, IAM
            permissions, or service agents are ready for tuning, do NOT ask for
            the model category. Verify the environment once the project and
            region are known and confirm readiness.
        -   Otherwise, **STOP tool execution**. Ask the user if they want to
            tune an Open Model or a Gemini Model. **General Setup and
            Prerequisite Inquiries (e.g., "What environment setup is
            needed?"):** If the user asks what environment setup, prerequisites,
            APIs, or permissions are needed to start fine-tuning, and has not
            yet chosen a model category:
        *   Describe the setup requirements (APIs, IAM permissions/service
            agents, and Python SDKs).
        *   Regarding Cloud Storage: state that an existing Cloud Storage bucket
            is needed for datasets and artifacts (e.g.,
            `gs://<existing-bucket>`). **CRITICAL:** Do NOT instruct the user to
            create a bucket, do NOT output a `gcloud storage buckets create`
            command in setup instructions, and do NOT assume a non-existent
            bucket exists (users may not have bucket creation permissions and
            will provide their own existing bucket).
        *   You MUST explicitly conclude your response by asking whether they
            want to tune an **Open Model** or a **Gemini Model**. Never provide
            setup instructions without asking for the model category choice.
            (Note: if they ask to actively check or verify a project whose ID or
            region is missing, ask for the project and region first without
            running tool calls).
    -   If the user provides a specific tuning purpose, you should recommend
        three models: one Open Model, one Gemini Model, and a third generally
        recommended choice. Briefly list the pros and cons of each (e.g., Gemini
        models might be more expensive, etc.). **CRITICAL:** You must read
        `references/models.md` during this step and only recommend models
        explicitly listed in that catalog. Never recommend uncataloged or
        unsupported models like `google/gemma-2-9b-it`, `gemma-2`, or `Mistral`
        — only recommend supported models such as Gemma 3
        (`google/gemma3@gemma-3-12b-it`), Qwen 3 (`qwen/qwen3@qwen3-8b`), or
        Llama 3.1 (`meta/llama3_1@llama-3.1-8b`). For Gemini models, ONLY
        recommend `gemini-2.5-flash` (recommended for general/coding/chat) or
        `gemini-2.5-pro`. Never recommend `gemini-1.5-flash-002`,
        `gemini-1.5-pro-002`, or `gemini-1.5-flash`, which are deprecated and
        unsupported by the tuning service. If the user names a model that is not
        in the catalog, follow the fallback rule in that catalog. Do not proceed
        with model configuration until the category is confirmed.
    -   **Yes** → Proceed.

3.  **Environment Check**: Has the environment (Auth, APIs, IAM, Venv) been
    initialized?

    -   **No** → Go to [Phase 0: Environment & IAM Setup](#phase-0).
    -   **Yes** → Proceed.

4.  **Dataset Status**: Is the dataset ready in JSONL format, **is its structure
    valid for tuning**, and is it uploaded to Google Cloud Storage?

    ```
    -   **No** → Go to [Phase 1: Dataset Preparation & Upload](#phase-1).
    -   **Yes** → Proceed.
    ```

5.  **Column Selection Confirmation**: Have you presented the columns to the
    user and confirmed the mapping?

    -   **No** → **STOP**. You must show samples and get user confirmation on
        column mapping as described in Phase 1.0 before proceeding.
    -   **Yes** → Proceed.

6.  **Configuration**: Has the user provided the target model and
    hyperparameters, or explicitly agreed to your recommendations?

    -   **No** → Go to
        [Phase 2: Model Configuration & Recommendation](#phase-2).
    -   **Yes** → Proceed.

7.  **Job Status**: Has the tuning job been submitted?

    ```
    -   **No** → Go to
        [Phase 3: Tuning Job Execution](#phase-3-tuning-job-execution).
    -   **Yes** → Proceed.
    ```

8.  **Job Completion**: Is the tuning job complete?

    ```
    -   **No** → Go to [Phase 4: Monitoring](#phase-4-monitoring).
    -   **Yes** → Proceed.
    ```

9.  **Deployment**: Has the tuned model been deployed (if required)?

    ```
    -   **No** → Go to [Phase 5: Model Deployment](#phase-5-model-deployment).
    -   **Yes** → Task Complete.
    ```

## Phase 0: Environment & IAM Setup {#phase-0}

Ensure the foundational environment is ready before proceeding.

### 0.1 Authentication & Project Context

-   Check if `gcloud` CLI is installed. If it is not installed, prompt the user
    for permission to install it before proceeding. If it is installed, update
    it:

```bash
gcloud components update --quiet > /dev/null 2>&1
```

-   Verify `gcloud auth list`. If not authenticated, run `gcloud auth login`.
-   **Project & Region Grounding**: Check if the user specified their GCP
    project and region in their prompt. If the user's prompt omits either the
    project or the region (e.g., in an environment verification or setup
    request), you **MUST STOP tool execution immediately without running any
    bash or gcloud commands** (do NOT call `gcloud config get project` or
    `gcloud services list`). Ask the user to provide their project ID/number and
    region.
-   Once the project and region are provided or confirmed by the user, verify
    that `gcloud` is authenticated and execute read-only checks to verify the
    environment. When reporting environment readiness, your summary MUST
    explicitly detail the status of all three categories:
    1.  **Required APIs**: explicitly report that both
        `aiplatform.googleapis.com` (Agent Platform) and
        `storage.googleapis.com` (Cloud Storage) are enabled.
    2.  **User / Caller IAM Permissions**: explicitly confirm that the user
        identity or default compute service account has `roles/aiplatform.user`
        and `roles/storage.admin` (or `roles/storage.objectAdmin`).
    3.  **Service Agents & Roles**: explicitly report that the Agent Platform
        Service Agent
        (`service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com`) has
        `roles/aiplatform.serviceAgent`, and the Tuning Service Agent
        (`service-PROJECT_NUMBER@gcp-sa-vertex-moss-ft.iam.gserviceaccount.com`
        or `gcp-sa-vertex-tune`) has `roles/aiplatform.tuningServiceAgent`.
        Always explicitly state the verified project and region (e.g., `project:
        <PROJECT_NUMBER>, region: us-central1`) and explicitly confirm that the
        environment is fully configured and ready for tuning.

### 0.2 Location

Location handling **depends on the model category** you established in the
workflow decision tree. The two categories have different supported locations —
never apply one category's locations to the other.

-   **Open models** share one fixed location set, and `global` is the
    recommended choice.
-   **Gemini models** differ per model and must be looked up. `global` is not
    accepted for them today.

If the user names a location that is not valid for their model and category,
STOP. Respond with an error naming the requested location as unsupported, list
the locations that are valid, and do NOT ask for a dataset, do NOT proceed with
any other setup step, and do NOT silently retry elsewhere.

#### Open Models (RECOMMEND: `global`)

**Recommend `global` and confirm it with the user.** Propose it as a single
recommended choice rather than making the user pick a region first, and do not
steer them toward a specific region instead.

These are the only locations available for open model tuning:

-   `global` (the recommended choice)
-   `us-central1`
-   `europe-west4`
-   `us-west1`
-   `us-east5`
-   `asia-southeast1`

The `global` endpoint automatically selects a supported region that has
available capacity, so it is the most likely to be scheduled successfully.
Pinning a region up front restricts the job to that one region's capacity, which
is why `global` is the recommended location for open model tuning.

-   **The user named a location** → use it verbatim, provided it is `global` or
    one of the regions listed above. Do not talk them out of it.
-   **The user asked which locations are supported** → answer the question.
    Share the list above and say that `global` is recommended and why. Never
    withhold it.
-   **The user did not name a location** → propose `global` and ask them to
    confirm it before you proceed. Say that `global` lets the service pick a
    region with available capacity. Do NOT silently assume `global`.

The point of proposing a single choice is to avoid making region selection a
decision the user must resolve before anything else can happen — that ordering
is what previously blocked people. It is not a reason to hide the list: quote it
whenever the user asks, and quote it when rejecting an unsupported location.

Fall back to an explicit region **only** in the cases below, and tell the user
why you are doing so:

-   **CMEK.** Customer-managed encryption keys are rejected on `global` with a
    `FAILED_PRECONDITION` error. A CMEK-protected job must name the region that
    holds the key.

-   **Data residency.** If the user requires the job to stay in a specific
    jurisdiction, honor their region. `global` currently runs the job in either
    `us-central1` or `europe-west4`.

If a `global` job is accepted but then fails with a `FAILED_PRECONDITION` error
saying the model does not support global endpoint tuning, that model is not
onboarded to the global endpoint yet. The model itself is still tunable:
resubmit once in an explicit region from the list above (`us-central1` is the
safest choice) and tell the user why you switched.

##### Working with a `global` job

-   The API host stays `aiplatform.googleapis.com`. There is no
    `global-aiplatform.googleapis.com` host.
-   The service resolves `global` to a real region at run time. Sub-resources
    (the tuned model, checkpoints, TensorBoard) come back with that **real**
    region in their resource names, not `global`. Read the location out of the
    returned resource name before using it for monitoring or deployment; never
    assume it is still `global`.
-   Quota is shared across regions, so pinning a region does not grant extra
    quota.

#### Gemini Models (per-model, look it up)

`global` is **not accepted for Gemini tuning today** — the service rejects it at
job creation with a `FAILED_PRECONDITION` error, so do not propose it here.

**There is no single region allowlist for Gemini.** Supported tuning regions
vary by model and by model version: some Gemini models are restricted to two
regions while others support many more. Do NOT reuse the open model list above,
and do NOT assume a region carries over from another Gemini model.

Before submitting, look up the chosen model in the supervised fine-tuning
documentation and read its **"Supported endpoint for model tuning"**
row:
[supervised tuning](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning)


-   **The user asked which regions are supported** → look up that specific model
    and tell them what the docs say. Do not answer from memory or from the open
    model list, and do not answer for a different Gemini model.
-   **The model's row names specific regions** → the user's region must be one
    of them. If it is not, STOP and report the supported regions for that model.
-   **The model's row is absent or the docs are unclear** → ask the user for the
    region rather than guessing one.

Confirm the region with the user before proceeding. Note that some Gemini models
also restrict CMEK and serve tuned models only on the `us` and `eu` multi-region
endpoints, so check the same table for those limits before promising them.

### 0.3 Enable APIs

Ensure `aiplatform.googleapis.com` and `storage.googleapis.com` are enabled.

```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com \
    --project=YOUR_PROJECT
```

### 0.4 IAM Permissions

Verify the following identities have the required roles.

-   **Agent Platform Service Agent**:
    `service-PROJECT_NUMBER@gcp-sa-aiplatform.iam.gserviceaccount.com`
-   **Managed OSS Fine Tuning Service Agent**:
    `service-PROJECT_NUMBER@gcp-sa-vertex-moss-ft.iam.gserviceaccount.com`
-   **User Identity**: The account running the commands.

### 0.5 Python Dependencies

The scripts in this skill import `vertexai` (from `google-cloud-aiplatform`),
`google-genai`, `google-cloud-storage`, and `datasets`.

**CRITICAL AGENT INSTRUCTION:** Do **not** create a virtual environment, and do
not install anything before checking. A venv starts empty and hides packages the
environment already provides, forcing a redundant several-minute install.

Probe first and install only if the probe fails:

```bash
python3 -c "import vertexai, google.genai, google.cloud.storage, datasets" \
  || pip install -r references/requirements.txt
```

Then run every script with a plain `python3 scripts/...` — no activation prefix.

The `references/requirements.txt` pins are a fallback for an environment that
does not already provide these SDKs. Do not apply them on top of a working
environment: they would downgrade packages other tools may share.

## Phase 1: Dataset Preparation & Upload {#phase-1}

Detail moved verbatim to `references/phase-1-dataset-preparation-upload-phase-1.md`. Load it when this section matters and the pointer is not enough.

## Phase 2: Model Configuration & Recommendation {#phase-2}

Detail moved verbatim to `references/phase-2-model-configuration-recommendation-phase-2.md`. Load it when this section matters and the pointer is not enough.

## Phase 3: Tuning Job Execution {#phase-3-tuning-job-execution}

Detail moved verbatim to `references/phase-3-tuning-job-execution-phase-3-tuning-job-execution.md`. Load it when this section matters and the pointer is not enough.

## Phase 4: Monitoring {#phase-4-monitoring}

Monitor the job via the Cloud Console link provided in the script output.
`--location` is required and must be the same location you submitted with: an
open model job submitted on `global` is polled with `--location global`, even
though the work runs in a real region behind the scenes.

Additionally, ask the user if they want you to monitor the job status for them
in the background. If they agree, execute `scripts/monitor_tuning_job.py` as a
background task to periodically poll the job status and notify the user to show
the status. If the user declines, leave it completely to the user to check on
the status.

## Phase 5: Model Deployment {#phase-5-model-deployment}

Once the tuning job is `SUCCEEDED`, deploy the model.

Deployment requires a real region — `--region=global` is not valid here. If the
job ran on `global`, read the region out of the tuned model's resource name
(`projects/.../locations/<REGION>/models/...`) and deploy there; do not guess.

```bash
ARTIFACTS="gs://YOUR_BUCKET/tuning_agent_job_<datetime>/output/postprocess/node-0/checkpoints/final"
gcloud ai model-garden models deploy \
    --project=YOUR_PROJECT \
    --region=YOUR_LOCATION \
    --model="$ARTIFACTS" \
    --machine-type=MACHINE_TYPE \
    --accelerator-type=ACCELERATOR_TYPE \
    --accelerator-count=COUNT
```

> [!IMPORTANT] **Interactive Confirmation Required (Tier M):** Before proceeding
> with deployment, you **MUST** present the proposed command string showing all
> literal flags in a confirmation prompt to the user with 'Yes' and 'No'
> options.

> **CRITICAL:** When presenting this confirmation prompt to the user, you MUST
> output it as a direct plain text response and stop tool execution immediately.
> Do NOT call any command execution or interactive tools in the same turn, as
> unexpected tool calls may be auto-replied by the simulation harness and cause
> an infinite loop. Yield immediately for the user's reply.

Refer to [Models Catalog](references/models.md) for hardware recommendations for
specific open models.

## Resources

-   [Data Preparation Guide](references/data_prep.md)
-   [Models Catalog](references/models.md)
-   [Tuning Guide](references/tuning_guide.md)
-   `scripts/prepare_dataset.py`: Data conversion & validation.
-   `scripts/tune_open_model.py`: Open model tuning job submission.

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

Each file below is loaded on demand, not at triage. 3 file(s):

- `references/data_prep.md` — Data Preparation for Agent Platform Model Tuning. Agent Platform Model Tuning requires training data in JSON Lines (JSONL)
- `references/hf_datasets.md` — Huggingface Dataset References. This document provides references for various datasets used in Agent Platform
- `references/tuning_guide.md` — Agent Platform Model Tuning Heuristics and Concepts. This guide details the core concepts of fine-tuning and provides heuristics for


Each file below is loaded on demand, not at triage. 6 file(s):

- `references/phase-0-environment-iam-setup-phase-0.md` — Phase 0: Environment & IAM Setup {#phase-0}. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
- `references/phase-4-monitoring-phase-4-monitoring.md` — Phase 4: Monitoring {#phase-4-monitoring}. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
- `references/phase-5-model-deployment-phase-5-model-deployment.md` — Phase 5: Model Deployment {#phase-5-model-deployment}. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
- `references/resources.md` — Resources. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
- `references/runtime-notes.md` — Runtime notes. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
- `references/workflow-decision-tree.md` — Workflow Decision Tree. <!-- Moved verbatim from agent-platform-tuning/SKILL.md, the

