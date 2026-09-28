<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'quick-start-image-classification' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Quick start — Image Classification

```python
IC_SCRIPT_ARGS = [
    "--model_name_or_path", "timm/mobilenetv3_small_100.lamb_in1k",
    "--dataset_name", "ethz/food101",
    "--output_dir", "food101_classifier",
    "--num_train_epochs", "5",
    "--per_device_train_batch_size", "32",
    "--per_device_eval_batch_size", "32",
    "--learning_rate", "5e-5",
    "--eval_strategy", "epoch",
    "--save_strategy", "epoch",
    "--save_total_limit", "2",
    "--load_best_model_at_end",
    "--metric_for_best_model", "eval_accuracy",
    "--greater_is_better", "True",
    "--no_remove_unused_columns",
    "--push_to_hub",
    "--hub_model_id", "username/food101-classifier",
    "--do_train",
    "--do_eval",
]
```

```python
from huggingface_hub import HfApi, get_token
api = HfApi()
job_info = api.run_uv_job(
    script="scripts/image_classification_training.py",
    script_args=IC_SCRIPT_ARGS,
    flavor="t4-small",
    timeout=7200,
    env={"PYTHONUNBUFFERED": "1"},
    secrets={"HF_TOKEN": get_token()},
)
print(f"Job ID: {job_info.id}")
```

### Key IC `script_args`

- `--model_name_or_path` — any `timm/` model or Transformers classification model (see model table above)
- `--dataset_name` — the Hub dataset ID
- `--image_column_name` — column containing PIL images (default: `"image"`)
- `--label_column_name` — column containing class labels (default: `"label"`)
- `--hub_model_id` — `"username/model-name"` for Hub persistence
- `--num_train_epochs` — 3-5 typical for classification (fewer than OD)
- `--per_device_train_batch_size` — 16-64 (classification models use less memory than OD)
- `--train_val_split` — fraction to split for validation (default 0.15), set if dataset lacks a validation split
- `--max_train_samples` / `--max_eval_samples` — truncate for quick tests
