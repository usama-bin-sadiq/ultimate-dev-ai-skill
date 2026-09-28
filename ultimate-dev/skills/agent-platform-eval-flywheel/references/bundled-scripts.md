<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the
     'bundled-scripts' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Bundled scripts

Script                   | When to use
------------------------ | -----------
`validate_dataset.py`    | Before Stage 3 — catch malformed `EvaluationDataset` JSON.
`parse_adk_traces.py`    | Stage 1 — convert ADK session dumps to the canonical dataset shape.
`inspect_results.py`     | Stages 3/4 — render summary + per-case scores. `--save-html` for a browsable report.
`compare_results.py`     | Stage 5 — diff baseline vs. candidate, detect regressions.
`render_html_report.py`  | Render HTML from a saved result JSON or loss-clusters JSON.
`endpoint_evaluation.py` | Stages 2/3 against a deployed Agent Platform endpoint (BYOM). See [references/deployment.md](references/deployment.md).
`maas_evaluation.py`     | Stages 2/3 against a Model-as-a-Service model by ID. See [references/deployment.md](references/deployment.md).
