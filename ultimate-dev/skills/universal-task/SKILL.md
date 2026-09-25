---
name: universal-task
description: >
  Universal fallback for unfamiliar, unclassified, cross-domain, or capability-
  constrained tasks. Classifies the requested deliverable, captures a portable
  task envelope, researches only what is needed, completes a bounded result,
  and reports assumptions, confidence, limitations, and capability gaps.
triggers: [unknown task, unclassified task, unfamiliar domain, novel capability, no matching skill, capability gap, arbitrary deliverable]
provides: universal_task_fallback
---

# Universal Task — Safe Fallback for Any Deliverable

Use this skill when the exact department or specialist is not known, the task
combines unfamiliar domains, or the host lacks a required capability. It is a
fallback, not a replacement for an exact match.

## Route priority

1. Apply the universal task envelope.
2. Use an exact capability when one exists.
3. Use a common skill for a single-domain deliverable.
4. Use one primary specialist per material domain only when needed.
5. Use this skill for the unknown/unclassified remainder.
6. Escalate material legal, financial, security, privacy, safety, or employment
   decisions to a qualified human reviewer.

## Task envelope

Read `../../contracts/task-envelope.yaml`. Capture:

- `intent`, `deliverable`, `size`, `domains`, `risk`, and `clarity`;
- inputs, constraints, assumptions, unknowns, and acceptance criteria;
- requested versus available capabilities;
- required evidence and output contract;
- `confidence`, human-review needs, and capability gap.

Empty or unknown values must remain explicit. Do not invent data, sources,
permissions, tools, or company policy.

## Unknown-domain method

1. Restate the bounded goal and identify the requested deliverable.
2. Separate facts, assumptions, and decisions.
3. Ask one focused question when a missing answer changes the result materially.
4. Prefer official or primary sources when research is available; record source
   limits and freshness.
5. Decompose the work into small verifiable steps and execute the safe portion.
6. Check the result against the envelope's acceptance and evidence fields.
7. Return a capability-gap report with missing capability IDs, impact, safe
   workaround, and escalation need.

## Output contract

```yaml
classification:
  deliverable: <type>
  domains: []
  risk: none|data|security|compliance
  confidence: low|medium|high
  confidence_reason: null
result:
  status: completed|partial|failed|blocked|not_run
  summary: <bounded result>
evidence:
  checks: []
  sources: []
  artifacts: []
assumptions: []
unknowns: []
limitations: []
capability_gap:
  level: none|partial|blocking
  missing: []
  reason: null
  workaround: null
  escalation: null
next_actions: []
```

Use `not_run` honestly. Do not claim an external action, provider call, or
specialist execution that the host did not actually perform. A single unknown
task is evidence for a future evaluation, not permission to auto-generate a
permanent skill. Use `self-evolve` only after repeated evidence and review.

## Boundaries

This skill does not replace legal, tax, financial, medical, security, or
employment advice. It does not install providers, bypass approvals, or make a
human decision. Load the selected domain skill/reference after the envelope is
understood; do not load the full registry. If an organization supplies an
optional company context pack, use its scoped links and freshness metadata;
never invent missing company policy.
