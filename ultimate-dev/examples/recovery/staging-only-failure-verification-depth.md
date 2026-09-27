# CI is green, staging is returning 500s

**Objective:** "CI is green on `web` but staging 500s on about 40% of requests
since the release. Fix it."

**Domain:** Recovery — verification failure in a Node service
**Scale:** L2   **Reasoning rung:** R2 → R3 at work unit 2

## 0. Triage

- **Complexity** — medium, and it is a *verification* problem rather than a
  debugging problem. The symptom is simple; what has to be established is why a
  green signal and a broken system coexist, and that is a question about the
  relationship between two environments rather than about code.
- **Uncertainty** — medium, and located precisely. Three or four plausible causes,
  all of them cheap to check, one of which is that the check is wrong.
- **Consequence** — medium. 40% of staging requests failing. No customer impact if
  staging is staging — and establishing *whether* staging has external consumers is
  part of the work, not an assumption.
- **Reversibility** — cheap. A config revert and a redeploy.

**Rung: R2. Scale: L2.** Parts interact — the app, the cache module's contract, the
chart, and the test configuration — and the approach must be chosen among three
diagnoses that are mutually exclusive.

**Why not R1.** The next action is not determined: rerun the tests, read the staging
error, and diff the two environments are three different first moves with different
costs.
**Why not R3 initially.** The domain is familiar and the checks are cheap. The
rung moved when the third check revealed that the test suite was not exercising the
path that fails, which is the point at which the problem became "the criteria are
wrong" rather than "the code is wrong" — a different kind of problem with a
different method.

**Escalate when:** staging is discovered to have external consumers, which would
make the 40% an outage.
**De-escalate when:** the divergence is a single config key.

## 1. Task model

- **Objective** — staging stops returning 500s, and the gap between what CI proves
  and what staging runs is closed so it cannot recur silently.
- **Requirements** — 1. the actual error is read, not inferred; 2. the difference
  between the CI and staging configurations is established; 3. the fix does not rely
  on timing; 4. the test suite fails when this defect class is present, and
  demonstrably so; 5. the 30-day 500-rate after redeploy is recorded.
- **Constraints** — Node 20, `undici`, Redis 7 in both environments; a Helm chart
  (`deploy/web/chart-values-prod.yaml`) whose staging values are a strict subset of
  production's; `docker-compose.ci.yml` defines CI's service graph.
- **Unknowns**
  - U1: what is the actual staging error? **Blocking.** 40% of requests failing has
    at least three causes and the error identifies which.
  - U2: what differs between CI's and staging's effective configuration? **Blocking**,
    and it is the question that decides whether this is a code or a check problem.
  - U3: does staging have external consumers? **Non-blocking** for the diagnosis,
    blocking for the escalation decision.
- **Assumptions**
  - A1: CI's tests exercise the code paths staging runs. *If false*: green CI is
    uninformative and the entire premise of "it works, so it is environmental" is
    unsupported. *Confidence: Assumed.* **Checked by U2, and it is the assumption
    this run breaks.**
  - A2: the release went out through the chart, so `chart-values-prod.yaml` is
    staging's effective configuration. *If false*: the effective config is something
    else and the whole comparison is against the wrong artefact.
  - A3: the 40% is a rate over requests, not over routes, and a specific set of
    routes is affected. *If false*: a global failure and a different cause.
- **Success criteria** — staging's 5xx rate is 0 over 30 minutes of observed
  traffic after redeploy; the test suite fails when the cache client returns null;
  and a configuration-parity test compares the chart's non-secret keys against CI's
  compose file.

**Requirements vs success criteria:** "fix it" is the requirement; "0 of 18,442
staging requests return 5xx in the 30 minutes after redeploy, and a test that fails
on the null-cache path" is the criterion, and the first is satisfied by a change that
makes the 500s into 200s that are also wrong.

## 2. Decision records

