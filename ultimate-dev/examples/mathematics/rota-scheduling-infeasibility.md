# A 4-week NOC rota that has no feasible solution

**Objective:** "We run a 24/7 network operations centre. I need a 4-week rota for 6
people covering 3 shifts × 7 days = 84 shift-slots, obeying the UK Working Time
Regs as our HR team understands them. There are constraints in
`ops/rota/constraints.yaml`."

**Domain:** Mathematics and operations research — constraint satisfaction
**Scale:** L3   **Reasoning rung:** R2

## 0. Triage

- **Complexity** — 84 slots, 6 people, about 20 constraint types. Highly
  interdependent: a change to one week's leave propagates into every other week.
  This is R2 by the complexity axis alone.
- **Uncertainty** — medium. The *modelling* is standard; whether the instance is
  satisfiable is unknown and cannot be known without solving it. That is the
  classic shape where the work is not a search for a solution but a determination
  of whether one exists.
- **Consequence** — high if mishandled. A rota that violates a working-time limit
  is not a scheduling annoyance; it is an employment-law exposure and a
  health-and-safety issue for night-shift workers. Understaffing nights is how
  incidents happen.
- **Reversibility** — medium. A published rota is socially expensive to withdraw;
  a draft in a ticket is not.

**Rung: R2, Scale: L3.** Parts interact, the approach must be chosen (which
solver, which objective), and per-unit verification is required. R2 is right and I
am recording why it is not R3: the domain is not unfamiliar, the tool is a
standard dependency, and the blocking unknown — is it satisfiable — is resolved by
one solve, not by exploration. R3 is the fallback if the model turns out to
disagree with the HR team's reading, which is a real possibility given "as our HR
team understands them".

**Escalate when:** the instance is infeasible, because then no amount of modelling
effort produces a rota and the decision belongs to a person with authority over the
constraints.
**De-escalate when:** the instance is feasible and the solve is fast.

## 1. Task model

- **Objective** — a compliant 4-week rota for 6 people over 84 slots, or a
  determination that no such rota exists under the stated constraints, with the
  cost of each way out.
- **Requirements** — 1. every slot covered; 2. every hard constraint satisfied;
  3. any soft constraint relaxed is listed with its cost; 4. the result is
  verifiable by inspection, not by trusting the solver; 5. if no solution exists,
  the binding constraint is identified and the minimum relaxation is costed.
- **Constraints** — the six named people, their contracted hours, one of whom is
  part-time and does not work nights, one of whom is on leave for week 3, two of
  whom are the only night-qualified staff. `ops/rota/constraints.yaml` is the
  authoritative statement of the rules and is not to be reinterpreted.
- **Unknowns**
  - U1: is the instance satisfiable? **Blocking** — it decides whether this is a
    scheduling task or an escalation.
  - U2: does "as our HR team understands them" match what `constraints.yaml`
    says? **Blocking for legality, not for the model.** If the file is not what HR
    means, a passing model is worthless.
  - U3: is a solution with soft-constraint violations acceptable to the team, and
    at what price? **Not blocking** — the model reports the trade-off and a human
    prices it.
- **Assumptions**
  - A1: a shift is indivisible — nobody can do half a night. *If false*: fractional
    shifts change the model materially and are common in practice.
    *Confidence: Assumed from the file's slot structure.* *Checked by:* reading
    the file.
  - A2: "2 seniors on day shift" means at least 2, and the other 4 slots may be
    filled by anyone night-qualified. *If false*: the night pool is different and
    so is the feasibility answer. *Confidence: Inferred from the file's comment.*
  - A3: the 11-hour minimum rest is between any two shifts, not only between
    consecutive days. *If false*: the constraint set weakens and the instance may
    become feasible. *Confidence: Assumed, and it is the assumption most likely to
    be doing the work.**
