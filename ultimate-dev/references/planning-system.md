# Planning System

The plan's unit of account is the **atomic work unit**, and the plan exists to
be revised. Produce the smallest set of units that each carry their own evidence,
order them by dependency, and change the moment observation says you are wrong.
A plan that survives contradicting evidence is worse than none.

## What makes a unit atomic

A work unit is atomic when all four hold: it is **independently verifiable** (a
check that can pass or fail without the rest of the plan); it declares its
**precondition** (the state that must be true before you start) and its
**expected result** (the observable outcome if it goes right); and it states what
would make it **fail**. If you cannot say how you would know a unit worked, it is
not a unit — it is an intention, and intentions cannot be verified or resumed.

## Order by dependency, and plan for interruption

Sequence units by what must exist before what. An easy unit that consumes an
unbuilt prerequisite is not earlier, it is blocked; a hard unit everything else
depends on is first regardless of difficulty. Sorting by apparent ease is the
most common planning error: it optimises the order you *can* do, not the one
that *works*.

Assume you will be cut off mid-unit. A unit you cannot resume from its own state
is not yet a unit: name the state it leaves behind, what a resuming context must
know, and which command reproduces its check. Break a long unit only where the
partial result is still meaningful.

## The plan is mutable, and that is the design

When observation contradicts the plan, that is the system working:

1. Stop at the unit boundary; do not push into a plan you now doubt.
2. Return to JEv. Write a **decision record**: what the observation was, what
   changed, why the old plan no longer holds, and what would reverse the new
   plan.
3. Re-plan **only the affected part.** A wrong unit 7 does not invalidate units
   1–6. Re-planning everything on every surprise is its own failure: it discards
   completed work and loses the reason the rest of the plan was right.
4. If a failed assumption is the cause, correct it and re-plan every unit that
   depended on it. Name them; silent partial replans leave orphans reasoning
   from a dead premise.

## Decomposition depth

Depth is a product of the rung and the scale, not of ambition.

| Scale | Shape | Planning |
|---|---|---|
| **L1** | One task | R0–R1, single pass, often no explicit plan |
| **L2** | Multi-step | Short plan, a few work units |
| **L3** | Professional | Decomposition, capability resolution, per-unit verification |
| **L4** | Multi-domain project | Workstreams, integration and cross-unit verification |
| **L5** | Large programme | Hierarchical planning, checkpoints, continuous evaluation |
| **L6–L7** | Extreme, unfamiliar, long-horizon | All of the above plus explicit risk retirement and staged delivery |

## Dependency graph, then schedule

The graph is where truth lives; the schedule is a rendering of it. Draw `Ui ->
Uj` for every requirement of a result, mark each join (where several units must
all verify before proceeding), and place a checkpoint at every join and before
any irreversible action. The critical path — the longest dependency chain — is the
floor on how fast this can go; mark what runs concurrently only where units
share no mutable state (`parallelism.md`), and order the rest by dependency.

## Work unit record

```text
UNIT          id            stable label; you will cite it in observations
  objective   one sentence, in outcome terms
  precondition the state that must hold before starting
  action      the concrete means
  expected    the observable result if it works
  verify      the check that passes or fails, and against what
  fails when  the named failure conditions
  depends on  unit ids, and why each is needed
  state       what this unit leaves behind, for resuming
  status      pending | active | done | blocked | dropped
  evidence    what was actually observed, once run
```

## Prohibitions

- **No unit with no check.** Unverifiable units are how a plan produces
  confident, unchecked output.
- **No permanent commitment.** A plan defended against its own evidence is the
  failure this system exists to prevent.
- **No decomposition below verifiability.** Finer is not better, and a three-step
  task split into twenty units is theatre (`reasoning-system.md`).
- **No silent unit drops.** If a unit is abandoned, record why, so later work
  does not rely on what it would have produced.

See `strategy-system.md` for the shape the units belong to, `execution-system.md`
for carrying them out, and `observation-system.md` for what invalidates one.
