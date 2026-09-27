# Unknown-domain traces

Two objectives in disciplines the kernel has no skill for: structural geology and
food microbiology. The rule these traces follow is the one `prd.md` §11 states and
`operating-model.md` makes architectural: **the system is not a router.** There is
no `if geology: use a geology agent`, and neither trace invents one.

What the kernel does instead is narrower and, when it works, more useful: it works
out *which part* of the problem is arithmetic (which it can do with a tool), which
part is a lookup (which it can fetch as data), and which part requires a
professional judgement it cannot make (which it says so about, in the sentence
where a reader would otherwise have trusted it).

## Kernel mechanisms stressed

- **No invented domain agent.** Both traces reach a capability gap, and both routes
  out of it are compose or acquire. Neither creates a "geology skill" or a
  "fermentation skill" for a single conversation.
- **The competence boundary is stated in the deliverable, not the disclaimer.**
  The geology trace computes an orientation table confidently and then says which
  four questions about the fold it cannot answer, with the measurement that would
  answer each.
- **A hypothesis the evidence refutes beats a confident answer.** The sourdough
  trace's first plan was a temperature correction; the user's own data refutes it
  within two exchanges, and the trace re-plans rather than defending.
- **The disqualifying question is asked out loud.** "Will this be needed again?" has
  a clear answer in both traces — no — and that is why nothing is created.
- **Cheap acquisition of a measurement instead of a capability.** In the sourdough
  trace the missing thing is two questions, not a skill, and the trace says so.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`folded-stratigraphy-field-log.md`](folded-stratigraphy-field-log.md) | Work out the geometry of a fold from a field log and 9 measurements | L2 / **R2** | PARTIAL (deliberately bounded) | Arithmetic done confidently; four interpretation questions named as not the kernel's to answer |
| [`sourdough-starter-not-rising.md`](sourdough-starter-not-rising.md) | Why has the starter not risen in 8 hours? | L1 / **R1** | PARTIAL (deliberately narrow) | A plan refuted by the user's own data, and the missing thing identified as two questions rather than a skill |

## The common misreading

> "The geology trace should have just answered the question about the fold."

It cannot, and the reason is specific rather than a refusal: the same nine
measurements are consistent with an upright asymmetric fold and with an overturned
one, and the measurements needed to tell them apart are measurements of the rocks,
not of the numbers. A kernel that produced a confident fold classification here
would be producing a plausible answer with no evidential path, which is a worse
failure than saying which four measurements would settle it.

The distinction these traces hold is between **arithmetic, which the kernel can do
and verify**, and **interpretation, which requires the training and the field
experience the kernel does not have**. Both traces do the first and bound the
second.

## Adjacent examples

- [`../science/`](../science/) — deep competence in one field, with the limits stated
  at its boundary. Read alongside these, they show the two ends of the same honesty.
- [`../operating-system/os-capability-benchmark.md`](../operating-system/os-capability-benchmark.md)
  — the decomposition test at extreme scale, where the workstream list shares only
  2 of 8 with an unrelated L5 objective.
- [`../research/`](../research/) — where a reference *can* be leaned on, which is
  the thing that is missing in both traces here.
