# Strategy System

A strategy is the **shape** of the approach, chosen at JEv — not a workflow you
follow and not a template you load. There is no default and no best strategy:
there is the one whose expected outcome justifies its cost, risk and residual
uncertainty, recorded together with what you rejected.

## The disqualifying question

Before selecting, ask: **is the approach even known, or am I choosing between
guesses?**

If it is not known, strategy selection is impossible. Stop selecting and acquire
the knowledge: read the domain, find the prior art, run one small probe.
Choosing an elaborate strategy over an unknown problem produces an elaborate
failure. Record that finding as the boundary; it is what `research-first` below
exists for.

## The candidate set

| Strategy | Choose when | Avoid when |
|---|---|---|
| **Direct** | The next action is already determined and the job is one step | Success needs several dependent parts |
| **Decomposition** | The objective holds separable sub-problems, each with its own success criteria | Parts share mutable state, so "separable" is false |
| **Sequential** | Each step consumes the previous step's output | Steps are independent — you are buying latency for nothing |
| **Parallel** | Units are genuinely independent, failure is contained, and wall-clock matters | Units contend for one resource, share state, or a later unit must see every earlier result |
| **Iterative** | The output improves against a measure you can read and stopping is definable | No measure of improvement exists — you are looping on a feeling |
| **Recursive** | One rule genuinely repeats at a new depth, on new data | The repetition is a coincidence of shape; depth is unbounded |
| **Research-first** | The approach is unknown or the vocabulary is unfamiliar | You already know the answer and only want to produce it |
| **Evidence-first** | A claim drives downstream work, or the result is externally visible | Nothing is load-bearing yet |
| **Experiment-driven** | The mechanism is contested or the environment unknown, and a cheap probe discriminates between explanations | The probe costs more than the answer, or is not reversible |

## Selecting: expected outcome against cost

Score candidates on **expected outcome per unit of cost, risk and uncertainty**.
Three ways to get the scoring wrong:

- **Minimising calls.** Fewer tool calls is not a good strategy; it is a cheaper
  route to an unverified answer. Paying more to avoid a costly failure is the
  correct trade, not an overrun.
- **Optimising only the visible cost.** Counted cost is not paid cost. A cheap
  action that destroys state is not cheap.
- **Treating confidence as evidence.** Certainty you feel is not support. Score
  the evidence, not the feeling.

Weight consequence explicitly. An irreversible or externally visible action
earns a slower strategy however obvious the immediate step looks.

## Strategies are provisional

A strategy is a hypothesis about the shape of the work, held at a stated
confidence. When observation contradicts it:

1. Stop the approach at the next unit boundary; do not finish the unit in the
   old shape.
2. Return to JEv and write a **decision record**: what changed, what you now
   believe, what you reject, and the condition that would reverse this decision.
3. Re-plan only the affected part. A wrong strategy for unit 7 does not
   invalidate units 1–6.
4. If a failed assumption is the cause, correct it and re-plan every unit that
   depended on it — and name those units.

Silently switching strategies is worse than choosing badly, because it leaves
the record inconsistent with the work. See `planning-system.md` for re-planning,
`observation-system.md` for what counts as a contradiction, and
`decision-fabric.md` for the record fields.

## Prohibitions

- **No strategy by default.** If you cannot name the rejected alternative, you
  did not choose. See `decision-fabric.md`.
- **No inherited strategy without a check.** One that worked on a similar task
  is a candidate, not a decision. Ask whether the similarity reaches the
  load-bearing part.
- **No decomposition past verifiability.** A unit too fine to verify is not
  progress; it is unverifiable motion.
- **No permanent commitment.** A strategy defended against its own evidence is
  worse than having had none.

The rung governs how much strategy deliberation is warranted at all. At R0 the
correct strategy is usually "direct", and spending this page to confirm it is the
waste `reasoning-system.md` calls difficulty worship.
