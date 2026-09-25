# Learning Record Template

Load this reference before authoring a learning candidate. Use it only after a
bounded task has produced evidence. Keep the source task generalized and remove
secrets, private URLs, client identifiers, and private reasoning.

```yaml
---
name: domain-capability-learned
description: >
  Evidence-backed method for <capability>. Use when <specific conditions>.
triggers: [<compound signals>]
anti_triggers: [<near misses>]
provides: <stable capability name>
status: candidate
confidence: low|medium|high
source_task: <redacted reference>
evidence_count: 0
---
```

Record:

- the deliverable and acceptance criteria;
- inputs and required host capabilities;
- official/reference sources and freshness;
- repeatable steps and decision points;
- outputs, evidence, and verification commands;
- failure modes, anti-patterns, and rollback;
- unresolved questions and confidence rationale.

Never mark a candidate `approved` from a single task. A reviewer must link it to
positive and negative evaluation cases before promotion.