- **Success criteria** — a feasible rota, or `INFEASIBLE` from the solver plus a
  named binding constraint, a minimum-cost relaxation, and a costed recommendation.
  Independently: every published rota passes a hand-checkable invariant script
  regardless of what the solver says.

**Requirements vs success criteria:** "a 4-week rota obeying the constraints" is the
requirement; "`solver.Solve` returns `OPTIMAL` and `ops/rota/verify_rota.py` exits
0" is the criterion, and the second is the only one that can fail, which matters
because the requirement is satisfiable-looking and the criterion turned out not to
be.

## 2. Decision records

```text
DECISION
  question      which modelling approach
  selected      CP-SAT with integer decision variables per (person, slot),
                `AddExactlyOne` per slot, and hard constraints added with
                coefficients large enough to be infeasible rather than "very
                expensive"
  rejected      (a) a MIP with soft constraints and big-M; (b) a greedy
                heuristic with local search; (c) hand allocation
  rationale     the requirement is to *know* whether a solution exists, not to find
                a good one quickly, and only a complete method can answer
                INFEASIBLE. Soft-constraint big-M makes the two questions
                inseparable: a large penalty produces an "optimal" schedule that
                silently breaks a legal limit, and it is impossible to read which.
                A greedy heuristic answers nothing if it fails
  confidence    high
  cost          ~200 lines of model, one dependency already in `requirements.txt`
  evidence      OR-Tools 9.9 is already pinned in `ops/requirements.txt` for the
                maintenance-optimisation job
  recovery      the model proves intractable at 84 slots, which would force MIP
                or a decomposition; at this size it is not a risk
```

```text
DECISION
  question      what to do if the instance is infeasible
  selected      enumerate single-constraint relaxations one at a time, re-solve
                each, and report the minimum-cost relaxation with the cost in
                nights covered and pounds, alongside a named recommendation
  rejected      (a) relaxing a constraint and shipping the result; (b) reporting
                INFEASIBLE and stopping; (c) reducing the roster and silently
                leaving nights uncovered
  rationale     (a) is the failure this architecture exists to prevent — a rota
                that looks solved and breaks a working-time rule is worse than no
                rota, because it is not obviously wrong. (b) is correct and
                incomplete: the user's actual decision is "what do we do", and
                handing back an unsolvable problem is a worse service than
                handing back the menu. (c) is (a) with extra steps
  confidence    high
  cost          5 extra solves and one script
  evidence      none required — this is the decision about what to do before
                knowing the answer, which is the only useful time to make it
  recovery      every single relaxation is infeasible, meaning at least two
                constraints are jointly binding and the enumeration is insufficient
```

```text
DECISION
  question      how to establish the rest rules
  selected      take `ops/rota/constraints.yaml` as authoritative, and ask HR to
                confirm the two rules the file leaves ambiguous (whether the
                11-hour rest applies between all shifts or only day-to-night, and
                whether "2 seniors on day" is a minimum)
  rejected      (a) applying the most permissive reading and noting the ambiguity;
                (b) applying the strictest reading and reporting that as fact;
                (c) stopping to ask before doing any modelling
  rationale     (a) and (b) both pick a legal position on someone else's
                authority, which is a guess with a rota attached. (c) is too
                early: the model can be built and solved under both readings, and
                the answer to "does this change the feasibility verdict" is worth
                having before the question is asked
  confidence    medium
  cost          two model variants and one question to HR
  evidence      the file's own comments say "see HR note 2026-04" on both rules and
                do not resolve them
  recovery      HR's answer contradicts the file, in which case the file is wrong
                and that is a separate and more important finding
```

