<!-- Moved verbatim from agent-platform-inference/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# 4. Custom Endpoints (tuned Gemini, self-deployed OSS LLM, legacy custom)

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
