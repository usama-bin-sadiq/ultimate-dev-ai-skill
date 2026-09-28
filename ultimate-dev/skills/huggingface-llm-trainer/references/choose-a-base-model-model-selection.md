<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the 'Choose a Base Model (Model Selection)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Choose a Base Model (Model Selection)

**Identify models to train based on task type or benchmark results.**

Use `scripts/hf_benchmarks.py` to identify top-performing models for specific tasks. This helps the user select a model as the base for training, whilst keeping size and hardware constraints in mind.

```bash
# Get help on the benchmarks command:
uv run scripts/hf_benchmarks.py --help
```

### Example -- choosing an OCR base model
```bash
# Search for benchmarks containing whose name contains the text `ocr`
uv run scripts/hf_benchmarks.py search --query ocr

# Get the ranked leaderboard for the allenai/olmOCR-bench benchmark 
uv run scripts/hf_benchmarks.py leaderboard allenai/olmOCR-bench
```
