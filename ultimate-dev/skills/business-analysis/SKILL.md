---
name: business-analysis
description: >
  Analyze a business problem, operating process, strategy, market, KPI, or
  decision using explicit evidence, assumptions, alternatives, and measurable
  outcomes. Use for company operations, product strategy, process improvement,
  competitive questions, and executive decision support.
triggers: [business analysis, strategy, operating model, process analysis, KPI, market analysis, decision support, business case]
provides: business_recommendation
---

# Business Analysis

Turn a business question into a decision-ready analysis without pretending
that missing data is known.

## Method

1. **Frame the decision** — what choice must be made, by whom, by when, and what
   happens if no decision is made.
2. **Map the current state** — stakeholders, process, constraints, dependencies,
   costs, risks, and existing measures.
3. **Define the desired outcome** — value, customer or employee impact, and
   measurable success criteria.
4. **Generate alternatives** — at least two viable options when a choice exists;
   include the do-nothing baseline.
5. **Make assumptions explicit** — mark each as sourced, estimated, or unknown;
   show sensitivity where the result changes.
6. **Recommend** — state the preferred option, rationale, trade-offs, risks,
   dependencies, and a reversible next step.
7. **Define measurement** — owner, baseline, target or decision rule, data
   source, review date, and stop/continue conditions.

## Output contract

```yaml
decision: <question>
current_state: [..]
desired_outcome: <..>
options:
  - option: <..>
    value: [..]
    cost: [..]
    risks: [..]
assumptions: [{claim: .., status: sourced|estimated|unknown, impact: ..}]
recommendation: <..>
metrics: [..]
next_step: <..>
```

## Boundaries

Do not fabricate market sizes, financial values, legal conclusions, or customer
findings. Keep regulated, financial, employment, and policy decisions subject
to qualified human review.
