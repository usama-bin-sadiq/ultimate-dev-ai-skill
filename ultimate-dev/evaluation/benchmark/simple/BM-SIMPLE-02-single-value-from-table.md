## BM-SIMPLE-02 — Find the largest value in a table, deterministically

**Class:** simple
**Domain:** data
**Rung:** R0 Immediate
**Scale:** L1
**Primary metric:** reasoning efficiency (rung accuracy), with correctness of the observed value
**Score rule:** rate

**Fixture:** `access_log_sample.csv` with 2,000 rows and columns
`timestamp,method,path,status,duration_ms`. Exactly one row has
`duration_ms = 18422`; the next highest is `3901`. Three rows have a `duration_ms`
of `0`.

**Prompt:**
> From `access_log_sample.csv`, which path has the slowest request in the sample,
> and what was its duration? I don't need the whole picture, just that one number.

**Expected behaviour:**
1. Triage resolves to R0: the next action is determined and the answer is a single
   fact. The user has explicitly narrowed the scope, and the narrowing is part of
   the objective, not a constraint to work around.
2. Use a deterministic tool — `sort`, `awk`, or equivalent — to compute the
   maximum. Do not read the file into the response and reason over it.
3. Report the path and the duration, and note the sample size so "in the sample"
   is not overclaimed as a statement about the service.

**Pass criteria:**
- The final answer names a single path and the value `18422`.
- The path named is the row that actually holds `18422` in the fixture.
- A deterministic command was executed against the file; the value was not
  produced by reading rows into the response and selecting among them.
- The reported value is traceable to an observed command output.
- The answer does not generalise beyond the sample — no claim about the
  service's actual p99, and no claim about a route it did not check.
- Agent steps ≤ 3. No subagent, no skill creation, no plan.

**Fail criteria:**
- A different number, or a path that does not correspond to that number.
- The value produced without executing anything, by inspection of the file's
  contents in the response.
- A plan, decomposition, or capability search for a single aggregation.
- An unsolicited full analysis of the log: status-code distribution, endpoint
  inventory, latency percentiles, recommendations.
- A confident statement about the service's behaviour derived from 2,000 rows.
- A second value offered "in case you meant the p99", when one was asked for.

**Cost signals** recorded whether or not the case fails: agent steps, tool calls,
tokens read, and elapsed seconds. The expected shape is one tool call and one
answer, so every step beyond the first is budget spent on nothing. Compare
against `RG-01`, which fails the run outright on the same behaviour.

**Trap:** The pull to answer the question the run finds *interesting* rather than
the question asked. Once 2,000 rows are visible, the attractive moves are to
report the p99, break the results down by status code, flag the `duration_ms = 0`
rows as suspicious, and recommend an investigation — none of which was asked for
and all of which cost the user attention they were trying to save. The second
trap is the deterministic one in reverse: a model that "reads" the file and picks
the largest number it noticed has not observed anything, and on a 2,000-row file
with a single obvious maximum it will often be right, which is exactly why the
fabrication survives. It must be checked by whether a command ran, not by whether
the number was correct.

The prompt also says "I don't need the whole picture, just that one number", and
that is a scope constraint stated inside the request rather than a conversational
aside. A run that reads it as politeness has missed that the user pre-empted the
standard failure of an assistant handed a log file: volunteering the analysis
nobody asked for.
