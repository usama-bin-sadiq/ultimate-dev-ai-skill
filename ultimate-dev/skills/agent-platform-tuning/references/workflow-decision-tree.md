<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
     'workflow-decision-tree' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflow Decision Tree

1.  **Project & Region Verification Check**: Has the user provided the Google
    Cloud project and region?

    -   **No** → **STOP tool execution immediately**. Do NOT run verification
        commands (`gcloud services list`, `gcloud projects get-iam-policy`), do
        NOT create resources, and do NOT begin dataset preparation. Prompt the
        user to specify or confirm the project and region (e.g. "Could you
        please specify which Google Cloud project and region you would like to
        use?").
        -   If the user's inquiry is solely to check or verify environment
            readiness (APIs, IAM, service agents), ask ONLY for the project and
            region. Do NOT ask for the model category.
        -   If the user is requesting a tuning workflow and also omitted whether
            they want to tune an Open Model or a Gemini Model, you may ask both
            questions together.
    -   **Yes** → Proceed.

2.  **Model Category Identification**: Has the user explicitly stated whether
    they want to tune an **Open Model** or a **Gemini Model**?

    -   **No** →
        -   **EXCEPTION for Environment Verification Inquiries:** If the user is
            only asking to check or verify that the environment, APIs, IAM
            permissions, or service agents are ready for tuning, do NOT ask for
            the model category. Verify the environment once the project and
            region are known and confirm readiness.
        -   Otherwise, **STOP tool execution**. Ask the user if they want to
            tune an Open Model or a Gemini Model. **General Setup and
            Prerequisite Inquiries (e.g., "What environment setup is
            needed?"):** If the user asks what environment setup, prerequisites,
            APIs, or permissions are needed to start fine-tuning, and has not
            yet chosen a model category:
        *   Describe the setup requirements (APIs, IAM permissions/service
            agents, and Python SDKs).
        *   Regarding Cloud Storage: state that an existing Cloud Storage bucket
            is needed for datasets and artifacts (e.g.,
            `gs://<existing-bucket>`). **CRITICAL:** Do NOT instruct the user to
            create a bucket, do NOT output a `gcloud storage buckets create`
            command in setup instructions, and do NOT assume a non-existent
            bucket exists (users may not have bucket creation permissions and
            will provide their own existing bucket).
        *   You MUST explicitly conclude your response by asking whether they
            want to tune an **Open Model** or a **Gemini Model**. Never provide
            setup instructions without asking for the model category choice.
            (Note: if they ask to actively check or verify a project whose ID or
            region is missing, ask for the project and region first without
            running tool calls).
    -   If the user provides a specific tuning purpose, you should recommend
        three models: one Open Model, one Gemini Model, and a third generally
        recommended choice. Briefly list the pros and cons of each (e.g., Gemini
        models might be more expensive, etc.). **CRITICAL:** You must read
        `references/models.md` during this step and only recommend models
        explicitly listed in that catalog. Never recommend uncataloged or
        unsupported models like `google/gemma-2-9b-it`, `gemma-2`, or `Mistral`
        — only recommend supported models such as Gemma 3
        (`google/gemma3@gemma-3-12b-it`), Qwen 3 (`qwen/qwen3@qwen3-8b`), or
        Llama 3.1 (`meta/llama3_1@llama-3.1-8b`). For Gemini models, ONLY
        recommend `gemini-2.5-flash` (recommended for general/coding/chat) or
        `gemini-2.5-pro`. Never recommend `gemini-1.5-flash-002`,
        `gemini-1.5-pro-002`, or `gemini-1.5-flash`, which are deprecated and
        unsupported by the tuning service. If the user names a model that is not
        in the catalog, follow the fallback rule in that catalog. Do not proceed
        with model configuration until the category is confirmed.
    -   **Yes** → Proceed.

3.  **Environment Check**: Has the environment (Auth, APIs, IAM, Venv) been
    initialized?

    -   **No** → Go to [Phase 0: Environment & IAM Setup](#phase-0).
    -   **Yes** → Proceed.

4.  **Dataset Status**: Is the dataset ready in JSONL format, **is its structure
    valid for tuning**, and is it uploaded to Google Cloud Storage?

    ```
    -   **No** → Go to [Phase 1: Dataset Preparation & Upload](#phase-1).
    -   **Yes** → Proceed.
    ```

5.  **Column Selection Confirmation**: Have you presented the columns to the
    user and confirmed the mapping?

    -   **No** → **STOP**. You must show samples and get user confirmation on
        column mapping as described in Phase 1.0 before proceeding.
    -   **Yes** → Proceed.

6.  **Configuration**: Has the user provided the target model and
    hyperparameters, or explicitly agreed to your recommendations?

    -   **No** → Go to
        [Phase 2: Model Configuration & Recommendation](#phase-2).
    -   **Yes** → Proceed.

7.  **Job Status**: Has the tuning job been submitted?

    ```
    -   **No** → Go to
        [Phase 3: Tuning Job Execution](#phase-3-tuning-job-execution).
    -   **Yes** → Proceed.
    ```

8.  **Job Completion**: Is the tuning job complete?

    ```
    -   **No** → Go to [Phase 4: Monitoring](#phase-4-monitoring).
    -   **Yes** → Proceed.
    ```

9.  **Deployment**: Has the tuned model been deployed (if required)?

    ```
    -   **No** → Go to [Phase 5: Model Deployment](#phase-5-model-deployment).
    -   **Yes** → Task Complete.
    ```
