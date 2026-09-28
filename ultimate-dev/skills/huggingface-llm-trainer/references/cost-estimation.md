<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the 'Cost Estimation' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Cost Estimation

**Offer to estimate cost when planning jobs with known parameters.** Use `scripts/estimate_cost.py`:

```bash
uv run scripts/estimate_cost.py \
  --model meta-llama/Llama-2-7b-hf \
  --dataset trl-lib/Capybara \
  --hardware a10g-large \
  --dataset-size 16000 \
  --epochs 3
```

Output includes estimated time, cost, recommended timeout (with buffer), and optimization suggestions.

**When to offer:** User planning a job, asks about cost/time, choosing hardware, job will run >1 hour or cost >$5
