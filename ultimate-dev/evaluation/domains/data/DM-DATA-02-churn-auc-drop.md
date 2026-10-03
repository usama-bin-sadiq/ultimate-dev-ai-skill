## DM-DATA-02 — Churn AUC fell from 0.81 to 0.72 with no code change

**Class:** complex
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** data
**Rung:** R3 Deep
**Scale:** L4
**Primary metric:** task success, with evidence preserved rather than destroyed
**Score rule:** rate

**Fixture:** A churn model in production, retrained weekly. Offline AUC on the
holdout fell from 0.81 (week 4) to 0.72 (week 9) with **no model or feature code
change**. The features include `tenure_days`, computed as `now() - signup_date`.
The warehouse completed its migration from `event_date` to `ingested_at` as the
partition key in week 6, and one feature, `days_since_last_session`, is derived by
joining to a table that was repopulated with a 3-day offset. Retraining is
scheduled for tomorrow 06:00 and the current model is the week-8 artefact.
Monitoring shows the production feature distributions shifted, and the share of
rows with a null `tenure_days` rose from 0.1% to 6%.

**Fixture required:** no
**Prompt:**
> Our churn model's AUC dropped from 0.81 to 0.72 over six weeks and nothing changed
> in the code. Diagnose it.

**Expected behaviour:**
1. Triage to R3. "Nothing changed in the code" is a premise that makes the code the
   least likely place to look, and the correct response is to accept the premise
   while rejecting its conclusion that nothing changed.
2. Take the two anchors in the fixture and put them in time order against the AUC
   curve. AUC declines begin after the week-6 migration and the null rate on
   `tenure_days` rises to 6%. The correlation is a hypothesis with a mechanism, not
   a coincidence, and it is specific enough to test.
3. Separate the candidate causes and the observation that would distinguish each:
   - the `event_date` to `ingested_at` partition change altered the join
     semantics or the completeness of `days_since_last_session`;
   - `tenure_days` depends on `now()`, so the feature's *value* drifts forward in
     time even with identical code — a time-dependent feature inside a fixed
     pipeline;
   - the repopulation offset introduced a 3-day shift into a recency feature;
   - genuine base-rate or population drift.
4. Do the things that destroy evidence first. Retraining tomorrow would overwrite
   the current model and clear the training logs needed to compare week-8 and
   week-9 feature values. Say so, and recommend snapshotting the pipeline state
   before the scheduled run.
5. Distinguish the two different questions: why the *offline* metric fell, and why
   *production* behaviour changed. They may have different causes, and a single
   explanation for both should be treated as suspicious.
6. Deliver a diagnostic sequence ordered by information gained per unit of risk, not
   a list. Each step should say what it would confirm and what it would rule out.

**Pass criteria:**
- The week-6 migration and the null-rate rise are placed in time order against the
   AUC decline.
- The migration is treated as a leading candidate with a named mechanism, not one
   of several equal items.
- `tenure_days`'s dependence on `now()` is identified as a code-independent drift
   path.
- The risk to tomorrow's scheduled retrain is flagged, with a recommendation to
   preserve state first.
- Offline-metric cause and production-behaviour cause are treated as possibly
   distinct.
- The next step is specified in terms of what it confirms and rules out.

**Fail criteria:**
- Retraining, or the retrain being scheduled or triggered.
- "Data drift" offered as the diagnosis with no mechanism and no observation.
- The migration not mentioned, or mentioned without the join or partition
   consequence.
- Feature code inspected and declared clean, with the conclusion that the data must
   be wrong.
- A feature-importance or SHAP analysis presented as a diagnosis.
- The offline and production declines assumed to have one cause without evidence.
- An A/B test of a new model proposed before the current one is understood.

**Trap:** The prompt says "nothing changed in the code", and that is true and
misleading in the way that matters: `tenure_days` uses `now()`, so the feature
changes value every day with identical code, which is a real and well-known failure
mode and which a code review will confirm as clean. The more immediate trap is the
retrain. There is a scheduled job tomorrow that will overwrite the artefact and the
logs needed to compare the two states, and the correct run's first action is
preventive rather than diagnostic. A run that starts by retraining — because
"diagnose it" suggests getting a model running — destroys the evidence, produces a
fresher number, and reports it as progress. The second trap is the bland one: the
answer "data drift" is true, sounds right, and changes nothing, because it does not
name which data, which change, or which observation would confirm it.
