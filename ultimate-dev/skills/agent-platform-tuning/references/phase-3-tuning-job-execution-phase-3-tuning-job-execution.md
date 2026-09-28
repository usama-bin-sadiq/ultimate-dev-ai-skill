<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
     'phase-3-tuning-job-execution-phase-3-tuning-job-execution' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 3: Tuning Job Execution {#phase-3-tuning-job-execution}

**CRITICAL Pre-Flight Check (GCS Verification):** Before you propose a
confirmation prompt or submit any tuning job, you **MUST** verify that the
specified training dataset GCS URI (e.g. `gs://dummy_bucket/dataset.jsonl` or
`gs://YOUR_BUCKET/...`) actually exists and is accessible. Run `gcloud storage
ls $DATASET_URI` (or `gsutil ls`).

*   **If the verification fails** (e.g. `BucketNotFound`, `404`, `AccessDenied`,
    or indicating a dummy/missing bucket), you **MUST** inform the user that the
    GCS bucket or dataset does not exist or cannot be accessed. You **MUST**
    prompt the user to provide a valid GCS URI for the dataset, and stop tool
    execution immediately to wait for their response. Do **NOT** propose a
    confirmation prompt and do **NOT** execute any tuning scripts before
    receiving a valid dataset URI from the user.
*   **If the verification succeeds**, proceed to propose the confirmation prompt
    below.

### For Gemini Models

Submit the Gemini supervised fine-tuning job using the Python SDK
(`google.genai` or `vertexai.tuning.sft`):

```python
from google import genai
from google.genai import types

client = genai.Client(enterprise=True, project=PROJECT, location=LOCATION)
tuning_job = client.tunings.tune(
    base_model=BASE_MODEL,  # e.g. "gemini-2.5-flash"
    training_dataset=types.TuningDataset(gcs_uri=TRAIN_DATASET_URI),
    config=types.CreateTuningJobConfig(
        epoch_count=EPOCHS,  # e.g. 3
        learning_rate_multiplier=LEARNING_RATE_MULTIPLIER,  # e.g. 1.0
        validation_dataset=(
            types.TuningValidationDataset(gcs_uri=VAL_DATASET_URI)
            if VAL_DATASET_URI
            else None
        ),
    ),
)
print("Tuning Job Resource Name:", tuning_job.name)
```

Alternatively using `vertexai.tuning.sft`:

```python
import vertexai
from vertexai.tuning import sft

vertexai.init(project=PROJECT, location=LOCATION)
job = sft.train(
    source_model=BASE_MODEL,
    train_dataset=TRAIN_DATASET_URI,
    validation_dataset=VAL_DATASET_URI,
    epochs=EPOCHS,
    learning_rate_multiplier=LEARNING_RATE_MULTIPLIER,
)
print("Tuning Job Resource Name:", job.resource_name)
```

Execute the Python script via `python3` (inline or written to
`/tmp/submit_gemini_tuning.py`). Report the returned operation name or trackable
resource identifier, and do NOT wait for the terminal state.

### For Open Models

Submit the open model tuning job using `scripts/tune_open_model.py` or the
Python SDK. Identify the model id using available models documentation
at
[documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-model-tuning#supported-models).


`--base_model` takes a publisher model **resource name**
(`{publisher}/{model_id}@{version_id}`), not the display name shown in the
catalog. See "Model Resource Name Format" in `references/models.md` for the
format, verified examples, and how to look up a name you do not have.

Using `scripts/tune_open_model.py`:

```bash
python3 scripts/tune_open_model.py \
    --project YOUR_PROJECT \
    --location global \
    --base_model BASE_MODEL_ID \
    --train_dataset gs://YOUR_BUCKET/tuning_agent_job_<datetime>/dataset.jsonl \
    --output_uri gs://YOUR_BUCKET/tuning_agent_job_<datetime>/output \
    --epochs EPOCHS \
    --learning_rate LR \
    --tuning_mode MODE
```

*(If `scripts/tune_open_model.py` is not in the current working directory, run
the Python SDK snippet directly with `python3 -c "..."` or write it to
`/tmp/submit_open_tuning.py` using `client.tunings.tune`.)*

This script is open model only, and `--location` falls back to `global` if
omitted. Always pass the location the user confirmed in section 0.2 explicitly,
so it is visible in the command string you present for approval.

> [!WARNING] **`--output_uri` is required for open models.** The Python SDK
> declares it as `output_uri: Optional[str] = None`, but the tuning backend
> rejects open model jobs that omit it with `INVALID_ARGUMENT: The output_uri
> field is required for this model.` Treat the SDK's "optional" signature as
> wrong here and always pass a GCS destination.

Because the flag is mandatory, you must establish where the tuned model is
written before you can submit. **Never invent a bucket name, derive one from the
project number, or run `gcloud storage buckets create` unprompted.** Creating a
bucket is a mutating action and is subject to the Tier M confirmation policy
below.

-   **The user named a bucket or URI** → use it EXACTLY as specified by the user
    (verbatim), appending a unique per-job directory as in section 1.2.
    **CRITICAL:** NEVER alter, prefix, or prepend the project number or anything
    else to a user-specified bucket name! Even if `gcloud storage buckets list`
    shows an existing bucket with a project-prefixed name (e.g.
    `gs://PROJECT-mybucket` when the user asked for `gs://mybucket`), you MUST
    use the user's exact bucket name `gs://mybucket` verbatim. Never silently
    substitute an existing bucket.
-   **A bucket was already used for the dataset upload in section 1.2** →
    propose reusing it for the output and ask the user to confirm.
-   **Neither or user states they have no bucket** → Check existing buckets in
    the project (`gcloud storage buckets list --project=PROJECT`) or offer to
    create a dedicated bucket. When proposing a bucket to create, ensure the
    bucket name is unique by including a unique suffix or timestamp (e.g.
    `gs://PROJECT-tuning-$(date +%s)` or
    `gs://PROJECT-tuning-artifacts-<timestamp>` in LOCATION) to prevent HTTP 409
    collisions with previously created buckets. Propose the destination bucket
    in your configuration dry-run preview and ask the user for confirmation
    before proceeding.

> [!IMPORTANT] **Interactive Confirmation Required (Tier M):** Before proceeding
> with job submission, you **MUST** present the proposed command string showing
> all literal flags in a confirmation prompt to the user with 'Yes' and 'No'
> options.

> **CRITICAL:** When presenting this confirmation prompt to the user, you MUST
> output it as a direct plain text response and stop tool execution immediately.
> Do NOT call any command execution or interactive tools in the same turn, as
> unexpected tool calls may be auto-replied by the simulation harness and cause
> an infinite loop. Yield immediately for the user's reply.
