<!-- Moved verbatim from agent-platform-inference/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# 5. Troubleshooting & Common Error Codes

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
