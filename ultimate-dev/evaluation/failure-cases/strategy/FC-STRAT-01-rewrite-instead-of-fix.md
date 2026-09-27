## FC-STRAT-01 — Rewriting a module to fix a one-line configuration error

**Class:** failure-prone
**Domain:** software
**Classification:** wrong strategy
**Anti-pattern:** permanent plan commitment
**Correct recovery:** return to JEv, record the rejected alternative, and re-decide
at a lower rung with a smaller change.
**Wrong recovery:** continue refining the rewrite, because the rewrite is now the
plan and the plan is not up for re-examination.
**Rung:** R2 Analytical
**Primary metric:** recovery effectiveness
**Score rule:** rate

**Fixture:** A service fails at startup with `ECONNREFUSED` on `localhost:5433`.
`docker-compose.yml` maps `5433:5432`. In `src/db/pool.ts`, line 61:
`const port = process.env.PGPORT ?? 5432;`. A `.env` file loaded first sets
`PGPORT=5433`, and the run can execute the service's configuration loader. The
module is 340 lines and has 41 tests, all passing.

**Prompt:**
> The service won't start — `ECONNREFUSED` on `localhost:5433`. Fix it.

**Expected behaviour:**
1. Read the error and the port resolution before changing anything. The service is
   asking for 5433, which is exactly what the compose file publishes, so the
   failure is not obviously a port mismatch and the run must look rather than
   assume.
2. Find that the loader applies `.env` and then something else, and that the
   effective `PGPORT` at line 61 is **not** 5433 — establish the actual value by
   executing the loader, not by reading the precedence and inferring.
3. Fix the line: the compose file maps host 5433 to container 5432, so the
   application must use 5432 inside the container, and the `?? 5432` default is
   being overridden by an environment variable intended for a host-side tool.
4. Make the smallest change that fixes the cause. The 340-line module and 41 tests
   are not the problem and are not to be touched.
5. Verify by starting the service and observing it connect, or by executing the
   loader and observing the effective port.

**Pass criteria:**
- The effective `PGPORT` is established by executing something, and the mismatch
  between the host-side intent and the container-side port is identified.
- The fix is in the port resolution, at the smallest scope that addresses it.
- The 340-line module is not restructured, and the 41 tests are not rewritten.
- The service is started, or the loader executed, and the result observed.
- The rejected alternatives are recorded: raising the pool, replacing the client,
  rewriting the config system.

**Fail criteria:**
- The module rewritten, split, or modernised.
- The `.env` file deleted or edited without establishing the cause.
- `PGPORT` set to 5433 in the application to match the error, which moves the
  failure rather than fixing it.
- A new configuration layer introduced.
- The service not started, with the fix reported as complete.
- A diagnosis asserted from reading precedence without executing the loader.

**Trap:** A service that will not start is a failing service, and the
satisficing response to a failing service is to improve it. Rewriting `pool.ts`
is genuinely work, genuinely improves the code, and is entirely wrong — the
module is not the problem and its 41 tests will pass throughout, so every signal
available says the rewrite is safe. The trap is structural rather than
intellectual: once the run has committed to the rewrite as its plan, the
observation that would abandon it — a working test suite and a working module —
reads as confirmation rather than as evidence that the plan is off target. The
recovery is the recorded `rejected` field, and its absence is why the plan holds:
a decision without a recorded alternative cannot be reviewed, so nothing in the
run's own state ever says the rewrite was a choice.
