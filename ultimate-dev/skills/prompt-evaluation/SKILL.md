---
name: prompt-evaluation
description: >
  Evaluate prompt and agent-skill behavior with representative tasks, routing
  expectations, anti-triggers, output rubrics, context budgets, and regression
  reporting. Use before changing routing, agents, skills, adapters, or model
  assignments and when measuring quality or cost.
triggers: [prompt test, skill evaluation, routing regression, golden cases, false activation, agent benchmark, context budget, quality evaluation]
provides: evaluation_report
---

# Prompt and Skill Evaluation

A valid Markdown file is not evidence that a prompt routes or performs well.
Measure behavior against representative tasks and publish the actual result.

## Method

1. **Define the evaluation contract** — task set, expected primary domain,
   acceptable alternatives, forbidden routes, risk class, and output rubric.
2. **Build representative cases** — positives, near-miss negatives, ambiguous
   cases, cross-domain cases, safety cases, and context-loss cases.
3. **Run comparable modes** — prompt-only host, tool-enabled host, and adapter
   mode when relevant; record model and host capabilities.
4. **Score deterministically first** — route, required/forbidden artifacts,
   schema, citations, and safety checks.
5. **Score quality with a rubric** — correctness, relevance, evidence,
   completeness, uncertainty, and actionability; calibrate human judgments.
6. **Measure efficiency** — loaded context, number of skills/agents, latency,
   retries, cost, and unnecessary clarification.
7. **Run the provider-free fixture audit** —
   `python3 scripts/benchmark-prompt-routing.py --strict` validates the case
   contract, deliverable/risk coverage, and negative/near-mix thresholds. It is
   not a model benchmark; use an injected host/model backend for that claim.
8. **Compare and report** — baseline versus candidate, regressions, confidence,
   limitations, and a decision.

## Minimum report

```yaml
suite: <name>
cases: <count>
routing_precision: <value>
false_activation_rate: <value>
forbidden_route_failures: <value>
deliverable_accuracy: <value>
unknown_fallback_rate: <value>
output_score: <value>
context_tokens: <value>
cost: <value>
regressions: [..]
not_run: [..]
recommendation: accept|revise|reject
```

## Boundaries

Never fabricate a benchmark result. A small deterministic suite can support a
structural claim, not a universal quality claim. Keep sensitive fixtures out of
public repositories and obtain approval before testing real external systems.
