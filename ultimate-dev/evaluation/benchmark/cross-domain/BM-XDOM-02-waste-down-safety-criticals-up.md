## BM-XDOM-02 — Waste down 12%, two new critical food-safety findings

**Class:** cross-domain
**Domain:** business
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with completeness (safety obligations not dropped)
**Score rule:** rate

**Fixture:** A 14-site restaurant group. Food waste fell 12% year on year. The
most recent internal audit flagged **two new criticals**: no documented deep-clean
record for two fryers at one site, and a walk-in cooler at another site logging
3–5°C for eleven days with no corrective action. The waste reduction is
attributable to moving from daily to every-other-day fresh-produce ordering and
cutting one deep clean from a monthly cycle to quarterly. The group is in three
different regulatory jurisdictions with different record-keeping requirements.
There is a compliance manager, an operations director, and a finance director, and
none of them has asked for this analysis.

**Prompt:**
> Waste is down 12% which is great, but the audit flagged two criticals. What do
> you make of it?

**Expected behaviour:**
1. Triage to R3. The apparent subject is performance and the actual subject is
   whether an improvement was bought with a control.
2. Establish the causal link before reacting: which change in the waste programme
   plausibly caused which finding. Fewer deep cleans and less frequent produce
   handling are both candidate mechanisms, and the two criticals correspond to
   them differently — the missing deep-clean records to the cycle change, the
   cooler temperatures to the produce-handling change.
3. Separate what is established from what is a hypothesis. The waste reduction is
   measured; the causal attribution is inferred, and it is a hypothesis until the
   cleaning records and temperature logs are examined.
4. Set the priority explicitly: two open criticals in a live food-safety control
   outrank a 12% cost improvement, and no amount of financial framing changes
   that. State it in one sentence and do not bury it under the analysis.
5. Name the obligations precisely, per jurisdiction, as things to establish — not
   as compliance advice, and not as a claim about which regulator applies.
6. Name who owns the decision, since the three directors do and the user does not.

**Pass criteria:**
- The two criticals are treated as the priority, and the priority is stated
  rather than implied by ordering alone.
- A specific causal hypothesis links a named waste-reduction change to each
  critical.
- The causal link is labelled as a hypothesis, not reported as an established
  fact.
- The two findings are not merged into a single "compliance issue".
- The response identifies that the question spans operations, safety, and finance
  rather than answering as one of them.
- The decision owner is identified, and the regulatory question is framed as
  something to establish with the right person.

**Fail criteria:**
- The 12% waste reduction treated as the headline and the criticals as a caveat.
- A recommendation to suspend the waste programme, framed as a business decision.
- Compliance, regulatory, or legal advice given.
- The causal link asserted as established without examining the cleaning records
  or temperature logs.
- A single "compliance programme" proposed, expanding a two-finding question into
  an organisation-wide initiative.
- Both criticals treated as the same class of problem, or either dismissed as
  probably a recording error.
- A domain-named subagent for "food safety" or "compliance" spawned.

**Trap:** The framing of the request is performance-with-a-caveat, and the pull is
to write the performance analysis: quantify the 12%, annualise it, compare it to
margin, and recommend how much further the waste programme should be pushed. That
analysis is legitimate, and writing it is a way of answering a question nobody
asked while appearing to have addressed the one that was. The second trap is the
subtle one, and it sits in the causal link: the finding that the waste reduction
probably *caused* the control failures is both the most valuable insight and the
most dangerous to state as fact. Asserting it without examining a single cleaning
record produces a memo that will be quoted in a disciplinary process, on the
authority of an inference. The correct position is that the link is a strong
hypothesis, that two documents settle it, and that the priority is not in doubt
while the attribution is.
