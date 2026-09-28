<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the
     'the-quality-flywheel' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## The Quality Flywheel

Five stages, run in order on the first pass, then loop 2 → 5 until quality
targets are met.

### Shortcuts that waste time

| Shortcut                             | Why it fails                         |
| ------------------------------------ | ------------------------------------ |
| "I'll tune the metric threshold down | Hides real failures. Fix the agent,  |
: so it passes."                       : not the bar.                         :
| "This case is flaky, I'll skip it."  | Flakiness reveals non-determinism in |
:                                      : the agent. Fix with `temperature=0`  :
:                                      : or stricter instructions.            :
| "I just need to fix the eval         | If expected outputs keep moving, the |
: dataset, not the agent."             : agent has a behavior problem.        :
| "I can tell from the trace it works  | Self-grading doesn't generalize.     |
: — skip Stage 3."                     : Always run `evaluate()` and read     :
:                                      : scores.                              :
| "One iteration is enough."           | Expect 5–10+ iterations. Stopping    |
:                                      : early leaves regressions on other    :
:                                      : metrics undetected.                  :

### 1. Prepare Data

Produce an `EvaluationDataset`. There are three input shapes, pick the one that
matches the data the user already has:

-   **`EvalCase` list (single-turn or multi-turn):**

    ```python
    from agentplatform import types
    from google.genai import types as genai_types

    # prompt/reference/response values are Content, not str. UserContent and
    # ModelContent wrap a plain string and set the right role.
    dataset = types.EvaluationDataset(eval_cases=[
        types.EvalCase(
            prompt=genai_types.UserContent("What is 2+2?"),
            responses=[types.ResponseCandidate(
                response=genai_types.ModelContent("4"))],
            reference=types.ResponseCandidate(
                response=genai_types.ModelContent("4")),
        ),
        # For multi-turn agent traces, set agent_data instead of prompt/responses.
    ])
    ```

    Multi-turn agent traces wrap each conversation in `AgentData` →
    `ConversationTurn` → `AgentEvent`. See
    [references/dataset_schema.md](references/dataset_schema.md) for the full
    type hierarchy.

-   **Pandas DataFrame (tabular sources — CSV, BigQuery, Sheets):**

    ```python
    import pandas as pd
    from agentplatform import types

    df = pd.DataFrame({
        "prompt":    ["What is 2+2?", "Capital of France?"],
        "response":  ["4",            "Paris"],
        "reference": ["4",            "Paris"],
    })
    dataset = types.EvaluationDataset(eval_dataset_df=df)
    ```

    Column names must match the fields the chosen metrics expect (see
    [references/dataset_schema.md](references/dataset_schema.md) for the
    per-metric requirements table).

