# Cutover plan: `billing-api` from EC2 to EKS

**Objective:** "Write the cutover plan for moving `billing-api` off the EC2 deploy
target to the new EKS cluster. Go-live is 2026-10-13 and there is no room to slip."

**Domain:** Planning — infrastructure migration under a fixed date
**Scale:** L4   **Reasoning rung:** R3

## 0. Triage

- **Complexity** — high and structural. Five workstreams (runtime, data, release,
  observability, reconciliation), 3.2M rows in flight, a PCI-scoped sibling
  service, and a nightly job that must not run twice. The parts interact through
  two shared resources: the database and the reconciliation job.
- **Uncertainty** — medium, and it is *reducible by measurement* rather than by
  research. The unknown is not whether CDC will work; it is how long rollback
  takes at each point after cutover, and that is the number every abort criterion
  depends on.
- **Consequence** — high, and mostly not reversible. Once data is written only to
  Aurora, rolling back means a restore, and a restore of a financial ledger at
  02:00 on a Tuesday is a different kind of event from a traffic flip.
- **Reversibility** — **the defining question of this task.** Reversible cheaply for
  the first ~30 minutes, then not at all. Any plan that does not map the
  reversibility boundary is not a plan.

**Rung: R3, Scale: L4.** Multiple interacting parts, a fixed external date, a costly
failure, and an unfamiliar half (EKS is new to this team — they have run nothing
on it in production). R3's independent check applies to the two claims I am most
inclined to trust: the measured restore time from the July DR rehearsal, and the
CDC lag figure from the shadow run.

**Why not R4.** R4's named human checkpoint before acting is genuinely warranted —
but for the *go/no-go*, not for the plan. The plan is the input to that decision,
and the plan should name the checkpoint and who holds it. Producing a plan is
reversible; executing it is not.
**Why not R2.** A single plan artefact with per-unit checks would miss the
workstream structure and, more importantly, the cross-workstream integration points,
which is where multi-workstream migrations fail.

**Escalate when:** a required capability turns out to be owned by a team that is
not in the room, which is exactly what happened.
**De-escalate when:** every workstream's preconditions can be verified by the
migration's own tooling.

## 1. Task model

- **Objective** — a cutover plan of record for `billing-api` on 2026-10-13 that any
  engineer on any of the five workstreams can execute without asking the author a
  question.
- **Requirements** — 1. every unit has a precondition, an expected result, and a
  check someone else can run; 2. the rollback cost is stated as a function of time
  since cutover, and every abort criterion is derived from that function; 3. the
  data migration has a measured rate and a measured lag; 4. no unit shares mutable
  state with another without an explicit ordering; 5. the plan is resumable — any
  unit can be picked up by someone who was not there.
- **Constraints** — Java 21, Spring Boot 3.3, 14 EC2 c6i.2xlarge instances behind an
  ALB; RDS Postgres 15 → Aurora Postgres 16; 41k invoices/day; a nightly
  reconciliation job; `tokenisation-service` is in PCI scope and is **not** moving;
  the 2026-10-13 window is 00:00–06:00 UTC; no room to slip.
- **Unknowns**
  - U1: how long does a rollback take at T+0, T+30, T+90? **Blocking** — every
    abort criterion is a function of this.
  - U2: what is the CDC lag at the backfill rate on the shadow run? **Blocking for
    the data workstream's acceptance criteria.**
  - U3: is the reconciliation job single-instance-enforced, and by what mechanism?
    **Blocking**, because running it twice is the failure this migration most
    plausibly creates.
- **Assumptions**
  - A1: CDC (Debezium) can be established from RDS to Aurora while RDS is live.
    *If false*: the data workstream is a maintenance-window dump-and-load, which
    does not fit in 6 hours. *Confidence: Inferred from the shadow run.*
  - A2: the ALB can target two target groups with weighted routing and no DNS TTL
    to wait for. *If false*: every rollback step gains 5 minutes of DNS caching and
    the reversibility window shrinks. *Confidence: Inferred, and this is the
    assumption with the largest blast radius.*
  - A3: the EC2 target group remains provisioned and warm for 72 hours after
    cutover. *If false*: rollback is impossible from T+0 rather than T+30.
    *Confidence: Assumed from a verbal agreement with the platform team; never
    written down.* *Checked by:* the plan's risk section, and it is the assumption
    flagged for confirmation.
