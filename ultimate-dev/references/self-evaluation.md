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

## The nine questions

Answer all nine at R3 and above. At R2, answer the first three and the last two.
At R0 and R1, this layer does not run — the process was short and determined.

| # | Question | A good answer names |
|---|---|---|
| 1 | Did this solve the task? | The criterion that holds, or the one that does not |
| 2 | Was the context necessary? | What was loaded and never used, and what would have changed without it |
| 3 | Was the reasoning sufficient? | Whether the rung was right, and what would have needed more or less |
| 4 | Was the strategy effective? | Whether the approach class was right, or only the execution |
| 5 | Were the capabilities appropriate? | Whether anything was created, composed, or acquired that was not needed |
| 6 | Was the verification adequate? | What no check covered, and whether that gap was load-bearing |
| 7 | What failed? | The failure, its classification, and whether the response was right |
| 8 | What could be reused? | A pattern worth a learning candidate, with the evidence it would need |
| 9 | What should not be repeated? | An approach that cost more than it returned |

Questions 2, 5, and 9 are the ones that catch waste. They are also the ones a run
skips, because waste is invisible from inside the run that caused it.

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

**Not delivered in full to the user.** Nine answers is a lot of attention to ask
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
- **Answering 8 and 9 and skipping 2 and 5.** The two that catch waste, dropped
  because they are the two that indict the run.
- **Treating self-evaluation as self-criticism of the answer.** Different
  question, and conflating them produces either duplicate verification or a review
  of nothing.

Cross-reference `verification-system.md` for checking the result,
`learning-system.md` for what happens to questions 8 and 9, `budget-system.md` for
the cost accounting question 2 feeds, and `decision-ledger.md` for the record this
layer reviews.
