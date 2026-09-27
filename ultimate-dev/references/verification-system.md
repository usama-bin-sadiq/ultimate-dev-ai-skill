# Verification System

Ask: **what must be true for this result to be trusted?** Then check that, and
nothing else. Verification answers a question; it is not a ritual, and the depth
it takes is set by risk, consequence, uncertainty, novelty and evidence quality —
never by the size of the deliverable.

## Proportionality

A low-stakes, well-understood, tool-confirmed result does not need a review
panel. A novel, high-consequence one does not get a glance. Scale the depth to:

- **Risk and consequence** — who absorbs the failure, and how badly.
- **Uncertainty** — how much of the result rests on unexamined assumptions.
- **Novelty** — whether this path has ever produced a trustworthy result before.
- **Evidence quality** — tool output beats inference; inference beats recollection.
- **Reversibility** — if it cannot be undone cheaply, verify before acting, not
  after.

Check the stated criteria and stop. Extra checks cost attention and can bury the
finding that mattered; a verification pass that produces six observations and no
verdict has failed at its job.

## Three kinds, in increasing strength

| Kind | Question | It fails when |
|---|---|---|
| **Evidence check** | Does the evidence actually support the claim, or does it merely exist? | A file exists, a command ran, a test was written — none of which shows the claim holds |
| **Validation check** | Does the result meet the stated success criteria? | It does what was intended, but not what was required |
| **Independent check** | Would this survive being derived a different way? | Only one derivation exists, so a systematic error in it is invisible |

An evidence check that passes is the minimum bar, not the goal. Most confident
errors pass an evidence check and fail an independent one, because the
underlying mistake is shared by every path that looked at it the same way.

## The three verdicts

Decide one, and say which:

- **VERIFIED** — the criteria hold and the evidence supports them. Name the
  criteria and the evidence.
- **PARTIAL** — some hold. State precisely which criteria hold, which do not,
  and what remains to be done.
- **FAILED** — they do not hold. Treat it as a real failure of the work, not of
  the check, and return to JEv.

`PARTIAL` is a real verdict and must be delivered as one. Reporting PARTIAL as
success is the failure. So is the opposite error: discarding sound, verified work
because one criterion failed, when the honest report is the two results and the
one gap. Say what is solid, say what is not, and hand both over.

Never soften a verdict to fit the shape of the answer you wanted. A verdict with
no confidence and no evidence attached is not a verdict, it is a mood.

## Depth by rung

| Rung | Depth required | Typical form |
|---|---|---|
| **R0** | Output check only | Did the action produce the output? One direct check, no record |
| **R1** | Per-step check | Each step checked as it completes; nothing carried on trust |
| **R2** | Evidence check per work unit | Unit result checked against its expected result and success criteria |
| **R3** | Evidence + validation, plus independent check on the load-bearing result | Derive the key claim a second way and compare |
| **R4** | R3 plus an independent check by someone or something that did not produce the first derivation, before delivery | Named reviewer, different route, disagreements recorded rather than averaged away |

The rung is a floor, so a genuinely easy task does not climb it. But R4 work
verified only by the effort that produced it is unverified: assurance is a
property of the check, not of the care behind the work.

## Rules of application

- Verify the **result**, not the process. A clean run of the right commands is
  not evidence the right thing happened.
- Verify before delivery, and for R4 before acting. After-the-fact verification
  of an irreversible action is a post-mortem.
- A check that cannot fail proves nothing. If a check cannot distinguish success
  from failure, it is not a check; make it discriminating or report the result as
  unverified.
- State what you could **not** establish. A limitation named plainly is worth
  more than a confident answer that hides one, because it tells the reader where
  not to trust you. See `output-contract.md`.
- When verification fails, re-enter at JEv. Do not adjust the criteria to match
  the result; a criterion changed after the fact is a new claim, and it needs a
  new decision record.

## Prohibitions

- No verdict without observed evidence behind it.
- No evidence check presented as an independent one.
- No PARTIAL reported as VERIFIED because the result is "mostly fine".
- No discarding verified work to make a verdict tidier.
- No verification theatre at R0.

See `evidence-system.md` for what makes evidence support a claim,
`observation-system.md` for producing evidence, `state-system.md` for recording
the verdict, and `reasoning-system.md` for the rung that sets the floor.
