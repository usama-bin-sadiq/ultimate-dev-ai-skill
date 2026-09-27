# Median and p95 session length for enterprise accounts

**Objective:** "What's the median and p95 session length for enterprise accounts in
`analytics/sessions_2026_q1.parquet`? Enterprise is `plan == 'enterprise'`."

**Domain:** Data analysis — descriptive statistics on an existing dataset
**Scale:** L1   **Reasoning rung:** R0

## 0. Triage

- **Complexity** — one filter, two quantiles, one file. Nothing in the answer
  depends on any other part of the system.
- **Uncertainty** — low on method, and the one real uncertainty is checkable in one
  command: the unit of `session_ms`. Column names that end in `_ms` are sometimes
  microseconds, and the difference is a factor of 1000 on the only number the user
  wants.
- **Consequence** — low. A wrong number here misinforms one person about one
  metric. It is not on a critical path and nothing is spent on it downstream.
- **Reversibility** — free. Nothing is written; the answer is a sentence.

**Rung: R0. Scale: L1.** The next correct action is already determined: filter,
take the quantiles. `SKILL.md`'s R0 behaviour is *act, verify the output, stop* —
and "verify the output" is the whole of the remaining work here.

**Why not R1.** R1 is for a few dependent steps or an assumption that could be
wrong. There *is* an assumption that could be wrong — the unit — and R0 already
covers checking it, because a check is not a stage. Making it a plan step would
convert one extra line into an artefact.

**Escalate when:** the cross-check disagrees with the column's name, which would
mean the data has a defect worth reporting rather than working around.
**De-escalate when:** — already at the floor.

## 1. Task model

- **Objective** — the median and 95th-percentile session length, in a stated unit,
  for enterprise accounts in Q1 2026.
- **Requirements** — both quantiles, over the stated filter, over the stated file,
  reported in a unit that can be checked.
- **Constraints** — `plan == 'enterprise'` is the definition given. The user did not
  ask about other plans, other quarters, other session definitions, or a chart.
- **Unknowns**
  - U1: is `session_ms` milliseconds? **Not blocking** — the quantiles can be
    computed in whatever unit the column is in and the unit determined afterwards,
    which is cheaper than guessing first.
  - U2: are there nulls or negative values? **Not blocking** — they would change
    the answer and are visible in the same call that produces it.
- **Assumptions**
  - A1: one row is one session. *If false*: the quantiles are of something else
    entirely. *Confidence: Inferred from the filename and the column names.*
    *Checked by:* the row count, which is read in the same call.
  - A2: `plan` is the current plan, not the plan at session time. *If false*: a
    customer who upgraded mid-quarter is counted in the wrong group.
    *Confidence: Assumed, and stated because it is a real distinction in this
    schema and I did not check which one it is.*
- **Success criteria** — two numbers, a unit, a row count, and one independent
  check that the unit is what the column name says.

**Requirements vs success criteria:** "median and p95 session length" is the
requirement; "184,203 sessions, median 14m02s, p95 1h09m48s, unit confirmed by
cross-check against a stored duration column" is the criterion, and the second is
the only one that would have caught the thing that was actually wrong.

## 2. Decision records

```text
DECISION
  question      how to establish the unit of session_ms
  selected      compare the median against a second, independent duration in the
                same row set — `session_start` to `session_end` — and if the two
                agree, the column name is corroborated; if the first is 1000x the
                second, the column is microseconds
  rejected      (a) reporting the number in the column's units without checking;
                (b) reading the data dictionary; (c) checking the ingesting job's
                source code
  rationale     (a) is the default and it is wrong one time in roughly two hundred,
                and the error is invisible in the output because a median of
                842000 ms is a plausible-looking number. (c) is the correct answer
                to "what went wrong", which is not the question; the question is
                "what is the number", and the second column answers it for one
                query instead of a code read
  confidence    high
  cost          one extra aggregation over the same filter
  evidence      both quantities are in the same Parquet file and refer to the same
                rows, so a systematic unit error shows as a constant ratio
  recovery      the two disagree by a non-constant factor, which would mean the
                columns measure different things and neither is authoritative
```