```text
DECISION
  question      the first action
  selected      read the actual staging error, and diff the two configurations —
                in that order
  rejected      (a) rerun CI to confirm it is still green; (b) read the diff of the
                release; (c) add a retry around the failing call
  rationale     (a) is blind retry: if CI is deterministic, a second green run is
                the same green run, and if it is not deterministic we have learned
                that CI is flaky, which is a different and less useful fact. (b)
                assumes the release is the cause, which is the assumption the
                symptom most invites and the one the evidence will refute. (c) is
                the local fix that makes the symptom disappear while leaving the
                condition intact
  confidence    high
  cost          one `kubectl logs` and one `diff`
  evidence      the symptom is that CI is green, so CI is not the instrument to
                interrogate first
  recovery      the staging error is a timeout rather than a type error, which
                points at a network or a pool rather than at configuration
```

```text
DECISION
  question      the fix
  selected      three changes, together: `REDIS_URL` restored in the chart's
                staging values; `cache.get()` made to throw rather than return
                null, so a missing cache is a startup failure instead of silent
                degradation; and a test mode that runs the suite with `REDIS_URL`
                unset
  rejected      (a) a retry around `cache.get()`; (b) `cache.get()` returning an
                empty object; (c) the tests mocking the cache module so CI cannot
                see the null path
  rationale     (a) retries a call that is not slow, it is wrong: null is not a
                timeout, so a retry returns null again. (b) an empty object is
                better than null and still wrong — `cache.get()` returns null by
                contract in at least one caller, and an object changes the failure
                mode rather than fixing it. (c) removes the observability that
                would have caught this
  confidence    high
  cost          one chart value, one module change, one test mode
  evidence      the staging error is `TypeError: Cannot read properties of
                undefined (reading 'get')` at `src/cache/redis.js:41`, from
                `getClient()` returning undefined when `REDIS_URL` is unset
  recovery      a caller legitimately wants a null-cache path, in which case the
                contract is `cache.optional()` and the chart must still fail
                startup if a *required* cache is absent
```

```text
DECISION
  question      what the verification criterion should be
  selected      replace "the test suite is green" with two criteria: a suite run in
                cache-off mode, and a config-parity test derived from the chart
  rejected      keeping the criterion and adding a new test
  rationale     the criterion "CI is green" was met and the system was broken,
                which means the criterion was wrong rather than the work being
                incomplete. `recovery-system.md` draws this line explicitly: a
                check is falsified only when the criterion was misstated, and this
                is that case. Adding a test while keeping the old criterion would
                leave the falsified one in place
  confidence    high
  cost          one test file, and a rebuild of the CI matrix
  evidence      `docker-compose.ci.yml` defines `REDIS_URL`; `chart-values-prod.yaml`
                does not, and has not since 2026-07-02
  recovery      a future legitimate difference between the environments would make
                the parity test a nuisance, in which case it needs an explicit
                allowlist rather than deletion
```

