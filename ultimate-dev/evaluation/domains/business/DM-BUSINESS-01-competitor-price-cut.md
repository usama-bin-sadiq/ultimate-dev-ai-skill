## DM-BUSINESS-01 — A competitor cut prices 15% and our revenue per customer fell 11%

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** business
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with the counterfactual handled correctly
**Score rule:** rate

**Fixture:** 4,200 customers, €186 average monthly revenue. A competitor cut
prices 15% in the core segment 7 weeks ago. Observed over those 7 weeks:
conversion on new signups fell from 3.1% to 2.7%; **revenue per customer fell 11%**;
**total revenue fell 4%**; churn in the core segment rose from 1.8% to 2.4%; and
gross margin fell from 71% to 64%. A 10% discount was tested in the core segment
in the same period as a limited promotion, so price and promotion are partially
confounded. There is no elasticity estimate for the segment.

**Prompt:**
> A competitor cut prices 15% in our core segment. Our revenue per customer is down
> 11% and conversion is down too. What do we do?

**Expected behaviour:**
1. Triage to R3 and check the arithmetic before reacting. Revenue per customer down
   11% and conversion down 12.9% (3.1% to 2.7%) with a customer count that is also
   affected by churn at 2.4% — these are different quantities and the total revenue
   figure, down 4%, is the one that describes the business. Reading "down 11%" as
   the headline overstates the damage by a factor of nearly three, and the run
   should say so.
2. Identify the confound. The 10% discount was tested in the same segment in the
   same period as a promotion, so the observed movement cannot be attributed to
   the competitor alone. State that the attribution is unresolved before any
   recommendation rests on it.
3. Separate the decisions that are actually available. "Match the price cut" is one
   option, and the fixture makes its cost computable: matching costs roughly 15% of
   price on the whole core segment, against a margin already down 7 points. The
   margin arithmetic is a stronger objection to matching than any general argument.
4. State what is not knowable now. There is no elasticity estimate, so the revenue
   effect of a price change cannot be computed, only bounded. Say that a proper
   answer requires an elasticity estimate, and name the cheapest way to get one
   that does not destroy the base price.
5. Recommend actions that are reversible and information-generating: stop or
   isolate the confounded discount promotion first, because it is currently
   generating a mixed signal, then run a bounded price test in a segment.
6. Do not present a confident recommendation where the data cannot support one, and
   do not present a decision framework in place of a decision. The user asked what
   to do.

**Pass criteria:**
- Revenue per customer, conversion, and total revenue are distinguished, and the
  4% total is identified as the figure describing the business.
- The confound between the discount test and the promotion is identified.
- The cost of matching the price cut is quantified against the margin movement.
- The absence of an elasticity estimate is named, and the consequence — that a
  revenue effect cannot be computed — is stated.
- A specific, reversible next action is recommended, with a reason.
- The recommendation is distinguishable from a framework-only response.

**Fail criteria:**
- A 15% price match recommended with no margin calculation.
- "Revenue per customer is down 11%" used as the headline impact figure.
- A revenue projection produced from no elasticity basis, with a point estimate.
- The confound ignored, or the discount blamed or credited without noting it.
- A recommendation to "improve the product" or "differentiate" with no
  specificity and no owner.
- A framework delivered in place of a decision, with no action named.
- Escalation of a staffing decision the user did not ask about.

**Trap:** The user has supplied two alarming numbers and they are the wrong two.
"Revenue per customer down 11%" and "conversion down" both describe a rate, and a
rate falling while the customer count holds steady produces an 11% headline for a
4% business impact — so a run that takes the user's framing at face value will
recommend a response sized three times too large. The second trap is the
recommendation that feels most decisive: "match the 15% cut" is what a competitor
reaction narrative demands, it is the option a board will expect to hear, and it
costs 15% of revenue on a business whose margin has already fallen 7 points. The
third trap is the confidence: with no elasticity estimate, any revenue projection
is arithmetic dressed as forecasting, and a run that produces one will be believed
because it has a number and a decimal place.
