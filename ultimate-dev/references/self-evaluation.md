# Self-Evaluation

The layer between verifying the work and delivering it. Verification asks *is the
result correct?*; self-evaluation asks *was the way we got here right?*

The second question is the one that improves the next run, and it is the one
routinely skipped — because the result is in hand, the deadline is now, and
reviewing your own process feels like a waste of the user's remaining attention.
Skipping it is why the same failure recurs with a different symptom.

It is also the layer with the worst incentive problem in the whole architecture.
The agent that produced the work is the agent judging the work, and a self-report
of "that went well" is worthless. So the output of this layer is not a verdict. It
is a set of specific answers that a reader can check.

## The fifteen questions

These are §45's fifteen, and `reflect` is the same list in state — all fifteen or
none, recorded before delivery rather than recalled afterwards:

```sh
python3 tools/run-state.py reflect --list
python3 tools/run-state.py reflect --answer "<question>=<answer>" --answer ...
```

The table below says what each one is *for*. It is not a second list to work
from: the command is the list, and this is the reasoning behind it.

| # | Question | A good answer names |
|---|---|---|
| 1 | Did we solve the task? | The criterion that holds, or the one that does not |
| 2 | Did we execute the required work? | Which units ran, and which were never opened |
| 3 | Did we use the correct capabilities? | Whether anything was created or acquired that was not needed |
| 4 | Did we invoke selected agents? | The capabilities that were selected and never invoked |
| 5 | Did we acquire context only when needed? | What was loaded and never used, and what would have changed without it |
| 6 | Was context sufficient? | What was missing, and whether it was a gap or a blocker |
| 7 | Was verification sufficient? | What no check covered, and whether that gap was load-bearing |
| 8 | Did we recover from failures? | Each failure, its classification, and whether the response was right |
| 9 | Did we unnecessarily load context? | The load that bought nothing this run needed |
| 10 | Did we unnecessarily delegate? | An approach that cost more than it returned |
| 11 | Did we under-delegate? | A capability the run was built around and stopped using |
| 12 | Did coordination fit the task? | The mode used, and whether a cheaper one would have done |
| 13 | Are any required work units incomplete? | The specific open units, by number |
| 14 | Is the blocker genuine? | Which of the five stop conditions holds, and which do not |
| 15 | Can anything else still be executed? | The next executable action, or that there is none |

Questions 9, 10, and 11 are the ones that catch waste, and 10 and 11 catch opposite
failures. Question 12 catches the mode case: loading four skills to answer a
one-line question, or handing off a thread one agent could have held, is isolation
nobody needed — and question 11 is the one that says a run can pay for that and
then do everything inline anyway, which feels compliant precisely because it is.

`reflect` refuses fifteen answers that name no fault. That is the one property of
this layer a command can check, and it is the right one: a favourable review of
your own run is worth nothing, whatever the wording. The rule is narrower than it
looks, in both directions.

A **verdict is not a finding**. Fifteen answers of the single word "no" are
fifteen verdicts and not one fault, and the first version of this check accepted
exactly that. So a finding has to say something: it has to open on a negation
*and* carry at least eight words after it, or open on a concession — `but`,
`however`, `although`, `except`, `despite`, `under-delegated` — and carry eight
words after that.

A **finding need not open the sentence**, and requiring it to was the same
mistake pointing the other way. Because most of what a run did was fine, the
honest shape of "mostly yes, except for this" is a positive first word and a
concession after it, and a floor that only reads a front negation refuses it.
That does not make a run write a false negative in order to satisfy a gate; it
makes the gate read what was written. "Yes, but the count of the gated rows was
self-reported" is a fault, and the check has to be able to see it.

No score is recorded, because a score invites optimisation and the output of
this layer is faults, not a mark. `--why` is the escape hatch for the run that
genuinely looked and found nothing: it skips the floor rather than fabricating a
finding to clear it.

## What counts as an answer

The table above says what a good answer *names*. It does not say what makes an
answer good, and without that the layer is unfalsifiable: "the reasoning was
sufficient" satisfies every question here, and so does the sentence written by a
run that learned nothing.

An answer counts when it is **falsifiable by a reader who disagrees**. Three
tests, and an answer needs all three:

