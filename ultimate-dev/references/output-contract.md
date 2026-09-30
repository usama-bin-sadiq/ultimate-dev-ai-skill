# Output Contract

The deliverable is not the work; it is the work **plus what a reader needs to
decide how far to trust it**. A correct answer with a hidden limitation is a
partially deceptive answer, because the reader has no way to know which part to
distrust.

Every field below is required at R2 and above, and proportionally lighter below —
but `outcome` and the statement of limitations are never omitted.

## Four statuses, four templates

The fields above are the shape of a delivery. The status is a claim about the run,
and it has exactly four values. Which one you may use is a rule, not a preference.

| Status | Only when | Never |
|---|---|---|
| `COMPLETED` | every required unit is done and every criterion is satisfied | because the deliverable exists |
| `PARTIAL` | useful execution genuinely occurred **and** required work remains | because execution became inconvenient |
| `BLOCKED` | a required dependency prevents further execution, after the routes are walked | because a capability was not found |
| `FAILED` | execution was attempted and did not succeed, after reasonable recovery | as a synonym for blocked |

`FAILED` means *tried and unsuccessful*. `BLOCKED` means *a required dependency
stops further execution*. A run that tried three approaches and exhausted them
failed; a run that cannot proceed because a dependency is absent is blocked; and
conflating them hides which of the two happened.

```text
Status: COMPLETED

Process:   P01 … P16
Result:    what was produced, and where it is
Verification: what was checked, and the evidence for each
State:     completed
Remaining: None
```

```text
Status: PARTIAL

Completed:  what genuinely got done
Remaining:  what did not, specifically
Recovery attempted: what was tried, and what it showed
Next executable action: the first route that is still open
```

Then keep executing whenever one is open. A `PARTIAL` delivery is a progress
report, not a conclusion.

```text
Status: BLOCKED

Blocked:    the specific part that cannot proceed
Why:        the dependency that is absent
Attempted:  what was tried
Alternative paths attempted: which of the routes were walked
Missing dependency: the named resource
What would unblock it: the condition, not the wish
```

A blocker must be evidence-based. "What would unblock it" is the field that
separates a finding from a surrender, and it is the one most often left empty.

```text
Status: FAILED

Attempted:  what was tried
Recovery:   the routes walked, and their outcomes
Why it failed: the failure that survived recovery
What remains: the state the work is in
```

## And the one that does not belong here

A delivery whose first line is one of the intermediate states — *I identified the
skill*, *I need more context*, *the first attempt failed* — is not any of the
four. It is a run that stopped, described as a result. `run-state.py audit`
refuses it, and the fix is to record which of the two conditions of the hard
rules actually holds, not to reword. `completion-law.md`.

## The fields

In this order. The ordering is the argument: what happened, why believe it, what
it assumed, where it stops, how much to trust it.

| Field | Content | Omit when |
|---|---|---|
| **Outcome** | What was delivered, first, before any explanation | never |
| **Evidence** | What was actually observed that supports it — commands run and their results, files changed, tests passed. Cite observations, not prose | the rung makes it noise |
| **Assumptions** | What was taken as true, and what breaks if false | none were made |
| **Limitations** | What could not be established, and why | nothing — but say so explicitly |
| **Confidence** | high / medium / low, **naming what it is about**, with the reason | never |
| **Verification** | VERIFIED / PARTIAL / FAILED, the criteria checked, and the evidence for each | never |
| **Cost** | Effort spent; any scope reduction; any figure that was unmeasured | nothing spent worth stating |

## The three that carry the weight

**Limitations.** State what you could not establish. A limitation named plainly is
worth more than a confident answer that hides one, because it tells the reader
exactly where not to trust you — which is the only thing that makes the rest of
the answer usable. "I could not verify the behaviour on the target platform; the
test suite runs only on the host" is a better deliverable than silence, because
silence reads as verified.

**Verification status.** One of the three verdicts, always named. `PARTIAL` is a
real verdict and the most commonly misreported one: reporting PARTIAL as success
is the failure, and so is discarding sound work because one criterion failed. If
some criteria hold, say which, and say what remains.

**Assumptions.** Any assumption still load-bearing in the delivered result. If a
reader must know what was never checked, this is where it goes.

## Evidence means observed

Evidence is what you saw, not what you expect.

