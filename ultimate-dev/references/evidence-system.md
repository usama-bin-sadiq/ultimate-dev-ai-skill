# Evidence system

Evidence is not material you have gathered; it is material that bears on the
specific claim you are about to make. Ask what would have to be false for that
claim to be false. If nothing could be, you have a fact, not a claim, and you are
about to overstate it.

## What counts as evidence

| Input | Verdict |
|---|---|
| an observation you ran and saw, bearing on the claim | evidence, at the strength in the hierarchy below |
| a document describing the system, for a claim about its actual behaviour | not evidence; C4 material to be checked against reality |
| a test that passes without exercising the changed path, or errors before its assertion | not evidence for that path; an unknown |
| your own prior conclusion, repeated | not evidence; a restatement |

## Strength hierarchy

Move up only by adding an independent observation, and never describe a weak rung
with the vocabulary of a strong one.

| Rung | Form | What it buys | What it does not buy |
|---|---|---|---|
| 1 | **Unverified assertion** | a hypothesis to test | nothing on its own |
| 2 | **Single observation** | one data point | generality, or that the observation was typical |
| 3 | **Tool-confirmed observation** | the check actually ran and its output is what you think | correctness of the check itself |
| 4 | **Repeated observation** | the result is stable across runs, inputs, or order | that the method is sound |
| 5 | **Independent corroboration** | a second, differently-derived line agrees | proof; it raises confidence to the level the stakes allow |

Two sources are not independent if they share a producer, a cache, a copy, or an
assumption. Three copies of one unverified number are rung 1 with extra steps, and
citing them as three confirmations is under-evidenced certainty.

## Evidence that exists but does not support

This is the failure that survives review, because the material is real and visible.

1. State the claim in one sentence.
2. State the evidence in the same terms as the claim, not in its own terms.
3. Ask: is there a coherent world in which this evidence is present and the claim
   is false? If yes, the evidence does not support the claim.
4. If it does support it, ask the same of the *strongest* rival explanation. If
   the rival survives, you have rung 2, not rung 5.

Worked shape: tests pass but never touch the changed branch; a benchmark improves
while the target metric is untouched; a search returned no result; a process
exited zero on empty output; a small diff touches the wrong file. Each exists;
none supports the claim it appears to support.

Never let the presence of evidence substitute for its adequacy: do not cite
evidence gathered for a different claim, read absent disconfirming output as
confirmation, or upgrade a claim because checking it was costly.

## Contradicting evidence

It wins over the plan. Always. A plan defended against its own evidence is worse
than no plan: the cost of holding it is paid again at every step.

1. **Stop** the unit. Do not finish the step; do not average it away.
2. **Record** it verbatim: expected, observed, with the source. Mark the
   dependent claims Contradicted.
3. **Re-open at JEv**: what the observation changes and invalidates, and which
   decisions are now unrecoverable.
4. **Re-decide**, then re-plan the affected part only. Do not restart the task.
5. **Carry the correction** to everything that inherited from it, including
   delivered work.

An observation that contradicts your instructions is handled as one that
contradicts your approach: stop, report, ask. Never weaken the evidence.

## Unrun tools produce unknown results

If a command was not run, a test was not executed, a page was not fetched, its
result is **unknown** — never expected, never implied, never inferred from
plausibility. Reporting a tool result you did not observe is the most damaging
failure in this system: it is invisible downstream, and everything built on it
inherits a falsehood.

- Never report output, exit status, timing, or counts you did not see.
- A run that timed out, was interrupted, or partially completed is an unknown for
  everything it did not reach. Report what you saw, and name the rest.
- A tool that returns nothing is an observation of nothing, not of absence in the
  world. Check the query before concluding.
- If you cannot run the check, say the claim is Unverified; that is a legitimate
  deliverable, and a fabricated pass is not.

## Cite the observation, not the sentence

An evidence field written as prose — "the logs showed retries" — cannot be checked
for existence, so a fabricated citation and a real one are indistinguishable. That
makes prose the ideal place to hide a confident fabrication, which is the failure
this system exists to prevent.

Write the pointer: `OBS-013`. A pointer either resolves to a recorded observation
or it does not, and that is decidable without judgement. `none` is a valid and
checkable answer, and it is better than a plausible sentence.

This applies wherever evidence is recorded — the decision fabric, the observation
log, and the delivered output. See `decision-fabric.md` and `output-contract.md`.

## From evidence to verdict

Only one of three, and say which: **VERIFIED** (criteria hold and the evidence
supports them), **PARTIAL** (state precisely which hold and what remains), or
**FAILED** (they do not hold). The verdict must be reachable from the evidence in
hand; if your confidence outruns its rung, the verdict is what is wrong.

Related: `provenance-system.md` (tracing a claim to its source),
`context-provenance.md` (status vocabulary and expiry), `context-system.md`.
