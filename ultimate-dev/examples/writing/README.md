# Writing traces

Two objectives, and the interesting one is not the longer. A request to "make the
install section clearer" turns out to be already done, and the correct response is
three sentences and one factual fix. A request to write a postmortem turns out to
contain a reporter's account that the logs contradict, and the correct response is
a claims table.

Writing is where under-evidenced certainty is cheapest to produce and hardest to
spot. A postmortem reads as authoritative precisely because it is a document. Both
traces are about what happens when a document's fluency outruns its evidence.

## Kernel mechanisms stressed

- **Over-orchestration avoided at the hardest moment.** `r0-readme-install-section.md`
  is R0, and its content is mostly what was *not* done: no reader research, no
  documentation style guide, no clarity checklist, no skill.
- **A claim table before a draft.** The postmortem's structure is a list of claims
  with provenance, and two of them fail verification. Drafting first and correcting
  later would have produced a document that read well and was wrong.
- **Correcting a person's account without overriding it.** The trigger attribution is
  wrong in the source notes and the postmortem says so, with the evidence and with
  notice to the person — not silently, and not by removing the original claim.
- **A fact fixed with one line, verified against the source of truth.** The R0 trace
  finds a real gap (`Node 20+` versus `"node": ">=20.11"`) and fixes it with one
  edit, checked against `package.json` and `node --version`.
- **Blameless as a check, not a style note.** The trace verifies that no sentence
  attributes cause to a person, as a testable property rather than a writing
  guideline.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`r0-readme-install-section.md`](r0-readme-install-section.md) | Make the install section of the README clearer | L1 / **R0** | VERIFIED | The kernel doing almost nothing, and the moment "cheap" ends at an externality |
| [`incident-postmortem-claims.md`](incident-postmortem-claims.md) | Write the postmortem for a 47-minute checkout outage | L2 / **R2** | VERIFIED | A reporter's account contradicted by logs, and a draft built from a claims table rather than from a narrative |

## Reading notes

**`incident-postmortem-claims.md` is the one worth the time.** Priya's notes are
reliable, specific, and wrong about the trigger — the connection pool saturated 21
minutes *before* the deploy everyone blames. The trace's response is not to
overwrite the account; it is to build a claims table, mark the two failing claims,
and tell her. That is the difference between a postmortem that is correct and one
that is merely agreeable.

**`r0-readme-install-section.md` is the counterweight to everything else here.** It
is 250 lines about one section of one file, and the section was already rewritten
six days ago. The trace's real content is the discipline of finding that out and
not manufacturing a project around it.

## Adjacent examples

- [`../recovery/`](../recovery/) — a failure classified and reported honestly, which
  is the other half of what a postmortem is for.
- [`../data-analysis/srm-before-reading-an-ab-result.md`](../data-analysis/srm-before-reading-an-ab-result.md)
  — the same "check before you quote it" discipline in a different register.
- [`../unknown-domain/`](../unknown-domain/) — where the honest output is a stated
  limit rather than a fluent document.