- A command was run and returned exit code 0 — say that.
- A command was not run — its outcome is unknown, and must not appear as evidence.
- A test suite exists — that is not evidence that it passed.
- A citation resolves to a claim — say which claim.

**Never report a tool result you did not observe.** This is the single most
damaging failure in the system, because it is invisible downstream: everything
built on the fabricated result is also fabricated, and the reader has no signal
to stop trusting. See `evidence-system.md` and `observation-system.md`.

## Calibration of confidence

| Confidence | Means |
|---|---|
| **high** | Criteria met, evidence tool-confirmed, assumptions either verified or not load-bearing |
| **medium** | Criteria met, but resting on at least one unverified assumption or partial evidence |
| **low** | Criteria not all met, or the evidence is thin — say so plainly rather than rounding up |

Confidence is about *your* epistemic position, not about how the work feels. If
you are guessing, `low` is the accurate answer and the useful one.

## Scaling to the rung

| Rung | Shape |
|---|---|
| R0 | Outcome. One line of limitations if any. |
| R1 | Outcome, evidence, verdict. |
| R2+ | All fields. |
| R3+ | Plus the decision ledger's material calls and any scope reduction. |

The point of scaling is not brevity for its own sake — it is that a reader's
attention is finite, and a 400-word report on a one-line fix is unread, therefore
useless.

## The four endings, and the record that has to match

The status is not a tone choice. It is a claim about the world, and it is the one
the reader will act on, so the state records it before the delivery is written
and `audit` reads the delivery against it.

| Status | Means | Carries |
|---|---|---|
| `completed` | Criteria met, verification passed, nothing outstanding | — (and it is refused unless all four of §35's conditions hold) |
| `partial` | Some work genuinely happened, required work remains | what remains, what recovery was tried, the next executable action |
| `blocked` | A dependency prevents further execution | what is blocked, why, what was attempted, the routes tried, what would unblock it |
| `failed` | Execution was attempted and did not succeed | what was attempted, what recovery was tried, the next action |

`failed` and `blocked` are opposite claims and are kept apart. `failed` means the
work was tried and lost; `blocked` means a dependency prevented it. Conflating
them is how "it did not work" gets reported as "it could not be done", and each
carries a different next move.

`partial` is only for work that genuinely happened. A run that never started
anything is `failed`, and a run that started and got there is `completed` —
`partial` is for the middle, which is the only place a reader who was not
watching needs detail.

Before delivery, record the process, then the ending, then read the result back:

```sh
python3 tools/run-state.py reflect --list          # §45's fifteen, all or none
python3 tools/run-state.py finish --status <one of four> [--remaining "..."]
python3 tools/run-state.py audit [--trivially]     # reads what the user receives
```

They are complements rather than duplicates, and a run that skips the first and
does the second still gets caught — the delivery is the thing that matters.

`audit` reads five sections: **Process**, **Result**, **Verification**,
**State**, **Remaining**. §47 asks for the headings and nothing checked their
presence, so a delivery could be fluent, correct, and missing half of what the
reader needs to judge it. `--trivially` is the exemption: a one-line answer is
not asked to carry five headings, and the same rung argument that removes a
field below R2 removes these. What `audit` refuses is a delivery that opens on a
named terminal justification ("this is as far as I can take it"), one that pairs
a non-action with a block conclusion, and one missing a section.

`reflect` runs before all three. It is the only one that is about the run rather
than the result, and it is the one most often skipped, because the result is in
hand and the deadline is now.

## Anti-patterns in delivery

- **Hedging everything.** Uniform low confidence trains a reader to ignore the
  confidence field, which destroys its value. Calibrate, including saying *high*
  when it is warranted.
- **Burying the failure.** Leading with method and ending with a caveat that the
  approach did not work. Lead with the outcome, including a failed one.
- **Padding with process.** The reader wants the result and its trustworthiness,
  not a narration of the plan.
- **Silent scope reduction.** Delivering 80% as though it were 100%. If budget
  forced a cut, the `Cost` field says so.
- **Fabricated completeness.** Presenting untested code as finished work, or a
  summary as though it were the deliverable.

See `verification-system.md` for producing the verdict, `provenance-system.md`
for the traceability chain behind the evidence field, and `anti-patterns.md` for
the failure modes this contract exists to prevent.
