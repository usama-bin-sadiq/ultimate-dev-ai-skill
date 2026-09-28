<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'training-workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Training workflow

Copy this checklist and track progress:

```
Training Progress:
- [ ] Step 1: Verify prerequisites (account, token, dataset)
- [ ] Step 2: Validate dataset format (run dataset_inspector.py)
- [ ] Step 3: Ask user about dataset size and validation split
- [ ] Step 4: Prepare training script (OD: scripts/object_detection_training.py, IC: scripts/image_classification_training.py, SAM: scripts/sam_segmentation_training.py)
- [ ] Step 5: Save script locally, submit job, and report details
```

**Step 1: Verify prerequisites**

Follow the Prerequisites Checklist above.

**Step 2: Validate dataset**

Run the dataset inspector BEFORE spending GPU time. See "Dataset Validation" section above.

**Step 3: Ask user preferences**

ALWAYS use the AskUserQuestion tool with option-style format:

```python
AskUserQuestion({
    "questions": [
        {
            "question": "Do you want to run a quick test with a subset of the data first?",
            "header": "Dataset Size",
            "options": [
                {"label": "Quick test run (10% of data)", "description": "Faster, cheaper (~30-60 min, ~$2-5) to validate setup"},
                {"label": "Full dataset (Recommended)", "description": "Complete training for best model quality"}
            ],
            "multiSelect": false
        },
        {
            "question": "Do you want to create a validation split from the training data?",
            "header": "Split data",
            "options": [
                {"label": "Yes (Recommended)", "description": "Automatically split 15% of training data for validation"},
                {"label": "No", "description": "Use existing validation split from dataset"}
            ],
            "multiSelect": false
        },
        {
            "question": "Which GPU hardware do you want to use?",
            "header": "Hardware Flavor",
            "options": [
                {"label": "t4-small ($0.40/hr)", "description": "1x T4, 16 GB VRAM — sufficient for all OD models under 100M params"},
                {"label": "l4x1 ($0.80/hr)", "description": "1x L4, 24 GB VRAM — more headroom for large images or batch sizes"},
                {"label": "a10g-large ($1.50/hr)", "description": "1x A10G, 24 GB VRAM — faster training, more CPU/RAM"},
                {"label": "a100-large ($2.50/hr)", "description": "1x A100, 80 GB VRAM — fastest, for very large datasets or image sizes"}
            ],
            "multiSelect": false
        }
    ]
})
```

**Step 4: Prepare training script**

For object detection, use [scripts/object_detection_training.py](scripts/object_detection_training.py) as the production-ready template. For image classification, use [scripts/image_classification_training.py](scripts/image_classification_training.py). For SAM/SAM2 segmentation, use [scripts/sam_segmentation_training.py](scripts/sam_segmentation_training.py). All scripts use `HfArgumentParser` — all configuration is passed via CLI arguments in `script_args`, NOT by editing Python variables. For timm model details, see [references/timm_trainer.md](references/timm_trainer.md). For SAM2 training details, see [references/finetune_sam2_trainer.md](references/finetune_sam2_trainer.md).

**Step 5: Save script, submit job, and report**

1. **Save the script locally** to `submitted_jobs/` in the workspace root (create if needed) with a descriptive name like `training_<dataset>_<YYYYMMDD_HHMMSS>.py`. Tell the user the path.
2. **Submit** using `hf_jobs` MCP tool (preferred) or `HfApi().run_uv_job()` — see directive #1 for both methods. Pass all config via `script_args`.
3. **Report** the job ID (from `.id` attribute), monitoring URL, Trackio dashboard (`https://huggingface.co/spaces/{username}/trackio`), expected time, and estimated cost.
4. **Wait for user** to request status checks — don't poll automatically. Training jobs run asynchronously and can take hours.
