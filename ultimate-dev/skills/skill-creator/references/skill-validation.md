# Skill validation

Validation is a judgement, not a check. A mechanical pass proves the files are
well-formed; it answers none of the seven questions below, and a skill that has
passed a validator is still an untested claim.

A finding is **recorded, not summarised away**. "Mostly fine", "looked good", and
"one concern" are not verdicts.

## The seven questions

| # | Question | The test that answers it | Fails when |
|---|---|---|---|
| 1 | **Correctness** | Derive the result a second, independent way for one named case and compare. | The only evidence is the run that produced it. Evidence that exists is not evidence that supports. |
| 2 | **Completeness** | List every way you could make it fail. Each must appear in the contract's failure modes with a response. | You find a way to break it that the spec does not name. |
| 3 | **Applicability** | Run the trigger positives and the negative set. Confirm it fires when it should and stays quiet when it should not. | It misses a positive, or the negatives are unmeasured. Unmeasured is not a pass. |
| 4 | **Ambiguity** | Find one step with no decision. Ask what a competent reader would do differently. | Two competent readers would do different things and both be right. |
| 5 | **Failure behaviour** | Run an adversarial case and check that the response the spec names actually appears. | It improvises, retries blindly, or reports success on a failed step. |
| 6 | **Interaction** | Run the interaction cases against every near neighbour. Confirm one owner per request. | Two skills claim the same request, or a composition was missed (`compose-or-create.md`). |
| 7 | **Security** | The full review in `skill-security.md`. | Any finding at all, and no verdict in the other six overrides it. |

Question 7 is delegated. Do not answer it here, and do not treat a clean run of
1–6 as partial credit on it.

## Verdicts

Record one verdict per question, with the evidence that produced it.

| Verdict | Meaning | Consequence |
|---|---|---|
| `PASS` | The test ran and the answer held | Proceed to the next question |
| `FAIL` | The test ran and the answer did not hold | Named defect; return to CANDIDATE |
| `UNANSWERED` | The test could not be run, or the evidence was never gathered | Blocks promotion exactly as `FAIL` does |

An unanswered question is not a neutral one. A candidate promoted with any
`UNANSWERED` was promoted on assumption, which is the failure this engine exists
to prevent.

## What the tools decide, and what you decide

- `grade.py` decides assertions. It reports per-assertion verdicts and a pass
  rate; `manual` assertions are recorded as undecided and excluded, so a
  subjective judgement never inflates a score.
- `run_eval.py` produces the runs; `aggregate_benchmark.py` produces means,
  variance, and — with two configurations — a delta.
- `quick_validate.py` proves structure.

None of these answers questions 1, 4, 5, or 7. Those are yours. Do not report a
pass rate as validation, and do not let a green validator stand in for
question 3: applicability is measured by trigger behaviour, which is a different
number from the pass rate.

## The record

For each question: the question, the test you ran, the observed answer, the
evidence, and the verdict. A finding carries the same fields, plus what would
resolve it and which state the candidate returns to. Keep the failures — they are
the most useful part of the record, and they are the input to the revise
disposition in `skill-promotion.md`.

## Stop conditions

Stop at the first `FAIL`: fix the named defect, return to CANDIDATE, and re-run
the questions the defect touches. Stop with no promotion at all while any
question is `UNANSWERED`. Stop and reject outright when a defect cannot be
repaired without widening authority, or when the seventh question has an
outright disqualifier.
