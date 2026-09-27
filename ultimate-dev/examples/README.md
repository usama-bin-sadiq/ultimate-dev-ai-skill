# Examples

Worked kernel runs. Each shows the same machinery applied to a different
problem, which is the only way to demonstrate that the architecture is genuinely
domain-independent: if the procedure is the same everywhere, the traces should
look alike even when the subject matter does not.

Read these before changing the kernel. A change that breaks the pattern visible
here has broken something that is hard to see in a specification.

## What every trace shows

Each trace follows one structure, so two traces can be compared line by line:

| Section | What it establishes |
|---|---|
| Triage | The four questions answered, and why the chosen rung is the lowest adequate one |
| Task model | Requirements separated from success criteria, assumptions with consequences |
| Decision records | `rejected` populated, confidence and recovery stated |
| Context | What was loaded, and what was deliberately **not** loaded |
| Capability | Where the resolution ladder stopped, and why it did not go further |
| Plan | Atomic work units with preconditions and expected results |
| Execution | What actually happened, including the surprise |
| Verification | `VERIFIED` / `PARTIAL` / `FAILED` with the evidence |
| Recovery | Present when something failed; the wrong response that was avoided |
| Delivery | Outcome first, then evidence, assumptions, limits, confidence |
| Learning | Candidates only, with what promotion would require |

**Every trace contains a place where reality contradicted the plan.** A trace
where everything went smoothly proves nothing about a kernel whose defining
feature is what it does when the plan is wrong.

## By domain

| Domain | Traces | What it stresses |
|---|---|---|
| [software-engineering](software-engineering/) | R0 variable rename; 412M-row column add; retry storm after node restart | The R0 boundary, reversible-but-expensive work, resource failure |
| [operating-system](operating-system/) | Capability benchmark; MBR boot sector | Extreme scale staged honestly rather than claimed |
| [distributed-system](distributed-system/) | Kafka rebalance on pod restart; lock timeout without fencing | Partial failure, correctness under concurrency |
| [data-analysis](data-analysis/) | R0 session-length computation; SRM before reading an A/B result | Deterministic computation, a trap in the data itself |
| [mathematics](mathematics/) | R0 integral substitution; rota infeasibility | Doing almost nothing, and an unfeasibility verdict |
| [science](science/) | pH meter verification checkpoint; XRD cubic indexing | Instrument calibration as a gate, domain indexing |
| [research](research/) | T5 WMT14 BLEU reproduction; onboarding experiment power | External reproduction, statistical power before running |
| [business](business/) | List-price increase; observability vendor renewal | Consequence-bearing decisions under uncertainty |
| [writing](writing/) | R0 README install section; incident postmortem claims | The R0 boundary, and claims-versus-evidence in prose |
| [planning](planning/) | R1 Japan itinerary constraints; billing API cutover | Constraint satisfaction, irreversible cutover planning |
| [cross-domain](cross-domain/) | Phase 2b trial costing; SOC 2 CC6.1 deprovisioning evidence | Two domains composed, not one wearing a hat |
| [unknown-domain](unknown-domain/) | Sourdough starter not rising; folded stratigraphy field log | Operating where no skill exists, and admitting it |
| [recovery](recovery/) | Backfill OOM; staging-only failure | Classification before response, against blind retry; verification depth as the real defect |

## The five that matter most

If you read five, read these.

1. **[`software-engineering/r0-renaming-userid-in-reconcile.md`](software-engineering/r0-renaming-userid-in-reconcile.md)** — a task that looks like it needs a plan and does not. This is the R0 boundary, and over-orchestrating it is the architecture's most common failure.
2. **[`data-analysis/srm-before-reading-an-ab-result.md`](data-analysis/srm-before-reading-an-ab-result.md)** — the plan was going to be right about the wrong thing. Shows a discovery that invalidates the framing rather than the estimate.
3. **[`unknown-domain/sourdough-starter-not-rising.md`](unknown-domain/sourdough-starter-not-rising.md)** — a discipline the kernel has no skill for. Watch what it declines to claim.
4. **[`operating-system/os-capability-benchmark.md`](operating-system/os-capability-benchmark.md)** — how OS-scale is handled as a stress test and delivered in stages, not as a single pass that produces an operating system.
5. **[`recovery/backfill-oom-resource-failure.md`](recovery/backfill-oom-resource-failure.md)** — a failure classified before it is responded to, with the blind retry named and refused.

## Cross-references

- `evaluation/benchmark/TRIGGER-NEGATIVES.md` — the tasks that must **not** trigger
  this machinery. Several of them are the inverse of traces here.
- `evaluation/failure-cases/` — the same failures as gradeable cases
- `references/anti-patterns.md` — the defects these traces are chosen to avoid
