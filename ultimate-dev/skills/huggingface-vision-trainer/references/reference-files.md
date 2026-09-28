<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'reference-files' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Reference files

- [scripts/object_detection_training.py](scripts/object_detection_training.py) — Production-ready object detection training script
- [scripts/image_classification_training.py](scripts/image_classification_training.py) — Production-ready image classification training script (supports timm models)
- [scripts/sam_segmentation_training.py](scripts/sam_segmentation_training.py) — Production-ready SAM/SAM2 segmentation training script (bbox & point prompts)
- [scripts/dataset_inspector.py](scripts/dataset_inspector.py) — Validate dataset format for OD, classification, and SAM segmentation
- [scripts/estimate_cost.py](scripts/estimate_cost.py) — Estimate training costs for any vision model (includes SAM/SAM2)
- [references/object_detection_training_notebook.md](references/object_detection_training_notebook.md) — Object detection training workflow, augmentation strategies, and training patterns
- [references/image_classification_training_notebook.md](references/image_classification_training_notebook.md) — Image classification training workflow with ViT, preprocessing, and evaluation
- [references/finetune_sam2_trainer.md](references/finetune_sam2_trainer.md) — SAM2 fine-tuning walkthrough with MicroMat dataset, DiceCE loss, and Trainer integration
- [references/timm_trainer.md](references/timm_trainer.md) — Using timm models with HF Trainer (TimmWrapper, transforms, full example)
- [references/hub_saving.md](references/hub_saving.md) — Detailed Hub persistence guide and verification checklist
- [
Each file below is loaded on demand, not at triage. 6 file(s):

- `references/finetune_sam2_trainer.md` — Fine-tuning SAM2 with HF Trainer. Fine-tune SAM2.1 on a small part of the MicroMat dataset for image matting,
- `references/hub_saving.md` — Saving Vision Models to Hugging Face Hub. ---
- `references/image_classification_training_notebook.md` — Image classification. ---
- `references/object_detection_training_notebook.md` — Object Detection Training Reference. ---
- `references/reliability_principles.md` — Reliability Principles for Training Jobs. ---
- `references/timm_trainer.md` — Using timm models with Hugging Face Trainer. Transformers has first-class support for timm models via the TimmWrapper classes.

references/reliability_principles.md](references/reliability_principles.md) — Failure prevention principles from production experience
