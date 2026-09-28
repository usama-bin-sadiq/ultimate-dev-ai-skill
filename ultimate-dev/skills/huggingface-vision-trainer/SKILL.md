---
name: huggingface-vision-trainer
description: Trains and fine-tunes vision models for object detection (D-FINE, RT-DETR v2, DETR, YOLOS), image classification (timm models — MobileNetV3, MobileViT, ResNet, ViT/DINOv3 — plus any Transformers classifier), and SAM/SAM2 segmentation using Hugging Face Transformers on Hugging Face Jobs cloud GPUs. Covers COCO-format dataset preparation, Albumentations augmentation, mAP/mAR evaluation, accuracy metrics, SAM segmentation with bbox/point prompts, DiceCE loss, hardware selection, cost estimation, Trackio monitoring, and Hub persistence. Use when users mention training object detection, image classification, SAM, SAM2, segmentation, image matting, DETR, D-FINE, RT-DETR, ViT, timm, MobileNet, ResNet, bounding box models, or fine-tuning vision models on Hugging Face Jobs.
---

# Vision Model Training on Hugging Face Jobs

Train object detection, image classification, and SAM/SAM2 segmentation models on managed cloud GPUs. No local GPU setup required—results are automatically saved to the Hugging Face Hub.

## When to Use This Skill

Use this skill when users want to:
- Fine-tune object detection models (D-FINE, RT-DETR v2, DETR, YOLOS) on cloud GPUs or local
- Fine-tune image classification models (timm: MobileNetV3, MobileViT, ResNet, ViT/DINOv3, or any Transformers classifier) on cloud GPUs or local
- Fine-tune SAM or SAM2 models for segmentation / image matting using bbox or point prompts
- Train bounding-box detectors on custom datasets
- Train image classifiers on custom datasets
- Train segmentation models on custom mask datasets with prompts
- Run vision training jobs on Hugging Face Jobs infrastructure
- Ensure trained vision models are permanently saved to the Hub

## Related Skills

- **`hugging-face-jobs`** — General HF Jobs infrastructure: token authentication, hardware flavors, timeout management, cost estimation, secrets, environment variables, scheduled jobs, and result persistence. **Refer to the Jobs skill for any non-training-specific Jobs questions** (e.g., "how do secrets work?", "what hardware is available?", "how do I pass tokens?").
- **`hugging-face-model-trainer`** — TRL-based language model training (SFT, DPO, GRPO). Use that skill for text/language model fine-tuning.

## Local Script Execution

Helper scripts use PEP 723 inline dependencies. Run them with `uv run`:
```bash
uv run scripts/dataset_inspector.py --dataset username/dataset-name --split train
uv run scripts/estimate_cost.py --help
```

## Prerequisites Checklist

Before starting any training job, verify:

