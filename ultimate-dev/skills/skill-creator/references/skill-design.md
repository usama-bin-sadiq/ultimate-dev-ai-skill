# Skill design

A skill earns its existence by being needed again in a shape you can predict.
Prove the gap is real before you design anything — a candidate written for a gap
that reuse or composition would have closed is worse than no skill at all,
because it splits the trigger signal and must be maintained forever.

The disqualifying question is **will this be needed again?** Answer it with named
recurrences, not with the impression that this looks reusable.

## A one-off is a step in a plan

If the second occurrence is hypothetical, do not create a skill. Write the
procedure as a work unit, run it, and record in the ledger that it happened. A
skill is a promise that future runs will find it, load it, and trust it, and a
promise with one use behind it has no evidence behind it.

| The need is | The artifact is |
|---|---|
| This task, once | A step in the plan |
| This shape of task, repeatedly | A candidate skill |
| This shape plus its neighbours | An extension of an existing skill |
| A capability the system lacks entirely | An acquired one, validated before use |

## Resolution order

The kernel reaches this engine at capability resolution step 4 or 5, after
doing-it-directly, using an existing capability, and composing have all
genuinely failed. Re-establish that. Do not fall through a rung that was
adequate because you are already thinking about the one below it.

```text
GAP
 ├─ 1 reuse an existing capability?  ── yes → use it, record, stop
 ├─ 2 compose two or more?          ── yes → record the chain, stop
 ├─ 3 acquire an external one?      ── yes → validate it, then use it, stop
 └─ 4 create a candidate            ── only when 1–3 each failed on evidence
```

`skill-discovery.md` covers rung 1. `compose-or-create.md` covers rung 2.

## The cost side of the ledger

A new skill is a permanent claim on the user's attention and on your own future
runs. Write both sides down before deciding.

| The skill buys | The skill costs |
|---|---|
| A procedure the reader does not re-derive | One more description competing for every selection |
| Consistency across runs | A second place to be wrong, forever |
| A named, testable, revisable unit | Test cases, a version, a provenance record |
| Encoded failure modes | Maintenance as the surrounding system changes |

A skill out of ACTIVE service still costs the first row. A skill that fires on
the wrong requests costs it twice: once in selection, and again in the reader's
attention spent on a process they did not need.

## The four checks

All four must resolve to *create* before you generate anything. Each has a
passing answer, and any other answer ends the design here.

1. **Recurrence.** Name the next two situations that need this, without
   stretching. If you can only reach the third by inventing it, the answer is a
   plan step.
2. **Coverage.** No existing skill covers the gap. A near-miss means extend, not
   create — see `skill-discovery.md`.
3. **Composability.** No chain of existing capabilities produces the same
   result. If one does, compose — see `compose-or-create.md`.
4. **Reusable capability.** The procedure generalises across inputs; you are
   capturing a *kind* of work, not this instance. If the description would have
   to name today's file, today's path, or today's bug, it is a one-off.

## Then write the design note

Six lines, before any file is created. It becomes the head of the provenance
record (`skill-provenance.md`) and the input to `skill-contract.md`: the name;
the scope, with the adjacent requests it is *not* for; a one-sentence purpose a
stranger could check; why now, with the evidence the earlier rungs failed; three
trigger queries that must fire and three that must not; and the observable
condition that says the skill is right.

## Stop conditions

Stop and record instead of designing when: the four checks do not all pass; the
procedure cannot be stated as a sequence of decisions; the skill would need an
authority no existing skill holds; or the trigger already belongs to a skill you
found. Rejecting a design at this stage is a normal outcome, not a failure — see
`skill-promotion.md`.
