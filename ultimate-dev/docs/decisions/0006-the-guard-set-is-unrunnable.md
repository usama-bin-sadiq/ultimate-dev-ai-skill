# 0006. The guard set is unrunnable, and that is the defect

Status: Accepted
Date: 2026-09-27
Deciders: architecture maintainers

## Context

The owner has said, repeatedly and correctly, that this skill performs badly on
simple tasks. The evaluation suite contains twenty-five must-not-fire guard cases
(`NM-*`, `TN-*`) written to measure exactly that.

They were run. Both arms, all twenty-five, 50 model calls, 411 seconds against
`opencode/space-bunny-free`. The result:

```text
runs 50 · decided 2 · passed 1 · failed 1
harness_failures 45 · environment_failures 0
negatives_decided 2 · min_decided_for_a_rate 30 · publishable FALSE
```

The harness correctly refused to publish a false-trigger rate, because two decided
cases cannot support one. That refusal is the system working.

**The cause is fixture coverage, not the skill.** `tools/build-fixtures.py`
registers fourteen fixture builders against one hundred and twenty-two cases.
Twenty-one of the twenty-five guard cases have no fixture, which accounts for 42
of the 45 harness failures. The guard cases were never runnable. They have been
described in this repository's own planning notes as "unrun", which implied they
were runnable and merely not yet run. They were not runnable.

This is the project's recurring defect, sixth instance, and it is the same one
found in decision records, in the dispatch table, and in a hand-written count: a
quantity was correct while the thing it counted was not. The count of eval cases
was 122. The count of *measurable* eval cases was 3 asserted and 16 runnable. The
first number was reported; the second was not.

**Nothing about effectiveness can be established until this is fixed.** The
paired result is 3/3 against 3/3 with zero discordant pairs — a null. The
false-trigger rate has a 95% upper bound of 63%, derived from five of thirty guard
cases ever having run. Both numbers are consequences of the same gap: the suite
reports case counts where it should report decidable-case counts.

## Decision

**Make the guard set runnable before importing anything, and report decidable-case
coverage rather than case coverage from now on.**

1. Every `NM-*` and `TN-*` case gets a fixture, or the case is removed from the
   suite with its removal recorded. A case that cannot run is a claim about
   behaviour with nothing behind it, which is the failure the whole kernel exists
   to prevent.
2. `RESULTS.md` reports, for every family: total cases, cases with a fixture,
   cases with an objective assertion, and cases actually decided in a run. The
   four numbers are different and conflating them is what produced the null.
3. `validate-skills.py` gains a check that every trigger-negative case resolves to
   a fixture. A guard case with no fixture is an error, not a warning, because it
   makes the false-trigger rate unmeasurable while appearing to measure it.
4. The guard set is re-run in both arms and the false-trigger rate is published
   only if at least thirty cases decide, per the threshold the harness already
   enforces.
5. Only after that number exists does the import decision in `0005` execute,
   because the import changes the description and the trigger boundary, and
   measuring the trigger before changing it is the only way to attribute any
   later change.

### Decision record

```text
DECISION
  question   sequencing: what is measured before what is built
  selected   build the missing guard fixtures, publish decidable-case coverage,
             re-run both arms, and hold the import until the trigger baseline
             exists
  rejected   (a) import first, measure afterwards -- rejected because the import
                 rewrites the description and the trigger surface, so a
                 measurement taken afterwards cannot attribute a trigger change
                 to the import or to anything else
             (b) author objective assertions for the guard cases instead of
                 fixtures -- rejected because the guard cases are must-not-fire
                 judgements about whether the kernel loaded at all; an assertion
                 cannot be evaluated until the run happens, and the run cannot
                 happen without a fixture
             (c) report the false-trigger rate over the two decided cases --
                 rejected outright; the harness already refuses it, and a rate
                 over n=2 is noise presented as a measurement
  rationale  the owner's complaint is about simple tasks; the guard set is the
             only instrument that measures it; the instrument is broken; fixing
             the instrument outranks using it indirectly
  confidence high in fixture coverage being the binding constraint, because the
             run output names it and the builder registry confirms it;
             medium in twenty-one fixtures being sufficient, since three guard
             cases may need a runtime rather than a file;
             low in the resulting false-trigger rate being acceptable -- if the
             skill over-triggers, this decision surfaces that rather than hiding
             it, which is the point
  cost       twenty-one fixture builders and one re-run; buys the first real
             measurement of the owner's actual complaint
  evidence   OBS-005, OBS-006
  recovery   if fixtures are built and the rate comes back high, the defect is in
             the kernel's description and trigger boundary, not in the harness;
             the import is then deferred again and the description is rewritten
             against the observed trigger failures
```

## Consequences

The suite will report fewer cases than it did. That is the point: a smaller
honest denominator beats a larger fictional one, and every prior null result in
this repository traces to the same confusion between the two.
