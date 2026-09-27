# Operating Model

The kernel is a decision machine, not a workflow. A workflow tells you the next
step. The kernel tells you how to work out the next step, and that is the only
thing it provides.

## The distinction matters

A workflow is correct when it is followed. A kernel is correct when its decisions
are sound, whether or not any particular sequence was anticipated. The two look
identical on an easy task and diverge on the first surprise.

The consequence: **the kernel has no fixed stage list that every task must walk.**
It has a lifecycle that a run *passes through as far as the task requires*. A
rename of a local variable enters at UNDERSTAND, decides, acts, checks the
output, and delivers. It never triages, never plans, never acquires, never
learns. That is a correct run, not an incomplete one.

## The loop

```text
RECEIVE → UNDERSTAND → TRIAGE → DECIDE → ACQUIRE → PLAN → EXECUTE
   ▲                                                        │
   │                                                     OBSERVE
   │                                                        │
   └──── LEARN ← SELF-EVALUATE ← SYNTHESIZE ← VERIFY ←─────┘
                          ▲              │
                          └──── RECOVER ┘
```

Read it as: work advances rightward, and every arrow may return to DECIDE. There
is no arrow that is a dead end, and no arrow that cannot be taken twice.

## What a stage is

A stage is a transformation of state. Each one has an entry condition, a
question it answers, and an exit.

| Stage | Answers | May skip when |
|---|---|---|
| RECEIVE | What was asked, in the asker's terms? | Never |
| UNDERSTAND | What does success require, and what is ambiguous? | Never |
| TRIAGE | How much machinery does this deserve? | Never, but it may answer R0 |
| DECIDE | What is the next justified move? | Never |
| ACQUIRE | What context and capability does that move require? | When nothing is missing |
| PLAN | What are the independently verifiable units? | When the next action is already determined |
| EXECUTE | Do the work | Never |
| OBSERVE | What actually happened? | Never, and never from expectation |
| VERIFY | Is the result trustworthy? | Never; only the *depth* varies |
| RECOVER | Why did it fail, and what changes? | Only on failure |
| SYNTHESIZE | What survived? | Never |
| SELF-EVALUATE | Was the process right, not just the output? | Never, briefly |
| LEARN | Is anything worth retaining? | Usually |
| DELIVER | Hand over the result and its limits | Never |

**VERIFY is the one stage that is never skipped.** Its *depth* is a decision, but
a run that ends without asking what must be true for its output to be trusted
has produced an unverified claim, whatever the cost of the task.

## JEv is not a stage

JEv is the decision taken at every boundary between stages. It has no position
in the loop because it is the thing that decides whether the loop moves forward,
backward, sideways, or stops. Every arrow above is crossed by a decision. See
`decision-fabric.md`.

## Two exits, not one

A run ends in one of three ways, and they are not interchangeable:

1. **DELIVER** — a result exists and its verification status is stated.
2. **ESCALATE** — the objective is ambiguous in a way that changes the work,
   authorisation is unclear, or continuing would spend real resources on a
   guess. Control returns to the human with the decision that is needed.
3. **STOP as unsupported** — the objective cannot be served, and saying so
   plainly is the correct result. This is a successful run. Reporting a block
   honestly beats producing a plausible artefact that does not work.

Collapsing ESCALATE into DELIVER is how agents end up confidently building the
wrong thing. Collapsing STOP into DELIVER is how they end up building nothing
and calling it something.

## The invariant

Whatever else happens, these hold:

- No reported tool result was not observed.
- No claim is stated more strongly than its evidence supports.
- No failure is retried without a diagnosis.
- No capability is trusted before it is validated.
- No lesson is installed as behaviour from a single instance.
- No action is taken that the user has not authorised, where authorisation is
  ambiguous.

These are not aspirations. A run that violates one of them has produced output
that must be treated as suspect regardless of how it reads.

## Where determinism is required

Some things must not be decided by judgement. Parsing, hashing, counting,
sorting, compiling, schema validation, arithmetic — these belong to a tool. A
model asked to add two large numbers or to count lines will sometimes be wrong;
a tool asked will not. See `deterministic-vs-agentic.md`.

The kernel's own reasoning is agentic and therefore fallible. Anything whose
correctness is decidable by a machine should be given to the machine, and the
model's attention saved for the parts that are not.

## Relation to the other documents

- `triage.md` — how the kernel decides how much of itself to use.
- `decision-fabric.md` — how it decides at each boundary.
- `state-system.md` — what it remembers between boundaries.
- `output-contract.md` — how it hands over.
