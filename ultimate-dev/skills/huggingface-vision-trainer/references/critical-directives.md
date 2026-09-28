<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'critical-directives' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Critical directives

These rules prevent common failures. Follow them exactly.

### 1. Job submission: `hf_jobs` MCP tool vs Python API

**`hf_jobs()` is an MCP tool, NOT a Python function.** Do NOT try to import it from `huggingface_hub`. Call it as a tool:

```
hf_jobs("uv", {"script": training_script_content, "flavor": "a10g-large", "timeout": "4h", "secrets": {"HF_TOKEN": "$HF_TOKEN"}})
```

**If `hf_jobs` MCP tool is unavailable**, use the Python API directly:

```python
from huggingface_hub import HfApi, get_token
api = HfApi()
job_info = api.run_uv_job(
    script="path/to/training_script.py",  # file PATH, NOT content
    script_args=["--dataset_name", "cppe-5", ...],
    flavor="a10g-large",
    timeout=14400,  # seconds (4 hours)
    env={"PYTHONUNBUFFERED": "1"},
    secrets={"HF_TOKEN": get_token()},  # MUST use get_token(), NOT "$HF_TOKEN"
)
print(f"Job ID: {job_info.id}")
```

**Critical differences between the two methods:**

| | `hf_jobs` MCP tool | `HfApi().run_uv_job()` |
|---|---|---|
| `script` param | Python code string or URL (NOT local paths) | File path to `.py` file (NOT content) |
| Token in secrets | `"$HF_TOKEN"` (auto-replaced) | `get_token()` (actual token value) |
| Timeout format | String (`"4h"`) | Seconds (`14400`) |

**Rules for both methods:**
- The training script MUST include PEP 723 inline metadata with dependencies
- Do NOT use `image` or `command` parameters (those belong to `run_job()`, not `run_uv_job()`)

### 2. Authentication via job secrets + explicit hub_token injection

**Job config** MUST include the token in secrets — syntax depends on submission method (see table above).

**Training script requirement:** The Transformers `Trainer` calls `create_repo(token=self.args.hub_token)` during `__init__()` when `push_to_hub=True`. The training script MUST inject `HF_TOKEN` into `training_args.hub_token` AFTER parsing args but BEFORE creating the `Trainer`. The template `scripts/object_detection_training.py` already includes this:

```python
hf_token = os.environ.get("HF_TOKEN")
if training_args.push_to_hub and not training_args.hub_token:
    if hf_token:
        training_args.hub_token = hf_token
```

If you write a custom script, you MUST include this token injection before the `Trainer(...)` call.

- Do NOT call `login()` in custom scripts unless replicating the full pattern from `scripts/object_detection_training.py`
- Do NOT rely on implicit token resolution (`hub_token=None`) — unreliable in Jobs
- See the `hugging-face-jobs` skill → *Token Usage Guide* for full details

### 3. JobInfo attribute

Access the job identifier using `.id` (NOT `.job_id` or `.name` — these don't exist):

```python
job_info = api.run_uv_job(...)  # or hf_jobs("uv", {...})
job_id = job_info.id  # Correct -- returns string like "687fb701029421ae5549d998"
```

### 4. Required training flags and HfArgumentParser boolean syntax

`scripts/object_detection_training.py` uses `HfArgumentParser` — all config is passed via `script_args`. Boolean arguments have two syntaxes:

- **`bool` fields** (e.g., `push_to_hub`, `do_train`): Use as bare flags (`--push_to_hub`) or negate with `--no_` prefix (`--no_remove_unused_columns`)
- **`Optional[bool]` fields** (e.g., `greater_is_better`): MUST pass explicit value (`--greater_is_better True`). Bare `--greater_is_better` causes `error: expected one argument`

Required flags for object detection:

```
--no_remove_unused_columns          # MUST: preserves image column for pixel_values
--no_eval_do_concat_batches         # MUST: images have different numbers of target boxes
--push_to_hub                       # MUST: environment is ephemeral
--hub_model_id username/model-name
--metric_for_best_model eval_map
--greater_is_better True            # MUST pass "True" explicitly (Optional[bool])
--do_train
--do_eval
```

Required flags for image classification:

```
--no_remove_unused_columns          # MUST: preserves image column for pixel_values
--push_to_hub                       # MUST: environment is ephemeral
--hub_model_id username/model-name
--metric_for_best_model eval_accuracy
--greater_is_better True            # MUST pass "True" explicitly (Optional[bool])
--do_train
--do_eval
```

Required flags for SAM/SAM2 segmentation:

```
--remove_unused_columns False       # MUST: preserves input_boxes/input_points
--push_to_hub                       # MUST: environment is ephemeral
--hub_model_id username/model-name
--do_train
--prompt_type bbox                  # or "point"
--dataloader_pin_memory False       # MUST: avoids pin_memory issues with custom collator
```

### 5. Timeout management

Default 30 min is TOO SHORT for object detection. Set minimum 2-4 hours. Add 30% buffer for model loading, preprocessing, and Hub push.

| Scenario | Timeout |
|----------|---------|
| Quick test (100-200 images, 5-10 epochs) | 1h |
| Development (500-1K images, 15-20 epochs) | 2-3h |
| Production (1K-5K images, 30 epochs) | 4-6h |
| Large dataset (5K+ images) | 6-12h |

### 6. Trackio monitoring

Trackio is **always enabled** in the object detection training script — it calls `trackio.init()` and `trackio.finish()` automatically. No need to pass `--report_to trackio`. The project name is taken from `--output_dir` and the run name from `--run_name`. For image classification, pass `--report_to trackio` in `TrainingArguments`.

Dashboard at: `https://huggingface.co/spaces/{username}/trackio`
