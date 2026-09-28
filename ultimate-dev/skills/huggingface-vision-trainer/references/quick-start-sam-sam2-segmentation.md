<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'quick-start-sam-sam2-segmentation' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Quick start — SAM/SAM2 Segmentation

```python
SAM_SCRIPT_ARGS = [
    "--model_name_or_path", "facebook/sam2.1-hiera-small",
    "--dataset_name", "merve/MicroMat-mini",
    "--prompt_type", "bbox",
    "--prompt_column_name", "prompt",
    "--output_dir", "sam2-finetuned",
    "--num_train_epochs", "30",
    "--per_device_train_batch_size", "4",
    "--learning_rate", "1e-5",
    "--logging_steps", "1",
    "--save_strategy", "epoch",
    "--save_total_limit", "2",
    "--remove_unused_columns", "False",
    "--dataloader_pin_memory", "False",
    "--push_to_hub",
    "--hub_model_id", "username/sam2-finetuned",
    "--do_train",
    "--report_to", "trackio",
]
```

```python
from huggingface_hub import HfApi, get_token
api = HfApi()
job_info = api.run_uv_job(
    script="scripts/sam_segmentation_training.py",
    script_args=SAM_SCRIPT_ARGS,
    flavor="t4-small",
    timeout=7200,
    env={"PYTHONUNBUFFERED": "1"},
    secrets={"HF_TOKEN": get_token()},
)
print(f"Job ID: {job_info.id}")
```

### Key SAM `script_args`

- `--model_name_or_path` — SAM or SAM2 model (see model table above); auto-detects SAM vs SAM2
- `--dataset_name` — the Hub dataset ID (e.g., `"merve/MicroMat-mini"`)
- `--prompt_type` — `"bbox"` or `"point"` — type of prompt in the dataset
- `--prompt_column_name` — column with JSON-encoded prompts (default: `"prompt"`)
- `--bbox_column_name` — dedicated bbox column (alternative to JSON prompt column)
- `--point_column_name` — dedicated point column (alternative to JSON prompt column)
- `--mask_column_name` — column with ground-truth masks (default: `"mask"`)
- `--hub_model_id` — `"username/model-name"` for Hub persistence
- `--num_train_epochs` — 20-30 typical for SAM fine-tuning
- `--per_device_train_batch_size` — 2-4 (SAM models use significant memory)
- `--freeze_vision_encoder` / `--freeze_prompt_encoder` — freeze encoder weights (default: both frozen, only mask decoder trains)
- `--train_val_split` — fraction to split for validation (default 0.1)
