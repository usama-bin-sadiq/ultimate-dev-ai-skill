<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# SDK Quick Reference

```python
import agentplatform
from agentplatform import types
from google.genai import types as genai_types
import pandas as pd

# Initialize client
client = agentplatform.Client(project="PROJECT_ID", location="LOCATION")

# --- SINGLE-TURN EVAL (pandas DataFrame) -- RECOMMENDED ---
# The converter wraps plain strings for you.
df = pd.DataFrame({
    "prompt":   ["Q1", "Q2"],
    "response": ["A1", "A2"],
})
dataset = types.EvaluationDataset(eval_dataset_df=df)

# --- SINGLE-TURN EVAL (direct EvalCase) ---
# Verbose and easy to get wrong; see references/dataset_schema.md for the
# exact types before using this form.
dataset = types.EvaluationDataset(eval_cases=[
    types.EvalCase(
        prompt=genai_types.UserContent("Query here"),
        responses=[types.ResponseCandidate(
            response=genai_types.ModelContent("Model response here"))],
        reference=types.ResponseCandidate(
            response=genai_types.ModelContent("Ground truth here")),
    ),
])

# --- MULTI-TURN AGENT EVAL ---
agent_data = types.evals.AgentData(
    agents={"my_agent": types.evals.AgentConfig(
        agent_id="my_agent", instruction="You are helpful.")},
    turns=[types.evals.ConversationTurn(turn_index=0, events=[
        types.evals.AgentEvent(author="user",
            content=genai_types.Content(role="user",
                parts=[genai_types.Part(text="Hello")])),
        types.evals.AgentEvent(author="my_agent",
            content=genai_types.Content(role="model",
                parts=[genai_types.Part(text="Hi! How can I help?")])),
    ])],
)
dataset = types.EvaluationDataset(
    eval_cases=[types.EvalCase(agent_data=agent_data)])

# --- METRICS ---
predefined = types.RubricMetric.MULTI_TURN_TRAJECTORY_QUALITY
custom_llm = types.LLMMetric(name="tone",
    prompt_template="Is this polite? Response: {response}")
custom_code = types.CodeExecutionMetric(name="check",
    custom_function='def evaluate(instance): return {"score": 1.0}')

# --- EVALUATE ---
result = client.evals.evaluate(dataset=dataset, metrics=[predefined])

# --- RESULTS ---
for s in result.summary_metrics:
    print(f"{s.metric_name}: mean={s.mean_score}, pass_rate={s.pass_rate}")
for case in result.eval_case_results:
    for cand in case.response_candidate_results:
        for name, r in cand.metric_results.items():
            print(f"  {name}: score={r.score}, explanation={r.explanation}")
```

See [references/sdk_patterns.md](./sdk_patterns.md) for advanced
patterns: synthetic data generation, pairwise comparison, `MetricPromptBuilder`,
multi-agent evaluation.
