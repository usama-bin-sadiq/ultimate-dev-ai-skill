<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'quick-start-object-detection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Quick start — Object Detection

The `script_args` below are the same for both submission methods. See directive #1 for the critical differences between them.

```python
OD_SCRIPT_ARGS = [
    "--model_name_or_path", "ustc-community/dfine-small-coco",
    "--dataset_name", "cppe-5",
    "--image_square_size", "640",
    "--output_dir", "dfine_finetuned",
    "--num_train_epochs", "30",
    "--per_device_train_batch_size", "8",
    "--learning_rate", "5e-5",
    "--eval_strategy", "epoch",
    "--save_strategy", "epoch",
    "--save_total_limit", "2",
    "--load_best_model_at_end",
    "--metric_for_best_model", "eval_map",
    "--greater_is_better", "True",
    "--no_remove_unused_columns",
    "--no_eval_do_concat_batches",
    "--push_to_hub",
    "--hub_model_id", "username/model-name",
    "--do_train",
    "--do_eval",
]
```

```python
from huggingface_hub import HfApi, get_token
api = HfApi()
job_info = api.run_uv_job(
    script="scripts/object_detection_training.py",
    script_args=OD_SCRIPT_ARGS,
    flavor="t4-small",
    timeout=14400,
    env={"PYTHONUNBUFFERED": "1"},
    secrets={"HF_TOKEN": get_token()},
)
print(f"Job ID: {job_info.id}")
```

### Key OD `script_args`

- `--model_name_or_path` — recommended: `"ustc-community/dfine-small-coco"` (see model table above)
- `--dataset_name` — the Hub dataset ID
- `--image_square_size` — 480 (fast iteration) or 800 (better accuracy)
- `--hub_model_id` — `"username/model-name"` for Hub persistence
- `--num_train_epochs` — 30 typical for convergence
- `--train_val_split` — fraction to split for validation (default 0.15), set if dataset lacks a validation split
- `--max_train_samples` — truncate training set (useful for quick test runs, e.g. `"785"` for ~10% of a 7.8K dataset)
- `--max_eval_samples` — truncate evaluation set
