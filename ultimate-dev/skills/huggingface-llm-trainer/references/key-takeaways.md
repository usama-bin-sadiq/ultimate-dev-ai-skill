<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the 'Key Takeaways' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Key Takeaways

1. **Submit scripts inline** - The `script` parameter accepts Python code directly; no file saving required unless user requests
2. **Jobs are asynchronous** - Don't wait/poll; let user check when ready
3. **Always set timeout** - Default 30 min is insufficient; minimum 1-2 hours recommended
4. **Always enable Hub push** - Environment is ephemeral; without push, all results lost
5. **Include Trackio** - Use example scripts as templates for real-time monitoring
6. **Offer cost estimation** - When parameters are known, use `scripts/estimate_cost.py`
7. **Use UV scripts (Approach 1)** - Default to `hf_jobs("uv", {...})` with inline scripts; TRL maintained scripts for standard training; avoid bash `trl-jobs` commands in Claude Code
8. **Use hf_doc_fetch/hf_doc_search** for latest TRL documentation
9. **Validate dataset format** before training with dataset inspector (see Dataset Validation section)
10. **Choose appropriate hardware** for model size; use LoRA for models >7B
