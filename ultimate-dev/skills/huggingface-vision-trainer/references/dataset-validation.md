<!-- Moved verbatim from huggingface-vision-trainer/SKILL.md, the
     'dataset-validation' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