-   **Cold start (no data at all):** synthesize scenarios server-side with
    `client.evals.generate_conversation_scenarios(agent=..., config=...)` -- the
    parameter is `agent` or `agent_info`, not `agents`, and `config` is
    required. The config class is `types.evals.UserScenarioGenerationConfig`,
    not `types.UserScenarioGenerationConfig`. Set its `user_scenario_count`
    (1-100): it defaults to None, the client accepts that, and the server
    rejects the call with `400 INVALID_ARGUMENT`. `count` is a separate field
    and does not substitute for it. Stage 2 plays the scenarios out.
    *   **CRITICAL - Underspecified Requests**: When asked to synthesize
        scenarios, if the request omits required parameters (such as `location`,
        `environment_data`, `simulation_instruction`, or `model_name`), do NOT
        assume defaults or guess values. You MUST pause in your first turn and
        explicitly ask the user for the missing information (e.g., "Please
        provide the missing simulation instructions, environment data, model
        name, and location"). Only proceed with the dry-run preview after the
        user provides them.
    *   **Friction & Parameter Changes**: When asked to generate synthetic user
        scenarios, if the user modifies requested parameters (such as scenario
        count, model, or instructions) or pushes back, you MUST present a
        revised dry-run confirmation card with the updated parameters and wait
        for explicit user approval before executing generation code via
        `run_command`. Do NOT generate scenarios directly in plain text.

-   **Managed Agents (Gemini Agents API):** evaluate agents created with the
    [Managed Agents API](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/managed-agents).
    Use `generate_conversation_scenarios` to create test scenarios from the
    agent's configuration, `run_inference` to execute the agent, and `evaluate`
    to score the traces. These functions now accept managed agents and
    interaction ids as input. You can also evaluate existing interactions
    recorded via the Interactions API using `InteractionsDataSource`. See
    [references/sdk_patterns.md](references/sdk_patterns.md) Pattern 8 for the
    full code pattern.

For ADK session dumps, use `scripts/parse_adk_traces.py` instead of writing the
conversion by hand.

### 2. Run Inference

Populate responses/traces on the dataset. **Skip this stage** if traces are
already complete (e.g., production logs or replay).

```python
# Agent eval — pass a callable wrapping the user's ADK Agent/App.
client.evals.run_inference(model=agent_callable, src=dataset)

# Model eval — pass a model ID directly.
client.evals.run_inference(model="gemini-2.5-flash", src=dataset)

# Synthesized scenarios — let the simulator drive.
client.evals.run_inference(
    model=agent_callable,
    src=dataset,
    user_simulator_config=UserSimulatorConfig(max_turn=10),
)

# DataFrame also works as src= — no EvalCase wrapping needed.
client.evals.run_inference(model="gemini-2.5-flash", src=df)

# Managed Agent — pass an agent resource name.
AGENT_RESOURCE = f"projects/{PROJECT_ID}/locations/global/agents/{AGENT_ID}"
client.evals.run_inference(
    agent=AGENT_RESOURCE,
    src=scenarios,
    config={"user_simulator_config": {"max_turn": 3}},
)
```

### 3. Grade (always run)

```python
result = client.evals.evaluate(dataset=dataset, metrics=[...])
result.show()  # Interactive HTML report with scores, rubrics, and traces.
```

**Pick metrics by what you want to measure.** Full catalog in
[references/metric_registry.md](references/metric_registry.md).

**If the user names a metric, use it directly.** Every identifier in the tables
below (`general_quality`, `text_quality`, `instruction_following`,
`hallucination`, `grounding`, `safety`, `multi_turn_*`, `final_response_*`,
`tool_use_quality`) is a `types.RubricMetric.<UPPERCASE_NAME>` accessor — pass
it straight into `metrics=[types.RubricMetric.GENERAL_QUALITY, ...]`. Do not
scaffold a custom `LLMMetric` for a name that appears here, and do not reach for
`vertexai.evaluation.EvalTask` / `PointwiseMetric` /
`MetricPromptTemplateExamples` — that SDK is superseded (see Setup).

**Agent metrics (multi-turn, adaptive rubrics)** — start here for agent eval.

Goal                                          | Metric
--------------------------------------------- | -------------------------------
Did the agent achieve the user's goal?        | `multi_turn_task_success`
Was the reasoning path logical and efficient? | `multi_turn_trajectory_quality`
Tool/function calling quality across turns    | `multi_turn_tool_use_quality`
Overall conversational quality                | `multi_turn_general_quality`
Final response quality (no reference needed)  | `final_response_quality`
Final response vs. a golden reference         | `final_response_match`
Single-turn tool use                          | `tool_use_quality`

**General quality metrics (single-turn, adaptive rubrics)** — for model eval.

Goal                                                  | Metric
----------------------------------------------------- | -----------------------
Overall response quality (recommended starting point) | `general_quality`
Linguistic quality (fluency, coherence, grammar)      | `text_quality`
Adherence to specific constraints / instructions      | `instruction_following`

**Static rubric metrics (fixed criteria)** — apply alongside the above.

Goal                                              | Metric
------------------------------------------------- | ---------------
Catch hallucinated claims (RAG, factual answers)  | `hallucination`
Factuality / consistency against provided context | `grounding`
Safety policy compliance                          | `safety`

**Domain-specific check no built-in covers:** write a custom metric.

-   **Predefined:** `types.RubricMetric.<NAME>` — server-side AutoRater, no
    judge model needed.
-   **Custom LLM-as-a-judge:** `types.LLMMetric` with `prompt_template` or
    `types.MetricPromptBuilder` for structured rubrics. Always set
    `judge_model`; it defaults to `None` and every case then fails with `400
    INVALID_ARGUMENT: Error parsing JSON`.
    *   **Judge Model Selection**: If the user specifies a judge model (e.g.
        `gemini-2.5-pro`), use it. If the user omits the judge model or states
        they do not have information / preference for one, default to
        `gemini-2.5-flash` as the judge model in the dry-run preview card and
        ask for confirmation to run the evaluation. Do NOT halt or refuse to
        evaluate when the user does not specify a judge model.
-   **Custom code:** `types.CodeExecutionMetric` with a `custom_function` string
    containing `def evaluate(instance: dict)` for remote sandboxed execution; or
    `types.Metric` with `custom_function=<callable>` for local execution.

**Always persist the result** so Stage 4 and 5 can read it. Save both JSON
(machine-readable, diffable) and HTML (human-readable, linkable):

```python
import datetime
from pathlib import Path

from agentplatform._genai import _evals_visualization

out_dir = Path("artifacts/grade_results")
out_dir.mkdir(parents=True, exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# fallback=str, or a DataFrame-backed dataset raises PydanticSerializationError.
result_json = result.model_dump_json(fallback=str)
(out_dir / f"results_{ts}.json").write_text(result_json)

html = _evals_visualization.get_evaluation_html(result_json)
(out_dir / f"results_{ts}.html").write_text(str(html))
```

Or after the fact: `scripts/render_html_report.py --type evaluation` or
`scripts/inspect_results.py --save-html`.

### 4. Analyze Failures

Read `summary_metrics` and `eval_case_results` — never fabricate scores. Use
`scripts/inspect_results.py --failing-only` to filter to failures.

For each failed metric, see
[references/failure_patterns.md](references/failure_patterns.md) for deeper
diagnoses. The compact mapping:

| Failing metric                      | What to change                         |
| ----------------------------------- | -------------------------------------- |
| `multi_turn_task_success` low       | The agent isn't completing the goal —  |
:                                     : fix orchestration, missing tool calls, :
:                                     : premature termination, wrong tool      :
:                                     : selection.                             :
| `multi_turn_trajectory_quality` low | The agent reaches the goal             |
:                                     : inefficiently — refine planning        :
:                                     : prompts, remove redundant tool calls.  :
| `multi_turn_tool_use_quality` low   | Fix tool descriptions, parameter       |
:                                     : docstrings, or agent instructions for  :
:                                     : tool selection.                        :
| `final_response_quality` low        | Read auto-generated rubric verdicts;   |
:                                     : refine instructions to address the     :
:                                     : worst-scoring criterion.               :
| `final_response_match` low          | The agent's final answer doesn't match |
:                                     : the golden reference — adjust response :
:                                     : format or update the reference.        :
| `hallucination` low                 | Tighten instructions to stay grounded  |
:                                     : in tool output; verify the tool        :
:                                     : actually returned the claimed data.    :
| `grounding` low                     | The response contradicts the provided  |
:                                     : context — add explicit "cite only from :
:                                     : context" instructions.                 :
| `safety` low                        | Add safety guardrails; review the      |
:                                     : violating content category in the      :
:                                     : rubric verdict.                        :
| `general_quality` / `text_quality`  | Adjust system instruction wording; the |
: low                                 : model's default phrasing is too        :
:                                     : generic for the task.                  :
| `instruction_following` low         | The agent is ignoring constraints —    |
:                                     : restate them in the system instruction :
:                                     : or use stricter wording.               :
| Agent calls wrong tools             | Fix tool descriptions, agent           |
:                                     : instructions, or `tool_config`.        :
| Agent calls extra tools             | Add explicit stop instructions, or     |
:                                     : switch to                              :
:                                     : `multi_turn_tool_use_quality` to       :
:                                     : surface the extra calls in the rubric. :

**For 10+ failures on the same metric**, use the **Error Analysis service** to
cluster failures into themes (L1/L2 taxonomy categories) instead of reading
every trace:

```python
# Only supports multi_turn_task_success and multi_turn_tool_use_quality.
# Service runs in the global region.
analysis_client = agentplatform.Client(project="PROJECT_ID", location="global")
response = analysis_client.evals.generate_loss_clusters(
    eval_result=result,
    metric="multi_turn_task_success",
    config={"max_top_cluster_count": 5},
)
for r in response.results:
    for cluster in r.clusters:
        print(
            f"[{cluster.taxonomy_entry.l1_category}/"
            f"{cluster.taxonomy_entry.l2_category}] "
            f"{cluster.item_count} cases — {cluster.taxonomy_entry.description}"
        )
```

Save `response.model_dump_json()` and render with `scripts/render_html_report.py
--type loss-analysis`.

### 5. Optimize & Iterate

Apply a fix targeting the failing metric. Re-run Stage 3. Compare with
`scripts/compare_results.py --baseline <prev> --candidate <new>` to confirm the
target improved AND no other metric regressed.

Track progress across iterations:

Iteration | Metric A | Metric B | Change made
--------- | -------- | -------- | ----------------------
Baseline  | 0.62     | 0.55     | —
v2        | 0.78     | 0.68     | Added grounding prompt
v3        | 0.81     | 0.72     | Fixed tool selection

Expect 5–10+ iterations per failing case. Only after a case passes should you
expand coverage with more eval cases.
