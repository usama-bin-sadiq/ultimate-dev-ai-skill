## DM-SOFTWARE-01 — 200 concurrent requests and the API stops answering

**Class:** medium
**Domain:** software
**Kernel specialisation:** none — the kernel has no code path for this, and no
software-specific agent is available to it
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with correctness of the mechanism
**Score rule:** rate

**Fixture:** A Go HTTP service. Under ~200 concurrent requests it stops responding
entirely; the goroutine dump shows ~400 goroutines blocked in `acquireConn` in
`internal/pool/pool.go`. The pool has `maxOpen = 50`, `maxIdle = 10`,
`maxLifetime = 30 * time.Minute`. Every code path that opens a connection either
closes it or returns it, and the difference is a `defer` that sits *inside* an
`if err != nil { return }` block rather than at the top of the function, so it
does not run on the success path. There is no query timeout. Upstream Postgres
has `max_connections = 200`.

**Prompt:**
> Under load our API hangs completely — not errors, just nothing comes back. It
> starts around 200 concurrent requests and it doesn't recover. Find the cause and
> fix it.

**Expected behaviour:**
1. Triage to R2 and obtain the evidence before theorising. The goroutine dump is
   the evidence; it says the threads are blocked *acquiring* connections, which
   locates the problem in pool exhaustion rather than in the database, the
   network, or the handler.
2. Establish the arithmetic: 50 maximum open connections, 400 blocked waiters,
   every waiter holding a request goroutine. The service is not slow, it is dead,
   and the distinction matters for the fix.
3. Find the mechanism: the connection-return `defer` is scoped inside the error
   branch, so connections taken on the success path are never returned. The pool
   leaks, not the database.
4. Fix the scoping so the return happens on every exit path, not only on error.
5. Decide separately whether a query timeout and a `maxLifetime` health check are
   warranted, and say so as additions rather than as the fix — they would bound
   the damage and neither addresses it.
6. Verify: reproduce the leak with the existing load test or a bounded
   reproduction, and observe pool metrics before and after.

**Pass criteria:**
- The cause is identified as connections not being returned on the success path,
  with a reference to the misplaced `defer`.
- The distinction between pool exhaustion and database exhaustion is made
  explicitly, using the dump.
- The fix is the `defer` scope, not a timeout, a larger pool, or a retry.
- Pool state is observed before and after the fix, from a command that ran.
- Any mitigation — timeout, lifetime check — is labelled as mitigation and not as
  the cause's fix.
- A concurrency test or reproduction exists that would fail before the fix.

**Fail criteria:**
- The pool limit is raised, or `max_connections` is raised on Postgres.
- A timeout added and reported as the fix.
- The goroutine dump not read, and the cause asserted from the symptom alone.
- "The database is overloaded" proposed, with no evidence.
- A retry layer added around connection acquisition.
- The pool metrics quoted without being observed, or a load test described as run
  when it was not.

**Trap:** The symptom is a hang under concurrency, and the two most common
production causes are a downstream outage and a slow query, both of which are
plausible, both of which are visible in the fixture's symptoms, and neither of
which is supported by the goroutine dump that was handed over. The attractive fix
is a connection acquisition timeout, which is what most runbooks prescribe, which
converts an infinite hang into a fast error, and which makes the service look
healthy in every dashboard while the pool leaks exactly as much as before. The
trap is that a timeout *is* a real improvement and it is not the answer, and the
only thing separating them is whether the run noticed that the dump says
`acquireConn` — a fact that was in hand and cost one read.
