<!-- Moved verbatim from agent-platform-inference/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# 2. OpenMaaS Models (Llama, DeepSeek, Qwen, etc.)

For OpenMaaS (Model-as-a-Service) models, the **HIGHLY RECOMMENDED** approach is
to use the standard **OpenAI SDK** with a specific Vertex AI endpoint.

> [!WARNING] While `GenerativeModel` *can* support some OpenMaaS models, it is
> **discouraged**. Use the OpenAI SDK for best compatibility (especially for
> Chat Completions).

### Installation

```bash
pip install openai google-auth
```

### Authentication for OpenAI SDK

You **MUST** use a Google Cloud OAuth access token as the API key for the OpenAI
SDK.

```python
import subprocess

def get_gcp_access_token():
    return subprocess.check_output(
        ["gcloud", "auth", "print-access-token"]
    ).decode("utf-8").strip()
```

> [!NOTE] Google Cloud access tokens typically expire after 1 hour. The
> `get_gcp_access_token()` function above retrieves a *fresh* token at the time
> it is called. For long-running
> applications, you implement a refresh mechanism. See
> [Refresh the access token](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate/openai/auth-and-credentials?hl=en#refresh_your_credentials)
> for details.

### Configuration (Base URL)



-   **Global Endpoint** (Recommended for most models requiring global
    availability):
    `https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/endpoints/openapi`
-   **Regional Endpoint**:
    `https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/endpoints/openapi`


### Python Example (OpenMaaS - Chat Completions)

See [`scripts/openmaas_openai_sdk.py`](../scripts/openmaas_openai_sdk.py) for the
complete code.

> [!TIP] **Alternative: Environment Variables** You can set environment
> variables in your shell instead of updating the code.
>
> **Alternative: Environment Variables** You can set environment variables in
> your shell instead of updating the code.

```bash
export OPENAI_BASE_URL="https://aiplatform.googleapis.com/v1/projects/YOUR_PROJECT_ID/locations/global/endpoints/openapi"
export OPENAI_API_KEY="$(gcloud auth application-default print-access-token)"
```
> Then initialize the client without arguments: `client = OpenAI()`

### Python Example (OpenMaaS - Completions API)

The following models support the legacy Completions API: `zai-org/glm-5-maas`,
`moonshotai/kimi-k2-thinking-maas`, `minimaxai/minimax-m2-maas`,
`deepseek-ai/deepseek-v3.1-maas`, and `deepseek-ai/deepseek-v3.2-maas`.

```python
response = client.completions.create(
    model="deepseek-ai/deepseek-v3.2-maas",
    prompt="Once upon a time",
    max_tokens=100
)
print(response.choices[0].text)
```

### Python Example (OpenMaaS - Embeddings)

```python
# Verify specific Embedding Model ID on Model Garden (e.g., intfloat/multilingual-e5-small)
response = client.embeddings.create(
    model="intfloat/multilingual-e5-large-maas",
    input="The quick brown fox jumps over the lazy dog",
)
print(response.data[0].embedding)
```

### Alternative: GenAI SDK

The `google-genai` SDK can also access OpenMaaS models via the `vertexai`
backend.

See [`scripts/openmaas_genai_sdk.py`](../scripts/openmaas_genai_sdk.py) for the
complete code.

> [!IMPORTANT]
> **Model ID Format**: For GenAI SDK with OpenMaaS, you **MUST** use the full
> path: `publishers/PUBLISHER/models/MODEL` (e.g.,
> `publishers/zai-org/models/glm-5-maas`).

### Legacy: Agent Platform SDK (OpenMaaS)

For OpenMaaS, you can also use `GenerativeModel` (if supported).

See [`scripts/openmaas_vertexai_sdk.py`](../scripts/openmaas_vertexai_sdk.py) for
the complete code.

> [!IMPORTANT] **Model ID Format**: For Agent Platform SDK with OpenMaaS, you
> **MUST** use the full path: `publishers/PUBLISHER/models/MODEL`.

### Model Reference & Availability

**Documentation**:
[Use Open Models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/use-open-models)

> [!TIP]
> **Self-Deployment for Control**: If you need **dedicated hardware**
> (GPUs/TPUs), **guaranteed capacity**, or **specific regional placement** not
> offered by MaaS, you can **Self-Deploy** these models to Agent Platform
> Endpoints. Search for the model in Model Garden and click "Deploy" to select
> your machine type. See the `agent-platform-deploy` skill for the deployment
> workflow, and **section 4 of this skill** for how to invoke the resulting
> self-deployed endpoint (use `/chat/completions` on the dedicated endpoint
> DNS, NOT the OpenMaaS publisher URL above).

> [!IMPORTANT] **Finding Inference Examples**: The list above is a starting
> point. For the **definitive** inference snippets (especially for Chat
> Completions payload structure): 1. Consult the
> [Use Open Models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/use-open-models)
> list. 2. Click the link for your specific model (e.g., "DeepSeek-V3") to visit
> its **Model Garden** page. 3. Look for the **"Sample Code"** or **"Use this
> model"** button on the Model Garden page to get the exact `curl` or Python
> code for that specific model version.

> [!NOTE] This list is **INCOMPLETE**. See
> [Use Open Models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/use-open-models)
> for the full list of supported models.

Model Family  | Model ID Examples                              | Location      | Notes
:------------ | :--------------------------------------------- | :------------ | :----
**Llama 4**   | `meta/llama-4-maverick-17b-128e-instruct-maas` | `us-east5`    |
**Llama 4**   | `meta/llama-4-scout-17b-16e-instruct-maas`     | `us-east5`    |
**Llama 3.3** | `meta/llama-3.3-70b-instruct-maas`             | `us-central1` |
**DeepSeek**  | `deepseek-ai/deepseek-v3.2-maas`               | `global`      | Global ONLY
**DeepSeek**  | `deepseek-ai/deepseek-v3.1-maas`               | `us-west2`    | US-West2 ONLY
**DeepSeek**  | `deepseek-ai/deepseek-r1-0528-maas`            | `us-central1` |
**Qwen 3**    | `qwen/qwen3-coder-480b-a35b-instruct-maas`     | `global`      |
**Qwen 3**    | `qwen/qwen3-next-80b-a3b-instruct-maas`        | `global`      |
**Kimi**      | `moonshotai/kimi-k2-thinking-maas`             | `global`      |
**MiniMax**   | `minimaxai/minimax-m2-maas`                    | `global`      |
**GLM**       | `zai-org/glm-4.7-maas`, `zai-org/glm-5-maas`   | `global`      |
