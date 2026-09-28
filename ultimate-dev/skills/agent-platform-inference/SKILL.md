---
name: agent-platform-inference
metadata:
  version: "1.0.0"
  category: AiAndMachineLearning
description: >-
  Connects to and performs inference with Google Cloud Agent Platform GenAI
  models, including First-Party Gemini models and Third-Party OpenMaaS models
  (Llama, DeepSeek, Qwen, etc.). Use when asked to perform inference, ask a
  model a question, run a test prompt, execute chat completions, or generate
  code for calling Gemini or OpenMaaS models, authenticate with GenAI SDK,
  OpenAI SDK, or legacy Agent Platform SDK, configure base URLs and
  global/regional endpoints, or troubleshoot 429 Resource Exhausted (DSQ), 400
  User Validation, or 404 Not Found errors. Don't use for deploying models to
  endpoints or for running model evaluations.
---

# Agent Platform GenAI Inference Skill

This skill provides instructions for authenticating and connecting to Google
Cloud Agent Platform to use Generative AI models. It covers:

*   **First-Party publisher models** (Gemini) — section 2.
*   **Third-Party publisher models** (OpenMaaS: Llama, DeepSeek, Qwen, etc.)
    — section 3.
*   **Custom endpoints** (any model on a numeric `projects/.../endpoints/<id>`
    resource — tuned Gemini models, OSS LLMs self-deployed from Model Garden
    via the `agent-platform-deploy` skill, and legacy custom models) —
    section 4.

## Safety & Confirmation Tiers (CRITICAL)

Detail moved verbatim to `references/safety-confirmation-tiers-critical.md`. Load it when this section matters and the pointer is not enough.

## Phase 0: Environment Setup

Detail moved verbatim to `references/phase-0-environment-setup.md`. Load it when this section matters and the pointer is not enough.

## Parameter Grounding & Clarification Protocol (CRITICAL)

Detail moved verbatim to `references/parameter-grounding-clarification-protocol-critical.md`. Load it when this section matters and the pointer is not enough.

## Workflow Decision Tree

1.  **Model Specified?**
    *   **No** (user omitted model name/family) -> **Ask the user** which model
        or model family, target region, and SDK preference they want to use.
    *   **Underspecified** (e.g., user said "DeepSeek" or "Llama" without
        version) -> **Ask the user** which specific model version they prefer
        (e.g., `deepseek-ai/deepseek-r1-0528-maas`,
        `deepseek-ai/deepseek-v3.2-maas`, `meta/llama-3.3-70b-instruct-maas`).
    *   **Yes** -> Proceed to Step 2.

2.  **Model Family & SDK Selection**:
    *   **Gemini** (e.g., `gemini-2.5-pro`, `gemini-2.5-flash`) -> Preferred:
        **GenAI SDK** (`google-genai`). Proceed to [1. Gemini Models].
    *   **OpenMaaS** (e.g., `deepseek-ai/*`, `meta/llama-*`, `qwen/*`) ->
        Preferred: **OpenAI SDK** (`openai`). Proceed to [2. OpenMaaS Models].
    *   **Custom Endpoint** (numeric endpoint ID
        `projects/.../endpoints/<id>`) -> Proceed to [4. Custom Endpoints].

3.  **Troubleshooting**: Is the user reporting an error (429 Resource Exhausted,
    400 User Validation, 404 Not Found, empty response due to token limits,
    etc.)?
    *   **Yes** -> Proceed to [5. Troubleshooting & Common Error Codes].
    *   **No** -> Present Tier R confirmation prompt with all required fields
        (Project ID, Region, Model ID, SDK, Input Prompt), wait for user
        confirmation, then execute via Python SDK.

## 0.5 Region Availability Check for Publisher Endpoints (Gemini + LoRA base)

Detail moved verbatim to `references/0-5-region-availability-check-for-publisher-endpoints-gemini-lora-base.md`. Load it when this section matters and the pointer is not enough.

## 1. Gemini Models

For Gemini models (e.g., `gemini-2.5-pro`, `gemini-3-flash-preview`), the
**GenAI SDK** (`google-genai`) is the **PREFERRED** method. The legacy
`vertexai` SDK is still supported but GenAI SDK is recommended for new projects.

