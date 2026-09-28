<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     'safety-confirmation-tiers-critical' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Safety & Confirmation Tiers (CRITICAL)

Before executing any commands or scripts on behalf of the user, you must adhere
to the following safety tiers based on the action requested. (The skill is
read-only; other safety tiers are omitted):

1.  **Tier R: Read-only / Inference (`client.models.generate_content`,
    `client.chat.completions.create`, `client.completions.create`,
    `client.embeddings.create`)**
    *   Requires **interactive confirmation** with 'Yes'/ 'No' options before
        executing model inference on behalf of the user, to prevent unexpected
        cost or quota consumption.
    *   **Required Fields in Confirmation Card**: The confirmation prompt must
        clearly explain the proposed inference execution and explicitly list all
        of the following parameters:
        *   **Project ID**: The Google Cloud project ID or number (e.g.
            `123456789012`, `my-project`).
        *   **Region / Location**: The target region (e.g. `us-central1`,
            `global`).
        *   **Model ID**: The exact model ID (e.g. `gemini-2.5-flash`,
            `deepseek-ai/deepseek-v3.2-maas`).
        *   **SDK**: The SDK choice (e.g. `Google GenAI SDK (google-genai)`,
            `OpenAI SDK`).
        *   **Input Prompt** (or **Input Image** / **Input Media**): The prompt
            text or media URI.
        *   Any additional generation parameters (e.g. `max_output_tokens`,
            `response_schema`) if specified.
        Natural-language paraphrases without explicitly listing these
        parameters are NOT sufficient.
    *   **Same-turn restriction**: Do not execute the inference scripts or
        commands in the same turn as presenting the confirmation prompt. Stop
        and wait for the user's reply; only execute after explicit 'Yes' /
        approval.
    *   **Gold Standard Example**:
        > I will perform model inference with the following parameters. Please
        > confirm this information before I proceed:
        > * **Project ID**: `my-project`
        > * **Region**: `us-central1`
        > * **Model ID**: `gemini-2.5-pro`
        > * **SDK**: Google GenAI SDK (`google-genai`)
        > * **Input Prompt**: "Summarize the plot of Hamlet in 3 sentences"
        >
        > Do you confirm? [Yes/No]
    *   **Post-Execution Response Grounding (CRITICAL)**:
        After receiving explicit user approval and executing the inference call
        via the SDK, the response returning the generated text **MUST
        explicitly confirm the execution parameters** alongside the model's
        output. Never return a bare model response alone. Always include:
        *   **Model ID**: The exact model ID used (e.g. `gemini-2.5-pro`
            or `<MODEL_ID>`).
        *   **SDK**: The SDK used (e.g. `Google GenAI SDK (google-genai)`
            or `OpenAI SDK`).
        *   **Project ID**: The Google Cloud project ID/number used.
        *   **Region**: The region or endpoint location used (e.g. `global`
            or `us-central1`).
        *   **Generated Output**: The model's complete generated answer.
