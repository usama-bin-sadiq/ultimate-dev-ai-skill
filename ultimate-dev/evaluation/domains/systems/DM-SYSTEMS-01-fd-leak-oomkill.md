## DM-SYSTEMS-01 — FDs leak over three days, then the pod is OOMKilled

**Class:** medium
**Kernel specialisation:** none — the kernel has no code path for this domain, and no
domain-specific agent is available to it
**Domain:** systems
**Rung:** R2 Analytical
**Scale:** L3
**Primary metric:** task success, with correctness of the mechanism
**Score rule:** rate

**Fixture:** A container that has run for 3 days gets OOMKilled and restarted. Its
memory rises linearly: 180 MiB at hour 0, 1.9 GiB at hour 72, limit 2 GiB. The
`/proc/1/fd` count rises in step: 14 at hour 0, ~2,900 at hour 72. The container
has `limits.memory: 2Gi` and no CPU limit. A sidecar writes an entry to a
`/var/log/trace` file per request via a `logrotate`-managed handle opened inside
the request handler and never closed. Heap profiles show no object retention
growth.

**Prompt:**
> This pod gets OOMKilled every three or four days and I can never catch it in the
> act. Work out what's going on.

**Expected behaviour:**
1. Triage to R2 and look at the wrongness that matters. The user says "OOMKilled"
   and the pull is to treat it as a memory problem. The container is killed for
   exceeding its *memory limit*, which is not the same as leaking heap, and the
   distinction is decided by evidence already available.
2. Use the two curves. Memory and file-descriptor count rising in lockstep over
   time is a resource being consumed once per unit of work and never released.
   Heap profiles showing no retention growth independently exclude a heap leak.
3. Find the mechanism: a file handle opened per request inside the handler and
   never closed, in a component that was added 6 weeks ago. Each handle costs
   kernel memory, which counts against the cgroup limit whether or not it is
   JavaScript heap.
4. Fix it: open the log handle once, or use a rotating stream that owns its own
   lifecycle, and close on the error path too.
5. Address the observability problem the user actually stated. They cannot catch
   it in the act because it takes 72 hours. A memory-only alert at 85% would have
   fired 9 hours before the kill, and an FD-count alert would have fired on day
   one. Adding the alert is part of the answer, not an extra.
6. Verify: observe the FD count across a sustained run after the fix, or state
   that it cannot be observed in the time available and say so.

**Pass criteria:**
- The cause is identified as unreleased file handles, not heap growth.
- The correlation between FD count and memory is used as the evidence.
- The heap profile's flat retention is used to exclude the memory-leak
  hypothesis.
- The fix closes the handle or lifts it out of the per-request path.
- A monitoring change is proposed that would have detected this before 72 hours.
- The verification verdict is stated, and any projection is labelled as one.

**Fail criteria:**
- The memory limit raised, or heap size tuned.
- A GC tuning change, or a heap dump, proposed as the main line of attack.
- "Memory leak" stated as the diagnosis with the FD count ignored.
- The run reporting the leak fixed without observing the FD count after the fix.
- An alert proposed only on memory percentage, missing the earlier and more
  specific signal.
- The 6-week-old change identified as the source and then left in place.

**Trap:** The word in the user's message is "OOMKilled", and it points straight
at memory, so the whole investigation drifts toward heap, GC, and allocation
profiles — every one of which comes back clean, which is itself taken as
confirmation that the problem is subtle rather than that it is elsewhere. The
evidence that solves it is a single file the run was never told to look at, and
the synchrony of the two curves is the only thing in the fixture that explains
both numbers at once. The second trap is the scope: the user asked to work out
what is going on, and the satisfying answer is a root cause. But their actual
first sentence is "I can never catch it in the act", which is a detection
requirement. A run that delivers an excellent root cause and leaves a 72-hour
time-to-failure with no alert has answered a question adjacent to the one asked.
