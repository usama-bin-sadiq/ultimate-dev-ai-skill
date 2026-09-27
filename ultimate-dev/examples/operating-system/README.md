# Operating-system traces

These are not a claim that one pass builds an operating system. They are the
benchmark the PRD names: the stress-test metaphor for whether the *architecture*
holds at extreme complexity, using OS construction as one representative
instance rather than the product's purpose.

The honest version of that claim is a property of the machinery, not an artefact.
So the two traces here are arranged as a pair:

- **`os-capability-benchmark.md`** is the L7 pass. It receives the objective
  "Build an operating system", recognises a programme rather than a task,
  derives its own decomposition instead of reading one from a table, sets an
  explicit bound, and delivers a staged plan with one stage executed. Its
  verification is an **invariance test**: the same kernel is run on a completely
  unrelated L5 objective and the *shape* of its behaviour is compared. If the
  behaviour were hard-coded for "OS", the two shapes would be identical, and that
  would be the evidence of cheating.
- **`stage0-mbr-boot-sector.md`** is the L4 pass that actually executes Stage 0:
  a 512-byte MBR that the CPU reaches, writes a string to a UART, and halts, in
  QEMU, built by NASM, verified byte-for-byte and rebuilt from a clean directory
  to prove reproducibility.

## Kernel mechanisms stressed

- **Scale without architectural change.** Same loop, same rung ladder, same
  work-unit discipline at L1 and L7. Only the resource count changes.
- **Decomposition as derivation.** Eight workstreams derived from "what must be
  true for a machine to reach our code", including one — the emulation and
  observation harness — that appears in no reference decomposition, because the
  kernel's own rule that no unobserved result may be reported forces it.
- **Capability acquisition with validation.** `nasm` checked, `qemu` acquired
  then validated, a stereonet-class tool *not* acquired because it could not be
  validated, and nothing created in either trace.
- **Staged delivery against a stated bound.** The L7 pass delivers Stage 0 and
  says so; 0% of an operating system is the true figure and it is stated.
- **A verification criterion that reality can falsify.** `int 10h` output is
  unobservable in a headless emulator, so the criterion was wrong before the
  code ran, and the check was rewritten before it was claimed as passed.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`os-capability-benchmark.md`](os-capability-benchmark.md) | "Build an operating system." | L7 / **R4** | PARTIAL | What an honest extreme-complexity bound looks like, and the invariance test that replaces a fake completion claim |
| [`stage0-mbr-boot-sector.md`](stage0-mbr-boot-sector.md) | Prove Stage 0 end to end, reproducibly | L4 / **R3** | VERIFIED | A vertical slice that actually ran, and a verification criterion invalidated by the harness before the code existed |

## The common misreading

> "Stage 0 of a 512-byte boot sector is not an operating system, so the L7 pass
> failed."

The L7 pass did not fail. It was asked for a programme, and it returned a programme
with a bound, a derived decomposition, a first stage executed and verified, and a
falsifiable test of its own architecture. What it did not return is an operating
system, and the trace says so in the delivery rather than implying otherwise through
volume of output. The distinction the PRD draws is the one the trace holds:
*OS-scale capable means the architecture can manage and solve the work through
decomposition, acquisition, execution, integration, and verification — not that a
single model generates an entire operating system in one pass.*

## Adjacent examples

- [`../unknown-domain/`](../unknown-domain/) — the same discipline with the ambition
  removed, a more direct test of whether the decomposition was derived.
- [`../cross-domain/`](../cross-domain/) — L4, where several domains must be
  composed rather than one deep one traversed.
- [`../planning/`](../planning/) — the same hierarchical work-unit machinery where a
  real rollback exists.
