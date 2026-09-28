<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the 'Reference files' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Reference files

These ship with the skill and are read on demand; none is needed to
use it. Each answers one question the sections above do not.

- [`./reliability_principles.md`](./reliability_principles.md)

### Scripts (In This Skill)
- `scripts/train_sft_example.py` - Production SFT template
- `scripts/train_dpo_example.py` - Production DPO template
- `scripts/train_grpo_example.py` - Production GRPO template
- `scripts/unsloth_sft_example.py` - Unsloth text LLM training template (faster, less VRAM)
- `scripts/estimate_cost.py` - Estimate time and cost (offer when appropriate)
- `scripts/convert_to_gguf.py` - Complete GGUF conversion script
- `scripts/hf_benchmarks.py` - Search for benchmark results and leaderboards by task, alias or free text.

### External Scripts
- [Dataset Inspector](https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py) - Validate dataset format before training (use via `uv run` or `hf_jobs`)

### External Links
- [TRL Documentation](https://huggingface.co/docs/trl)
- [TRL Jobs Training Guide](https://huggingface.co/docs/trl/en/jobs_training)
- [TRL Jobs Package](https://github.com/huggingface/trl-jobs)
- [HF Jobs Documentation](https://huggingface.co/docs/huggingface_hub/guides/jobs)
- [TRL Example Scripts](https://github.com/huggingface/trl/tree/main/examples/scripts)
- [UV Scripts Guide](https://docs.astral.sh/uv/guides/scripts/)
- [UV Scripts Organization](https://huggingface.co/uv-scripts)
