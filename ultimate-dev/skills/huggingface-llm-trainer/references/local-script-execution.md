<!-- Moved verbatim from huggingface-llm-trainer/SKILL.md, the
     'local-script-execution' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Local Script Execution

Repository scripts use PEP 723 inline dependencies. Run them with `uv run`:
```bash
uv run scripts/estimate_cost.py --help
uv run scripts/dataset_inspector.py --help
```
