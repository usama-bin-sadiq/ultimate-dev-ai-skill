# Prompt Evaluation Fixtures

`golden-cases.yaml` is the provider-free routing fixture. It is not a model
benchmark and does not prove answer quality.

## Run the fixture audit

```bash
python3 scripts/benchmark-prompt-routing.py --strict
python3 scripts/benchmark-prompt-routing.py --json
```

Without `--classifier`, the runner validates case structure, deliverable/risk
vocabulary, unknown cases, forbidden-route declarations, case count, and the
negative/near-miss threshold. It reports `fixture_audit_pass` with
`scored: false`; it never calls a model or external service.

## Case fields

Required legacy fields:

```yaml
id: stable-unique-id
task: bounded request
expected_size: atomic|moderate|complex
expected_domains: []
expected_risk: none|data|security|compliance
```

New cases should also include:

```yaml
category: positive|negative|near-miss|unknown|multilingual
expected_deliverable: <taxonomy key>
expected_forbidden_domains: []
expected_capability_gap: partial # required for unknown cases
```

`ambiguous` remains accepted only as a compatibility fixture alias. Every
ambiguous fixture now also declares `expected_clarity: blocked`; new requests
should use a normal size plus `clarity: blocked` in the task envelope. A
classifier used with the optional local replay mode must report
`activated_forbidden_domains` so forbidden routes can be checked independently.

## Evidence boundary

A model/host benchmark must inject its classifier, agent, verifier, backend
description, model capabilities, and provenance. Do not turn fixture-audit
metrics into a claim about model accuracy, latency, cost, or tool safety.
