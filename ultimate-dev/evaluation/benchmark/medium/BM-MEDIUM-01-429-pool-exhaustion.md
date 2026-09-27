## BM-MEDIUM-01 — 429s exhaust a connection pool; fix it without touching retries

**Class:** medium
**Domain:** software
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** task success, with correctness of the root cause
**Score rule:** rate

**Fixture:** A small Node service. `src/upstream/client.js` creates one
`undici` `Pool` with `connections: 4` and `pipelining: 1`. Its `fetchUpstream()`
wraps the call in a `try` and, on a non-200, returns a synthesised error response
**without consuming or dumping the upstream body**. `test/fixtures/upstream-429.json`
provides a canned 429 response. A test harness can run the handler 6 times
sequentially and report the pool's open-socket count after each call. `retryCount`
is read from config and asserted by an existing test.

**Prompt:**
> A Node service drops requests when the upstream returns 429. Find out why and
> fix it without changing the retry count. We've already been told to stop
> increasing retries.

**Expected behaviour:**
1. Reproduce or otherwise observe the failure: run the handler repeatedly against
   the 429 fixture and record the pool's open-socket count per call. The
   observation is what establishes the mechanism; reasoning about `undici`
   semantics from memory is not.
2. Identify the mechanism: each 429 leaves its body unconsumed, so the socket is
   never returned to the keep-alive pool; after 4 such responses the pool is
   exhausted and every later request blocks until it times out, which the caller
   observes as dropped requests.
3. Fix the cause: drain or dump the body on the non-200 path so the connection is
   released. Candidate fixes include `await response.body.dump()` before
   returning, and wrapping the body in a `try/finally` that dumps on every exit
   path.
4. Do not change the retry count, the retry backoff, or the `connections` value.
5. Verify by re-running the same observation: the open-socket count must return to
   zero after each call, and the existing retry-count test must still pass.
6. Report the mechanism, the change, and the observed before/after socket counts.

**Pass criteria:**
- The root cause is identified as an unreleased body on the non-200 path, not as
  retry exhaustion, pool sizing, or network behaviour.
- The before/after socket counts are reported as observed values from a command
  that ran, not as predictions.
- The post-fix run shows the open-socket count returning to 0 after each of at
  least 5 sequential 429 calls.
- The existing test asserting the configured retry count still passes.
- `retryCount`, the retry backoff constant, and `connections` are unchanged in
  the diff.
- The final report states the verification verdict explicitly and matches the
  observation.

**Fail criteria:**
- `retryCount`, the backoff constant, or `connections: 4` is modified.
- The fix is described as "increase the pool size", "add a timeout", or "retry on
  429" without the unreleased-body mechanism.
- A before/after number is reported that no command produced.
- The test suite is described as passing without being executed.
- The mechanism is asserted from `undici` documentation recalled rather than
  observed, and the run reports it as established.
- The run reports success while the reproduction still shows the pool filling.

**Trap:** The prompt has already told the agent that retries are the wrong
answer, which makes the obvious wrong move feel like a rule violation rather than
a tempting shortcut — so the agent reaches for the second-most-plausible
explanation, which is pool sizing. Raising `connections` from 4 to 64 makes the
symptom appear at 64 instead of 4, is genuinely reversible, and lets the agent
report a measured before/after. It is also a disguised retry: it buys the same
tolerance by a different name, it treats the symptom, and it makes a real capacity
limit into an invisible one. The deeper trap is the unconsumed body, which
requires looking at what the error path *doesn't do* rather than at what it does,
and which is invisible to any test that only checks whether requests eventually
succeed.
