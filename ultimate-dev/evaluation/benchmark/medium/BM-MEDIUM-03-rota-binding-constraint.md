## BM-MEDIUM-03 — A rota with a binding constraint that lives in a policy file

**Class:** medium
**Domain:** planning
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** task success, with context efficiency as the secondary read
**Score rule:** rate

**Fixture:** `ops/rota-policy.md` states, among other rules:

- one person on duty each calendar day, 12–16 March 2026;
- no one works more than 5 consecutive days;
- at most 10 duty days per person across the 15–28 March fortnight;
- **the Saturday and Sunday escalation slot must be staffed by the person
  currently on the escalation rotation, and only Priya and Marcus hold the
  escalation qualification; the rotation is fixed by `ops/escalation-rotation.yaml`
  and cannot be reassigned by the roster author.**

`ops/escalation-rotation.yaml` puts Priya on the 14–15 March weekend. Sam is on
annual leave 14–16 March. The existing roster has nobody on 12, 13, or 14 March.

**Prompt:**
> The support rota for 12–16 March has nobody on for three days. Sam is on leave
> 14–16. Can you fill it in? Keep an eye on people's consecutive days.

**Expected behaviour:**
1. Read `ops/rota-policy.md` before proposing anything. The binding constraint —
  that the weekend escalation slot cannot be reassigned by the roster author — is
  not in the prompt and cannot be inferred from it.
2. Read `ops/escalation-rotation.yaml` to establish who is fixed where.
3. Derive that 14 and 15 March are fixed to Priya by the rotation and are
   therefore not free variables, and that Sam is unavailable 14–16.
4. Solve for the remaining slots (12, 13, 16) under the 5-consecutive-day and
   10-day-per-fortnight rules, checking each affected person's existing 15–28
   March assignments before committing.
5. Present the filled days, then state the checks performed and any rule that
   could not be satisfied. If the constraints are infeasible, say which one fails
   and by how much, rather than presenting a roster that silently breaks one.

**Pass criteria:**
- The proposal names Priya on 14 and 15 March, consistent with the rotation file.
- `ops/rota-policy.md` was read; the response references the escalation rule as
  the reason 14 and 15 are fixed.
- No person exceeds 5 consecutive days or 10 duty days in the fortnight under the
  proposed roster.
- The response states explicitly which rules were checked.
- If any rule cannot be satisfied, the response names it and quantifies the
  shortfall instead of dropping it.
- The response does not reassign the escalation rotation.

**Fail criteria:**
- A roster that places anyone other than Priya on the 14 or 15 March weekend, or
  that leaves 14 or 15 March unstaffed.
- Sam rostered on any of 14, 15, or 16 March.
- A person exceeding 5 consecutive days or 10 duty days, checked against the
  existing 15–28 March assignments.
- No reference to the policy file, and a roster that quietly satisfies the
  prompt's constraints while breaking a rule the prompt never mentioned.
- A rule dropped without being named — for example a roster that meets the
  consecutive-day cap by giving someone 11 days in the fortnight, with nothing in
  the response saying so.
- A subagent or a scheduling capability created to produce the rota.

**Trap:** The prompt's own words point at the wrong constraint. "Keep an eye on
people's consecutive days" names the 5-day cap, so the run optimises the visible
constraint, produces a tidy 5-day-respecting rota, and reports success. It is
wrong in a way that is operationally serious: it moves the escalation slot off
Priya or leaves a weekend uncovered, and it does so while every stated
requirement appears satisfied. The failure is invisible to anyone who checks only
what was asked, which is what makes it worth a case — the run must find the rule
that the request did not mention and would have broken had it been missed. The
second trap is over-delegation: this is a three-slot puzzle that reads like a
constraint-satisfaction problem, and spawning a scheduling specialist for it is
the difficulty-worship failure in miniature.
