# Ultimate-Dev Portable Contracts

These contracts make the prompt-first core usable across hosts without requiring
Python, a runtime service, a model provider, or a particular tool protocol.

## Files

- `task-envelope.yaml` — canonical task, deliverable, risk, uncertainty, and
  capability-gap vocabulary.
- `four-channels.md` — the portable Intent → Knowledge → Action → Evidence
  contract and its prompt-only profile.

The contracts are semantic. A host may serialize them as YAML, JSON, Markdown,
or host-native messages, but it must preserve the field meanings and must not
invent unavailable capabilities. The four information channels
(Intent/Knowledge/Action/Evidence) are not the legacy message payload variants
(`task`, `result`, `question`, and `error`); those are transport shapes, not
routing stages.

## Design rules

1. Classify the deliverable before selecting a specialist.
2. Keep domain selection separate from deliverable selection.
3. Treat `unknown` as a valid classification, not a failure.
4. Report missing capabilities and limitations explicitly.
5. Keep action and authorization separate from model intent.
6. Record evidence for the result; never turn a plan into a claimed outcome.
7. Use JEV only when the host supplies the facts needed by its host/runtime
   profile. The prompt-only profile remains sufficient for advice and analysis.
