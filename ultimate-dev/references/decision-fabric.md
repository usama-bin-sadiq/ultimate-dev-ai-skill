# Decision Fabric (JEv)

JEv is the kernel's decision mechanism. It is not a stage, a component, or a
callable. It is the discipline of producing a defensible decision at every
boundary where the shape of the work could change.

## Spec boundaries and where they live

`new-arch.md` names seventeen decision boundaries. Four of them are named
differently here, and a reader cross-referencing the specification would not find
them by name. The mapping, so none of them looks missing:

| Spec boundary | Named here | Where |
|---|---|---|
| Task understanding | task interpretation | `task-model.md` |
| Coordination mode | coordination mode | `coordination-modes.md` |
| Reasoning effort | reasoning effort, the rung applied to a step | `reasoning-system.md` |
| Workflow selection | workflow selection | `runtime-portability.md` |
| Decomposition | decomposition | `planning-system.md` |
| Context retrieval | context depth | `context-system.md` |
| Context depth | context depth | `context-compiler.md` |
| Capability selection | capability choice | `capability-system.md` |
| Capability acquisition | capability acquisition | `capability-acquisition.md` |
| Strategy selection | strategy | `strategy-system.md` |
| **Workflow selection** | **capability resolution order** | `capability-system.md` |
| **Reasoning effort** | **rung** | `triage.md` |
| Specialist delegation | delegation | `delegation.md` |
| Parallelization | parallelism | `parallelism.md` |
| Research depth | context depth | `context-system.md` |
| Verification depth | verification depth | `verification-system.md` |
| Retry | retry | `retry-policy.md` |
| Replanning | replan | `recovery-system.md` |
| Escalation | escalation | `escalation.md` |
| Learning promotion | learning promotion | `learning-system.md` |

**Workflow selection has no separate boundary here, deliberately.** The
specification lists it alongside strategy selection as a distinct choice. This
kernel has one ladder that answers it — the capability resolution order — and
splitting "which workflow" from "which capability" would produce two questions
with one answer, and a record written twice for one decision. That is a
deliberate divergence, recorded in the decision records under `docs/`, and it is the one place the
boundary list is shorter than the specification's.

## What makes it a decision

An assertion is a statement. A decision is a statement plus what it chose
against. The distinguishing artefact is the **decision record**:

```text
DECISION
  question      the boundary being crossed
  selected      what to do
  rejected      what not to do, and why            <- the field that earns its place
  rationale     the reasoning, in one line
  confidence    high | medium | low — in WHAT, named explicitly
  cost          expected effort, and what it buys
  evidence      POINTERS to observations (OBS-n), not prose; "none" is valid
  recovery      the condition that would reverse this
```

If `rejected` cannot be filled, there was no decision — there was a default, and
it should be recorded as one. Defaults are fine; unexamined defaults presented as
choices are how a run becomes unreviewable.

## The objective function

```text
        expected outcome
JEv  =  ───────────────────
        cost + risk + uncertainty
```

Not tokens. Not tool calls. Not the fewest steps. The numerator is what you get
if you are right, weighted by consequence; the denominator is everything you
spend and everything you expose yourself to.

This has a consequence that is easy to get backwards: **paying more to avoid a
costly failure is the correct trade.** Running a five-minute confirmation step
to avoid an irreversible ten-hour recovery is a win, and a kernel that minimises
effort will avoid it and lose.

It also has a second consequence: a low-consequence task with a tool-confirmed
answer does not need more reasoning. Adding a review panel to a formatting fix
is a loss under this function, not a gain.

## The boundaries

Decisions that require a record:

| Boundary | The question |
|---|---|
| Task understanding | What is actually being asked? |
| **Coordination mode** | **How do the pieces come back together — inline, delegate, route, handoff?** |
| Decomposition | Does splitting help, or add coordination cost? |
| Context depth | How much do I need to know before deciding? |
| Context retrieval | From where, and how do I trust it? |
| Capability selection | Which means of making progress? |
| Capability acquisition | Install, fetch, or create? |
| Skill creation | Is a new skill justified, or is this a plan step? |
| Skill composition | Can existing capabilities be combined? |
| Strategy | Which approach class? |
| Reasoning depth | Which rung? |
| Model / resource | Does the work need a different tool or a different rigour? |
| Delegation | Does specialisation beat one context? |
| Parallelisation | Which units are genuinely independent? |
| Research depth | What must be looked up, and how far? |
| Verification depth | Shallow or exhaustive? |
| Retry | Is the cause known? |
| Replanning | Does the plan survive this evidence? |
| Escalation | Must a human decide? |
| Learning promotion | Does this generalise beyond this instance? |

Not every boundary needs a written record at every rung. At R0, none do. At R3,
most of them do. The rung sets the *default* granularity; the cost of being wrong
sets the actual one.

What is **not** negotiable is the shape. Whenever a record is written, `rejected`
and `recovery` are filled. Making all nineteen mandatory on every run would be
the most expensive possible assertion of diligence in a kernel whose most common
defect is doing too much, and agents reliably find valid approaches that a fixed
checklist did not anticipate — so a mandatory count buys assertion, not quality.

