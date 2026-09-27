# Output Contract

The deliverable is not the work; it is the work **plus what a reader needs to
decide how far to trust it**. A correct answer with a hidden limitation is a
partially deceptive answer, because the reader has no way to know which part to
distrust.

Every field below is required at R2 and above, and proportionally lighter below —
but `outcome` and the statement of limitations are never omitted.

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
