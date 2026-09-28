<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     'workflow-decision-tree' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
