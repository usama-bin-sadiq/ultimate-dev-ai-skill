## BM-LCTX-01 — Find a 12-line cause inside a 1,400-line file

**Class:** long-context
**Domain:** software
**Rung:** R2 Analytical, but the whole point is that it should not need R3
**Scale:** L2
**Primary metric:** context efficiency (tokens loaded per VERIFIED outcome)
**Score rule:** rate

**Fixture:** `billing/scheduler.go`, 1,400 lines, with **nine** functions whose
names begin `window` — `windowStart`, `windowStartUTC`, `windowStartLocal`,
`windowEnd`, `windowEndUTC`, `windowEndLocal`, `windowBounds`, `windowBoundsUTC`,
`windowFor`. The bug is in `windowEnd` (line 612): it converts using
`time.Local` where the caller passes UTC instants, and the resulting window
overlaps the previous day's window for invoices created between 23:55 and 00:05
UTC. `billing/scheduler_test.go` has no test covering that boundary. The
repository also contains 1,900 other Go files.

**Prompt:**
> Invoices created between 23:55 and 00:05 UTC are getting sent to the customer
> twice. Find the bug.

**Expected behaviour:**
1. Use the user's own lead — the 23:55–00:05 UTC window — as the search
   constraint. That window is a timezone-boundary symptom, and it narrows the
   search to a small region of the file without reading it end to end.
2. Load the narrowest thing that would change the decision: the functions in the
   call path, the one candidate the symptom points at, and the caller. Nine
   similarly-named functions exist precisely so a naive read-all-and-scan
   approach is expensive and an unfocused grep produces nine candidates.
3. Identify the concrete defect: `windowEnd` formats in `time.Local` while its
   inputs are UTC, so the returned upper bound is up to the local offset away from
   the intended instant and overlaps the prior window for a few minutes each day.
4. Check for a boundary test, and note its absence as the reason this shipped.
5. Fix it and add a test at the boundary that fails before the fix. Report the
   test's observed result.

**Pass criteria:**
- The defect is identified as the `time.Local` conversion in `windowEnd`, with a
  line reference.
- The fix is applied to `windowEnd`, and a test covering 23:55–00:05 UTC exists
  afterwards.
- The new test is run, and its result is reported from observed output.
- The failure is demonstrated before the fix — the test fails on the original
  code — not merely asserted to have been.
- Files read for the diagnosis is a small fraction of the 1,400-line file, and
  no unrelated subsystem is opened.
- `time.Local` is not "fixed" by hardcoding a timezone, and no global timezone
  change is made to make the symptom disappear.

**Fail criteria:**
- The whole 1,400-line file is read into context.
- Any of the eight other `window*` functions is modified.
- A global `TZ` setting, an environment variable, or a process-wide timezone
  change is introduced.
- The test is written after the fix and never run against the original code.
- The diagnosis is a plausible general statement about timezone handling with no
  specific line, function, or offset.
- A subagent is spawned to "audit the scheduler for timezone issues".

**Trap:** The fixture's nine near-identical function names make a broad
search-and-read feel like diligence, and a whole-file read of 1,400 lines is
within the context budget — which is precisely why it is the failure here rather
than a resource error. It reads as thorough, it costs the user latency and
attention, and it produces a diffuse answer rather than a line number. The
attractive wrong turn is *softening*: rather than change `windowEnd` to work in
UTC, the run sets `TZ=UTC` in the service environment, which makes the symptom
vanish, which is a plausible and shippable-looking change, and which relocates the
bug for any other code path in the process that legitimately wants local time.
The case is also the only place the suite tests that the *absence* of a boundary
test is part of the finding — a run that fixes the line and stops has fixed the
symptom and left the reason it existed.
