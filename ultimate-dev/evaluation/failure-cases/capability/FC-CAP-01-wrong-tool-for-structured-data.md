## FC-CAP-01 — The right tool is the wrong kind of tool

**Class:** failure-prone
**Domain:** data
**Classification:** wrong capability
**Anti-pattern:** blind retry
**Correct recovery:** stop, classify the capability as wrong, and re-resolve — for
JSON Lines the correct capability is a line-oriented parser, not a text matcher.
**Wrong recovery:** add a second pattern to the `grep` and run it again.
**Rung:** R1 Structured
**Primary metric:** recovery effectiveness
**Score rule:** rate

**Fixture:** `events-2026-04.jsonl`, 48,000 lines, one JSON object per line, with
keys `id,ts,user,kind`. The target: count events with `"kind":"refund"`. The file
contains **nested objects**, so the substring `"kind":"refund"` also appears inside
a `context` field on lines whose top-level `kind` is `chargeback`. A naive `grep
-c` over the file returns 1,204; the correct count is 968. `jq` is available.

**Prompt:**
> Count the refunds in `events-2026-04.jsonl` and tell me if there are more than
> 1,000.

**Expected behaviour:**
1. Resolve the capability from the shape of the data. One JSON object per line with
   nested objects is a structured query, and `jq` is the right capability.
2. Count top-level `kind` values: `jq -r '.kind' | sort | uniq -c`, or equivalent.
3. Report 968, and answer the actual question: no, there are not more than 1,000.
4. Note that a substring count would over-count, since `kind` appears inside a
   nested `context` object on some lines — because a number that looks wrong is
   worth one line of explanation, not a bare correction.

**Pass criteria:**
- The count `968` is reported, and the answer to the question is "no".
- The count came from a structured parse of the top-level `key`, not a substring
  match.
- The over-counting mechanism is identified in the response.
- The answer is delivered as the user framed it — a count and a yes/no.
- No second `grep` pattern was added after the first returned a different number.

**Fail criteria:**
- `1204` reported.
- The number reported as correct without noting the nested-key cause.
- `grep` used for the final count, even if the number happens to be right.
- The threshold question left unanswered.
- A second `grep` variant tried after the first result looked high.
- A `jq` filter used without checking whether `.kind` is the top-level key.

**Classification note:** the run will usually classify this as an execution
failure, because a command ran and a number came back. It is a wrong-capability
failure, and the distinction is what determines the response: an execution
failure is fixed by fixing the command, a wrong-capability failure by changing
the tool. Retrying is neither.

**Trap:** The failure looks like a number that came out high, and the reflex is to
tighten the pattern — `grep '"kind":"refund",'` with a trailing comma, or a word
boundary, or excluding lines containing `context`. Every one of those produces a
different wrong number, and the run will be performing recovery the entire time,
which is the appearance of diligence. The classification is wrong capability: the
capability is a line-oriented structured parser, and no pattern refinement turns a
text matcher into one. The tell is available at the point of failure — the user
asked for a count and the tool returned a count, so nothing errored and nothing
signalled that recovery was needed. A run that sees a plausible number and stops has
never noticed it was wrong, and reports 1,204 with a verification verdict.

The case is worth reading twice, because the number the naive path returns is
the number the user is primed to expect. A high count is consistent with the
user's framing, so it does not read as suspicious the way a low count would,
and the run that reports it will be believed. The count the correct path
returns is lower, and a run that reached it has to explain why the tool
disagreed with the obvious reading. That discomfort is the signal, and it is
the one a wrong-capability failure always produces: a number that is right
and that the run cannot immediately account for.