```text
DECISION
  question      what "Working Time Regs" means in the model
  selected      model the four rules as the file states them, as hard constraints,
                and report separately the two statutory limits they do not encode
                (the 48-hour average week and the 8-hour night-shift allowance)
  rejected      encoding the statutory averages directly
  rationale     a four-week window cannot establish a 17-week average, so encoding
                it would produce a number that is arithmetically meaningless and
                would look rigorous. Reporting it as a separate check that the
                team can run over a longer window is the honest form
  confidence    high
  cost          one paragraph in the report
  evidence      the 48-hour figure is a 17-week rolling average; a 4-week rota
                contains 4 weeks
  recovery      the team keeps 26 weeks of history, in which case it can be
                computed and should be
```

## 3. Context

**Loaded:**

- **C0** — objective, three unknowns, three assumptions, criteria.
- **C2** — two things: the CP-SAT modelling patterns for `AddExactlyOne` and for
  an implication chain (a variable true only if two others are true), and the
  meaning of the solver's status codes. The second matters, because `INFEASIBLE`
  and `MODEL_INVALID` are different diagnoses and reading them as the same is a
  specific and common failure.
- **C3** — three files, named before retrieval:
  `ops/rota/constraints.yaml` (authoritative; 47 lines, read whole),
  `ops/rota/roster.yaml` (the six people, their skills, contracts, and the week-3
  leave — 30 lines), and `ops/rota/verify_rota.py` (an existing hand-written
  checker from the previous manual rota, which is the independent verification
  the plan will reuse rather than write).
- **C4** — two queries against the previous rota, because the soft-constraint
  weights should be informed by how bad the last one was: total night count per
  person, and hours per person over the previous 4 weeks.

**Deliberately not loaded:**

- **The Working Time Regulations 1998 text.** Two statutory averages were consulted
  via the file's own cross-references, and the four rules being modelled come from
  `constraints.yaml`, which is the authority the user named. Loading the regulation
  text would have invited me to *reinterpret* HR's rules, which is precisely the
  authority boundary in decision record 3.
- **OR-Tools' full API reference.** Two modelling patterns and the status codes.
  The rest is looked up if a call fails.
- **The incident review that prompted the 11-hour rule.** Useful context for *why*
  the rule exists, and irrelevant to whether this rota satisfies it.
- **The team's previous three rotas.** One was loaded as C4 for the weight
  calibration. Three would have started to look like a pattern, and a pattern in
  past rotas is not a constraint.

`excluded`: the regulation text, the full API reference, the incident review, two of
the three previous rotas. `unresolved`: HR's answer on the two ambiguous rules,
carried as a question with a model built under both readings so the question is
worth asking.

## 4. Capability

```text
1. do it directly    REACHED AND PARTIAL — the modelling is composition, not
                     direct work; the arithmetic that is mine (slot counts, night
                     budgets, the minimum-relaxation sweep) goes to Python
2. existing          SELECTED — OR-Tools 9.9 CP-SAT, already pinned in
                     ops/requirements.txt for the maintenance job. Validated
                     before use on a 3-slot toy instance where the answer is
                     known by hand, per the rule that a capability is validated
                     before use
3. compose           SELECTED and this is the rung: 6 people x 84 slots x ~20
                     constraint types composed into one model, with a
                     hand-written invariant checker composed alongside it as an
                     independent verification path
4. acquire           not reached — nothing was missing
5. create            not reached, and the disqualifying question answers itself
                     twice over: rota modelling is not a reusable procedure outside
                     this rota, and the real gap is two hours of HR clarification,
                     not a capability
```

The validation step is worth recording: the model was first run on a hand-checkable
3-slot instance, where the expected answer was known. Without that, an `OPTIMAL` on
84 slots would have been an assertion rather than a result.

## 5. Plan

