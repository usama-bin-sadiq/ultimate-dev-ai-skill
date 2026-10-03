## DM-RESEARCH-02 — Design an experiment on one GPU in three weeks

**Class:** complex
**Domain:** research
**Kernel specialisation:** none
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with the design actually able to answer the question
**Score rule:** rate

**Fixture:** One A100 80GB, shared with two other projects that book it in 12-hour
blocks. The team has 3 weeks. A feature X is being added to a recommendation
model. The training set is a fixed 90-day window, 40M rows. There is a
**Fixture required:** no
**feature-store change shipping in week 2** that will alter the logging of
historical features, so the training data for anything recorded after the
deploy differs in distribution from before it. The current model's offline AUC is
0.741. There is no held-out future data — only the same 90 days, split randomly.
The team wants "to know whether feature X helps".

**Prompt:**
> We want to know whether adding feature X helps the model. We've got three weeks
> and one GPU. Design the experiment.

**Expected behaviour:**
1. Triage to R3 and establish what "helps" has to mean before designing anything.
   Offline AUC gain, online revenue, calibration, long-tail coverage — each implies
   a different design, and the request names none of them. Resolve it with the
   user, or design for the most defensible reading and say which.
2. Identify the design constraint that decides the answer: the feature-store
   change in week 2 means training data logged before and after the deploy is not
   identically distributed. Any comparison that trains on a mix of the two
   confounds the feature with the logging change, and this is the single most
   important thing in the design.
3. Address the temporal structure. A random split of a 90-day window measures
   interpolation and reports it as generalisation. Time-based splits are required,
   and the last N days should be held out entirely.
4. Address the compute budget honestly: 12-hour booking blocks, one GPU, three
   weeks. A design that assumes 40 training runs does not fit, and a design that
   fits by dropping all repeated seeds does not support a claim about a 0.005 AUC
   difference.
5. Address the decision rule in advance: what magnitude of improvement would
   justify shipping, decided before seeing the number, so the experiment can
   return a negative result. Include what happens if the result is inside the
   noise band.
6. Be explicit that a 3-week single-GPU study can establish an offline effect with
   a stated interval, and cannot establish an online one.

**Pass criteria:**
- The feature-store change in week 2 is identified as a confound and the design
  handles it — by restricting the training window, by logging a version marker, or
  by excluding post-deploy data.
- A time-based split is specified, and the random-split failure is named.
- The run count is reconciled against the 12-hour booking blocks and the 3-week
  window.
- Repeated seeds or an interval is included, sufficient to distinguish the
  magnitude the team will care about.
- A decision rule and a noise band are stated in advance.
- The scope of what can be concluded is stated: offline only, single GPU, and what
  that rules out.

**Fail criteria:**
- A design that trains on data spanning the feature-store deploy.
- A random split proposed for time-ordered data without comment.
- A run count that does not fit the available GPU time, or no seeds and no
  interval, with a conclusion stated anyway.
- No decision rule, or a decision rule expressed as "p < 0.05" without an effect
  threshold.
- "Improvement" left undefined, with a design produced for one interpretation.
- An online experiment proposed as deliverable within three weeks on one GPU.
- A "learn new skills" or model-training subagent spawned to make training faster.

**Trap:** The request is a design question with a resource constraint, and the
attractive answer is an experiment plan with a nice factorial structure that
demonstrates methodological fluency. Two things in the fixture punish that. The
first is the feature-store deploy in week 2: a design whose training window spans
it is measuring two changes at once and will produce a number the team believes,
because the model *will* differ, and the difference will be attributed to feature
X. The second is that the decision the team faces is "ship or not", and a design
without a pre-declared effect threshold returns "the difference was 0.003, within
the standard error of our 0.004 spread" — which is not a result, is not a
recommendation, and will be resolved by whoever argues hardest in the next
meeting. A design that fixes the threshold in week one has done more for the team
than a better-powered one.
