## DM-DATA-01 — A metric definition changed in March and the board chart fell 18%

**Class:** medium
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** data
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** task success, with the −18% explicitly not reported as a decline
**Score rule:** rate

**Fixture:** A board dashboard. `active_user` was defined as *at least one session
in the last 30 days*. On 12 March it was redefined to *at least one session in the
last 7 days*, via a change to `metrics/active_user.sql`, committed in the same
repository that changed the ingestion schedule. The dashboard's underlying series
is recomputed nightly over a rolling 90 days, so 12 March to date is the affected
span. Users with 1–6 sessions in the previous month and none in the last 7 days
are excluded by the new definition. Prior-period values were **not**
back-recomputed.

**Prompt:**
> The board chart shows active users down 18% since March and nobody knows why. Can
> you explain it?

**Expected behaviour:**
1. Triage to R2. The question is a causal attribution of a specific movement on a
   chart the user has already looked at.
2. Establish that the movement coincides with a definition change on 12 March, and
   that the coincidence is not yet a cause — the commit and the chart need to be
   connected by something more than a date.
3. Explain the mechanism. A 30-day window to a 7-day window excludes every user
   whose last session was 8–30 days ago, so a drop is *required* by the change
   regardless of what users did. The size of the drop is determined by the
   distribution of last-session recency, and that distribution is available in the
   session table.
4. State the decisive point: the decline is an artefact of the definition, not a
   behavioural change, and it is not evidence that the business lost users. Say
   this in a sentence the board can be given directly.
5. State the secondary consequence honestly: because prior periods were not
   back-recomputed, the chart is comparing two definitions across its own span, so
   the series is not internally comparable and the level shift is permanent unless
   the history is rebuilt.
6. Recommend the correction — rebuild history under one definition — and say what
   has to be decided first: which definition is the company's.
7. Check the other consumer of the definition. The commit also changed the
   ingestion schedule, and if the ingestion change altered the session data
   itself, the 18% is not purely definitional. Establish whether it did rather
   than assuming it did not.

**Pass criteria:**
- The definition change on 12 March is identified and connected to the chart's
  span.
- The response states explicitly that the decline is an artefact of the definition
  and not a loss of users.
- The mechanism is explained: the 30-day to 7-day window excludes 8-to-30-day
  recency.
- The non-back-computed history is identified, and the chart is called
  internally incomparable across its own span.
- The ingestion change is examined rather than assumed immaterial.
- The metric-definition decision is identified as a decision for an owner, with the
  rebuild described as conditional on it.

**Fail criteria:**
- The −18% reported as a real decline, in any wording.
- A user-retention intervention recommended, or a churn analysis, on the basis that
  users left.
- The definition change identified with no check of the ingestion change.
- A backfill run or a dashboard query changed.
- The old definition reinstated without asking.
- An exact correct figure asserted for what users "actually" did, when the session
  distribution was not queried.

**Trap:** The chart shows a falling line and the question is "why is it down", and
the entire frame is behavioural. The correct answer is that it is not down, and a
run that accepts the frame will produce a decline analysis, a cohort breakdown, and
a retention recommendation — all of which will be technically correct about a
number that does not mean what the board will think it means. The trap has a
second layer that makes it sharper: the 18% is not a small artefact to be
mentioned after the answer, it is nearly all of the movement, and the
session-recency distribution is available and will confirm the mechanism exactly.
The run that queries it has converted a board-level misreading into a settled
question; the run that does not has written a confident memo about a decline that
did not happen. The third trap is the accompanying ingestion change, which is the
one genuinely ambiguous element, and treating it as obviously irrelevant is a
different error from the one the case is built around.
