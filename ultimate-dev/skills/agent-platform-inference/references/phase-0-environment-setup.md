<!-- Moved verbatim from agent-platform-inference/SKILL.md, the
     'phase-0-environment-setup' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 0: Environment Setup

**CRITICAL**: Before running any of the Python sample scripts in the `scripts/`
directory (e.g., `scripts/openmaas_openai_sdk.py`), you MUST ensure the
environment is correctly initialized by following these steps:

1.  **Google Cloud Authentication**: Authenticate with your Google Cloud
    credentials and configure active Application Default Credentials (ADC) for
    Agent Platform access:

    ```bash
    gcloud auth login
    gcloud auth application-default login
    ```

2.  **Enable API** (if not already enabled):

    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

3.  **Python Dependencies**: The scripts import `vertexai` (from
    `google-cloud-aiplatform`), `google-genai`, and `openai`. Do **not** create
    a virtual environment — it starts empty and hides packages the environment
    already provides, forcing a redundant install. Probe, and install only what
    is missing:

    ```bash
    python3 -c "import vertexai, google.genai, openai" \
      || pip install -r scripts/requirements.txt
    ```

    `scripts/requirements.txt` is a fallback for an environment that does not
    already provide these SDKs; do not install it on top of a working
    environment.

4.  **Verify Setup (Optional)**: Run all sample scripts at once to verify the
    environment is working end-to-end:

    ```bash
    ./scripts/verify_all.sh
    ```

5.  **Execution**: Run the scripts with a plain `python3 scripts/...`. There is
    no environment to activate first.



> [!IMPORTANT] **CRITICAL: Model IDs & Availability** * **Gemini Models**: See
> [Gemini Models][gemini-models-docs] for valid Model IDs and Regions. *
> **OpenMaaS Models**: See
> [Use Open Models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/use-open-models)
> for Llama, DeepSeek, Qwen, etc. * **Incomplete Lists**: The Model IDs listed
> in this skill are **examples only** and may be incomplete or outdated. *
> **Action**: Always verify the Model ID and Region using the links above before
> generating code.
>
> \[gemini-models-docs]:
> https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate
>
