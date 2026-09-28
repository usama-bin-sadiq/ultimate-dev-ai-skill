<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the
     'phase-1-dataset-preparation-upload-phase-1' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 1: Dataset Preparation & Upload {#phase-1}

### 1.0 Dataset Discovery & Confirmation

-   **User-Provided Dataset Verification:** If the user specifies a dataset
    filename or path in their prompt, verify its existence in the workspace
    (e.g. via script execution or checking for typos).
    *   **If the file cannot be found anywhere**, you **MUST** inform the user
        that the dataset file does not exist or cannot be accessed. You **MUST**
        prompt the user to provide a valid dataset path. Alternatively, if
        candidate dataset files are found in the workspace during your search,
        you **MUST** present the candidates to the user and ask them to select
        one. You **MUST** stop tool execution immediately after reporting the
        missing file or presenting candidates, and wait for the user's response.
        Do **NOT** ask for 90/10 validation split permission, and do **NOT**
        attempt to upload the dataset before receiving a valid dataset file
        selection from the user.
    *   **If the file is found and verified**, proceed to Step 1.1 Formatting &
        Validation below.
-   **Auto-Discovery: From User Bucket:** If the user does not have a dataset
    and no suitable alternative is found in the Hugging Face reference, offer to
    search the user's GCS buckets for potential training data. Prioritize
    searching for files with extensions like `.jsonl`, `.json`, `.csv`, and
    `.parquet`. If such files are found, read the first few lines/records of
    each to determine if they contain text-based data suitable for tuning (e.g.,
    prompt/completion pairs) that can be modified to follow
    [Data Preparation Guide](references/data_prep.md) and is related to the
    tuning task requested. **DO NOT** search without prompting first.
-   **Auto-Discovery: From Task to Huggingface:** If the user has a specific
    task (e.g. math reasoning, coding, instruction following) or wants to use a
    Hugging Face dataset without naming a specific one, refer to
    [Huggingface Datasets Reference](references/hf_datasets.md) and recommend
    matching datasets (e.g., `open-r1/OpenR1-Math-220k` or
    `AI-MO/NuminaMath-TIR` for mathematical reasoning; `openai/gsm8k` is also
    widely used). For each dataset recommended, provide some information about
    the dataset and provide some reasonable splits, and ask the user to select
    one. Do NOT output generic instructions telling the user to prepare and
    upload their own data — proactively guide the interactive dataset discovery,
    preview, and preparation flow.

    > [!IMPORTANT] **CRITICAL: Ask for Confirmation and Column Selection.** Once
    > the dataset is selected, execute Python via `run_command` to inspect the
    > dataset using `load_dataset(..., streaming=True)`. Do not proceed with
    > dataset preparation or upload until you perform the following steps and
    > get user confirmation: 1. **Dataset and Split Confirmation:** Present the
    > dataset and available splits to the user and have them confirm which to
    > use. 2. **Column Selection (Hugging Face or Custom Datasets):** You
    > must: - Provide a list of all available columns in the selected dataset
    > split. - **Show a few samples from the dataset** to help the user
    > understand the content and make the choice of columns. - Recommend which
    > columns should be mapped to `prompt` (or user message) and `completion`
    > (or assistant response), offering a few reasonable options if
    > applicable. - Ask the user to confirm the column mapping or specify which
    > columns to use.

### 1.1 Formatting & Validation

-   **Conversion**: If data is in CSV, JSON, or Parquet, use
    `scripts/prepare_dataset.py` to convert.
-   **Validation Split Confirmation**: Whenever generating or preparing a single
    dataset without an explicit validation set (including when generating sample
    chat/instruction datasets or preparing training datasets), you MUST generate
    or process the data using Python via `run_command` and **you MUST prompt the
    user** to seek permission to split the training dataset 90/10 to form a
    validation dataset (using `--validation_split 0.1` or Python script). If
    they agree, proceed with the split. If they decline, just use the training
    dataset without a validation dataset. Do **NOT** offer an 80/20 split; the
    tuning service rejects it, for the reason given in
    the
    [Data Preparation Guide](references/data_prep.md#sizing-the-validation-split).
 Do NOT proceed to upload the dataset or
    submit the tuning job before asking the user about the 90/10 validation
    split!
-   **Validation**: If data is already in JSONL, validate it before uploading.
    Simply having a `.jsonl` extension is not enough. You must verify that the
    content schema is valid for tuning (e.g. correct system/user/model roles).

```bash
python3 scripts/prepare_dataset.py \
    --input my_data.jsonl \
    --format <messages|messages_gemini> \
    --validate_only
```

*(Use `--format messages` for open models and `--format messages_gemini` for
Gemini models.)* - Refer to [Data Preparation Guide](references/data_prep.md)
for required schemas.

### 1.2 Upload

Upload formatted `.jsonl` files to GCS using a unique directory (e.g., with a
datetime timestamp) to avoid overwriting outputs from different runs. If the
user named a bucket (e.g., `gs://mybucket`), use that bucket name EXACTLY as
provided (verbatim) and NEVER prepend the project ID or modify the bucket name.

```bash
ARTIFACTS="gs://YOUR_BUCKET/tuning_agent_job_<datetime>/dataset.jsonl"
gcloud storage cp dataset.jsonl "$ARTIFACTS"
```
