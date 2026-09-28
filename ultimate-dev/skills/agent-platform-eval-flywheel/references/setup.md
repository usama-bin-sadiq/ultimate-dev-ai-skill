<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the
     'setup' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Setup

The scripts need `vertexai` (from `google-cloud-aiplatform[evaluation]`),
`google-genai`, `pandas`, and `requests`. Do **not** create a virtual
environment — it starts empty and hides packages the environment already
provides, forcing a redundant install. Probe, and install only what is missing:

```bash
python3 -c "import vertexai, google.genai, pandas, requests" \
  || pip install 'google-cloud-aiplatform[evaluation]>=1.163.0' 'google-genai>=1.0.0'
```

The version specifiers must stay quoted: unquoted, bash reads `>=1.154.0` as a
redirect and silently writes an empty file instead of constraining the install.

Need `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.

-   **Preserve User Project and Location**: Always prioritize the user's
    explicitly provided project and location (e.g. `project='<PROJECT_NUMBER>'`,
    `location='us-central1'`). Never change or override the user's requested
    location to 'global' unless the user explicitly requested 'global'.
-   **Missing Parameters**: If the user's request omits the project or location,
    you MUST pause in your response and ask the user for the missing
    location/project before preparing or running the evaluation.

### Correct SDK entrypoints

```python
import agentplatform
client = agentplatform.Client(project=PROJECT, location=LOCATION)

client.evals.run_inference(model=..., src=...)
client.evals.evaluate(dataset=..., metrics=...)
client.evals.generate_conversation_scenarios(...)
```

Two imports that look plausible and are not:

-   `from agentplatform.types import evals` -- `ModuleNotFoundError`. `types` is
    a module, not a package; use `from agentplatform import types`.
-   `from vertexai.evaluation import PointwiseMetric, EvalTask` -- the
    superseded SDK. Its classes take different arguments (`PointwiseMetric` has
    no `system_instruction`), so code written against it fails with `TypeError`
    rather than an import error. Use `agentplatform` throughout.
