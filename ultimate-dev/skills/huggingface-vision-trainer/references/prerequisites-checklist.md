<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'prerequisites-checklist' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
