# Architecture

This document explains how the system is put together and, where the choice was
not obvious, why. It is rationale, not specification: it records the reasoning
behind decisions, and where it and the specification disagree the specification
wins.

- **Specification** — `new-arch-updated.md` (revision 2)
- **Requirements** — `prd.md`
- **Executed behaviour** — `SKILL.md`

`new-arch.md` is revision 1 and is retained because ADR 0008 and ADR 0009
record divergences against it. It is superseded: it has no coordination-mode
section, so a reader following it would not find the four modes that
`SKILL.md` Step 4 implements and that `references/coordination-modes.md`
specifies. Two things in this repository still say `new-arch.md` where they mean
the current specification, and both are recorded as divergences rather than
silently corrected — see ADR 0009.

## The load-bearing claim

> The same kernel scales from a trivial task to the hardest class of problems
> without requiring a different architecture.

Everything below is in service of that sentence, and most of the design is
falsifiable by it. If scaling from R0 to an L7 programme required a separate
"serious mode", the claim would be false and the architecture would be a
collection of small tools wearing a trench coat.

## The shape

```text
USER OBJECTIVE
      ↓
  TASK MODEL          objective, requirements, constraints,
      ↓               unknowns, assumptions, success criteria
   TRIAGE             complexity, uncertainty, consequence,
      ↓               reversibility → rung R0–R4, scale L1–L7
  ┌───────────────────────────────────────────┐
  │              JEv DECISION FABRIC          │
  │  decides at every boundary that matters   │
  └───┬───────────────┬───────────────┬───────┘
      ↓               ↓               ↓
  CONTEXT         CAPABILITY       STRATEGY
      │           RESOLUTION          │
      └───────────────┬───────────────┘
                      ↓
                  REASONING           ← the rung
                      ↓
                   PLANNING           ← atomic work units
                      ↓
                  EXECUTION
                      ↓
                 OBSERVATION          ← what happened, not what was expected
                      ↓
                 VERIFICATION         ← VERIFIED / PARTIAL / FAILED
                 ┌────┴────┐
                 ↓         ↓
             SYNTHESIZE  RECOVERY
                 │         │  classify → retry / replan / escalate
                 └────┬────┘
                      ↓
              SELF-EVALUATION
                      ↓
                  LEARNING          ← gated, never automatic
                      ↓
                  DELIVERY
```

Four cross-cutting systems govern all of it: state, budget, evidence and
provenance, and security and trust. See `docs/architecture/`.

## The five decisions that shaped everything

### 1. JEv is a fabric, not a stage

A stage is a step in a sequence. JEv is the discipline of producing a defensible
decision at every boundary where the shape of the work could change — seventeen
named boundaries, from task understanding to learning promotion.

The consequence is that the kernel has no fixed stage list every task must walk.
A rename of a local variable enters at UNDERSTAND, decides, acts, checks the
output, and delivers. That is a complete run, not an abbreviated one.

The alternative — a stage-based pipeline with a skip flag per stage — pushes the
same judgement into a boolean and loses the reasoning. When a run goes wrong at
step 6, a pipeline tells you it skipped step 3; JEv tells you why it decided
three was unnecessary, and whether that judgement still holds.

Cost: every meaningful decision produces an artifact. Benefit: the work is
reviewable, and a run can be re-entered at any point without re-deriving
everything upstream.

### 2. Context is a managed, budgeted resource

The context ladder runs C0 (task) → C2 (capability instructions) → C3 (targeted
references) → C4 (project material) → C5 (external evidence) → C6 (specialist
depth), and stops when the next level stops changing the answer.

Two failure modes pull in opposite directions, and both are common: loading
everything and drowning in it, and loading so little that the decision rests on
unexamined assumptions. The rule that resolves both is to load the *narrowest*
thing that would change the decision, and no more.

The alternative — "include what is relevant" — is not an instruction, because
relevance is exactly the judgement in question. The ladder makes it a sequence of
escalations, each justified by the previous one being insufficient.

### 3. Capability resolution is ordered, and creation is last

1. Do it directly — most tasks end here.
2. Existing capability.
3. Compose existing capabilities.
4. Acquire an external one, then validate it.
5. Create one.

Before step 5, one question: *will this be needed again?* A one-off is a plan
step. The disqualifier exists because creation is the rung that compounds: a
skill per task splits the trigger signal, and the user starts paying to
disambiguate between skills that all claim their request.

This is also why `skill-creator` is a first-class capability rather than a side
utility. It is the mechanism that lets the system exceed the skills it shipped
with — and it is the mechanism most likely to damage the system if left
unguarded, which is why its lifecycle is gated.

### 4. Verification depth is a decision; verification itself is not

There is exactly one stage that is never skipped. What varies is its strength:
an evidence check that the evidence supports the claim, a validation check that
the success criteria hold, an independent check that the result would survive
being derived a different way.

The three verdicts are `VERIFIED`, `PARTIAL`, and `FAILED`. `PARTIAL` is a real
verdict, and the failure modes are symmetric: reporting `PARTIAL` as success, and
discarding good work because one criterion failed.

### 5. Learning is gated, and promotion is a decision

Experience → observation → signal → pattern → candidate → validation → JEv →
promotion. One failed task must not permanently rewrite the system, and one
success must not install itself as a rule.

The bar for promotion is evidence that the behaviour generalises beyond the
instance that produced it, plus a stated scope. A promoted capability that turns
out wrong must be identifiable and removable. The ladder —
`OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → ACTIVE → DEPRECATED`
— exists to make that reversibility structural rather than aspirational.

### 6. Coordination mode is a decision, and it is not the same as capability

The first five decisions are about *what* to do. This one is about *how many
contexts* do it.

