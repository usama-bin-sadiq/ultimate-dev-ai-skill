# Grounding Rules (compact)

## Grounding Sources (in order)
1. Code in repo
2. Loaded module principles
3. Sourced lookup per protocol

## Steps
1. **Identify claim type**:
   - Named library → official docs first
   - Broad concept → web search, authoritative sources
   - No tools → disclose as unverified

2. **Execute lookup**:
   - WebSearch/WebFetch if available
   - Named: official docs, npm/pypi/cargo, GitHub README
   - Frameworks: official guides

3. **Record note**: source URL + claim verified

4. **Persist**: recurring lookups → module tooling-notes

## Anti-Rules
- Never fabricate sources
- Never use blogs/forums over official docs
- Never present training-cutoff as current

## Compact Output
```
[ grounded: yes|no | source: <url> | claim: <what> ]
```

## Evidence Grade (runtime plane)


Grounding answers *is this true*. The evidence grade answers *did this happen*.
Both are required; neither substitutes for the other.

Run the detection recipe in `AGENTS.md` §0 once per session, then:

| Detection | Grade | May authorize completion? |
|---|---|---|
| `RUNTIME_AVAILABLE` | `TOOL_ATTESTED` | Yes, for observed side effects |
| `PROMPT_ONLY` | `SELF_REPORTED` | **No** for any side effect |

```text
CLAIMED CHANGE ≠ OBSERVED CHANGE
KNOWLEDGE     ≠ EVIDENCE
```

`runtime/core/attestation.py` enforces this when the runtime is present: it
stamps every side-effecting execution with an observation derived from the
executor's actual return, and overwrites any caller-supplied `observation`.

## Anti-Rules
- Never report a side effect as `pass` on a `SELF_REPORTED` grade
- Never write `attested_by: runtime` yourself — only the runtime may attest
- Never infer a side effect happened because the code looks correct
- On `PROMPT_ONLY`, name the check a human can run instead
- Never assume a capability exists. Run `scripts/capability-probe.py` first:
  the prompt core issues shell commands unconditionally, and a host without a
  shell must degrade to `not_run`, not to an error
- Never call a tool that is not in the host's tool list. If a command needs a
  capability you do not have, say which one is missing