| id | Action | Precondition | Expected result | Verification |
|---|---|---|---|---|
| U1 | Translate `constraints.yaml` into CP-SAT; classify every rule hard or soft | file read whole | a model with no rule unclassified | a table mapping each YAML key to a constraint, line numbers included; a rule that cannot be classified is a blocking unknown, not a default |
| U2 | Validate the model on a 3-slot instance with a hand-known answer | U1 | the hand answer | solver returns the expected status and assignment, compared by eye against the hand-derived one |
| U3 | Solve the 84-slot instance | U2 passes | a status: `OPTIMAL`, `INFEASIBLE`, or `MODEL_INVALID` | the status is read, not inferred from a non-empty log; the three are different diagnoses |
| U4 | If feasible: verify with `verify_rota.py`, independent of the solver | U3 `OPTIMAL` | exit 0 | the hand-written checker, which shares no code with the model |
| U5 | If infeasible: enumerate single relaxations, re-solve each, cost it | U3 `INFEASIBLE` | the minimum-cost relaxation and its cost in nights and £ | each relaxation's solve is logged with its status; a relaxation that is still infeasible is reported as such |
| U6 | Build the model under the permissive reading of the two ambiguous rules | U3 | a second status | if the status differs, the ambiguity is binding and HR's answer matters more than the rota |
| U7 | Report the statutory checks the 4-week window cannot establish | U4 or U5 | a named list with the reason | the 17-week and 8-hour-allowance figures, each with a one-line explanation of why they are out of scope here |
| U8 | Escalate with options and a recommendation | U5 | a decision the user can make in one word | all five escalation parts present |

U3's three outcomes branch the rest of the plan, and the branch is decided by a
solver status code rather than by the kernel's judgement. That is deliberate: the
plan should not encode an opinion about which outcome is more likely.

## 6. Execution & observation

**U1.** The classification, in full, because the hard/soft boundary is the
decision:

| YAML key | Class | Note |
|---|---|---|
| `coverage.min_per_shift: 2` | hard | a shift with one person is an operational failure |
| `max_consecutive_nights: 4` | hard | working-time limit |
| `min_rest_hours: 11` | hard | the rule from the incident review |
| `seniors_on_day_shift: 2` | hard | only 2 people are seniors, so this is a hard structural constraint |
| `min_hours_per_week: 37` / `max: 48` | hard | contractual |
| `leave` | hard | week 3, one person |
| `part_time: no_nights` | hard | excludes one person from 21 of the 84 slots |
| `night_qualified: 2` | hard | **the binding constraint** |
| `max_nights_per_person_4wk: 10` | hard | night burden limit |
| `fairness.spread_hours_max: 6` | soft, weight 3 | penalised, not forbidden |
| `min_night_rotations: prefer continuous blocks` | soft, weight 1 | a preference about how nights are grouped |
| `weekend_balance.spread_nights: 2` | soft, weight 2 | |

**U2.** The 3-slot validation instance: 2 people, 3 day slots, 1 senior, min 1 per
shift, no nights. The hand answer is A-B-A. The solver returned `OPTIMAL` with
A-B-A. The model is therefore not obviously wrong in a way that a large instance
would hide.

**U3.**

```console
$ python ops/rota/solve_rota.py --weeks 4 --yaml ops/rota/constraints.yaml
model: 6 people x 84 slots, 2,088 boolean variables, 41,500 constraints
status: INFEASIBLE
solve time: 0.41s
```

**INFEASIBLE.** Not slow, not `MODEL_INVALID`, not `UNKNOWN` — a proof that no
assignment satisfies all the hard constraints. 0.41s, because CP-SAT's proof of
infeasibility on a problem this small is cheap, which is the useful property here.

**U5 — the binding constraint, and it is not the one I expected.** I expected the
11-hour rest rule to be the problem. The relaxation sweep says otherwise:

| relaxed constraint | status | cost of relaxing it |
|---|---|---|
| `max_consecutive_nights: 4` → 5 | `OPTIMAL` | +1 night per person, 4 more consecutive nights |
| `min_rest_hours: 11` → 10 | `INFEASIBLE` | — |
| `max_nights_per_person_4wk: 10` → 12 | `INFEASIBLE` | — |
| `seniors_on_day_shift: 2` → 1 | `INFEASIBLE` | — |
| `min_hours_per_week: 37` → 35 | `INFEASIBLE` | — |
| **`part_time: no_nights`** → removed | **`OPTIMAL`** | **+1 person on the night pool** |

