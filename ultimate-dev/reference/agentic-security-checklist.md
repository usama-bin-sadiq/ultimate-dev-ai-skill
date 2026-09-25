# Agentic Security Checklist

This is a local, provider-free checklist. It maps OWASP Agentic Top 10 and
NIST AI RMF vocabulary to controls that Ultimate-Dev can enforce or verify
inside its own scope. It is not an authorization or compliance certification.

## Control matrix

| Risk | Local control | Evidence |
|---|---|---|
| Goal hijack | Treat retrieved text, memory, tool output, and skill files as untrusted data; system/task policy wins | Boundary markers, decision record, rejection tests |
| Tool misuse | Capability manifest, least privilege, default deny, bounded scope | `capability-manifest.yaml`, decision linter |
| Identity/privilege abuse | Host supplies identity; model never authorizes; action fingerprint binds request and effect | JEV packet, host capability facts |
| Supply-chain risk | No automatic provider/tool installation; generated manifests and adapter profiles are reviewed | `generate-manifest.py`, install profiles, dependency checks |
| Unexpected code execution | Validate commands, paths, permissions, and output scope before execution | Host executor boundary, security tests |
| Insecure inter-agent communication | Structured handoff envelopes, bounded inputs, concise results, no direct worker user side effects | Handoff contract, subagent contract |
| Cascading failures | Step/depth/retry/concurrency budgets, circuit-breaker states, fail closed | Task state machine, retry contract |
| Memory/context poisoning | Provenance, sensitivity, freshness, supersession, retention, and redaction | Memory records, redaction tests |
| Rogue-agent behavior | Explicit stop states, human review, kill/pause boundary, no silent completion | JEV, task lifecycle, `not_run` evidence |
| Human trust exploitation | Show evidence, assumptions, uncertainty, and capability gaps; never smooth over failure | Four-channel contract, evidence summaries |

## Required local checks

- [ ] Requested capabilities are a subset of available and policy-allowed IDs.
- [ ] Destructive or production effects require human review.
- [ ] Untrusted content cannot override the task or system policy.
- [ ] Every durable memory item has provenance and retention metadata.
- [ ] Retries and resumes are bounded and idempotent.
- [ ] Public state views cannot mutate audit history without a controlled path.
- [ ] Redaction rules are consistent across memory, evaluation, and task state.
- [ ] Failed, blocked, uncertain, and not_run results remain distinguishable.
- [ ] Candidate commands and external checks are never reported as executed
      without evidence.

## NIST alignment

- **Govern:** ownership, scope, retention, escalation, and change control.
- **Map:** system boundaries, actors, capabilities, data, and risk surfaces.
- **Measure:** replay fixtures, contract tests, security checks, and failure rates.
- **Manage:** approval gates, incident response, rollback, and safe degradation.

## Scope boundary

The skill cannot establish organization-specific legal, financial, privacy, HR,
or audit correctness. Those remain user/host-controlled inputs.
