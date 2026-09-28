<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'model-hardware-selection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Model & hardware selection

### Recommended object detection models

| Model | Params | Use case |
|-------|--------|----------|
| `ustc-community/dfine-small-coco` | 10.4M | Best starting point — fast, cheap, SOTA quality |
| `PekingU/rtdetr_v2_r18vd` | 20.2M | Lightweight real-time detector |
| `ustc-community/dfine-large-coco` | 31.4M | Higher accuracy, still efficient |
| `PekingU/rtdetr_v2_r50vd` | 43M | Strong real-time baseline |
| `ustc-community/dfine-xlarge-obj365` | 63.5M | Best accuracy (pretrained on Objects365) |
| `PekingU/rtdetr_v2_r101vd` | 76M | Largest RT-DETR v2 variant |

Start with `ustc-community/dfine-small-coco` for fast iteration. Move to D-FINE Large or RT-DETR v2 R50 for better accuracy.

### Recommended image classification models

All `timm/` models work out of the box via `AutoModelForImageClassification` (loaded as `TimmWrapperForImageClassification`). See [references/timm_trainer.md](references/timm_trainer.md) for details.

| Model | Params | Use case |
|-------|--------|----------|
| `timm/mobilenetv3_small_100.lamb_in1k` | 2.5M | Ultra-lightweight — mobile/edge, fastest training |
| `timm/mobilevit_s.cvnets_in1k` | 5.6M | Mobile transformer — good accuracy/speed trade-off |
| `timm/resnet50.a1_in1k` | 25.6M | Strong CNN baseline — reliable, well-studied |
| `timm/vit_base_patch16_dinov3.lvd1689m` | 86.6M | Best accuracy — DINOv3 self-supervised ViT |

Start with `timm/mobilenetv3_small_100.lamb_in1k` for fast iteration. Move to `timm/resnet50.a1_in1k` or `timm/vit_base_patch16_dinov3.lvd1689m` for better accuracy.

### Recommended SAM/SAM2 segmentation models

| Model | Params | Use case |
|-------|--------|----------|
| `facebook/sam2.1-hiera-tiny` | 38.9M | Fastest SAM2 — good for quick experiments |
| `facebook/sam2.1-hiera-small` | 46.0M | Best starting point — good quality/speed balance |
| `facebook/sam2.1-hiera-base-plus` | 80.8M | Higher capacity for complex segmentation |
| `facebook/sam2.1-hiera-large` | 224.4M | Best SAM2 accuracy — requires more VRAM |
| `facebook/sam-vit-base` | 93.7M | Original SAM — ViT-B backbone |
| `facebook/sam-vit-large` | 312.3M | Original SAM — ViT-L backbone |
| `facebook/sam-vit-huge` | 641.1M | Original SAM — ViT-H, best SAM v1 accuracy |

Start with `facebook/sam2.1-hiera-small` for fast iteration. SAM2 models are generally more efficient than SAM v1 at similar quality. Only the mask decoder is trained by default (vision and prompt encoders are frozen).

### Hardware recommendation

All recommended OD and IC models are under 100M params — **`t4-small` (16 GB VRAM, $0.40/hr) is sufficient for all of them.** Image classification models are generally smaller and faster than object detection models — `t4-small` handles even ViT-Base comfortably. For SAM2 models up to `hiera-base-plus`, `t4-small` is sufficient since only the mask decoder is trained. For `sam2.1-hiera-large` or SAM v1 models, use `l4x1` or `a10g-large`. Only upgrade if you hit OOM from large batch sizes — reduce batch size first before switching hardware. Common upgrade path: `t4-small` → `l4x1` ($0.80/hr, 24 GB) → `a10g-large` ($1.50/hr, 24 GB).

For full hardware flavor list: refer to the `hugging-face-jobs` skill. For cost estimation: run `scripts/estimate_cost.py`.
