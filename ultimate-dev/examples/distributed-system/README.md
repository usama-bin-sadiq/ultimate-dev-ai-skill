# Distributed-system traces

Two objectives where the fault crosses a process boundary, so neither can be
reasoned about from inside one codebase. In both, the tempting fix is a local
change that makes a symptom go away without changing the invariant that was
violated.

The kernel has no opinion about consensus, partitions, or clocks. What it has is
an effort gate, a place to record what a decision *rejected*, and a rule that a
failure is classified before it is responded to. Those are enough to stop both of
the failure modes below, and they are enough whether the domain is distributed
systems or accountancy.

## Kernel mechanisms stressed

- **The local fix versus the invariant.** A bounded retry, a longer lock TTL, a
  bigger connection pool — all of these make the symptom disappear and none of
  them address the condition. Both traces name the invariant that was violated
  and fix that instead.
- **Time as a hidden variable.** Both failures turn on a duration nobody had
  written down: an 11.4-second critical section under a 5-second lease, and a
  360-second poll loop under a 300-second rebalance interval. Neither number
  existed anywhere in the source until the trace measured it.
- **Assumptions carrying consequences.** "The critical section is short" and "the
  handler is fast enough" are both recorded with what breaks if false, and both
  are false.
- **Verification that can fail.** A clock-injected test that forces the failure
  deterministically, and a rolling-restart measurement, not a unit test of the
  happy path.
- **De-escalation by measurement.** In `kafka-rebalance-after-pod-restart.md` the
  first proposed fix — raising `max.poll.interval.ms` — is rejected on measurement,
  because it makes rebalance detection slower rather than rebalancing faster.

## Traces

| File | Objective | Scale / Rung | Verdict | Load it for |
|---|---|---|---|---|
| [`redis-lock-without-fencing.md`](redis-lock-without-fencing.md) | Fix a nightly settlement job that ran twice and disagreed with the bank by £48,200 | L3 / **R2 → R3** | VERIFIED | A lock that prevents overlap but cannot prevent *staleness*, and the monotonic token that fixes it |
| [`kafka-rebalance-after-pod-restart.md`](kafka-rebalance-after-pod-restart.md) | Cut 4–7 minute rebalances after a pod restart below 30 seconds | L3 / **R2** | VERIFIED | Rejecting the obvious fix because a measurement says it fixes the wrong thing |

## Reading notes

**`redis-lock-without-fencing.md` is the one to read for correctness reasoning.**
The mechanism is that a distributed lock is not a mutex: it bounds how long two
workers can *believe* they are alone, and a worker that is descheduled past its
lease keeps writing. The fix is not a longer TTL. The fix is a number the store
can compare — a fencing token — so that a late writer is rejected by the thing it
is trying to write, rather than trusted because it believes it holds a lock.

**`kafka-rebalance-after-pod-restart.md` is the one to read for effort
discipline.** The user asked for a latency improvement, the kernel's first answer
was a well-known configuration change, and measurement showed that the first
answer was wrong about which quantity it improved. The trace keeps the rejected
option in the record with the number that killed it.

## Adjacent examples

- [`../software-engineering/retry-storm-node-upload-client.md`](../software-engineering/retry-storm-node-upload-client.md)
  — the same Node service, and the case where the amplifier was on the other side
  of the process boundary entirely.
- [`../recovery/`](../recovery/) — two failures classified before they were
  responded to, which is the discipline both of these depend on.
- [`../cross-domain/`](../cross-domain/) — where several domains have to be
  composed rather than one traversed.
