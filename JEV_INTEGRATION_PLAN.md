# JEV Host-Native Integration Plan

## Goal

Add JEV System One as a deterministic decision kernel inside Ultimate-Dev
without requiring Python, Docker, Playwright, a package manager, a model
provider, or an external service.

JEV is not a new intelligence layer. The model still owns intent, planning,
and strategic decisions. JEV evaluates structured facts and returns an
explainable packet; the Runtime owns persistence, confirmation, execution,
verification, and recovery.

## Architecture

```text
MODEL / ORCHESTRATION
    │ assessment + capability proposal
    ▼
JEV DECISION KERNEL
    │ NOUL + CHOICE + SCORE → aggregate → guard → recommend
    ▼
DECISION PACKET
    │
    ▼
ULTIMATE-DEV RUNTIME
    │ persist → confirm → execute → observe → verify → recover
    ▼
HOST-NATIVE CAPABILITIES
```

## Completed in this migration

- [x] Replace the unsafe Python JEV behavior with a versioned JSON contract.
- [x] Add a dependency-free reference engine using ECMAScript built-ins only.
- [x] Keep model intelligence, orchestration, runtime state, and capabilities
      in their original ownership layers.
- [x] Add deterministic guardrail precedence: `deny > human_review > approve`.
- [x] Make human review and missing capabilities execution-blocking.
- [x] Make capability selection intersection-only and budget-aware.
- [x] Remove JEV imports from the Python SessionManager/Runtime path.
- [x] Add a host-executor seam to the legacy Python Runtime.
- [x] Add direct JEV behavior and contract tests.
- [x] Update architecture, protocol, adapter, and runtime documentation.

## Contract artifacts

- `ultimate-dev/runtime/schemas/jev-decision-request.schema.json`
- `ultimate-dev/runtime/schemas/jev-decision-packet.schema.json`
- `ultimate-dev/runtime/jev-policy.json`
- `ultimate-dev/runtime/jev/engine.mjs`
- `ultimate-dev/runtime/jev/README.md`
- `ultimate-dev/tests/jev/engine.test.mjs`

## Runtime seam

1. The host discovers native capabilities and builds host facts.
2. The model returns an assessment and capability proposal.
3. The host evaluates the JEV contract using the reference engine or a native
   implementation.
4. The Runtime persists the decision packet.
5. Only an `approve` packet with `execution_effect: execute` may reach the
   mapped host capability.
6. Review/stop packets remain blocked until a new trusted decision is made.

## Explicitly out of scope

- Bundled Docker, Podman, Firecracker, gVisor, or local subprocess fallback.
- Bundled Playwright, Puppeteer, Selenium, or browser installation.
- Provider-specific model adapters inside JEV.
- Automatic dependency installation.
- Replacing the existing skills, agents, router, workflows, or modules.
- A repository-wide rewrite of unrelated legacy Python maintenance tooling.

## Verification

```bash
node --test ultimate-dev/tests/jev/engine.test.mjs
node -e "for (const f of process.argv.slice(1)) JSON.parse(require('fs').readFileSync(f, 'utf8'))" \
  ultimate-dev/runtime/schemas/jev-decision-request.schema.json \
  ultimate-dev/runtime/schemas/jev-decision-packet.schema.json \
  ultimate-dev/runtime/jev-policy.json
```

The full legacy suite may be run separately when its existing Python test
dependencies are already available. It is not a prerequisite for the JEV
contract or for host operation.

## Migration rule

The old `ultimate-dev/runtime/core/jev/` Python package remains isolated for
one compatibility window, but it is not a safe behavioral baseline and must not
be imported by new code. Pre-existing untracked files are preserved for
separate review.
