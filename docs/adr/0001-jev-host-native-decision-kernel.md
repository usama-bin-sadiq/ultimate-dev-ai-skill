# ADR-0001: JEV as a Host-Native Decision Kernel

## Status

Accepted — 2026-09-24

## Context

Ultimate-Dev already separates model intelligence, orchestration patterns, the durable runtime, and host capabilities. The new JEV design adds three decision heads and deterministic policy aggregation, but the current Python implementation is large, directly coupled to the durable runtime, untested at the decision boundary, and contains broken classifier, guardrail, aggregation, and tool-slimming behavior.

The product requirement is model portability and host portability. JEV therefore cannot require Python, a container engine, a browser automation package, an external decision service, or a package manager.

## Decision

JEV is a **side-effect-free decision kernel inside the Ultimate-Dev runtime boundary**.

```text
MODEL / ORCHESTRATION
    │ model assessment + capability proposal
    ▼
JEV DECISION KERNEL
    │ validate → aggregate → guard → route → slim
    ▼
DECISION PACKET
    │
    ▼
ULTIMATE-DEV RUNTIME ── persisted state/evidence ──► HOST CAPABILITIES
```

The kernel:

- receives typed model assessment, orchestration state, host capability descriptors, policy, and scoped approvals;
- evaluates NOUL, CHOICE, and SCORE heads;
- aggregates with hard safety floors rather than probability averaging;
- returns `approve`, `human_review`, or `deny`;
- returns a versioned decision packet with an allowlist of canonical capability IDs;
- never invokes a model or tool and never installs, discovers, or substitutes a provider.

Canonical contracts are JSON Schema. A dependency-free ECMAScript module is a reference implementation for hosts that already have a JavaScript runtime. Other hosts may implement the same contract natively; the protocol is not tied to one language.

## Safety Boundary

The model proposes. The host supplies facts and policy. JEV combines them deterministically. The runtime still enforces the final action policy.

A JEV decision cannot grant a capability that the host did not advertise. Tool slimming is intersection-only:

```text
selected = requested ∩ host_available ∩ policy_allowed
```

Missing required capabilities are reported as unavailable. The kernel does not install Docker, Playwright, a browser, a shell, or any other dependency.

Unisolated code execution is not advertised as a secure sandbox. If the host cannot provide an approved execution boundary, JEV returns no executable capability for that operation and the runtime reports a blocker or requests review.

## Alternatives Considered

1. **Repair the Python JEV modules** — rejected because they are already unsafe, oversized, untested at the decision boundary, and coupled to the legacy runtime.
2. **Deploy JEV as a microservice** — rejected because it adds network availability, serialization, security, and operational dependencies without improving the decision algorithm.
3. **Put all decisions in the model prompt** — rejected because guardrails and tie-breaking must be deterministic and auditable.
4. **Bundle sandbox and browser stacks** — rejected because the host already owns tools and policy; bundling providers duplicates capabilities and creates installation/security risk.
5. **Host-neutral contract plus a dependency-free reference engine** — selected because it preserves deterministic behavior while allowing each host to use native tools.

## Consequences

### Positive

- One decision contract works across models and agent hosts.
- No package installation or external service is required for JEV.
- Decisions are deterministic, versioned, testable, and explainable.
- Runtime state remains authoritative and independent of JEV.
- Capability schemas can be pruned before reaching the executor.

### Negative

- Existing Python JEV callers are not source-compatible.
- Each host adapter must map canonical capability IDs and enforce policy.
- The reference engine and contracts must be kept in sync.

### Risks and Mitigations

- **A host bypasses JEV** — mitigate by making `assess()` mandatory in the runtime adapter contract and rejecting unassessed privileged actions.
- **Model scores are treated as probabilities** — mitigate by naming them confidence/support and recording reasons.
- **A capability name leaks provider details** — mitigate with canonical IDs and host-side mapping.
- **Legacy code remains in the repository** — mark it legacy/adjacent and exclude it from the canonical JEV path; migrate it separately rather than silently expanding this change.

## Migration Rule

The replacement is a deliberate JEV subsystem migration, not a repository-wide language rewrite. Tracked Python JEV code is retired from the canonical path. Unrelated Python runtime and maintenance tooling remain optional/legacy until separately reviewed. Pre-existing untracked files are preserved.