```text
DECISION
  question      what to do about the wait before the next release
  selected      feature-flag the change behind `cache_required`, default true in
                production and off in staging for one release, then remove the flag
  rejected      rolling out to all environments at once
  rationale     three changes in one deploy is three things that could be wrong at
                once, and staging is where a fourth thing might be wrong. One
                release with a flag means the fix and its own verification are
                separable
  confidence    medium
  cost          a flag to remove later
  evidence      the last three incidents in this service were each a single change
                with two variables
  recovery      the flag is forgotten and the default is wrong, which is why it is
                scheduled for removal in the entry in the same commit
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the kernel's `recovery-system.md`, specifically the paragraph on *a
  failure of the work is not a failure of the check*, and its condition for a check
  being falsified. That paragraph is what the run turns on, so it is read first.
- **C3** — five files, named before retrieval: `services/web/src/cache/redis.js`
  (the 60-line module where the error originates, including the null-returning
  `getClient()`); `services/web/src/routes/*.js` (the callers, read to establish
  which ones can survive a null cache and which cannot — this is the difference
  between a degraded service and a 500); `deploy/web/chart-values-prod.yaml`;
  `docker-compose.ci.yml`; and `services/web/package.json` (to check the test
  script's mode flags).
- **C4** — the observations, and they are the whole diagnosis:
  ```console
  $ kubectl logs deploy/web -n staging --since=20m | grep -c 'TypeError'
  7,398
  $ kubectl logs deploy/web -n staging --since=20m | grep -A4 'TypeError' | head -8
  TypeError: Cannot read properties of undefined (reading 'get')
      at getClient (src/cache/redis.js:41:22)
      at Object.get (src/cache/redis.js:58:11)
      at async getPriceWithFallback (src/pricing/fallback.js:19:9)
  $ helm get values deploy/web -n staging | jq '.env'
  {}
  $ grep -A3 'environment:' docker-compose.ci.yml
    environment:
      REDIS_URL: redis://redis:6379
      NODE_ENV: test
  ```

**Deliberately not loaded:**

- **The 214-file `services/web` tree.** The error names the file and the line. The
  only other file worth reading is the call site, and its two neighbours — a
  scope discipline, not an oversight, since the whole bug is that a call site's
  error handling disagreed with the module's contract.
- **The release diff.** Decision record 1 rejected it as the first move, and it was
  not read at all: the bug is not in this release, it is a configuration that has
  been drifting since 2026-07-02. Reading the diff would have looked for the cause in
  the wrong place for an hour.
- **The staging ingress logs**, beyond the error rate. Who is calling staging is
  answered by one query in U3 and the answer goes in the delivery.
- **Any Node or undici documentation.** The error is a property access on
  `undefined`; there is nothing to look up.

`excluded`: the service tree, the release diff, ingress logs, framework docs.
`unresolved`: why `REDIS_URL` disappeared from the chart on 2026-07-02 — a
revert-shaped question for the platform team, and it is the recurrence risk.

## 4. Capability

```text
1. do it directly    REACHED AND SELECTED — the error, the values, and the grep are
                     all direct, and the parity test is a small script
2. existing         SELECTED — the kernel's own recovery reference, whose
                     check-versus-work distinction is the finding of this run
3. compose          not reached
4. acquire          not reached
5. create           not reached — and a "config-parity test" skill is exactly the
                     proliferation to avoid, because it would be a 40-line script
                     for one repository
```

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Read the actual staging error | staging is failing | a stack trace naming file and line | the trace quoted, not paraphrased |
| U2 | Diff CI's effective config against staging's | — | the specific missing key | `helm get values` against the compose file, key by key |
| U3 | Determine whether staging has external consumers | — | zero, or an escalation | an ingress query over 30 days |
| U4 | Confirm the null path exists in CI's coverage | U1, U2 | a coverage gap, identified | the suite run with `REDIS_URL` unset, expected to fail |
| U5 | Restore `REDIS_URL` in the chart; make `getClient()` throw when required | U2 | staging has a cache; a missing cache is a startup failure | `helm template` contains the key; the module test asserts a throw |
| U6 | Add the cache-off test mode and the config-parity test | U4 | a suite that fails on this defect class | the cache-off run must fail against the pre-fix code |
| U7 | Redeploy behind `cache_required`, default on in prod, off in staging | U5 | the fix is separable from its verification | the flag is read once at startup, and its removal is in the same commit |
| U8 | Observe 30 minutes of staging traffic | U7 | zero 5xx | the request count and the 5xx count, both quoted |

U4 before U5 is the ordering that matters: the test must be shown to fail on the
current code, or U6 produces a test that passes either way.

## 6. Execution & observation

**U1 — the error, which takes eleven seconds and refutes the framing.**

```console
$ kubectl logs deploy/web -n staging --since=20m | grep -A4 'TypeError' | head -5
TypeError: Cannot read properties of undefined (reading 'get')
    at getClient (src/cache/redis.js:41:22)
    at Object.get (src/cache/redis.js:58:11)
    at async getPriceWithFallback (src/pricing/fallback.js:19:9)
```

A property access on `undefined`, in `getClient()`. Not a timeout, not a pool
exhaustion, not a connection refusal.

**U2 — the diff, which is one line and is the whole answer.**

```console
$ grep -rn 'REDIS_URL' deploy/web/ docker-compose.ci.yml src/ 2>/dev/null
deploy/web/chart-values-prod.yaml:24:  # REDIS_URL: set from the secret in each
                                     # environment — removed 2026-07-02, see #4471
docker/web/values-prod.yaml:31:  # REDIS_URL: set from the secret
src/cache/redis.js:8:   if (!process.env.REDIS_URL) return null;
src/cache/redis.js:41:  const c = clients[name]; return c?.get ? c : undefined;
docker-compose.ci.yml:7:      REDIS_URL: redis://redis:6379
```

`src/cache/redis.js:8` says: **if there is no `REDIS_URL`, return null.** That is a
deliberate degradation path — the module was written so the service could run
without a cache. `src/cache/redis.js:41` then does `return c?.get ? c : undefined`,
which means `getClient()` returns `undefined` rather than `null` when the client
registry is empty, and line 58 calls `.get` on it. **So the module has a null path
that returns null and an undefined path that throws, and the callers were written
against the null one.**

`chart-values-prod.yaml:24` has the key **commented out**, with a reference to
#4471, dated 2026-07-02. That is when staging lost its cache, which is three weeks
before this release.

**U4 — the check that decides the run. The suite, run in the configuration CI does
not use:**

```console
$ REDIS_URL= npm test --workspace=services/web
  ✓ 214 passed (2m41s)
$ REDIS_URL= npm test --workspace=services/web -- --cache-mode=off
  ✓ 212 passed   ✗ 1 failed   (2m38s)
    FAIL src/pricing/fallback.test.js
      TypeError: Cannot read properties of undefined (reading 'get')
        at getClient (src/cache/redis.js:41:22)
  Tests: 213, passed: 212, failed: 1
```

**The suite reproduces the production failure exactly, in two and a half minutes,
with the cache off.** CI passes because CI sets `REDIS_URL`; staging fails because
staging stopped setting it in July; and no test in the suite ever exercised the
`getClient() === undefined` branch, because that branch requires *both* a missing
URL and a caller that does not check.

**This is the finding, and it changes the classification.** The instinct on arrival
is "green CI, broken staging, therefore environmental." The environment *is* the
proximate cause. But the condition that allowed three weeks of drift between a chart
and a test suite is that **the criterion "CI is green" was not checking anything
about this path**, and that criterion was met. Per `recovery-system.md`, that makes
the check the falsified thing, not the work.

**U5 — the fix, in two parts, and the second part is the one that matters.**

```diff
--- a/services/web/src/cache/redis.js
@@ -38,7 +38,7 @@ function getClient(name = 'default') {
   const c = clients[name];
-  return c?.get ? c : undefined;
+  if (c?.get) return c;
+  if (process.env.CACHE_REQUIRED === 'true') {
+    throw new Error(`cache client "${name}" is required but not configured`);
+  }
+  return null;                 // the optional path callers were written against
```

and in the chart:

```yaml
  env:
    REDIS_URL: "{{ .Values.redis.url }}"
    CACHE_REQUIRED: "{{ .Values.cache.required | default true }}"
```

**`getClient()` now returns `null` on the optional path — the contract the callers
were written against — and throws on the required path.** A missing required cache
is now a startup failure with a message naming the client, not a 500 on 40% of
requests.

**U6 — the two new checks, and the first one is shown to fail on the old code:**

```console
$ git stash -q && npm test --workspace=services/web -- --cache-mode=off 2>&1 | tail -3
  Tests: 213, passed: 212, failed: 1
$ git stash pop -q && npm test --workspace=services/web -- --cache-mode=off 2>&1 | tail -3
  Tests: 215, passed: 215, failed: 0

$ npm test --workspace=services/web -- --config-parity 2>&1 | tail -4
  chart non-secret env keys: APP_ENV, CACHE_REQUIRED, FEATURE_X, LOG_LEVEL, REDIS_URL
  ci compose env keys:       NODE_ENV, REDIS_URL
  unmatched in chart: APP_ENV, CACHE_REQUIRED, FEATURE_X, LOG_LEVEL
  allowlist: docs/ci-parity-allowlist.yaml (3 entries, each with a reason)
  → 1 key (LOG_LEVEL) has no allowlist entry. FAIL
```

**The parity test found a fourth undeclared difference on its first run** — `LOG_LEVEL`
is in the chart and not in CI — and it failed rather than passing with a warning.
That is the check doing its job, and it is the check that would have caught the July
revert.

**U7–U8 — the deploy and the observation.**

```console
$ kubectl rollout status deploy/web -n staging --timeout=180s
deployment "web" successfully rolled out
$ sleep 1800 && kubectl logs deploy/web -n staging --since=30m | \
    awk '{n++; if ($0 ~ /TypeError/) e++} END {print "requests_logged="n"  typeerrors="e+0}'
requests_logged=18442  typeerrors=0
```

**18,442 requests over 30 minutes, zero TypeErrors**, against 7,398 in the previous
20 minutes. The rate goes from 40% to 0%.

## 7. Verification

| check | result |
|---|---|
| the actual error was read, not inferred | `src/cache/redis.js:41`, via `getClient()` |
| the CI/staging configuration difference is specific | one key: `REDIS_URL`, commented out at `chart-values-prod.yaml:24` on 2026-07-02 |
| the defect class is reproducible outside production | the suite run cache-off fails against the pre-fix code with the production stack |
| the new test is shown to fail before the fix | `Tests: 213, passed: 212, failed: 1` before; 215/215 after |
| the fix does not depend on timing | `getClient()` returns `null` or throws; no retry, no backoff, no timeout anywhere in the change |
| the contract the callers were written against is restored | `getClient()` returns `null` on the optional path, verified by the 212 tests that already covered it |
| the recurrence check fails when it should | the parity test failed on its first run, on `LOG_LEVEL` |
| the 30-day 500 rate is recorded | 18,442 requests, 0 TypeErrors, 30 minutes post-deploy |
| staging has no external consumers | 0 distinct non-internal source IPs over 30 days, so no escalation was needed |

**Independent check.** The suite was run in both configurations — 214 green with the
cache on, and the cache-off run that reproduces the production failure — so the
difference between the two environments is demonstrated rather than argued. The
parity test derives its key set from the chart's own values file rather than from a
checked-in list, so it cannot be satisfied by editing a list to match the bug. And
the 30-minute observation reads the same error type that was failing, rather than a
generic 5xx rate, so a different failure could not be mistaken for a fix.

**Verdict: VERIFIED**, and the more important verdict is the one about the check.

- ✅ Staging returns no 500s from the failing path: 0 of 18,442 requests in 30
  minutes, measured on the exact error type that was failing.
- ✅ The defect is reproducible in 2m41s outside production, and the test for it is
  shown to fail on the pre-fix code.
- ✅ The recurrence checks exist and one of them failed on its first run.
- ✅ **The criterion "CI is green" is falsified and has been replaced**, not
  supplemented.
- ⚠️ The `LOG_LEVEL` parity finding is fixed in the allowlist but not explained, and
  its cause is the same class of drift that caused this.

## 8. Recovery

**Classified: verification failure — and specifically, a falsified criterion rather
than a failing check.** Those are different findings and conflating them is the
central error in this trace.

- A **failing check** against good work means the work is wrong, and the response is
  to fix it.
- A **falsified criterion** means the criterion was misstated. The work can be
  perfect and the criterion still wrong. The response is a task-model correction, and
  the first thing that is forbidden is loosening the check.

`recovery-system.md` is explicit: *the first response is never to loosen the check.*
So the three responses this trace could have taken, and did not:

**1. Rerun CI (blind retry).** CI was green; the symptom was elsewhere; a second
green run is the same run. And if it had come back red, the action would have been
to investigate a flaky suite, which is a different problem with a different cost. The
step that actually found the bug was reading a stack trace: eleven seconds.

**2. Loosen the check.** Three variants, all available, all wrong:

- *Increase the timeout.* There is no timeout involved. The call is not slow, it is
  null. A longer timeout would have made the 500s take longer.
- *Add a retry around `cache.get()`.* Null is not a transient failure. A retry
  returns null again, three times, then throws — a slower version of the same
  defect, and one that would have made the 40% look like a latency problem in the
  next incident.
- *Mark the test flaky.* The test was not flaky. The **criterion was wrong**, and a
  flaky marker on a passing suite is a false statement about reliability, which is
  exactly the information an on-call engineer needs and cannot afford to have
  corrupted.

**3. Fix the environment and stop.** Restoring `REDIS_URL` alone would have turned
staging green within ten minutes. It would also have left a module that returns
`undefined` where its callers expect `null`, a chart that can lose a key without any
check noticing, and a test suite that cannot see the failure — which is why the
next occurrence would have been found the same way, by a customer report or an
on-call engineer, three months later.

**The second recovery, a real one.** The first version of the config-parity test
compared the chart's keys against a checked-in list of CI keys and reported
differences as a warning, so it passed on a repo where the two had diverged. That
is a check that cannot fail on the thing it exists to detect. It was rewritten to
derive the key set from the compose file at runtime and to exit non-zero, and it
immediately failed on `LOG_LEVEL`. **A test that passes on the state it was written
for is a description, not a check.**

## 9. Delivery

**Outcome. Staging's 40% 500 rate is 0 — 0 of 18,442 requests over 30 minutes,
measured on the exact error type that was failing.** The root cause is a chart key
commented out on 2026-07-02, three weeks before this release, combined with a cache
module whose "no cache configured" path returns `undefined` where its callers expect
`null`.

**Three changes, and the second is the one that stops it recurring:**

1. `REDIS_URL` restored in `deploy/web/chart-values-prod.yaml`, from the secret
   rather than a literal.
2. `getClient()` now **returns `null` on the optional path** — the contract the
   callers were written against — **and throws when `CACHE_REQUIRED=true`**. A
   missing required cache is a startup failure naming the client, not 40% of
   requests.
3. Two new tests: `--cache-mode=off`, which runs the whole suite with the cache
   unconfigured, and `--config-parity`, which compares the chart's non-secret
   environment keys against `docker-compose.ci.yml` and fails on anything
   unaccounted for.

**The finding that matters is not the fix.** The suite reproduces the production
failure in 2m41s:

```console
$ REDIS_URL= npm test --workspace=services/web          # CI's configuration
  ✓ 214 passed
$ REDIS_URL= npm test --workspace=services/web -- --cache-mode=off
  ✗ 1 failed — the production stack trace, exactly
```

**CI was green and staging was broken because the criterion "CI is green" never
checked the path that staging runs.** That criterion has been replaced rather than
supplemented — adding a test while keeping the falsified one would leave the reason
this happened in place. And the parity test failed on its *first* run, on a fourth
undeclared difference (`LOG_LEVEL`), which is the point of it.

**The three responses this did not take**, because taking any of them would have
shipped the defect: rerunning CI, which is blind retry and would have produced the
same green run; adding a retry around `cache.get()`, which retries a null and makes
a correctness bug look like a latency problem; and marking the test flaky, which
would have been a false statement about reliability to the on-call engineer who
needs it.

**Evidence.** The stack trace, naming `src/cache/redis.js:41`. The chart diff,
showing the key commented out at line 24 on 2026-07-02 with a reference to #4471.
The suite green in CI's configuration and red in the cache-off configuration, before
and after the fix. The parity test's first-run failure. 18,442 requests and zero
TypeErrors in the 30 minutes after redeploy.

**Assumptions.**
- A1 ("CI exercises the paths staging runs") — **contradicted.** It does not, and
  that is the run's central finding. Every conclusion below follows from breaking
  this assumption rather than from working around it.
- A2 (staging runs the chart's values) — **held**; `helm get values` was empty and
  matches the file.
- A3 (40% of requests, a route subset) — **corrected in detail**: it is 40% of
  requests and all of them are on the `getPriceWithFallback` path, which is why the
  rate is a round figure rather than a scatter.

**Limitations.**
- **The cause of the 2026-07-02 revert is not established.** Line 24 references
  #4471, which I did not read. Whether it was a deliberate "the secret is injected
  elsewhere" change or an accident is the recurrence risk, and it is the platform
  team's question rather than this service's.
- `LOG_LEVEL` is in the same parity class and its allowlist entry says "benign" —
  which is my judgement, not a checked fact.
- The cache-off mode runs the suite with the environment variable unset. It does not
  exercise a *partially* configured cache, which is the adjacent failure and remains
  untested.
- The fix was verified over 30 minutes. A cache that fails after a TTL expiry or a
  pod eviction would not have shown up in that window, and the module's behaviour on
  eviction is not covered by the new tests.
- The `cache_required` flag defaults to `true` in production and `false` in staging
  for one release, which means staging is *not* currently testing the required path
  end to end. It is testing it from the next release.

**Confidence.** High that the immediate defect is fixed — the exact error type, zero
occurrences in 18,442 requests, and a test that reproduces the failure on the old
code. High that the class will be caught next time, because the parity test failed
on its first run on a different key. **Medium on the recurrence prevention overall**,
because the flag keeps staging off the required path for one release and the
underlying revert is unexplained.

**Verification status.** VERIFIED against all four criteria. One recovery occurred,
was classified as a falsified criterion rather than a failing check, and cost one
extra unit — a test written to fail on the pre-fix code — which was the unit that
found the problem.

## 10. Learning

**Candidate, not promoted.** When a check passes while the system fails, test the
*criterion* before the work: enumerate what the criterion does not exercise, and
find the branch that production takes and the test configuration does not. The
`--cache-mode=off` run is that test, and it took two and a half minutes.

**What evidence would be needed to promote it.** A second instance in this
repository where a green CI and a broken staging were caused by a configuration
divergence rather than a code defect. One instance is suggestive, and the general
form — *a check's validity is a property of the check's configuration, not of the
check* — is a strong idea that this run has tested exactly once. It also has a
clear false-positive mode (environments that are *meant* to differ), which is why
the parity test ships with an allowlist rather than as a hard rule.

**A second candidate, specific and better supported.** A config-parity test should
derive its expected values from the deployment artefact at runtime, and should exit
non-zero. The first version compared against a checked-in list and passed on the
diverged state, which means a check can be present, run in CI, and be incapable of
failing on the thing it was written for.

**Not worth retaining:** 18,442, `redis.js:41`, `LOG_LEVEL`, the 30-minute window.
All in the commit, the tests, and this document.

**Routed rather than created.** A `deployment-config-parity` capability — derive
non-secret keys from the deployment artefact, compare against the test environment,
require an allowlist entry with a reason for every difference — is genuinely
reusable and will be needed in every service that has a chart and a compose file.
It goes to `skill-creator` with the scope "Node services deployed by Helm", and it
should be written as a script first, because the mechanism generalises further than
the framing does.

## What this example proves

- **A falsified criterion is a different finding from a failing check.** CI's
  greenness was met and the system was broken, which means the criterion was
  misstated, and the response was a task-model correction rather than more tests.
- **The three tempting fixes were all rejected with reasons.** Rerunning CI is
  blind retry; a retry around `cache.get()` retries a null and disguises a
  correctness bug as latency; a flaky marker corrupts the reliability information
  an on-call engineer depends on.
- **The defect was made reproducible outside production in 2m41s**, and the
  reproduction is the diagnostic tool as well as the regression test.
- **A check that passes on the state it was written for is not a check.** The parity
  test's first version compared against a checked-in list and passed on a diverged
  repo; rewritten to derive its inputs, it failed immediately on a different key.
- **Restoring the environment alone was the wrong fix.** It would have left a module
  returning `undefined` where callers expect `null`, and the same drift would have
  been found by a customer three months later.
- **The proximate cause was three weeks old and unrelated to the release.** Reading
  the release diff — the most natural first move — would have looked in the wrong
  place for an hour.
- **A limit is stated where it matters.** Staging is off the required path for one
  release by design, and the deployment notes say so rather than leaving the flag to
  be discovered later.
