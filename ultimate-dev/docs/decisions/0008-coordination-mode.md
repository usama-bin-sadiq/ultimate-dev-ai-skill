# 0008. Coordination mode is a decision, and JEv survives the handoff

Status: Accepted
Date: 2026-09-27
Deciders: architecture maintainers
Amends: `new-arch.md` §"Agent / Specialist Model" and the boundaries list
Constrains: 0002 (skills are resources, not agents)

## Context

The architecture specified two of the four standard multi-agent patterns and ruled out
the other two in a box:

> **Agents are NOT the architecture.**
> Agents are optional execution resources selected by the architecture when
> specialization provides sufficient expected value.

The two it had were **skills** — progressive disclosure, the context ladder, and the
core principle that the agent is not given everything — and **subagents** — the
Agent/Specialist Model, in which JEv asks whether specialisation is justified and a
stateless specialist answers in one result.

It did not have **router** (classify, dispatch N in parallel, synthesize) or
**handoffs** (the active agent changes and state carries across turns). That was not an
oversight so much as a position: handoffs require the *active agent* to change, and this
architecture holds control in one place.

It was also incomplete in a way that was not visible. Capability resolution conflated
two different questions — *which* capability, and *how many* — under one step. A run that
loaded four skills to answer a one-line question looked identical, in the record, to a run
that correctly needed four skills. Nothing distinguished paying for isolation nobody
needed from paying for it deliberately.

## Decision

**Coordination mode becomes its own JEv boundary, asked before capability selection.**

Four modes, selected cheapest-first:

| | Mode | Cost | Buys |
|---|---|---|---|
| ① | `inline` | 0 extra calls | — (context accumulates) |
| ② | `delegate` | +1 call per result | context isolation |
| ③ | `route` | N calls, parallel | parallelism and synthesis |
| ④ | `handoff` | stateful | a staged conversation |

The mode is a required decision field carrying its reason and the condition that would
reverse it, so a wrong mode is a recorded fact rather than an invisible one. `RunState`
gains `active_agent` and `authority`.

**The claim is narrowed, not abandoned:**

> Agents are not the architecture. **JEv is — including when it hands off.**

The active agent changes; the decider does not. A handoff is an ordinary decision record
whose effect is to write `active_agent`. The specialist still has no workflow of its own
— it cannot triage, verify, or recover.

**`RunState` becomes an artifact.** It was specified in `references/state-system.md` for
the whole life of the repository with nothing reading or writing it, which meant every
claim about resumption rested on a file that did not exist. `tools/run-state.py` now
creates, reads, updates and checks it.

## Why not the alternative

**Adopt handoffs wholesale.** Rejected. It requires the control plane to be split across
agents, and the reason this kernel holds control in one place is decision 0002: a library
of specialists each with their own workflow is how an architecture becomes a convention.
The handoff is the useful part of the pattern; the distributed control plane is not.

**Keep capability resolution as one step.** Rejected. It is the reason a wasteful run and
a correct run look the same in the record. Splitting the question costs one field.

**Make the mode inferred rather than recorded.** Rejected, and this is the load-bearing
part. An inferred mode is whatever the agent happened to do. The failure this exists to
prevent is choosing ④ when ① would do — and if the mode is not written down, nothing
distinguishes a considered choice from an expensive default.

## Consequences

**Better:** a wasteful coordination choice is now visible and reviewable. A repeated mode
error is classifiable as a *mode* error rather than a broken specialist. `RunState` exists,
so the resumption claims have something to rest on.

**Worse, and accepted:** nineteen boundaries instead of seventeen, and one more field to
fill at one boundary. The rung still governs how many records are written.

**Not fixed by this decision, and stated so it is not discovered later:**

- All four modes coordinate inside a live context window. None survives one closing. The
  L4+ rows of the scale ladder — multi-domain project, large programme, long-horizon —
  still depend on state that this decision only now makes writable.
- Mode ③ parallelises within one context. It is not distributed execution and has no
  failure isolation: one specialist that hangs holds the synthesis.
- The cost problem is mitigated, not solved. Mode ① is free per call and can cost most
  overall, because loaded skills accumulate. The honest consequence is that some
  capabilities must stop being skills and become delegates — a content decision about the
  corpus, not one this architecture can make.

**Constraint inherited from 0002, and it bites harder now.** Selection must stay gated on
reachability. 291 roles ship and nineteen carry a dispatch condition. Adding a mode that
*selects* specialists by description sharpens the trigger-signal split rather than
solving it: with overlapping descriptions the wrong specialist is chosen as often as the
right one, and the failure presents as incompetence rather than misconfiguration, so it
does not get debugged. Unreachable specialists are not spare capacity.

## Artefacts

- `new-arch-updated.md` — the revised specification
- `references/coordination-modes.md` — the four modes, costs, selection test
- `tools/run-state.py` — RunState, including the `check` gate
- `SKILL.md` Step 4 — the mode step in the kernel
- `references/decision-fabric.md` — the nineteenth boundary
