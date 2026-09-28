<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Common failure modes

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

For comprehensive troubleshooting: see [references/reliability_principles.md](./reliability_principles.md)
