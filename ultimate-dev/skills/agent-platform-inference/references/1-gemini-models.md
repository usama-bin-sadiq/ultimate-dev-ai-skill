<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     '1-gemini-models' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
