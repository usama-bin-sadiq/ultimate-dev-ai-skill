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

The fixture audit also checks whether `expected_domains` uses IDs from the
current `config/capability-index.yaml`. Legacy labels are reported as a warning
rather than silently treated as current routing vocabulary. The reviewable,
comparison-only policy in `domain-aliases.yaml` separates safe umbrella aliases
from ambiguous labels; ambiguous cases are not domain-scored until reviewed.
Migrate or explicitly approve those labels before using domain accuracy as a
model-quality metric. The current suite has no ambiguous domain cases remaining;
the quarantine mechanism remains for future fixtures.

For a recorded host-session replay, export the hidden sample and predictions as
JSON, then run:

```bash
python3 scripts/compare-routing-predictions.py \
  --gold evidence/behavioral-gold.json \
  --predictions evidence/behavioral-predictions.json \
  --strict --json
```

The comparison is dependency-free, accepts structured capability-gap objects,
normalizes only reviewed safe aliases, and leaves ambiguous domain cases
unscored. It is not an independent model benchmark.

A model/host benchmark must inject its classifier, agent, verifier, backend
description, model capabilities, and provenance. Do not turn fixture-audit
metrics into a claim about model accuracy, latency, cost, or tool safety.