> [!IMPORTANT]
> **Preview Models (including Gemini 3.1)** are often **ONLY** available in the
> `global` region. Stable models are available in `us-central1` and other
> regions.

### Choosing the Right SDK

*   **Gemini Models**: **GenAI SDK** (`google-genai`) is **PREFERRED**. Use
    OpenAI SDK for compatibility, or Legacy SDK (`vertexai`) if needed.
*   **OpenMaaS Models**: **OpenAI SDK** is **HIGHLY RECOMMENDED**. Use GenAI SDK
    or Legacy SDK if you have specific infrastructure requirements.

### Installation

```bash
pip install google-genai
```

### Python Example (GenAI SDK - Preferred)

See [`scripts/gemini_genai_sdk.py`](scripts/gemini_genai_sdk.py) for the
complete code.

### Alternative: OpenAI SDK (Chat Completions)

Use the standard OpenAI SDK with the Agent Platform endpoint. This is great for
cross-compatibility.

See [`scripts/gemini_openai_sdk.py`](scripts/gemini_openai_sdk.py) for the
complete code.

### Legacy: Agent Platform SDK

The legacy `vertexai` SDK is still widely used but `google-genai` is preferred
for new Gemini projects.

See [`scripts/gemini_vertexai_sdk.py`](scripts/gemini_vertexai_sdk.py) for the
complete code.

