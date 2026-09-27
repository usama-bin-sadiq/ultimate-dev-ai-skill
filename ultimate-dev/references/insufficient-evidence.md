# Insufficient Evidence

The most dangerous condition in the system is not missing capability — that is
visible and produces a clean "I cannot do this". It is proceeding to act when
the evidence does not support the claim. The work looks identical from the
outside. The difference is that the conclusion is unfounded.

Missing evidence is a **first-class state**, and reporting it is a success, not a
failure.

## The two questions

Keep them separate. They fail differently and are fixed differently.

1. **Is there enough evidence to act?** — can I proceed at all?
2. **Does the evidence support this specific claim?** — can I state *that*?

An answer can be true, well-supported, and still rest on a gap you have not
noticed. Answering only the first question is how confident nonsense is produced.

## The states

Use the vocabulary from `provenance-system.md`, and keep the qualifier attached
to the claim it qualifies. Dropping it is how an assumption becomes a fact in the
reader's mind without any step in between.

| Status | Meaning |
|---|---|
| **Known** | Directly observed or deterministically computed |
| **Inferred** | Derived from known facts by a stated reasoning step |
| **Assumed** | Taken as true without checking; consequence if false recorded |
| **Unverified** | Believed, with no check performed yet |
| **Uncertain** | Evidence exists but does not settle it |
| **Contradicted** | Evidence exists and disagrees — resolve before proceeding |

The failure is never the existence of an `Assumed` or `Unverified` claim. The
failure is an `Assumed` claim presented without its qualifier, so the reader
cannot tell it apart from a `Known` one.

## Required strength

Evidence must be strong enough for the claim, and the claim must be no stronger
than the evidence. Both halves fail in practice.

| Claim | Minimum acceptable evidence |
|---|---|
| A file was changed | Observe the change, not infer it from intent |
| Code works | Execute it, or state that it was not executed |
| Tests pass | Observe the run and its exit status |
| An external fact holds | A source you actually retrieved and read |
| A number is correct | Deterministic computation, not recall |
| A design is sound | Reasoning stated explicitly, assumptions named |

Note the recurring shape: **a claim about an action requires observing the
action.** Intention is not observation, and a plan that reads correctly is not
evidence that it was carried out.

## Contradicting evidence

When evidence disagrees with the plan, the evidence wins. Always.

1. Stop treating the plan as authoritative.
2. Record the contradiction as an observation, with its source.
3. Re-decide at JEv: is the plan wrong, or is the evidence wrong?
4. Re-plan only the affected part.
5. If the contradiction cannot be resolved, report it as unresolved — do not pick
   the convenient side.

Suppressing a contradiction because it is inconvenient is how a system ends up
confidently delivering the thing it was told not to build. An unresolved
contradiction reported honestly is worth more than a resolved one reached by
ignoring the inconvenient half.

## The gap between evidence and certainty

The characteristic error is stating a claim whose evidence does not reach it:

- "The API returns a list" when a single response was observed and pagination is
  undocumented.
- "This is safe" when it was reasoned about but never tested against an attack.
- "It works on Windows" when it was tested on one other platform.
- "The tests pass" when the suite was written after the code and passes by
  construction.

Each is a small step, and each is the same failure. The claim has outrun its
evidence, and the qualifier that would fix it is the part that got dropped.

## When evidence cannot be obtained

Sometimes there is none, and the work still has to proceed. Then:

- name the gap explicitly in the deliverable's **Limitations** field;
- state what the conclusion assumes as a result;
- lower the confidence accordingly — `low` is the accurate answer;
- do not upgrade the claim's language to compensate. Confident phrasing over thin
  evidence is the failure, not the remedy for it.

## Sibling references

`evidence-system.md` for what counts as evidence and the strength hierarchy,
`verification-system.md` for producing a verdict, `provenance-system.md` for
tracking each claim's chain, `unknown-domain.md` for the acquisition procedure
when you have no prior, and `escalation.md` for when an unclosable gap must
reach the human.
