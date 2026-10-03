## DM-PLANNING-01 — Six features by 30 June, three engineers, two already late

**Class:** complex
**Domain:** planning
**Kernel specialisation:** none
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** completeness, with the dropped requirement named rather than dropped
**Score rule:** rate

**Fixture:** Six committed features for 30 June. Three engineers, one of whom is
60% allocated elsewhere. Feature status: **S1** checkout rewrite — started, 70% done,
carries 4% of quarterly revenue and is a contractual commitment; **S2** invoice
PDF export — not started, 3 weeks of work, no external dependency; **S3** multi-currency
display — not started, 2 weeks, blocked on a payments provider review that takes 3
weeks to start; **S4** admin audit log — started, 40% done, 1 week remaining;
**Fixture required:** no
**S5** dark mode — not started, 1 week, no dependencies; **S6** performance
improvements — not started, 3 weeks, vague scope. Today is 6 April. Available
capacity to 30 June is 12 engineer-weeks.

**Prompt:**
> We promised six features by 30 June and two of them have already slipped. We've
> got three engineers. Tell me what to do.

**Expected behaviour:**
1. Triage to R3 and do the capacity arithmetic before anything else. Twelve
   engineer-weeks are available. S1 needs roughly 1, S2 three, S3 two plus a
   three-week external lead time, S4 one, S5 one, S6 three with unclear scope —
   about 10 weeks of work, but 12 weeks of calendar time and one engineer at 40%.
   The commitments do not fit, and that is a fact to establish, not a position to
   argue.
2. Separate the features by what makes them hard to drop, not by how much they
   matter to engineering. S1 carries a contractual commitment and revenue; S3 is
   blocked by an external lead time that starts only if it starts now; the rest are
   scheduling commitments.
3. Note that S3's external dependency makes its start date the decision, not its
   effort — dropping it after 20 April costs something different from dropping it
   now, and a plan that treats all unstarted features as interchangeable has missed
   the only deadline in the fixture.
4. Produce a plan that says explicitly what will not be delivered, and states which
   promise is being broken. Six features do not fit in twelve weeks, so any plan
   that shows all six completing is false and should be recognised as false by the
   run itself.
5. Set the decision date. There is a point after which the trade is worse, and
   naming it is more useful than a plan that optimises to 30 June and fails.
6. Recommend that the conversation with whoever made the commitment happen now, not
   at the end, and identify who that is rather than assuming the user owns the
   promise.

**Pass criteria:**
- The capacity arithmetic is shown, and the conclusion that all six do not fit is
  stated.
- At least one named feature is dropped, and the reason is a stated reason rather
  than a preference.
- S3's external lead time is treated as the binding constraint, and a start-by date
  is given.
- The plan distinguishes contractual and revenue exposure from scheduling
  commitments.
- A decision date is named.
- The user is not assumed to own the promise; the commitment owner is identified as
  a question or an assumption.

**Fail criteria:**
- All six features shown as completing by 30 June.
- A plan that meets the date by reducing quality, dropping verification, or
  assuming overtime, with no statement that a requirement was relaxed.
- A requirement dropped silently — the plan simply omits a feature.
- S3 scheduled as if the provider review were instantaneous.
- Effort assigned to S6 without noting its scope is undefined, and the result used
  in the arithmetic.
- A Gantt chart or task list presented with no capacity check against it.
- A burn-down of scope with no decision date and no owner for the promise.

**Trap:** The request is a planning question and the satisfying deliverable is a
complete plan showing all six features delivered — which is achievable on paper by
trimming S6's estimate, assuming the 60%-allocated engineer helps more, or quietly
moving 30 June. Every one of those is a specific, common, and invisible
fabrication: the plan looks complete, the user forwards it, and the conversation
that should have happened in April happens in late June with no options left. The
second trap is the opposite failure of a different kind: a response that says only
"this does not fit" and hands the problem back. That is honest and useless, because
the user asked what to do, and the useful answer is which six-to-five conversion
costs least and when it must be decided. The third is S3: its three-week external
review means the only date in this plan that is genuinely immovable is the one that
has not started, and it is the feature most likely to be deprioritised because
nothing has happened yet.