**Documentation**:
[Google GenAI SDK](https://github.com/googleapis/python-genai)

**Documentation**:
[Agent Platform Gemini Models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models)

## 2. OpenMaaS Models (Llama, DeepSeek, Qwen, etc.)

Detail moved verbatim to `references/2-openmaas-models-llama-deepseek-qwen-etc.md`. Load it when this section matters and the pointer is not enough.

## 4. Custom Endpoints (tuned Gemini, self-deployed OSS LLM, legacy custom)

This section covers how to invoke a model on an Agent Platform
**Endpoint** that belongs to your project — i.e., something with a
numeric resource name like
`projects/.../endpoints/5875254126916403200`. This is distinct from
calling the publisher MaaS surfaces in sections 2 and 3 (which hit
`publishers/.../models/...` or `endpoints/openapi`, not your endpoint
ID).

> [!IMPORTANT]
>
> **Publisher MaaS vs your endpoint (don't confuse them).** Section 3's
> OpenMaaS examples (e.g. `meta/llama-3.3-70b-instruct-maas`) hit a
> **shared publisher URL** at
> `/v1/projects/.../locations/.../endpoints/openapi`. This section's
> recipes hit **YOUR** endpoint at `/v1/projects/.../endpoints/<id>`.
> If you have a Llama / Gemma / etc. model deployed via Model Garden
> "Deploy" (NOT the MaaS publisher product), follow this section — not
> section 3.

> [!IMPORTANT]
>
> **Active Endpoint Discovery & Single Source of Truth**:
>
> *   To check if a model or tuned Gemini adapter is deployed and ready for
>     inference, run:
>
>     `gcloud ai endpoints list --project=<PROJECT_ID> --region=<REGION> --format=json`.
>
> *   **`gcloud ai endpoints list` is the ONLY authoritative source of active
>     serving endpoints.**
> *   Do NOT rely on historical `job.tunedModel.endpoint` identifiers from past
>     `gcloud ai tuning-jobs list` records — those record where an endpoint was
>     initially created during tuning, but if the endpoint was subsequently
>     deleted, undeployed, or expired, it is no longer active.
> *   If `gcloud ai endpoints list` returns empty `[]` or the requested tuned
>     model is not deployed on any listed endpoint, report directly to the user
>     that no active endpoint was found in that region and halt. **NEVER**
>     hallucinate that historical/deleted endpoints are ready, and **NEVER**
>     silently substitute the base model without explicit user instruction and a
>     fresh Tier R confirmation prompt.

> [!IMPORTANT]
>
> **Two orthogonal axes determine the call shape:**
>
> **Axis 1 — model family** drives the RPC method and payload:
>
> | Endpoint serves | Method | Payload |
> |---|---|---|
> | A **tuned Gemini model** (output of Gemini tuning — the endpoint is already deployed for you) | `:generateContent` | `contents` / `generationConfig` |
> | A **self-deployed OSS LLM** (Llama, DeepSeek, Qwen, Gemma, Mistral, etc., deployed via Model Garden) | `/chat/completions` | OpenAI-compatible `messages` |
> | A **legacy custom model** (classification, regression, custom-trained, embedding) | `:predict` | `instances` / `parameters` |
>
> Run `gcloud ai endpoints describe <ENDPOINT_ID> --region=<REGION>
> --format=json` and inspect `deployedModels[].model` to decide:
> contains `gemini` → tuned Gemini; matches an OSS publisher
> (`meta/`, `google/gemma-`, `deepseek-ai/`, `qwen/`, ...) → OSS LLM;
> otherwise → likely legacy custom.
>
> **Axis 2 — endpoint type (shared vs dedicated)** drives the URL host:
>
> | `dedicatedEndpointEnabled` | Host |
> |---|---|
> | `false` (default — shared endpoint) | `<REGION>-aiplatform.googleapis.com` |
> | `true` (dedicated endpoint, has its own DNS) | the value of `dedicatedEndpointDns` (format: `<ENDPOINT_ID>.<REGION>-<PROJECT_NUM>.prediction.vertexai.goog`) |
>
> A dedicated endpoint **cannot** be reached via the shared
> `<REGION>-aiplatform.googleapis.com` host (per the
> `Endpoint.dedicated_endpoint_enabled` proto: *"Once you enabled
> dedicated endpoint, you won't be able to send request to the shared
> DNS"*). Always check `dedicatedEndpointDns` in the describe output:
> if it's set, use it as the host; otherwise use the shared host.
>
> **Path is always
> `/v1/projects/.../locations/.../endpoints/<id>/...`** on both hosts.
> Both `/v1/` (GA) and `/v1beta1/` (beta) route to the same backend; the
> recipes in this skill use `/v1/`. The public
> [Gemma deployment notebook](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/community/model_garden/model_garden_gemma_deployment_on_vertex.ipynb)
> still uses `/v1beta1/`, which also works.

### 4a. REST recipe — tuned Gemini model

Output of Gemini tuning is always an endpoint that's already deployed for
you, reachable on the shared host with `:generateContent`.

```bash
PROJECT_ID=my-project
ENDPOINT_ID=5875254126916403200
REGION=us-central1
TOKEN=$(gcloud auth application-default print-access-token)

curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}:generateContent" \
  -d '{
    "contents": [
      {"role": "user", "parts": [{"text": "Hello! Introduce yourself briefly."}]}
    ],
    "generationConfig": {
      "temperature": 0.2
    }
  }'
```

> [!WARNING]
>
> **If you set `maxOutputTokens`, be generous for thinking models.**
> Gemini 2.5 Pro (and other thinking-enabled models) emit "thoughts"
> tokens that count against `maxOutputTokens` BEFORE any user-visible
> text. With a small cap (e.g. 100), the entire budget is consumed by
> thoughts and the response has empty `text` parts but a non-zero
> `usageMetadata.candidatesTokenCount`.
>
> If you don't need to constrain output length, omit `maxOutputTokens`
> entirely and let the model emit as much as it wants. If you do set
> it: `>= 512` for any chat-like use, `>= 1024` for a paragraph of
> output. If you see `finishReason: "MAX_TOKENS"` and no `text`
> content in the response, your cap is too low.

### 4b. REST recipe — self-deployed OSS LLM (Llama, DeepSeek, Qwen, Gemma, etc.)

Self-deployed OSS LLMs may be on a **shared** or **dedicated** endpoint
depending on how the deploy was configured (`dedicated_endpoint_enabled`
at create time). The recipe below handles both cases by checking
`dedicatedEndpointDns` in the describe output.

```bash
PROJECT_ID=my-project
ENDPOINT_ID=5875254126916403200
REGION=us-central1
TOKEN=$(gcloud auth application-default print-access-token)

# Step 1: discover host. dedicatedEndpointDns is empty for shared endpoints.
DEDICATED_DNS=$(gcloud ai endpoints describe "$ENDPOINT_ID" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format="value(dedicatedEndpointDns)")

if [ -n "$DEDICATED_DNS" ]; then
  HOST="$DEDICATED_DNS"
else
  HOST="${REGION}-aiplatform.googleapis.com"
fi

# Step 2: call /chat/completions. Path is identical for both hosts.
curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://${HOST}/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}/chat/completions" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Introduce yourself briefly."}
    ]
  }'
```

> [!NOTE]
>
> -   `max_tokens` (NOT `maxOutputTokens`) — this is OpenAI-compatible
>     vocabulary, not Vertex. Omit it entirely to let the model emit as
>     much as it wants; set it explicitly only if you need to cap output.
> -   The `"model"` field in the OpenAI-style payload can be omitted (or
>     set to `""`) for endpoint deployments — the endpoint already
>     determines which model serves the request.
> -   Same endpoint also exposes `/completions` (legacy text completion)
>     and `/embeddings` for embedding models.
> -   **Reasoning models** (DeepSeek-R1, Kimi-K2-Thinking, GLM-5 variants,
>     etc.) emit thinking tokens that count against `max_tokens` BEFORE
>     the final answer — same pathology as Gemini 2.5 Pro in section 4a.
>     If you DO set `max_tokens` and get an empty
>     `choices[0].message.content` or `finish_reason: "length"`, raise it
>     (>= 1024 for chat, >= 2048 for longer thinking chains) or omit it.

Python equivalent (OpenAI SDK) — mirrors the public
[Gemma deployment notebook](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/community/model_garden/model_garden_gemma_deployment_on_vertex.ipynb):

```python
import google.auth
from google.auth.transport.requests import Request
import openai

from google.cloud import aiplatform

PROJECT_ID = "my-project"
ENDPOINT_ID = "5875254126916403200"
REGION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=REGION)
endpoint = aiplatform.Endpoint(
    f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{ENDPOINT_ID}"
)
endpoint_resource_name = endpoint.resource_name  # full projects/.../endpoints/<id>
dedicated_dns = endpoint.gca_resource.dedicated_endpoint_dns  # empty if shared

host = dedicated_dns if dedicated_dns else f"{REGION}-aiplatform.googleapis.com"
base_url = f"https://{host}/v1/{endpoint_resource_name}"

import subprocess

token = subprocess.check_output(
    ["gcloud", "auth", "print-access-token"]
).decode("utf-8").strip()

client = openai.OpenAI(base_url=base_url, api_key=token)
response = client.chat.completions.create(
    model="",  # endpoint determines the served model
    messages=[{"role": "user", "content": "Hello! Introduce yourself briefly."}],
    # Omit max_tokens to let the model emit as much as it wants. Set it
    # only if you need to cap output length (see notes above).
)
print(response.choices[0].message.content)
```

See also: `agent-platform-deploy` skill section 4 "Verifying Deployment",
which uses the same pattern post-deploy.

### 4c. REST recipe — legacy `:predict` (custom / classification / embedding)

Same host-discovery logic as 4b (shared or dedicated based on
`dedicatedEndpointDns`):

```bash
DEDICATED_DNS=$(gcloud ai endpoints describe "$ENDPOINT_ID" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format="value(dedicatedEndpointDns)")
HOST=${DEDICATED_DNS:-${REGION}-aiplatform.googleapis.com}

curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://${HOST}/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}:predict" \
  -d '{
    "instances": [{"key": "value"}],
    "parameters": {}
  }'
```

The exact `instances` shape is model-specific; consult the deployed
model's documentation or the Model Garden card it was deployed from.

### 4d. Python (Vertex AI SDK) — tuned Gemini model

```python
from google import genai
import google.auth

_, project_id = google.auth.default()
client = genai.Client(vertexai=True, project=project_id, location="us-central1")

ENDPOINT_ID = "5875254126916403200"
response = client.models.generate_content(
    model=f"projects/{project_id}/locations/us-central1/endpoints/{ENDPOINT_ID}",
    contents="Hello! Introduce yourself briefly.",
    config={"temperature": 0.2},  # add max_output_tokens only if you need a cap
)
print(response.text)
```

## 5. Troubleshooting & Common Error Codes

### 429: Resource Exhausted

*   **Cause**: OpenMaaS and Gemini models use **Dynamic Shared Quota (DSQ)**.
    Resources are pooled and allocated dynamically based on availability. A 429
    error indicates the shared pool is temporarily exhausted, not necessarily
    that *your* specific project quota is hit (though it can be).
*   **Solution**: Implement strict **exponential backoff and retry** strategies.
*   **High Throughput**: For production workloads requiring high throughput or
    guaranteed capacity, consider **Provisioned Throughput (PT)**.
*   **Important**: Quota increases through normal cloud processes (Cloud
    Console) are **NOT** applicable for DSQ constraints.
*   **Documentation**:
    [Quotas and limits (DSQ)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/quotas)

### 400: User Validation Error

*   **Cause**: Invalid request format, unsupported parameter, or incorrect Model
    ID.
*   **Action**: Double-check your request payload and parameters. Verify the
    Model ID and Region are correct.
*   **Custom endpoints**: pick the right method + host per section 4's
    decision tables:
    *   Tuned Gemini + you called `:predict` → switch to `:generateContent`
        (section 4a). Error mentions "Required instances format mismatch".
    *   OSS LLM (Llama/DeepSeek/Qwen/Gemma/etc.) + you called
        `:generateContent` or `:predict` → switch to `/chat/completions`
        (section 4b). Error may be 404, 405, or "method not allowed".
    *   Legacy / custom-trained + you called `:generateContent` or
        `/chat/completions` → switch to `:predict` (section 4c).
*   **Dedicated endpoint reached on the shared host (or vice versa)**:
    *   Symptom: DNS resolution failure (`Could not resolve host`) or 404.
    *   Cause: dedicated endpoints don't accept traffic on
        `<REGION>-aiplatform.googleapis.com`, and the dedicated DNS
        (`*.prediction.vertexai.goog`) only exists when
        `dedicatedEndpointEnabled` is true.
    *   Action: re-check `gcloud ai endpoints describe ... --format=json`
        for the `dedicatedEndpointDns` field; use it iff non-empty (per
        the host-discovery snippets in section 4b/4c).

### Empty response text on Gemini deployed endpoints

*   **Cause**: `maxOutputTokens` is set too low. Gemini 2.5 Pro and other
    thinking models emit "thoughts" tokens that count against the budget
    BEFORE any user-visible text. With a small cap (e.g. 100), the entire
    budget is consumed by thoughts and the response has empty `text` parts
    but a non-zero `usageMetadata.candidatesTokenCount` and
    `finishReason: "MAX_TOKENS"`.
*   **Action**: Omit `maxOutputTokens` entirely (let the model emit as much
    as it wants), or raise it to >= 512 for chat-like use, >= 1024 for
    longer output. See section 4 "Custom Endpoints" for details.

### 404: Not Found / Model Not Available

*   **Cause**: The model is not enabled, or not available in the specified
    project or region.
*   **Action**:
    1.  **Check Location Availability**:
        *   **OpenMaaS**: Verify the model is available in your region. See
            [Model Availability by Location](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations#genai-open-models).
        *   **Gemini**:
            *   **Source of Truth**: Always check
                [Gemini Model Locations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations#google-models)
                for the authoritative list.
            *   **Preview Models**: All Preview models (e.g., Gemini 3.1,
                experimental versions) are often **ONLY** available in the
                `us-central1` or `global` regions.
            *   **Stable Models**: (e.g., Gemini 2.5 Pro) Available in
                `us-central1`, `europe-west4`, and many other regions.
            *   **Important**: If you get a 404/400 error, try switching your
                client location to `us-central1` or `global`.
    2.  **Enable Llama Models**: For **Llama 3.3** and **Llama 4**, you **MUST**
        enable the model in Model Garden before use. Go to the
        [Model Garden](https://console.cloud.google.com/agent-platform/model-garden),
        search for the model card (e.g., "Llama 3.3 API Service"), and click
        **Enable**. Only then can you make inference requests.

Each file below is loaded on demand, not at triage. 4 file(s):

- `references/1-gemini-models.md` — 1. Gemini Models. <!-- Moved verbatim from agent-platform-inference/SKILL.md, the
- `references/4-custom-endpoints-tuned-gemini-self-deployed-oss-llm-legacy-custom.md` — 4. Custom Endpoints (tuned Gemini, self-deployed OSS LLM, legacy custom). <!-- Moved verbatim from agent-platform-inference/SKILL.md, the
- `references/5-troubleshooting-common-error-codes.md` — 5. Troubleshooting & Common Error Codes. <!-- Moved verbatim from agent-platform-inference/SKILL.md, the
- `references/workflow-decision-tree.md` — Workflow Decision Tree. <!-- Moved verbatim from agent-platform-inference/SKILL.md, the