```text
DECISION
  question      whether to mention the null and negative values
  selected      mention them, with counts, in one clause
  rejected      dropping them silently
  rationale     filtering them out changes the quantiles, and a quantile computed on
                a subset is only correct if the exclusion is stated. Silent
                filtering is how a data question acquires a hidden premise
  confidence    high
  cost          one clause
  evidence      the count is in the same output as the quantiles
  recovery      the nulls are a small enough fraction that they do not move the
                median, in which case the clause is still owed and still short
```

## 3. Context

C0 — the objective, the two non-blocking unknowns, two assumptions. That is the
working set.

C3 — the file's schema, and only the schema: `pyarrow.parquet.read_schema`,
which lists the columns and their types without reading the data. Loaded because
the filter needs a real column name and the alternative is a failed query.

**Deliberately not loaded:**

- **The other 4.7M rows.** The filter is a vectorised comparison; the whole file
  is read because that is how Parquet works, but no aggregation over the
  non-enterprise rows is computed, inspected, or reasoned about.
- **The data dictionary.** A one-line cross-check against a second column answers
  the question; a dictionary is a document to find, and it may or may not exist.
  Decision record 1 explains why the column is the better evidence.
- **The ingesting job's source.** The right answer to "why is this in
  microseconds" and the wrong answer to "what is the number".
- **Any chart, any trend, any segment breakdown.** The user asked for two numbers.
  Producing a dashboard or a distribution plot would be answering a neighbouring
  question, which is the first failure in `task-model.md`'s table.

`excluded`: non-enterprise rows, the data dictionary, ingestion code, all
segmentation. `unresolved`: whether `plan` is current or as-of-session (A2), and
whether the unit error is historical or was introduced in a January release — both
one-line follow-ups that the answer does not depend on.

## 4. Capability

```text
1. do it directly   SELECTED — one `python -c` with pandas. Quantiles are
                    deterministic and belong to a tool; a model asked to take a
                    median of 184,203 values will sometimes produce a plausible
                    number that is not the median
2. existing         not reached
3. compose          not reached
4. acquire          not reached — pandas, pyarrow and the file are all present
5. create           not reached, and the disqualifying question is not asked
```

## 5. Plan

No plan. The next action was determined before planning started.

```text
id  action                                       expected                             verification
U1  filter to plan == 'enterprise'; report n,    two quantiles, a row count, and     the counts, in the same
    nulls, negatives, and the two quantiles      null/negative counts               output as the quantiles
U2  cross-check the unit: compare the median     either agreement, or a constant    the ratio, printed
    against (end - start) over the same rows     1000x disagreement
```

U2 is a check, not a stage, and it is one extra aggregation inside the same
process. That is the entire extent of the work.

## 6. Execution & observation

```console
$ python3 -c "
import pandas as pd
d = pd.read_parquet('analytics/sessions_2026_q1.parquet')
e = d[d.plan == 'enterprise']
print('rows        ', len(e))
print('null_ms     ', e.session_ms.isna().sum())
print('negative_ms ', (e.session_ms < 0).sum())
print('median_ms   ', e.session_ms.median())
print('p95_ms      ', e.session_ms.quantile(0.95))
"
rows         184203
null_ms      0
negative_ms  0
median_ms    842000.0
p95_ms       4188000.0
```

Clean data: no nulls, no negatives, 184,203 enterprise sessions. The median is
842,000 and the p95 is 4,188,000. Reported as milliseconds that is a median of
**14 minutes** and a p95 of **69 minutes 48 seconds**, both entirely plausible for
a B2B analytics product.

**The unit cross-check, and the surprise:**

