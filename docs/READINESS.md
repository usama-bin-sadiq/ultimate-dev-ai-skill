# Ultimate-Dev 10/10 Readiness Rubric

Ultimate-Dev is an all-in-one agentic CLI and software-engineering skill suite.
This rubric defines what “10/10” means for that product category. It does not
claim that the repository is an operating system or that external providers are
available in every environment.

## Scoring rule

Each dimension is scored from 0–10:

- **0–3:** missing or misleading foundation
- **4–6:** usable prototype with material gaps
- **7–8:** strong bounded implementation
- **9:** production-grade for the stated local/host scope
- **10:** production-grade, independently verified, observable, and documented
  for the stated deployment scope

A 10/10 overall product requires every locally controllable dimension to meet
its gate. External deployment controls must be marked `external`, not silently
counted as complete.

## Readiness dimensions

| Dimension | 10/10 gate |
|---|---|
| CLI and install UX | Interactive tool/generic → Global/Project flow; explicit automation flags; idempotent copy-only install; no symlink or surprise files. |
| Manifest consistency | Canonical VERSION, SKILL metadata, config versions, manifest paths/counts, agents, skills, modules, and adapters are machine-validated. |
| Skill quality | Every skill has valid metadata, clear triggers/provides, version/freshness policy, and a defined independent verification path. |
| Agent quality | Every agent has validated frontmatter, trigger/anti-trigger coverage, tools, model policy, freshness, and benchmark/quality evidence. |
| Routing | Ambiguous routes fail closed; selection is deterministic, persisted, bounded, and measured against routing fixtures. |
| Runtime durability | State transitions, idempotency, fencing, checkpoints, recovery, retention, and audit integrity survive restart and repeated execution. |
| Authorization | JEV/action/effect/approval/contract checks are fail-closed and covered by adversarial tests. |
| Host boundary | Capability availability, execution, failure, and reconciliation contracts are explicit for every supported adapter. |
| Data protection | Secrets are redacted/refused, memory retention is explicit, and deployment encryption/DLP requirements are documented as external controls. |
| Verification | Unit, contract, integration, security, installation, and host-native checks run in CI with real evidence. |
| Release supply chain | Versioned artifacts, generated files, release provenance/SBOM policy, protected environments, and rollback instructions are verified. |
| Observability | Health, audit, metrics, alerts, and incident ownership exist for local and hosted deployments. |
| Performance | Latency, throughput, concurrency, resource bounds, and failure-injection budgets are measured. |
| Documentation | Installation, adapters, trust boundaries, limitations, and recovery instructions match executable behavior. |

## Current local gates

The following are enforced by repository checks:

- Version and metadata consistency.
- Agent/skill frontmatter and freshness validation.
- Manifest path/count validation.
- JEV contract and decision tests.
- Runtime authorization, fencing, idempotency, evidence, and recovery tests.
- POSIX/PowerShell installer tests, including tool-specific targets and memory preservation.
- Structure, host-native, workflow-security, sync, compilation, and diff checks.
- Staged install cache exclusion and payload-size reporting.
- 154 provider-free routing fixtures with unknown and forbidden-route cases;
- capability-index vocabulary drift is reported rather than hidden in fixture metrics.
- Development dependency manifest and reproducible setup guide.
- Optional company-context template validation and path-rule generation.
- Dependency-free context benchmarks against three complete working trees of
  mature open-source repositories, with shallow history, bounded object storage,
  and cleanup evidence.

The current evidence-bounded prompt-only estimate is **8.6/10**. The staged
install measured 3,496 KiB across 422 files; see
`ultimate-dev/INSTALLATION.md` for the dependency matrix and measurement
method. This is not an independent model/host benchmark and does not satisfy
the 10/10 gate.

## External gates

These cannot be truthfully marked complete from this repository alone:

- Independent model/host behavioral benchmark with baseline, provenance, and calibrated judge.
- Organization-specific policy, jurisdiction, approval, and reviewer inputs.
- Real provider quality and latency benchmarks.
- Real browser/container/cluster integration tests.
- Kernel-grade isolation and multi-tenant security.
- Encryption/key management and complete DLP.
- External immutable audit storage, metrics, alerting, and incident response.
- Signed provenance, SBOM verification, protected release environments, and
  protected-branch approval.

See `docs/architecture/ARCHITECTURE.md` and the runtime README for the
host-neutral trust boundary.
