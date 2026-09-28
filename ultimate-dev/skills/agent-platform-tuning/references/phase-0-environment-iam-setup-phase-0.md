<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
     'phase-0-environment-iam-setup-phase-0' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