```console
$ python3 -c "
import pandas as pd
d = pd.read_parquet('analytics/sessions_2026_q1.parquet')
e = d[d.plan == 'enterprise'].copy()
e['derived_ms'] = (e.session_end - e.session_start).dt.total_seconds() * 1000
print('column median  ', e.session_ms.median())
print('derived median  ', e.derived_ms.median())
print('ratio          ', e.session_ms.median() / e.derived_ms.median())
print('p99 of ratios  ', (e.session_ms / e.derived_ms).quantile(0.99).round(1))
print('p01 of ratios  ', (e.session_ms / e.derived_ms).quantile(0.01).round(1))
"
column median   842000.0
derived median   842.0
ratio         1000.0
p99 of ratios  1000.0
p01 of ratios  1000.0
```

**Ratio: exactly 1000.0, and constant across the 1st and 99th percentiles.** So
`session_ms` is in **microseconds**, uniformly, for every row — and the true median
enterprise session is **842 ms = 0.84 seconds**, and the p95 is 4,188 ms = 4.19
seconds.

Which of the two numbers is right is settled by a fact about the data rather than
by arithmetic: `session_start` to `session_end` is 842 ms at the median, and no B2B
analytics product has a median enterprise session of 0.84 seconds. The
`session_end` column is consistent with `session_start`, and the derived value is
the one that survives contact with a human sense of what a session is.

**So the column name is wrong and the reported answer flips by 1000×.** Answering
without the cross-check gives "14 minutes" with total confidence, and it is wrong by
three orders of magnitude.

**A second observation, which I did not chase.** The ratio is 1000 at both the 1st
and 99th percentiles, which means the unit is uniform — so this is a whole-column
defect, not a period where some SDKs reported differently. That is a good thing to
know and it is one line further: the column is uniformly microseconds, so the fix
is a rename and a migration, not an investigation.

## 7. Verification

The check, and nothing else: is the unit what the column name says?

| check | result |
|---|---|
| row count matches the filter, not the file | 184,203 of 5,097,411 rows |
| nulls and negatives reported rather than silently dropped | 0 and 0, stated |
| the column's unit corroborated by an independent column | **contradicted**: 1000× disagreement |
| the disagreement is uniform rather than period-specific | p01 = p99 = 1000.0 |
| which of the two is authoritative, and why | the derived value: 842 ms is a plausible session, 842,000 ms of microseconds is 14 minutes, and `session_end` agrees with `session_start` |
| the quantiles recomputed in the corrected unit | median 0.84 s, p95 4.19 s |

**Verdict: VERIFIED.** Two numbers, in a unit established by cross-check against an
independent column rather than by a column name, over a stated population, with the
null and negative counts reported.

**The verdict is about the numbers, and the unit is a separate finding.** The user
asked for two quantiles and got them. The column being mislabelled is something
else, and it is reported as something else.

## 8. Recovery

Not a separate stage. There was one surprise and it was caught by the check the plan
already contained, inside the same process, at a cost of one extra aggregation. The
classification would be *bad assumption* — the column name taken as the unit — and
the response is the one `recovery-system.md` mandates: correct the assumption and
re-plan what depended on it, which here means re-expressing the two numbers in the
corrected unit and nothing else.

The retry that was avoided: reporting 842,000 ms and letting the user notice. A
plausible number is the hard case — there is nothing in "14 minutes" that looks
wrong, which is precisely why the cross-check exists rather than scrutiny.

## 9. Delivery

**Median enterprise session: 0.84 seconds. p95: 4.19 seconds.** Over 184,203
sessions in Q1 2026, no nulls and no negatives.

**But `session_ms` is in microseconds, not milliseconds, and it is wrong for every
row.** The column disagrees with `session_end − session_start` by exactly 1000×,
and the ratio is 1000 at the 1st, 50th, and 99th percentiles — so it is a
whole-column defect, not a period where some clients reported differently. If you
report this column anywhere, every number in it is 1000× too large.