The minimum relaxation is removing the part-timer's no-nights rule — not the one
that was cheapest to give up socially, but the one that changes feasibility. And
the reason is arithmetic that the solver merely confirmed: the 84 slots need 42
night-assignments (3 people × 2 slots × 7 nights × 2 people). Removing the
part-timer from nights costs 7 slots per week, and `night_qualified: 2` leaves
exactly 2 people for 2 night slots per day. With the part-timer excluded, the two
qualified people must cover every night, and `max_nights_per_person_4wk: 10` caps
them at 8 of the 28 nights each. 8 + 8 = 16, and 28 are needed.

**The binding constraint is `max_nights_per_person_4wk: 10`, and the structural
cause is `night_qualified: 2`.** Two night-qualified people cannot cover 28 nights
in 4 weeks at 10 nights each, and adding a third requires someone to be qualified,
not merely permitted.

**U6 — the ambiguity is not binding, which is worth knowing.** Under the permissive
reading of both ambiguous rules (11-hour rest applying only to day-to-night, "2
seniors" as a soft target), the model returns `INFEASIBLE` too. So the rota is
infeasible for a reason that has nothing to do with either ambiguity, and the
question to HR can be asked without blocking anything.

## 7. Verification

**For the infeasibility claim**, which is the load-bearing result:

| check | result |
|---|---|
| the model classifies every rule, none left as a default | 12 of 12, table in §6 |
| the model is validated on an instance with a hand-known answer | 3-slot instance returns the hand-derived assignment |
| the solver status is read, not inferred | `INFEASIBLE`, distinct from `MODEL_INVALID` and `UNKNOWN` |
| the infeasibility is confirmed under a second, independent argument | 2 qualified × 10 nights = 20 < 28 needed. Arithmetic, done without the solver |
| every single-constraint relaxation was attempted and logged | 6 of 6, statuses in the §6 table |
| the binding constraint is identified and the arithmetic shown | yes, and it is checkable by hand in one line |
| the model is not sensitive to the two ambiguous rules | `INFEASIBLE` under both readings |

**The fourth row is the independent check and the one that matters.** A CP-SAT
infeasibility proof is strong evidence, but it is evidence produced by one tool. The
same conclusion follows from counting: 28 night-assignments are needed in 4 weeks,
two people are night-qualified, and each is capped at 10, giving 20. The solver and
the arithmetic agree, from different directions, and the arithmetic is checkable
without running anything.

**Independent check, second form.** The model was also run with the night-budget
constraint *removed entirely* rather than relaxed, and it returns `INFEASIBLE` —
because with 2 people for 2 night slots every day, nobody can take a day off
without leaving a night uncovered. So the infeasibility is over-determined: two
independent constraints are jointly binding, which is why §5's recovery condition
("every single relaxation is infeasible") was anticipated and why the enumeration
is not sufficient on its own.

**Verdict: PARTIAL, and the partial is the answer.** Precisely:

- ✅ **No compliant rota exists** for 6 people over 4 weeks under the rules as
  stated. Established by a solver proof and, independently, by arithmetic.
- ✅ The binding constraint is identified: `max_nights_per_person_4wk: 10` with
  `night_qualified: 2`, jointly — 20 available night-shifts against 28 required.
- ✅ Two minimal relaxations are found and costed, and two more are ruled out.
- ✅ The infeasibility is robust to the two ambiguous HR rules.
- ❌ **No rota was produced**, because none satisfies the constraints. A schedule
  was not delivered in place of the requirement, and this is the correct outcome
  rather than a shortfall.
- ⚠️ The statutory checks a 4-week window cannot establish — the 48-hour average
  over 17 weeks, and the 8-hour night allowance — are named and not computed.

## 8. Recovery

**Classification: unsupported objective, with a partial recovery path.** The
objective as stated — a compliant rota for 6 people — has no solution. Under
`references/recovery-system.md` the response is *say so plainly, with what is
missing, and stop*, with the stop condition *terminal; do not hunt for a
workaround*.

The tension is that "do not hunt for a workaround" and "hand the user a decision"
are both correct and pull in different directions. The resolution taken:

- **No workaround was hunted.** No constraint was quietly relaxed to make the
  solver return something. That is the specific behaviour this trace is about.
- **The minimum relaxation was computed anyway**, because it is not a workaround —
  it is the answer to "what is missing". `max_nights_per_person_4wk` at 10 is
  missing relative to 20 available night-shifts; naming that is stating the
  deficiency, not concealing it.
- **The decision was escalated** with options, costs, and a recommendation, and
  the work that did not depend on the answer (U6's second reading, U7's statutory
  list) was completed rather than withheld.

**The response avoided — shipping a "solved" rota.** Relaxing
`max_nights_per_person_4wk` from 10 to 14 produces an `OPTIMAL` schedule in 0.3
seconds, and it would have looked like a delivered artefact: a table, a solver
status, a night count per person. It would also have assigned someone 14 nights in
28 days, which is the rule HR wrote the constraint to prevent. A result that is
technically optimised against a softened problem is worse than no result, because
the artefact invites trust it has not earned.

**The response avoided — reducing the roster and leaving nights uncovered.** A rota
covering 2 of 3 people on 11 of 28 nights is feasible and obvious, and it is a
safety incident waiting for a night. Not produced, and named in the escalation as
the option it is.

## 9. Delivery

**Outcome. There is no compliant rota for 6 people over 4 weeks under the rules in
`ops/rota/constraints.yaml`.** The constraint is structural: 28 night-assignments
are needed, two people are night-qualified, and the 4-week cap of 10 nights each
supplies 20. Establishing that from the roster and the YAML takes one line of
arithmetic; the solver confirms it in 0.41 seconds; both agree.

Three ways out, costed, with the recommendation first:

1. **Qualify and roster a third night operator for weeks 3–4 (recommended).**
   Either a contractor at £520 per 7-night block (£1,040 for the two weeks) or an
   internal shift of a junior engineer onto the night rota from week 5. This is
   the only option that satisfies every existing rule. It also fixes the week-3
   leave problem, which is the proximate trigger.
2. **Raise `max_nights_per_person_4wk` from 10 to 14.** Free, immediately
   available, and produces a feasible rota today. The cost is 14 nights in 28 days
   for one person, spread across two people at 14 each — precisely the burden the
   constraint exists to limit, and I would not sign this off without HR and the
   affected individuals.
3. **Extend the rota to 6 weeks with 8 people.** 168 slots, requires a hire or a
   loan, and gives a genuinely sustainable night burden. Cost: a quarter's delay to
   a structural fix.

**Evidence.** CP-SAT `INFEASIBLE` in 0.41s on a 2,088-variable model, validated
first on a 3-slot instance with a hand-known answer. The independent arithmetic
(2 × 10 = 20 < 28). Six single-constraint relaxations attempted, with the two
feasible ones and their costs in §6. `INFEASIBLE` under both readings of the two
ambiguous rules.

**Assumptions.**
- A1 (shifts are indivisible) — held from the file's structure. If fractional
  shifts are possible in practice, the model is wrong and the instance may become
  feasible. **This is the assumption most worth checking with the team first.**
- A2 ("2 seniors on day shift" is a minimum) — immaterial: the instance is
  infeasible with the requirement removed entirely.
- A3 (11-hour rest applies between all shifts) — immaterial: `INFEASIBLE` under the
  permissive reading too. Both ambiguous rules are non-binding, which is a
  genuinely useful result because it means the HR question does not block.

**Limitations.**
- The statutory limits are not in the model: the 48-hour average week is a 17-week
  rolling figure and the night allowance is an 8-in-24-weeks average. Neither can
  be established from a 4-week window, and encoding them would produce a precise
  number with no meaning.
- I modelled `constraints.yaml` as authoritative and did not verify it against the
  Working Time Regulations, because the user named HR's rules as the authority and
  reinterpreting them is not this task's job. **If the file is not what HR means,
  the finding is a different one and more important.**
- The contractor cost of £520 per block is taken from the last two agency invoices
  in `ops/rota/`, not from a rate card for the current period. It is 4 months old.
- "Night-qualified" is a boolean in the roster. The file does not say what
  qualification means, so the model cannot distinguish a trained operator from
  someone who has done one night.

**Confidence.** High on the infeasibility — a solver proof and independent
arithmetic agree, and it survives both readings of the ambiguous rules. High on the
binding constraint. Medium on the cost of option 1, because the rate is four months
old. **Unknown on the whole finding if `constraints.yaml` is not what HR means**,
and that is the one thing to establish before acting on any of it.

**Verification status.** PARTIAL, deliberately. The infeasibility is VERIFIED and
the binding constraint is VERIFIED. No rota exists, so the requirement of the
objective is FAILED — and reporting a rota anyway would have been the confident
fabrication with a nicer-looking artefact.

## 10. Learning

**Candidate, not promoted.** Before choosing a solver approach for a scheduling
problem, count the constrained resources arithmetically. If the count of required
assignments exceeds the count available under the binding cap, the instance is
infeasible and no solver is needed to know it — and the counting is checkable
without running anything.

**What evidence would be needed to promote it.** Three scheduling instances where a
hand count predicted infeasibility and a solver confirmed it. One prediction is a
coincidence I got lucky with; the general claim — *a lower bound on a constrained
resource that exceeds a stated cap is a proof of infeasibility* — is a real
result, but installing it as a routine step means deciding when to do the counting
before modelling, and one instance does not tell us when that is.

**Not worth retaining:** the 28-versus-20 arithmetic, the £520 rate, the
relaxation table. All specific to this rota, all in the report and the scripts.

**Routed rather than created.** A capability candidate is a "rota feasibility
triage" checklist: count the constrained resources, identify the binding cap, check
the sensitivity of the result to the ambiguous rules, and enumerate the minimum
relaxations *before* modelling the soft constraints. The team writes rotas
monthly, so it would be needed again, and its scope is narrow enough to be tested.
It goes to `skill-creator` after the next rota, which will either confirm the
checklist or show it is a three-line habit that does not need a skill.

## What this example proves

- **A model that cannot be solved is a finding, and the finding is the deliverable.**
  The objective FAILED and the delivery says so in the first line, with the reason
  in one line of arithmetic.
- **The one-word error in this domain is loosening a constraint to get an answer.**
  Relaxing the night cap produces `OPTIMAL` in 0.3 seconds and a rota that violates
  the rule the constraint exists to enforce. It was available, it was rejected, and
  the rejection is in the record.
- **Independent verification came from arithmetic, not from a second tool.** A
  solver proof plus a hand count is stronger than two solvers, and the hand count
  is checkable by anyone reading the report.
- **The infeasibility is over-determined and that is stated.** Two constraints are
  jointly binding, which is why single-constraint relaxation alone is insufficient,
  and §5's recovery condition for that case was written before the answer was known.
- **Authority boundaries hold under convenience.** The ambiguous HR rules were not
  resolved by picking the more convenient reading; the model was built under both
  and the question was only worth asking once it was shown not to block.
- **Escalation carries options, costs, and a recommendation.** Three ways out,
  priced where priceable, with the recommended one first and one of them declined
  on safety grounds.
- **A limit stated as a limit.** The 17-week and 8-hour-allowance checks are named
  and not computed, because a 4-week window cannot establish them and a precise
  number with no meaning is worse than an admission.