### Account & Authentication
- Hugging Face Account with [Pro](https://hf.co/pro), [Team](https://hf.co/enterprise), or [Enterprise](https://hf.co/enterprise) plan (Jobs require paid plan)
- Authenticated login: Check with `hf_whoami()` (tool) or `hf auth whoami` (terminal)
- Token has **write** permissions
- **MUST pass token in job secrets** — see directive #3 below for syntax (MCP tool vs Python API)

### Dataset Requirements — Object Detection
- Dataset must exist on Hub
- Annotations must use the `objects` column with `bbox`, `category` (and optionally `area`) sub-fields
- Bboxes can be in **xywh (COCO)** or **xyxy (Pascal VOC)** format — auto-detected and converted
- Categories can be **integers or strings** — strings are auto-remapped to integer IDs
- `image_id` column is **optional** — generated automatically if missing
- **ALWAYS validate unknown datasets** before GPU training (see Dataset Validation section)

### Dataset Requirements — Image Classification
- Dataset must exist on Hub
- Must have an **`image` column** (PIL images) and a **`label` column** (integer class IDs or strings)
- The label column can be `ClassLabel` type (with names) or plain integers/strings — strings are auto-remapped
- Common column names auto-detected: `label`, `labels`, `class`, `fine_label`
- **ALWAYS validate unknown datasets** before GPU training (see Dataset Validation section)

### Dataset Requirements — SAM/SAM2 Segmentation
- Dataset must exist on Hub
- Must have an **`image` column** (PIL images) and a **`mask` column** (binary ground-truth segmentation mask)
- Must have a **prompt** — either:
  - A **`prompt` column** with JSON containing `{"bbox": [x0,y0,x1,y1]}` or `{"point": [x,y]}`
  - OR a dedicated **`bbox`** column with `[x0,y0,x1,y1]` values
  - OR a dedicated **`point`** column with `[x,y]` or `[[x,y],...]` values
- Bboxes should be in **xyxy** format (absolute pixel coordinates)
- Example dataset: `merve/MicroMat-mini` (image matting with bbox prompts)
- **ALWAYS validate unknown datasets** before GPU training (see Dataset Validation section)

### Critical Settings
- **Timeout must exceed expected training time** — Default 30min is TOO SHORT. See directive #6 for recommended values.
- **Hub push must be enabled** — `push_to_hub=True`, `hub_model_id="username/model-name"`, token in `secrets`

## Dataset Validation

**Validate dataset format BEFORE launching GPU training to prevent the #1 cause of training failures: format mismatches.**

**ALWAYS validate for** unknown/custom datasets or any dataset you haven't trained with before. **Skip for** `cppe-5` (the default in the training script).

### Running the Inspector

**Option 1: Via HF Jobs (recommended — avoids local SSL/dependency issues):**
```python
hf_jobs("uv", {
    "script": "path/to/dataset_inspector.py",
    "script_args": ["--dataset", "username/dataset-name", "--split", "train"]
})
```

**Option 2: Locally:**
```bash
uv run scripts/dataset_inspector.py --dataset username/dataset-name --split train
```

**Option 3: Via `HfApi().run_uv_job()` (if hf_jobs MCP unavailable):**
```python
from huggingface_hub import HfApi
api = HfApi()
api.run_uv_job(
    script="scripts/dataset_inspector.py",
    script_args=["--dataset", "username/dataset-name", "--split", "train"],
    flavor="cpu-basic",
    timeout=300,
)
```

### Reading Results

- **`✓ READY`** — Dataset is compatible, use directly
- **`✗ NEEDS FORMATTING`** — Needs preprocessing (mapping code provided in output)

## Automatic Bbox Preprocessing

The object detection training script (`scripts/object_detection_training.py`) automatically handles bbox format detection (xyxy→xywh conversion), bbox sanitization, `image_id` generation, string category→integer remapping, and dataset truncation. **No manual preprocessing needed** — just ensure the dataset has `objects.bbox` and `objects.category` columns.

## Training workflow

Detail moved verbatim to `references/training-workflow.md`. Load it when this section matters and the pointer is not enough.

## Critical directives

Detail moved verbatim to `references/critical-directives.md`. Load it when this section matters and the pointer is not enough.

## Model & hardware selection

Detail moved verbatim to `references/model-hardware-selection.md`. Load it when this section matters and the pointer is not enough.

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

## Quick start — SAM/SAM2 Segmentation

Detail moved verbatim to `references/quick-start-sam-sam2-segmentation.md`. Load it when this section matters and the pointer is not enough.

## Checking job status

**MCP tool (if available):**
```
hf_jobs("ps")                                   # List all jobs
hf_jobs("logs", {"job_id": "your-job-id"})      # View logs
hf_jobs("inspect", {"job_id": "your-job-id"})   # Job details
```

**Python API fallback:**
```python
from huggingface_hub import HfApi
api = HfApi()
api.list_jobs()                                  # List all jobs
api.get_job_logs(job_id="your-job-id")           # View logs
api.get_job(job_id="your-job-id")                # Job details
```

## Common failure modes

### OOM (CUDA out of memory)
Reduce `per_device_train_batch_size` (try 4, then 2), reduce `IMAGE_SIZE`, or upgrade hardware.

### Dataset format errors
Run `scripts/dataset_inspector.py` first. The training script auto-detects xyxy vs xywh, converts string categories to integer IDs, and adds `image_id` if missing. Ensure `objects.bbox` contains 4-value coordinate lists in absolute pixels and `objects.category` contains either integer IDs or string labels.

### Hub push failures (401)
Verify: (1) job secrets include token (see directive #2), (2) script sets `training_args.hub_token` BEFORE creating the `Trainer`, (3) `push_to_hub=True` is set, (4) correct `hub_model_id`, (5) token has write permissions.

### Job timeout
Increase timeout (see directive #5 table), reduce epochs/dataset, or use checkpoint strategy with `hub_strategy="every_save"`.

### KeyError: 'test' (missing test split)
The object detection training script handles this gracefully — it falls back to the `validation` split. Ensure you're using the latest `scripts/object_detection_training.py`.

### Single-class dataset: "iteration over a 0-d tensor"
`torchmetrics.MeanAveragePrecision` returns scalar (0-d) tensors for per-class metrics when there's only one class. The template `scripts/object_detection_training.py` handles this by calling `.unsqueeze(0)` on these tensors. Ensure you're using the latest template.

### Poor detection performance (mAP < 0.15)
Increase epochs (30-50), ensure 500+ images, check per-class mAP for imbalanced classes, try different learning rates (1e-5 to 1e-4), increase image size.

For comprehensive troubleshooting: see [references/reliability_principles.md](references/reliability_principles.md)

## Reference files

Detail moved verbatim to `references/reference-files.md`. Load it when this section matters and the pointer is not enough.

Each file below is loaded on demand, not at triage. 17 file(s):

- `references/automatic-bbox-preprocessing.md` — Automatic Bbox Preprocessing. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/checking-job-status.md` — Checking job status. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/common-failure-modes.md` — Common failure modes. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/dataset-validation.md` — Dataset Validation. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/external-links.md` — External links. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/finetune_sam2_trainer.md` — Fine-tuning SAM2 with HF Trainer. Fine-tune SAM2.1 on a small part of the MicroMat dataset for image matting,
- `references/hub_saving.md` — Saving Vision Models to Hugging Face Hub. ---
- `references/image_classification_training_notebook.md` — Image classification. ---
- `references/local-script-execution.md` — Local Script Execution. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/object_detection_training_notebook.md` — Object Detection Training Reference. ---
- `references/prerequisites-checklist.md` — Prerequisites Checklist. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/quick-start-image-classification.md` — Quick start — Image Classification. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/quick-start-object-detection.md` — Quick start — Object Detection. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/related-skills.md` — Related Skills. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
- `references/reliability_principles.md` — Reliability Principles for Training Jobs. ---
- `references/timm_trainer.md` — Using timm models with Hugging Face Trainer. Transformers has first-class support for timm models via the TimmWrapper classes.
- `references/when-to-use-this-skill.md` — When to Use This Skill. <!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the



## External links

- [Transformers Object Detection Guide](https://huggingface.co/docs/transformers/tasks/object_detection)
- [Transformers Image Classification Guide](https://huggingface.co/docs/transformers/tasks/image_classification)
- [DETR Model Documentation](https://huggingface.co/docs/transformers/model_doc/detr)
- [ViT Model Documentation](https://huggingface.co/docs/transformers/model_doc/vit)
- [HF Jobs Guide](https://huggingface.co/docs/huggingface_hub/guides/jobs) — Main Jobs documentation
- [HF Jobs Configuration](https://huggingface.co/docs/hub/en/jobs-configuration) — Hardware, secrets, timeouts, namespaces
- [HF Jobs CLI Reference](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-jobs) — Command line interface
- [Object Detection Models](https://huggingface.co/models?pipeline_tag=object-detection)
- [Image Classification Models](https://huggingface.co/models?pipeline_tag=image-classification)
- [SAM2 Model Documentation](https://huggingface.co/docs/transformers/model_doc/sam2)
- [SAM Model Documentation](https://huggingface.co/docs/transformers/model_doc/sam)
- [Object Detection Datasets](https://huggingface.co/datasets?task_categories=task_categories:object-detection)
- [Image Classification Datasets](https://huggingface.co/datasets?task_categories=task_categories:image-classification)