1. **It names a specific thing.** Not "the context was mostly necessary" but
   "thirty of thirty-six files loaded were never read; the decision needed four".
   A claim with no count, no name, and no consequence is a mood.
2. **It could come out the other way.** "I did not check whether verification
   covered the rollback path" is a real answer and may be wrong in the run's
   favour. "The verification was thorough" cannot be wrong, which is the tell.
3. **It is separated into what was noticed and what was checked.** An unchecked
   thing is not a passed thing. Asserting that the untested path was fine is the
   failure this layer exists to catch, and it is the one an agent is most
   inclined to produce, because the run feels smooth.

**A run that answers all fifteen favourably has not passed this layer.** It has
demonstrated that the questions are easy to satisfy without thinking, which is a
finding about the layer rather than a result. Two or three findings against your
own run is the expected output; zero is a signal to look harder, not a
certificate. This is the property `reflect` checks.

That is the whole criterion, and it is deliberately not a score. There is no
fifteen-out-of-fifteen, and a rubric that rewards a high total rewards the thing
this layer is trying to prevent: a uniformly positive self-assessment, which
trains the reader to skip the section and is worthless in a specific way.

## The three that actually change behaviour

**Question 2 — was the context necessary?** This is the anti-over-orchestration
instrument. A run that loaded forty files and used six has found the mechanism by
which it will over-orchestrate next time. The answer is uncomfortable precisely when
it is useful.

**Question 5 — were the capabilities appropriate?** Every capability created,
composed, or acquired is a permanent cost: a description that competes for future
triggers, and something to maintain. A run that created a skill and does not say
so has hidden its own most consequential side effect.

**Question 9 — what should not be repeated?** The negative case, which is the only
one that prevents a loop. If the same approach fails twice, the answer to question
9 is that approach, and it belongs in the delivery rather than in a private note.

## What this layer is not

**Not self-criticism of the output.** That is verification, and re-reading your
own work adds no information — it shares every blind spot with what it is checking.
This layer reviews the *process*, which verification cannot see, because
verification only looks at whether the answer came out right.

**Not a confidence update.** Confidence describes the result. This describes the
run. A correct result from an unsound process is a warning, not a success, and it
is the case most likely to fail differently next time.

**Not delivered in full to the user.** Ten answers is a lot of attention to ask
for. What belongs in the delivery is question 9 and anything from questions 2, 5,
or 7 that the user would want to know. The rest is the run's own record, and its
purpose is the next run.

## Answering honestly

The failure mode is a uniformly positive self-assessment, and it is worthless in a
specific way: it trains the reader to skip the section. A run whose
self-evaluation never finds fault is not reflecting carefully.

Two disciplines make it usable:

- **Name the specific thing.** "The context was mostly necessary" is a claim no one
  can check. "Thirty of thirty-six files loaded were never read; the decision
  needed four" is a finding.
- **Separate what you noticed from what you checked.** If the honest answer is "I
  did not check whether the verification covered the migration rollback path", say
  that rather than asserting the path was fine. An unchecked thing is not a passed
  thing.

## Relationship to learning

Questions 8 and 9 are the only input to the learning lifecycle. Neither produces a
promotion; both produce a **candidate**, and a candidate needs the generalisation
evidence in `learning-system.md` before it can become behaviour.

The most common misuse is treating a good answer to question 8 as licence to
install a rule. One run noticing a pattern is exactly the situation
`learning-safety.md` exists to constrain — and note the self-conditioning risk in
that file: a conclusion this run reached, checked by this run, is the weakest
available source, and the weakest case for retention is the one that feels most
like insight.

## Anti-patterns

- **The uniformly positive review.** Every answer favourable, which makes the
  section decorative.
- **Critiquing the result instead of the process.** Verification's job, done badly.
- **The private ledger.** Findings recorded and never surfaced, so the reader
  cannot act on them and the next run cannot inherit them.
- **Answering 8 and 9 and skipping 2, 5, and 10.** The ones that catch waste,
  dropped because they are the ones that indict the run.
- **Treating self-evaluation as self-criticism of the answer.** Different
  question, and conflating them produces either duplicate verification or a review
  of nothing.

Cross-reference `verification-system.md` for checking the result,
`learning-system.md` for what happens to questions 8 and 9, `budget-system.md` for
the cost accounting question 2 feeds, and `decision-ledger.md` for the record this
layer reviews.