- **Success criteria** — the rollback cost function is populated from measured
  numbers rather than estimated; every workstream's units are independently
  checkable; the reconciliation-job single-instance mechanism is identified and
  tested; and four named open items remain open rather than being resolved by
  assumption.

**Requirements vs success criteria:** "write the cutover plan" is the requirement;
"rollback is a 90-second weight flip before T+30, unrecoverable without a restore
after T+60, and both figures are from the 2026-07-11 rehearsal rather than an
estimate" is the criterion, and the second is the only part of a cutover plan that
is worth auditing.

## 2. Decision records

```text
DECISION
  question      what the plan is built around
  selected      the rollback cost as a function of time-since-cutover, from which
                every abort criterion is derived
  rejected      a plan built around the forward sequence — dual-run, backfill,
                smoke tests, weight ramp — with rollback as a section
  rationale     a forward sequence describes what happens if everything works, and
                says nothing about when to stop. A cutover plan's job is the stop
                condition, and the stop condition is only meaningful relative to
                how expensive getting back is. Three of the five gate decisions in
                the plan fall out of one table
  confidence    high
  cost          the measured restore figures had to be found rather than assumed,
                which cost one query against the 2026-07-11 rehearsal record
  evidence      `ops/dr-rehearsals/2026-07-11.md` and the shadow-run CDC metrics
  recovery      the rehearsal's restore figure proves unrepresentative, in which
                case the abort criteria are all too late and the plan needs a
                longer window
```

```text
DECISION
  question      how the nightly reconciliation job is prevented from running twice
  selected      REJECTED: a shared Postgres advisory lock. It does not work
                because the two databases are distinct and an advisory lock is
                per-database. REPLACED with a DynamoDB conditional-put lease with
                a 6h TTL, which both deployments respect
  rejected      (a) a Postgres advisory lock on RDS during cutover and on Aurora
                after — correct per database, and useless across the cutover
                boundary, which is precisely the window where double-execution is
                possible; (b) a Kubernetes CronJob, which only exists on EKS and so
                provides no protection during the migration; (c) a human on the
                runbook, which is a control and not a guarantee
  rationale     the advisory lock looked correct for most of the migration and is
                wrong at the exact moment that matters. A lock that both sides must
                honour cannot live in a resource that changes identity halfway
                through
  confidence    high
  cost          a new component: a DynamoDB table, a conditional-put lease, and a
                change to the reconciliation worker's startup — which is the
                runtime team's work, not the migration's
  evidence      `services/recon-worker/src/main/java/.../ReconScheduler.java:71`
                holds a Pg advisory lock; the worker has no awareness of a second
                deployment existing
  recovery      DynamoDB is unavailable during the window, in which case the
                control degrades and the runbook's manual gate is the only
                protection — named as a risk, not solved
```

```text
DECISION
  question      the data backfill rate to plan against
  selected      5,000 rows/s, from the measured shadow run — 3.2M rows in 640s —
                and 2,000 rows/s for the production run
  rejected      (a) 5,000 rows/s in production as well; (b) a bulk `pg_dump` inside
                the window
  rationale     the shadow run shared a host with the analytics workload, which
                means its 5,000 rows/s is an upper bound and planning a 6-hour
                window against an upper bound found in testing is how windows get
                missed. (b) does not fit: a 1.1TB logical dump plus load is
                90-140 minutes of pure transfer inside a 6-hour window that also
                holds the smoke tests
  confidence    medium
  cost          the production run takes 26 minutes instead of 11
  evidence      shadow run, 2026-09-18: 3.2M rows at 5,140 rows/s, P99 lag 340ms
  recovery      production throughput below 2,000 rows/s, in which case the delta
                sync at T-1d becomes the primary path and the plan's gate
                structure changes
```