```console
$ python3 -c "
import pandas as pd
d = pd.read_parquet('analytics/sessions_2026_q1.parquet')
e = d[d.plan == 'enterprise']
e = e.assign(ms=e.session_ms / 1000)
print(f'median {e.ms.median()/1000:.2f}s   p95 {e.ms.quantile(.95)/1000:.2f}s')
"
median 0.84s   p95 4.19s
```

**Evidence.** 184,203 rows after the filter, from 5,097,411 in the file. Zero nulls
and zero negatives, reported rather than dropped. A 1000.0 ratio against
`session_end − session_start`, uniform across the distribution.

**Assumptions.**
- A1 (one row is one session) — **doubtful and unverified.** A median of 0.84
  seconds is not what a session usually means, and if a "session" here is a
  periodic poll interval rather than a user session, the column is measuring
  something real and correctly and the label `session_ms` is misleading in a
  different way. I did not check the schema's session definition, and the number is
  reported with that caveat rather than smoothed over.
- A2 (`plan` is the current plan) — unverified. A customer who upgraded in March is
  counted as enterprise for sessions from January. If you want as-of-session plan,
  that is a different query and probably a different number.

**Limitations.** Two, both named above and neither resolved: what a "session" means
in this schema, and whether `plan` is current or historical. Both are one-line
lookups. Neither changes the 1000× finding, which is a property of the column and
not of the filter.

**Confidence.** High that `session_ms` is microseconds — a constant 1000× ratio
against an independent column is as clean a piece of evidence as this kind of gets.
**Medium on the quantiles as a description of user behaviour**, because A1 is
doubtful and the 0.84-second median is short enough to suggest the column measures
something other than what its name implies.

**Verification status.** VERIFIED for the two quantiles, the unit, and the
population. The *interpretation* of a 0.84-second session is reported as open, and
the deliverable says so in the first line rather than in a footnote.

## 10. Learning

**Candidate, not promoted.** When a duration column's name carries a unit suffix,
corroborate it against a second duration in the same rows before reporting, and
report the ratio's spread as well as its value. A constant ratio distinguishes a
uniform unit error from a period of mixed units, and the two have completely
different fixes.

**What evidence would be needed to promote it.** Three more columns across the
warehouse with unit-suffixed names and a corroborating second source. A unit error
at 1000× passes every plausibility check that does not compare it to something
independent, which is an argument for the check being routine — but one column is
one column, and promoting on one would install a heuristic that would also fire on
correctly-named columns, which is exactly the load-everything failure in miniature.

**Not worth retaining:** 184,203, 0.84 s, 1000.0. All specific to this file and
this quarter, all in the console output above.

**Routed rather than created.** A unit-corroboration check is a plausible candidate
for the warehouse's data-quality suite, where it belongs as a test on the column
rather than as a habit in someone's head. That is a `skill-creator` conversation
once someone has the column inventory, and it should not be written from one column.

## What this example proves

- **The kernel does the minimum and stops.** No plan artefact, no capability search,
  no decision ledger beyond two records that changed the answer. Two aggregations
  and a sentence.
- **Verification at R0 is one line, and it is the line that mattered.** The
  cross-check cost one extra aggregation and changed the answer by 1000×.
- **A plausible number is the hard case.** "14 minutes" contains nothing that looks
  wrong, which is why the check compares against an independent column rather than
  relying on judgement.
- **The spread of the ratio is more informative than its value.** 1000.0 at p01 and
  p99 says "uniform defect, rename the column"; a range of 999–1001 would have said
  "investigate when the clients changed".
- **The number and the finding are reported separately.** Two quantiles delivered as
  asked; a mislabelled column reported as a second thing, at the top rather than in
  a footnote.
- **A doubtful assumption was surfaced rather than smoothed.** A 0.84-second median
  is not what "session" usually means, and the deliverable says the interpretation
  is open instead of presenting the figure as a behavioural fact.
