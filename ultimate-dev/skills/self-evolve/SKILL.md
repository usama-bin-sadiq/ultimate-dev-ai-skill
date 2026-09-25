---
name: self-evolve
description: >
  Safe learning workflow for a genuinely missing or repeatedly weak capability.
  Research the unfamiliar domain, complete a bounded task, record reusable
  evidence, and promote a new skill only after review and regression cases.
triggers: [capability gap, repeated workflow gap, missing reusable method, learn a new capability, evolve a skill]
provides: self_evolution_pattern
---

# Self-Evolution — Evidence-Gated Learning

Use this skill when the capability index and common skills cannot safely handle a
recurring task. A one-off unknown task is a reason to research and report, not a
reason to create permanent prompt content.

## Safe lifecycle

1. **Detect** — record the missing capability, deliverable, risk, and evidence.
2. **Classify** — use `universal-task` to bound the work and identify unknowns.
3. **Research** — prefer authoritative documentation; record source quality,
   date, and unresolved questions. If research capability is unavailable, say so.
4. **Execute** — complete the smallest safe portion through host capabilities.
5. **Verify** — run independent checks and record actual `pass`, `fail`, or
   `not_run` results.
6. **Extract** — write patterns, pitfalls, inputs, outputs, and applicability
   boundaries to a candidate record.
7. **Review** — require repeated independent evidence, a reviewer, regression
   cases, provenance, confidence, and a rollback path before promotion.

## Promotion gate

Keep a candidate outside the canonical package until all of these are true:

- at least three successful uses across meaningfully different tasks;
- no unresolved security, privacy, safety, or authority boundary;
- a concise skill contract with triggers, anti-triggers, output, and verification;
- positive and negative evaluation cases;
- independent review and an owner for future maintenance.

With durable runtime, stage and evaluate candidates under the project's
`.memory/ultimate-dev/evolution/` area and issue a memory receipt. In a
prompt-only host, return a candidate handoff; do not write package files. An
explicit package-maintainer request may register a reviewed artifact later.

A failed or ambiguous use lowers confidence or returns the candidate to research.
Never promote from one successful task, and never hide a failed approach.

## When not to use

Do not use self-evolution for a one-off question, a normal unknown-domain task,
a provider/tool error, a missing approval, or a task already covered by a
common skill. Use the capability-gap report and human review instead.

## Progressive references

Load no reference for a one-off unknown task. Load
`references/learning-record-template.md` before authoring a candidate, and
`references/promotion-gates.md` before review or promotion. The references are
instructions for durable learning maintenance, not automatic package writes.

## Output contract

```yaml
learning_candidate:
  name: <stable-kebab-case>
  domain: <domain-or-unknown>
  deliverable: <type>
  source_task: <redacted-reference>
  patterns: []
  pitfalls: []
  evidence: []
  confidence: low|medium|high
  promotion_status: candidate|review|approved|rejected|retired
  next_evidence_needed: []
```

Store detailed templates and promotion evidence in
`references/learning-record-template.md` and
`references/promotion-gates.md`. Do not persist secrets, private reasoning, or
client-identifying detail in reusable content.
