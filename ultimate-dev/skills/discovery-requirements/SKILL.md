---
name: discovery-requirements
description: >
  Clarify product, engineering, research, and business requests into a grounded
  requirements contract with users, scope, acceptance criteria, assumptions,
  risks, and evidence. Use when a request is ambiguous, a PRD or user story is
  needed, or implementation should not start before purpose and success are clear.
triggers: [requirements, discovery, PRD, user story, acceptance criteria, scope, product brief, clarification]
provides: requirements_contract
---

# Discovery and Requirements

Turn an ambiguous request into a contract another person can evaluate and an
agent can execute safely.

## Method

1. **Capture the intended outcome** — who benefits, what changes, and why now.
2. **Inspect available evidence** — repository, product context, prior decisions,
   data, and user-provided constraints. Separate facts from assumptions.
3. **Define scope** — in, out, dependencies, constraints, deadlines, and risks.
4. **Make success testable** — write observable acceptance criteria, examples,
   failure cases, and required evidence.
5. **Resolve only material ambiguity** — ask one focused question when a missing
   decision changes the design or risk; otherwise state a safe assumption.
6. **Freeze a contract** — record the outcome, non-goals, decisions, open
   questions, and approval owner before implementation.

## Output contract

```yaml
outcome: <one sentence>
users: [primary users/stakeholders]
in_scope: [..]
out_of_scope: [..]
constraints: [..]
assumptions: [..]
acceptance_criteria: [testable statements]
required_evidence: [..]
risks: [..]
open_questions: [..]
```

## Boundaries

- Do not invent user needs, market facts, legal requirements, or numeric targets.
- Do not turn a request for analysis into implementation without agreement.
- Keep the contract small; load detailed domain references only after approval.
- For regulated, financial, privacy, or safety decisions, identify the human
  reviewer and the evidence required before proceeding.
