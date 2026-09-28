<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 2: Model Configuration & Recommendation {#phase-2}

Help the user choose the best model and parameters. **Always seek user
confirmation before submitting the job.**

-   If the user does not specify a specific model in their prompt, calculate
    recommendations based on the **Models Catalog**.
-   **Prompt for Confirmation:** Present the recommended model to the user and
    ask for their confirmation before configuring hyperparameters.

### 2.1 Configuration

#### For Open Models

-   Recommend `tuning_mode`, `epochs`, `learning_rate`, and `adapter_size` based
    on the [Tuning Guide](./tuning_guide.md) and model-specific
    baselines in the [Models Catalog](./models.md).

#### Verify the Live Model ID

Before submitting the job, run `scripts/list_models.py` and pick `--base_model`
only from its `models` output. Do not invent IDs or version numbers.

```bash
python3 scripts/list_models.py --project YOUR_PROJECT --filter gemini
```

Output: `{"models": [...], "total_count": N, "truncated": bool}`.

-   For Gemini, strip `google/` and `@default` (e.g.
    `google/gemini-2.5-flash@default` → `gemini-2.5-flash`); for open models,
    pass `publisher/family@version` as-is.
-   Skip Gemini variants ending in `-embedding`, `-tts`, `-image`,
    `-computer-use`, or `-native-audio`; they are not tunable.
-   If `truncated` is `true`, re-run with a tighter `--filter` (e.g.
    `gemini-2.5`) before deciding the target version is unavailable.
-   If `models` is empty, stop and ask the user.

### 2.2 Calculating Cost (Open Models Only)

> [!WARNING] **CRITICAL: Always Use `run_command` with
> `scripts/calculate_cost.py`** Do **NOT** call the `estimate_cost` ADK tool for
> model tuning. The `estimate_cost` tool only supports specific endpoint serving
> pricing and will fail with `Unsupported request type` on tuning requests. You
> **MUST** call the `run_command` tool to execute Python code or
> `scripts/calculate_cost.py` (or
> `/workspace/skills/agent-platform-tuning/scripts/calculate_cost.py`) to
> calculate the cost. Whenever a model is chosen or the user switches models
> (e.g. from Llama to Gemma), you **MUST** call `run_command` to calculate or
> recalculate the cost before presenting the dry-run confirmation prompt. Always
> report the calculated dollar figure (e.g., `Estimated tuning cost: $X.XX`) in
> the dry-run confirmation prompt.

-   We calculate the estimated cost of tuning based on the dataset and the
    selected model in the [Models Catalog](./models.md):

    ```bash
    python3 scripts/calculate_cost.py \
        --input my_data.jsonl \
        --model MODEL_NAME \
        --tuning_mode TUNING_MODE \
        --epochs epochs
    ```

    `--model` takes either the display name (`Qwen 3 8B`) or the same resource
    name you pass to `--base_model` (`qwen/qwen3@qwen3-8b`), so the value chosen
    in Step 2.1 can be reused as-is.

> [!NOTE] **Handling Missing Dataset Errors:** If `scripts/calculate_cost.py`
> fails because the dataset file (e.g. `my_data.jsonl` or `dummy_data.jsonl`)
> cannot be found, you **MUST** inform the user that the dataset file does not
> exist or cannot be accessed. You **MUST** prompt the user to provide a valid
> dataset path, and stop tool execution immediately to wait for their response.
> Do **NOT** retry or loop, do **NOT** invent a specific cost number, and do
> **NOT** prompt for job submission approval before receiving a valid dataset
> from the user.

-   **Prompt for Confirmation:** Present the recommended hyperparameter
    configuration and estimated cost (with the concrete dollar figure calculated
    above) to the user and ask for their approval before proceeding to job
    submission. Make sure to note that the estimated cost is just an estimate
    and can vary from actual billing costs.
