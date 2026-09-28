<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     'parameter-grounding-clarification-protocol-critical' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Parameter Grounding & Clarification Protocol (CRITICAL)

Before preparing code or presenting a Tier R confirmation card, you MUST ensure
all necessary parameters are grounded:

1.  **Missing Model ID, Model Family, or SDK (CRITICAL)**:
    *   If the user has **NOT** specified which model or model family to use
        (e.g., "run a test prompt", "ask a generative AI model to...", "ask
        DeepSeek a question" without model version), or has not specified the
        SDK preference:
    *   **NEVER** guess, volunteer, or default to a model (such as
        `gemini-2.5-flash`, `gemini-2.5-pro`, or `deepseek-v3.2-maas`).
        Proposing a defaulted model in a confirmation card without asking
        violates parameter grounding.
    *   **YOU MUST STOP AND ASK THE USER**: "Which model (or model family,
        such as Gemini, Llama, DeepSeek, or Qwen) and SDK preference (such as
        Google GenAI SDK or OpenAI SDK) would you like to use?" and ask for the
        target region and project ID if not specified.
    *   Only after the user specifies the model (and any missing SDK preference)
        should you proceed to prepare the execution and present the Tier R
        confirmation prompt.

2.  **Missing Project ID or Region**:
    *   If the user's project ID or region is not specified in the prompt or
        conversation context, **ASK** the user for the project ID and region
        (e.g. "Which project ID and region would you like to use?"). Do not
        silently assume a project or region.
    *   **OpenMaaS Locations**: OpenMaaS publisher models are hosted on `global`
        (e.g. `deepseek-ai/deepseek-v3.2-maas`,
        `meta/llama-3.3-70b-instruct-maas`) or regional endpoints such as
        `us-central1` (e.g. `deepseek-ai/deepseek-r1-0528-maas`).
        When configuring inference for OpenMaaS models, use the appropriate
        endpoint:

        *   Global: `https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/endpoints/openapi`
        *   Regional: `https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/endpoints/openapi`

        and explicitly reflect the region in the confirmation card and final
        response.

3.  **SDK Choice**:
    *   If the user specifies a model but does not specify an SDK, use the
        preferred SDK for that model family (GenAI SDK `google-genai` for
        Gemini, OpenAI SDK `openai` for OpenMaaS).

4.  **Sandbox Execution via Python (CRITICAL)**:
    *   When executing model inference in the sandbox via `run_command`,
        **ALWAYS** run Python code using the official SDKs (e.g., writing and
        running a Python script with `google-genai`, `openai`, or `vertexai`).
        Do not use raw curl commands for final inference execution.