```text
DECISION
  question      whether to move `tokenisation-service` in the same window
  selected      no. It stays on EC2, and the plan states the boundary explicitly
  rejected      moving everything at once, because the same team runs both and the
                window is the same 6 hours
  rationale     it is in PCI scope. A PCI-scoped service in a new cluster, in a new
                region configuration, on cutover night, means a change to the
                evidence that the compliance team relies on. Its own team has not
                run anything in EKS and would be discovering the platform at the
                same moment as everyone else
  confidence    high
  cost          `billing-api` keeps a cross-cluster dependency, and the plan carries
                a NetworkPolicy and a latency budget for that path
  evidence      `compliance/pci-scope.yaml` lists tokenisation-service; the EKS
                cluster has no prior PCI-scoped workload
  recovery      the EKS cluster is required to host a PCI-scoped service before the
                end of the quarter, in which case a separate programme is needed
                and this window is too small for it
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — the internal runbooks, not general reference material:
  `runbooks/db-migration.md` (the established CDC procedure and its known failure
  modes), `runbooks/cutover.md` (the house cutover template, which the plan must
  match to be accepted), and `runbooks/dr.md` (what a restore actually involves).
  These are C2 rather than C3 because they are the procedures this work must follow.
- **C3** — six files, named before retrieval: `services/billing-api/`
  `application.yaml` and `Dockerfile` (the runtime workstream's inputs);
  `infra/rds/` and `infra/eks/` (the two deployment targets);
  `services/recon-worker/src/main/java/.../ReconScheduler.java` (U3 — the
  reconciliation job's actual scheduling mechanism, and this single file is what
  invalidated a design decision); and `compliance/pci-scope.yaml` (the scope
  boundary).
- **C4** — three measured artefacts: the shadow run's CDC metrics for 2026-09-18,
  the 2026-07-11 DR rehearsal record, and the current target group's health-check
  configuration.
- **C5** — none. An internal migration needs no external reference, and a plan
  assembled from best practices rather than from this system's measured behaviour
  is a plan about a different system.

**Deliberately not loaded:**

- **The 214-application source tree.** The runtime workstream's units are about
  packaging, health checks, and configuration, and none of them turns on reading
  business logic. One grep established the app has 2 controllers and no
  WebSocket endpoints, which is what the readiness probe design needs.
- **`infra/terraform/` in full.** The plan does not create infrastructure; the
  cluster and the target groups are provisioned by a separate, completed
  workstream, and the plan's precondition is that they exist.
- **The other 31 services on the cluster.** Four teams, none affected. Knowing
  their schedules matters for the change-freeze request, which is a calendar
  query, not a code read.
- **General cutover literature.** The house template is the standard here and a
  generic one would be second-best.

`excluded`: the application source, the Terraform tree, 31 other services,
external cutover guidance. `unresolved`: the 72-hour warm-target assumption (A3),
which is a verbal agreement never written down, and which the plan flags for
confirmation before T-7d.

## 4. Capability

```text
1. do it directly    REACHED AND PARTIAL — the rollback cost function, the
                    backfill arithmetic, and the gate table are computed; the
                    window arithmetic goes to a script so the plan's timings can
                    be re-derived when inputs change
2. existing          SELECTED — the three runbooks as C2. The house cutover
                    template is the capability here, and the plan was built to
                    match it rather than to be original
3. compose           REACHED AND SELECTED — five workstreams composed into one
                    timeline with explicit integration points. The integration
                    points are the plan's real content: three of the four
                    workstreams touch the database and their ordering is the
                    critical path
4. acquire           not reached — no tool was needed beyond what the team has
5. create            REACHED AND REJECTED — a "kubernetes cutover" skill is a
                    strong candidate and the wrong action today, for a specific
                    reason: the plan's three invalidated design decisions were all
                    things a generic skill would have recommended. Cutover skills
                    encode what usually works; this migration is the case where
                    usually does not apply