**Coordination mode is the one boundary that gates the others.** It is asked before
capability selection, because it determines which of the remaining eighteen are even
reachable: a run in mode `inline` has no delegation decision to make, and one in
mode `handoff` has a different set again. It carries an extra required field —
`coordination` — plus the condition that would reverse it, so a mode that turns out
to be wrong is a recorded fact rather than an invisible one. `tools/run-state.py
set-mode` writes it; `check` refuses a state where the mode has no stated reason.
See `references/coordination-modes.md`.

## Confidence must name its object

`confidence` is about the decision, not about the eventual outcome. Three values,
and they mean:

- **high** — the alternatives were considered and are clearly worse, and the
  evidence supports it.
- **medium** — the decision is reasonable and the alternatives are close, or
  evidence is partial.
- **low** — this is a bet, and here is what would settle it.

**Always write what you are confident about.** `high in the retry header being
present`, not `high`. A bare confidence value is read downstream as a property of
the conclusion rather than of the evidence, and that is precisely the over-trust
that automation-bias work documents: a system that sounds certain is checked
less, not more. Naming the object forces the distinction and makes the value
falsifiable.

`low` is an honest and useful value. A ledger where every entry is `high` is
either a run with no uncertainty or a run that is not being honest.

Note the coupling: `confidence: high` with `evidence: none` is a contradiction
unless the decision is reversible and cheap, in which case say so in `rationale`.

## Evidence must point, not narrate

Write `OBS-013`, not "the logs showed retries".

This is not a style preference. A prose evidence field cannot be mechanically
checked, so a fabricated citation and a real one are indistinguishable — which
makes it the ideal place to conceal the system's worst failure, the confident
fabrication. A pointer either resolves to a recorded observation or it does not,
and that is decidable without judgement.

`none` is a valid and checkable answer. Prefer it to a plausible sentence.

## Cost, and what it buys

`cost` is expected effort, and — more importantly — **what that effort buys**.
"Twenty minutes to establish the real cause before changing anything, versus
guessing at one of four mechanisms" is a useful cost statement. "Medium" is not.

Effort spent before acting is usually cheap. Effort spent recovering is
expensive. When uncertain, buy certainty before the irreversible step.

## Evidence

`evidence: none` is a valid and sometimes correct entry. What is not valid is
recording `none` while the rationale implies otherwise. "None, but the failure
mode is cheap and reversible" is a complete, honest decision.

## Recovery

Every decision names the condition that would reverse it. This is what makes
decisions falsifiable after the fact rather than merely justifiable. A decision
with no stated reversal condition has committed to being right forever, which is
the failure mode of plan-defence.

## Worked records

```text
DECISION
  question    Diagnose the reconciliation overrun before changing anything.
  selected    Instrument and measure; do not change the query yet.
  rejected    Rewriting the query on inspection — four plausible causes, and
              the rewrites are not obviously separable by their effect.
  rationale   A wrong fix costs a migration cycle and teaches nothing; a
              measurement costs one cycle and eliminates the guess.
  confidence  high in the four candidate causes being genuinely inseparable by
              inspection; low in which one is responsible, since none has been
              measured
  cost        One profiling run, minutes to hours depending on data volume.
              Buys: a cause that is a fact rather than a hypothesis.
  evidence    none — the 40-minute overrun is a reported symptom, not an
              observation this run made. Nothing has been timed yet, and
              confidence is high only about the cheapness of measuring, which
              is why it survives having no evidence.
  recovery    If instrumentation shows a single dominant cause, stop measuring
              and fix it.
```

```text
DECISION
  question    Add retries to the API client.
  selected    Exponential backoff, 3 attempts, honour Retry-After.
  rejected    Fixed 1s delay — ignores the server's own backoff signal.
              More than 3 attempts — no stated need, and it worsens the
              overload we are responding to.
  rationale   The server already tells us when to retry; believing it beats
              guessing a delay.
  confidence  high in the server emitting Retry-After on the 429s seen so far;
              medium in three attempts being the right ceiling, which is a
              judgement about our tolerance and not something observed
  cost        An afternoon, reversible in one commit.
  evidence    OBS-003, OBS-004 — two 429 responses captured with their
              Retry-After headers, recorded before this decision.
  recovery    If the 429s lack Retry-After, or success rate is unaffected by
              delay, revisit the strategy rather than tuning the numbers.
```

## Anti-patterns

- **The bare assertion.** A decision with no recorded alternative. Cannot be
  reviewed.
- **Retroactive justification.** The rationale is written after the outcome is
  known and describes the outcome. Detectable, and it destroys the ledger's
  value.
- **Unbounded hedging.** `confidence: low` on everything, which is a way of
  declining to decide.
- **Ledger bloat.** Recording every trivial choice until the record costs more
  than the decision. See `decision-ledger.md`.
- **Decision without a recovery condition.** A commitment that can never be
  shown to be wrong.
