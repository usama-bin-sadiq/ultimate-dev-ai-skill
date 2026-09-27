# Science traces

Two objectives in physical science, and they fail in opposite directions. One is
computational and reaches a number with two real ambiguities attached to it that
cannot be resolved from the data in hand. The other is a bench procedure where
the kernel's correct move is to stop and ask a named person before touching
anything.

The interesting common thread is that in both, the tempting output — a lattice
parameter with no caveats, a "yes, the meter is fine" — is a number the evidence
does not reach, and both traces end up narrower than the request.

## Kernel mechanisms stressed

- **Degenerate explanations are named, not resolved by preference.** Sample
  displacement error and instrument zero-shift produce the same offset in a single
  flat specimen. The trace reports both, prices the ambiguity, and says what
  measurement would separate them.
- **R4 with a named human checkpoint before acting.** The pH trace's action is
  externally visible (a shared instrument goes out of service for 20 minutes) and
  touches physical resources. The checkpoint names a person, a duration, and what
  is irreversible.
- **Criteria that can disagree with each other.** A pH meter can pass its slope
  specification and fail its absolute-offset specification. The trace checks both,
  because checking one would have produced a green result on a failing instrument.
- **Deterministic arithmetic to a tool.** Bragg's law, the lattice refinement, and
  the χ² computation are all in a committed script. The kernel does not do
  crystallographic arithmetic in its head.
- **Scope words that bind.** "Determined the lattice parameter" and "determined the
  crystal structure" are different claims, and only the first is supportable from a
  powder pattern.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`xrd-cubic-lattice-indexing.md`](xrd-cubic-lattice-indexing.md) | Determine the lattice parameter and phase from a Cu Kα powder pattern | L3 / **R3** | PARTIAL | A computed result with two unresolvable degeneracies and two unindexed peaks, reported as such |
| [`ph-meter-verification-checkpoint.md`](ph-meter-verification-checkpoint.md) | Decide whether tomorrow's 240-sample pH series can run tonight | L1 / **R4** | VERIFIED | A named human checkpoint before acting, and a two-point check that catches what the SOP's one-point check misses |

## Reading notes

**`xrd-cubic-lattice-indexing.md` demonstrates the discipline that is hardest to
teach: reporting a good number with the caveats attached rather than either
over-claiming or refusing to answer.** It produces a = 8.251(4) Å from eleven
indexed peaks, and then spends the rest of the trace on what that number does not
mean — it is degenerate with a specimen-displacement interpretation, and two
unindexed peaks are not explained by the cell.

**`ph-meter-verification-checkpoint.md` is the counterweight.** It is one bench
check, it takes twenty minutes, and it is R4 because a shared instrument going out
of service is externally visible. The R4 is not difficulty worship: the trace shows
the specific trigger, and it shows that the *check itself* had to be wider than the
SOP specified, because the SOP's one-point check passes an instrument that fails
its offset tolerance.

## Adjacent examples

- [`../mathematics/`](../mathematics/) — the same numerical care applied to a
  constraint problem, and a case where the answer is that no solution exists.
- [`../unknown-domain/`](../unknown-domain/) — where there is no reference to lean
  on at all, which is the harder version of the same problem.
- [`../data-analysis/srm-before-reading-an-ab-result.md`](../data-analysis/srm-before-reading-an-ab-result.md)
  — a validity check that has to run before any result is read.