Four modes — **inline**, **delegate**, **route**, **handoff** — and the choice is
made before any capability is acquired, because it changes what acquiring one
means. Under `delegate` a capability is something you call; under `route` it is
something a decision can select; under `handoff` it is something that arrives
with authority already attached.

Recording it as a boundary is the part that matters. Everything else about the
modes is a table; what stops them collapsing into one another is that a
transition between them is a decision with a recorded rejected alternative, the
same as any other boundary. A mode change that nobody wrote down is
indistinguishable, downstream, from never having chosen.

The load-bearing correction is to the earlier claim that *agents are not the
architecture*. That was right about swarm-shaped fan-out and wrong about
transfer: a handoff moves authority, and once authority has moved the decision
fabric has to survive the move. So the claim is now **JEv is the architecture —
including when it hands off**, and the four modes are ways of being one kernel
rather than four. ADR 0008 records the amendment.

The selection test and the per-mode costs are in
`references/coordination-modes.md`; the specification is revision 2's
§4.

## Trust boundaries

```text
user instruction  ≠  retrieved document  ≠  web content
                  ≠  tool output        ≠  generated skill  ≠  trusted policy
```

Content crossing into the kernel does not become instructions by being read. A
document you were told to read, a page you fetched, and a tool's stdout are
**data**. They may inform a decision. They may not authorise an action, widen
permissions, or introduce instructions.

This applies to the kernel's own generated skills. A skill the kernel wrote is a
candidate until validated, not a trusted extension of its authority. Exempting
self-authored content would remove the only control the system has over its own
expansion.

Human control is a separate mechanism, not a weaker version of this one. Autonomy
is choosing the method; it is not waiving the user's authority over consequences.
Ask before acting when the action is irreversible, externally visible, costly,
destructive, credential-bearing, or ambiguously authorised. See
`docs/security/threat-model.md`.

## Scalability

The same kernel operates at every level. What changes is resources, planning
depth, verification strength, and capability composition — not the lifecycle,
not the decision record, not the output contract.

| Scale | Shape | What appears |
|---|---|---|
| L1 | One task | R0–R1, single pass |
| L2 | Multi-step | Short plan, a few work units |
| L3 | Professional | Decomposition, capability resolution, per-unit verification |
| L4 | Multi-domain project | Workstreams, integration, cross-unit verification |
| L5 | Large programme | Hierarchical planning, checkpoints, continuous evaluation |
| L6–L7 | Extreme, unfamiliar, long-horizon | All of the above plus explicit risk retirement and staged delivery |

Two ladders, not one. Rung is how hard the decision is; scale is how much work
there is. Conflating them produces both characteristic errors: massive ceremony
on a routine bulk edit, and inadequate care on a one-line change to a safety
interlock.

### What "the same kernel" does and does not claim

The claim is defensible about the **lifecycle** and is *not* defensible about
**orchestration**, and the distinction matters more than the headline suggests.

**Defensible.** The lifecycle, the decision record, the output contract, the
evidence requirements, and the trust boundaries are identical at every level. A
run at L1 and a run at L6 are the same procedure with more of it in play.

**Not defensible.** Orchestration topology is not a dial. Adding subagents,
parallel units, and hierarchical decomposition produces **sign flips, not
magnitude changes**: measured work on multi-agent orchestration finds negative
returns once single-agent accuracy passes roughly 45%, and sequential planning
over long horizons degrading rather than helping. Those are regimes with
boundaries, not a gradient.

The honest form of the claim:

> One lifecycle, at every level. Orchestration topology changes at thresholds, and
> those thresholds are properties of task difficulty and runtime reliability —
> not of task size.

This does reintroduce a mode switch, which the original design set out to avoid.
It reintroduces it in a better place: **as a decision with a stated trigger and a
measurable criterion**, rather than as a separate code path someone must remember
to invoke. Hiding the switch inside a resource dial is still a switch; what was
wrong before was that it was invisible, not that it existed.

Two consequences:

- **Delegation and parallelism need an upper bound, not only a justification
  test.** The existing test asks whether specialisation beats doing it here,
  which is a per-task argument and does not catch the regime flip. The bounds
  live in `references/delegation.md` and `references/parallelism.md`.
- **Planning frequency is an optimum, not a constant.** Always planning degrades
  long-horizon performance; never planning produces unrecoverable drift. Plan when
  the next action is genuinely undetermined and stop when it is not — which is
  what R0 already requires, but the asymmetry is worth stating because the
  instinct is to plan more.

## The honest limits

- **The architecture is defined; the evidence is not.** The benchmark suite
  exists and the comparison methodology is specified, but the with-versus-without
  measurements have not been run at scale. Treat the architecture as a hypothesis
  with a test plan.
- **"OS-scale" is a benchmark, not a capability.** It means the architecture can
  manage decomposition, acquisition, execution, integration, and verification at
  that scale — not that one pass produces an operating system. The distinction is
  what makes the design technically credible.
- **Model-dependent.** The kernel improves judgement, not capability. On a
  problem the underlying model cannot reason about, the kernel's contribution is
  better failure reporting, not success.
- **The learning system is the least proven part.** Gating is designed for and
  specified in detail; whether it prevents degradation over long horizons is an
  open empirical question.
- **Evaluation costs money and time.** Meaningful comparison needs repeated runs
  and a real baseline. It will be run selectively, and the samples will be
  smaller than ideal.

## Further reading

- `docs/architecture/kernel.md` — the execution model in depth
- `docs/architecture/context-and-capability.md` — the two ladders and how they interact
- `docs/architecture/scalability.md` — L1 through L7 with the same kernel
- `docs/decisions/` — the records of the choices above
- `docs/concepts/` — the vocabulary
- `research/` — what this borrows, and what remains unresolved