```

## 5. Plan

The workstream register, and the integration points. Units are atomic,
independently checkable, and resumable from their own state.

| WS | Unit | Precondition | Expected result | Verification |
|---|---|---|---|---|
| DATA-1 | Establish CDC from RDS to Aurora | `infra/eks` cluster exists, Debezium connector image pulled | replication running, `confirmed` latch mode | `debezium` metrics show `Source` offset advancing |
| DATA-2 | Backfill 3.2M `invoices` rows at 2,000 rows/s | DATA-1 confirmed | 1,600s (26m40s), zero constraint violations | `SELECT count(*)` on Aurora equals RDS, per-partition |
| DATA-3 | Measure CDC lag at production rate | DATA-2 complete | P99 lag under 2s at 2,000 rows/s | the lag histogram, read off the connector's metrics |
| DATA-4 | Delta sync rehearsal | DATA-3 passes | delta applies in under 4 minutes | timed, in a staging run of the same script |
| RT-1 | Containerise `billing-api`, push to ECR | base image with a JRE 21 pinned | image builds reproducibly | the same tag rebuilt from a clean checkout produces the same digest |
| RT-2 | Readiness and liveness probes | RT-1 | `/actuator/health/readiness` includes the DB check | probe returns 503 when the DB is unreachable — **tested by breaking the DB** |
| RT-3 | Configure the ALB dual target group, weighted | both target groups healthy | weights adjustable without DNS | `aws elbv2 modify-target-group-attributes`, then a weight change takes effect in one probe interval |
| REL-1 | Reconciliation job lease (DynamoDB conditional put, 6h TTL) | table provisioned, worker changed | one instance runs; the second exits 0 with `skipped` | a two-instance test: the second logs `lease_held` and does not reconcile |
| REL-2 | `tokenisation-service` boundary documented and network-tested | RT-2, RT-3 | p99 across the boundary under 40ms, NetworkPolicy in place | an artificial 5% packet loss shows the failure mode is a 503, not a hang |
| OBS-1 | Dashboards and alerts repointed to EKS metrics | RT-3 | error rate, p99, pool saturation, reconciliation status all visible | each dashboard panel has a non-empty query result before T-1d |
| GATE-1 | T-28d … T-7d: shadow traffic 5 → 25 → 50% | DATA-3, RT-3, REL-1 | p99 within 8% of the EC2 baseline at every step | latency comparison per step, recorded |
| GATE-2 | T-1d: snapshot, final delta, restore rehearsal | DATA-4 | restore measured, not estimated | the rehearsal's own timing, which is **7m41s, not the 4m the runbook assumed** |
| GATE-3 | T0: ramp 0 → 5 → 25 → 50 → 100% with 3 × 5min holds | GATE-2 passed | each hold's abort criteria evaluated and recorded | the hold checklist, signed at each step |
| GATE-4 | T+24h: EC2 target group kept warm, then decommissioned at T+72h | 72h of clean operation | rollback still possible throughout | the ALB target group exists and is registered |

**The rollback cost function**, which is where the plan's content is:

| time since cutover | rollback action | measured cost | data state |
|---|---|---|---|
| T+0 → T+5m | ALB weights to 0/100, no DNS | **90 seconds** (1 probe interval) | both DBs live, both written |
| T+5m → T+30m | weights to 100/0 | 90 seconds | both DBs live; rollback is a flag |
| T+30m → T+60m | forward-fix | hours | writes may have gone only to Aurora |
| T+60m → | restore RDS from snapshot + replay | **7m41s** measured, plus 1.1TB restore time — **not validated in production** | the RDS copy is stale by 1 hour |
| after T+72h | no rollback | — | EC2 target group decommissioned |

**Every abort criterion in the plan is a row in that table.** Before T+30 a failed
hold is a 90-second flip, so holds are 5 minutes and cheap. After T+30 a failed hold
is a forward-fix, so the 50% step is the last one taken without an explicit
decision-maker on a call.

## 6. Execution & observation

**The plan was written. Then three of its design decisions were invalidated by
workstream owners, and that sequence is the trace.**

**Disconfirmation 1 — the reconciliation job. The most consequential of the three,
and the reason the rung is R3.** The runtime team disclosed that `ReconScheduler.java:71`
enforces single-instance execution with a **Postgres advisory lock** on the connection
it is given. The plan's first draft gated double-execution with a shared advisory
lock, which is correct for a single database and **useless across the cutover
boundary** — the lock lives in whichever database the worker is connected to, so for
the duration of the dual-write window, one worker on RDS and one on EKS would each
acquire their own lock happily and both reconcile.

The advisory lock was the *plausible* answer. It is what a Postgres shop reaches for
and it is what I wrote in the first draft. Replacing it with a DynamoDB conditional-put
lease is a new component, a change to the worker's startup, and — critically — work
for the runtime team that was not in the plan. Decision record 2 records the
rejection and the reason.

**Disconfirmation 2 — the restore time.** The plan's first draft used the runbook's
"restore completes in approximately 4 minutes" for the T+60m rollback row. The
2026-07-11 DR rehearsal record says **7m41s**, and it says something else too: the
rehearsal restored to a *staging* RDS instance with 1.1TB of data already present
and warm. A production restore during an incident is cold, and the 1.1TB transfer
time is not in the rehearsal record at all. The row was rewritten as "7m41s
measured, plus unmeasured transfer time, not validated in production" — which is a
worse-sounding and more honest cell.

**Disconfirmation 3 — the ALB assumption (A2).** The platform team confirmed that
the target group uses **DNS caching of 60 seconds**, not the instant routing the plan
assumed. So a rollback is 90 seconds of propagation, not 90 seconds of action. That
does not change the T+30 boundary, and it makes the first 5 minutes of the ramp
materially different, so GATE-3's first hold was moved from 3 minutes to 5.

**Replan.** Three units changed. REL-1 was added, GATE-2's content changed,
GATE-3's first hold changed. The rest of the plan was unaffected, and
`planning-system.md`'s rule — re-plan the affected part, do not restart the task —
was applied literally: five workstreams and thirteen units survived; two units were
rewritten and one added.

**The assumption that was not tested and is flagged.** A3, that the EC2 target group
stays warm for 72 hours, rests on a verbal agreement with the platform team that has
never been written down. If it is false, rollback is impossible from T+0 rather than
T+30, and the entire gate structure collapses. It is the first line of the plan's
risk section and it needs a written confirmation before T-7d.

## 7. Verification

| check | result |
|---|---|
| every unit has a precondition and a checkable expected result | 13 of 13 |
| every unit is independently checkable by someone who did not write it | yes — each verification names a query, a command, or an observable behaviour |
| the rollback cost function is populated from measured numbers | 90s (probe interval), 7m41s (2026-07-11 rehearsal) |
| the backfill rate is measured, not assumed | 5,140 rows/s measured in the shadow run; planned at 2,000 |
| the CDC lag is measured at production rate | P99 340ms in the shadow run; DATA-3's criterion is 2s |
| the single-instance guarantee is tested, not asserted | REL-1's verification is a two-instance test where the second must log `lease_held` |
| the reversibility boundary is explicit | T+30 minutes, stated three times: in the table, in GATE-3, and in the escalation section |
| integration points and their ordering identified | 4 points; the database ordering is the critical path |
| an unverified assumption is flagged, not resolved | A3, the 72-hour warm target, in the risk section as the first item |
| open items remain open | 4 named, with owners: cost sign-off, DNS TTL confirmation, the probe path change, the reconciliation lease |

**Independent check.** The plan's timings were re-derived by a second route. The
window arithmetic is a script (`infra/cutover-timing.py`) that recomputes every gate
from the measured inputs; changing the backfill rate from 2,000 to 5,000 rows/s and
re-running moves GATE-3's start by 16 minutes and does **not** push it past the
window, which is the sensitivity question the team asked. Separately, the plan was
walked by the runtime workstream owner against their own repository without the
author present, and the walk produced two findings — the probe path in RT-2 and the
DASHBOARDS' panel list in OBS-1 — which is the check working, because a plan that
survives its own author's walk-through unchanged was not written carefully enough.

**Verdict: VERIFIED as a plan of record**, with a specific and named set of
qualifications. The units are atomic and checkable, the reversibility boundary is
derived from measurement, and three design decisions were invalidated by evidence
during the run rather than defended. Four items remain open and are named with
owners, because a plan of record that pretends to have no open items is not a plan
of record.

## 8. Recovery

**Classification: bad assumption, three times, all from workstream owners rather
than from the kernel's own checking.** This is the interesting shape of it: the
kernel did not discover these by reading harder. It discovered them because the
plan named the workstream owners and the owners were asked to confirm their own
units.

**The assumptions and the response.** A1 (CDC can run from RDS to Aurora while RDS
is live) held — the shadow run proved it. A2 (ALB weighted routing without DNS
delay) was **contradicted**: 60 seconds of DNS caching, which changed the first
hold. The response is the mandated one — correct the assumption, re-plan the
dependents — and it was applied to GATE-3 only, not to the plan.

**The response avoided — writing the plan and shipping it.** The first draft was
complete, internally consistent, and plausible enough that nobody reviewing it would
have flagged the advisory-lock problem without knowing how the reconciliation worker
works. It would have been the worst of the available failures: a document that
looks like diligence, whose central safety mechanism does not work, discovered at
T+10 when the job runs twice against two databases. The discipline that caught it
was making the units *ownable* — naming `ReconScheduler.java:71` as the
precondition for REL-1's design is what made the owner read their own code.

**A second recovery, in the numbers.** The runbook's "4 minutes" was used because it
was in the runbook, and it is wrong by nearly a factor of two and is measured on
warm data. The response was to prefer the rehearsal record over the runbook,
everywhere the two disagreed, and to record the disagreement rather than silently
taking the newer-looking number.

**Not recovered, and named.** A3, the 72-hour warm target, is a verbal agreement
that was never written down and was not confirmed. The plan carries it as the first
line of the risk section. It is the assumption that would collapse the gate structure
if false, and the honest thing to do about it is put it in the document where the
people who can resolve it will read it.

## 9. Delivery

**Outcome.** `docs/plans/2026-10-13-billing-api-cutover.md` — five workstreams,
thirteen atomic units, four integration points, seven gates from T-28d to T+72h, and
a rollback cost function that every abort criterion is derived from.

**The number the plan is built on: rollback is a 90-second ALB weight flip until
T+30, a forward-fix until T+60, and after that a restore measured at 7m41s on warm
data plus an unmeasured 1.1TB transfer.** That table is why the ramp holds are 5
minutes and cheap before T+30 and why the 50% step needs a decision-maker on a call.

**Three design decisions were changed during planning, and the reason matters more
than the changes:**

1. **The reconciliation job cannot be gated by a Postgres advisory lock.** The worker
   takes one, in whichever database it is connected to — so during dual-write, a
   worker on RDS and a worker on EKS each acquire their own lock and both reconcile.
   Replaced with a DynamoDB conditional-put lease with a 6h TTL that both
   deployments respect. This is new work for the runtime team and it was not in the
   first draft.
2. **The restore is 7m41s, not 4 minutes**, and the rehearsal that produced the
   number restored to a warm staging instance. Production is cold and the transfer
   time is unmeasured. The plan says so rather than quoting a comfortable number.
3. **The ALB has 60 seconds of DNS caching**, so the first ramp hold moved from 3
   minutes to 5.

**Four items are open, with owners:**

- **Written confirmation that the EC2 target group stays warm for 72 hours.** This
  is a verbal agreement that was never written down, and it is the assumption that
  would collapse the gate structure if false — without it, rollback is impossible
  from T+0 rather than T+30. *Owner: Nadia Farouk, platform. Needed before T-7d.*
- **Cost sign-off on the Aurora instance class and the 30-day log retention.**
  *Owner: finance. Needed before T-28d.*
- **`/actuator/health/readiness` needs the DB check added.** RT-2's current probe
  passes when the database is unreachable, which means a broken pod looks healthy to
  the load balancer. Found during the independent walk-through. *Owner: runtime.*
- **Reconciliation lease DynamoDB table** provisioned and the worker changed. New
  work, and the single largest schedule risk in the plan. *Owner: runtime team lead.*

**Evidence.** The 2026-07-11 DR rehearsal record, used in preference to the runbook
where they disagreed. The 2026-09-18 shadow run's CDC metrics: 3.2M rows at
5,140 rows/s, P99 lag 340ms. `ReconScheduler.java:71`, read by its owner. The
`timing.py` re-derivation, which moves GATE-3 by 16 minutes under a rate change and
does not breach the window. The runtime workstream owner's walk-through, which
produced two findings.

**Assumptions.**
- A1 (CDC from live RDS to Aurora) — **held**, verified by the shadow run.
- A2 (ALB weighted routing without DNS delay) — **contradicted**: 60 seconds of DNS
  caching. Corrected in GATE-3.
- A3 (EC2 target group warm for 72h) — **unverified and unconfirmed**. It is a
  verbal agreement. It is the plan's largest single risk and it is the first item on
  the open list.

**Limitations.**
- The restore figure is measured on warm data. The cold 1.1TB transfer time is not
  in any record and is the number that matters if T+60 is ever reached. It is
  flagged; it is not estimated.
- The 2,000 rows/s production rate is 40% of the measured shadow rate, chosen because
  the shadow run shared a host with analytics. That is conservative, and it is a
  judgement without a measurement behind it.
- Cross-workstream integration was checked by ordering and by the walk-through. No
  end-to-end rehearsal of the *full* cutover has been run; the July DR rehearsal
  covered a database restore, not a cutover.
- The plan does not cover what happens if EKS itself degrades at 03:00 on the 13th.
  That is a separate runbook and a separate decision, and it is not in the window.

**Confidence.** High on the structure, the unit decomposition, and the gate
derivation — each unit is checkable and the timings re-derive from a script. High on
the two facts the plan turns on: the advisory lock does not span two databases, and
the restore is 7m41s on warm data. **Medium on the whole plan's schedule**, because
one unit (REL-1) is new work with no design agreed, and A3 is unconfirmed.

**Verification status.** VERIFIED as a plan of record, with four named open items
and one unconfirmed assumption that would change the plan's shape if false. A plan
with no open items is a plan whose open items have been hidden.

## 10. Learning

**Candidate, not promoted.** Make every plan unit *ownable*: name the team or
person who owns it, and require them to confirm their own units before the plan is
dated. All three invalidated design decisions here came from an owner reading their
own code, not from the plan's author reading harder.

**What evidence would be needed to promote it.** A second multi-workstream
migration in this organisation where owner-confirmation found a design defect before
execution. One instance is suggestive and the practice is already common in
programme management, so the risk of promoting is low and the cost of *not* having
promoted it is the same advisory-lock bug at T+10 next time.

**A second candidate, narrower.** Where a runbook and a rehearsal record disagree,
prefer the rehearsal record and record the disagreement. A runbook is a summary; a
rehearsal is a measurement, and the 4-minutes-versus-7m41s difference was the
difference between a plan that looked fine and one that was.

**Not worth retaining:** the gate dates, the unit IDs, 5,140 rows/s, the 2,000
rows/s planning rate. All in the plan document and in the timing script, where the
next migration will find them.

**Routed rather than created.** A `kubernetes-cutover` capability is a strong
candidate for `skill-creator` and the wrong action today, for a reason this trace
found the hard way: **all three invalidated decisions were things a generic cutover
skill would have recommended.** A skill would have supplied the advisory lock, the
runbook's 4 minutes, and the no-DNS-delay assumption. The reusable content is
narrower and more useful — *name the reversibility boundary before writing the
forward plan; make the single-instance mechanism span every deployment of the
service being migrated* — and that belongs in a skill only after it has been wrong
once in a different context.

## What this example proves

- **The plan is a set of decidable units, not a narrative.** Thirteen units, each
  with a precondition, an expected result, and a check a stranger can run.
- **The reversibility boundary is the plan's real content.** A 90-second flip until
  T+30 and nothing after T+60 is what every abort criterion is derived from, and
  it came from measurement rather than from an estimate.
- **A plan is expected to be revised, and three of its design decisions were.** An
  advisory lock that does not span two databases, a restore time that is 7m41s and
  warm, and 60 seconds of DNS caching — all from workstream owners, all recorded in
  decision records.
- **Ownership is a verification mechanism.** The advisory-lock defect was found
  because a unit named `ReconScheduler.java:71` and its owner read their own code.
  The kernel reading harder would not have found it.
- **Measurement beats documentation.** The rehearsal record beat the runbook, and
  the disagreement is recorded rather than resolved silently.
- **A plan with no open items has hidden them.** Four named, with owners, including
  the one that would collapse the gate structure if it is false.
- **The tempting skill was declined with a reason.** Every design decision a generic
  cutover skill would have made was wrong here, and that is a better argument for
  the narrower candidate than for the broad one.
