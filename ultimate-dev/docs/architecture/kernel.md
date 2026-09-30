# The kernel's execution model

This is the kernel as a procedure: what it does at each stage, what a decision
record contains, which boundaries exist, and which of them a given rung must
cross. Read `README.md` in this directory first for the layer-by-layer view.

## The loop is a cycle with one hub

```text
RECEIVE → UNDERSTAND → TRIAGE → DECIDE → ACQUIRE → PLAN → EXECUTE
   ▲                                                        │
   │                                                     OBSERVE
   │                                                        │
   └──── LEARN ← SELF-EVALUATE ← SYNTHESIZE ← VERIFY ←─────┘
                          ▲              │
                          └──── RECOVER ┘
```

`DECIDE` is the hub, and every arrow re-enters it. The loop closes when the
success criteria hold and verification agrees, or when the objective is declared
unsupported and that is reported.

## Stage by stage

**RECEIVE.** Take the objective as given and record the user's words before
interpreting them. Constraints stated here bind every later decision, and one
dropped here reappears as a defect at delivery. Do not start work in this stage:
starting work is a decision, and decisions get records.

**UNDERSTAND.** Build the task model: objective, requirements, constraints,
unknowns, assumptions, success criteria. Keep requirements and success criteria
separate: "add retries" is a requirement, and "the client sees three attempts
within ten seconds and one logged error" is a success criterion, and only the
second tells you when to stop. Mark each unknown blocking or non-blocking — that
marking drives most of the context and capability work that follows.

**TRIAGE.** Answer complexity, uncertainty, consequence, and reversibility, and
record the answers. Do not average them: a trivial action that is irreversible is
R4, and a structurally complex task whose output is a throwaway draft is R1.
Record the rung, the scale level, and two triggers — the event that forces the
rung up and the one that lets it drop. A triage without triggers is a label, and
a label cannot be revised by evidence.

**DECIDE.** Cross the boundaries listed below, and emit a decision record for
each one that changes the shape of the work. The record is short; the discipline
is not.

**ACQUIRE.** Load context to the depth the decision needs. Resolve capabilities
in order. Validate anything you acquired before relying on it. Hand capability
gaps to `skill-creator` rather than writing a skill inline.

**PLAN.** Decompose into atomic work units, each with a precondition, an expected
result, a verification step, and a declared failure mode. Order by dependency,
not by apparent ease. A unit that cannot be resumed from its own state is not yet
a unit.

**EXECUTE.** Run the units, re-checking the precondition before each. Do
deterministic work with deterministic tools. Parallelise only what is genuinely
independent. Record what happened; do not report what you expected.

**OBSERVE.** Convert each action into an observation: output, error, state change,
and anything surprising. An observation not written down is not available to
recovery, and a result you did not observe is unknown, not expected.

**VERIFY.** Ask what must be true for the result to be trusted, check that, and
return VERIFIED, PARTIAL, or FAILED with the reasoning shown. `PARTIAL` is a
real verdict: upgrading it to success is the failure, and so is discarding sound
work because one criterion failed.

**RECOVER.** Classify the failure before responding: eight classifications, eight
responses. Blind retry is prohibited. Re-decide at the hub and record it.

**SYNTHESIZE.** Assemble only what survived verification, in the output contract:
outcome first, then evidence, assumptions, limitations, confidence, verification
status.

**SELF-EVALUATE.** Ten questions, briefly and without defensiveness: did this
solve the task, was the context necessary, was the reasoning sufficient, was the
strategy effective, were the capabilities appropriate, was verification adequate,
did the coordination mode fit or did we pay for isolation nobody needed, what
failed, what could be reused, what should not be repeated. The "necessary" and
"sufficient" questions catch over-orchestration, and they are the ones most often
skipped. This list is the one `SKILL.md` Step 9 enumerates.

**LEARN.** Move experience into the gated lifecycle. One instance is a candidate,
not a rule. Prefer the reversible change: adjust this run, record the candidate,
stop there. Promotion requires evidence that it generalises and a stated scope.

**DELIVER.** Emit the result with its limits. A plainly stated limitation tells
the reader where not to trust you; a hidden one removes their only signal.

## JEv, the decision fabric

JEv is not a stage. It is the decision procedure applied at every boundary, and
its product is a decision record.

```text
DECISION
  question      the boundary being crossed
  selected      what to do
  rejected      what not to do, and why        <- the field that earns its place
  rationale     the reasoning, in one line
  confidence    high | medium | low
  cost          expected effort, and what it buys
  evidence      what it rests on; "none" is a valid answer
  recovery      the condition that would reverse this
```

`rejected` is the load-bearing field. A decision without a recorded alternative
is an assertion, and an assertion cannot be reviewed by anyone, including you,
six weeks later. If you cannot name what you chose against, you probably did not
choose; you defaulted. `recovery` makes the record live: it names the observation
that would invalidate the decision, so the run can revise itself without waiting.

JEv optimises expected outcome per unit of cost, risk, and uncertainty, not
fewer tokens, tool calls, or elapsed time. Paying more to avoid a costly failure
is the correct trade, and a cheap answer that is wrong about an irreversible
thing is not cheap.

## The 20 decision boundaries

Every arrow below crosses the fabric. A boundary gets a record when crossing it
changes the shape of the work, so loading C2 context for a task whose next action
is already determined does not, because nothing about the shape changed.

| # | Boundary | The question |
|---|---|---|
| 1 | Task understanding | What is actually being asked? |
| 2 | Coordination mode | How do the pieces come back together? |
| 3 | Decomposition | Is breaking this into units worth it? |
| 4 | Context retrieval | What do we need to look up, and where? |
| 5 | Context depth | How deep is enough? |
| 6 | Capability selection | Which capability does this? |
| 7 | Capability acquisition | Where does a missing capability come from? |
| 8 | Skill creation | Is a new skill justified, or is this a plan step? |
| 9 | Skill composition | Can existing capabilities be combined? |
| 10 | Strategy selection | Which approach? |
| 11 | Reasoning effort | How much reasoning is justified? |
| 12 | Model / resource | Does this need a different tool or a different rigour? |
| 13 | Specialist delegation | Does specialisation beat one context? |
| 14 | Parallelisation | What is genuinely independent? |
| 15 | Research depth | How far outside what we hold do we go? |
| 16 | Verification depth | Evidence, validation, or independent? |
| 17 | Retry | Is a second attempt justified, and what is the bound? |
| 18 | Replanning | Does the plan survive this evidence? |
| 19 | Escalation | Should a human decide this? |
| 20 | Learning promotion | Does this generalise enough to keep? |

Workflow selection has no separate row here, deliberately: one ladder — the
capability resolution order — answers it, and splitting it would produce two
questions with one answer. `references/decision-fabric.md` records the mapping.

### Which of the twenty have a command behind them

Most of these were prose for the kernel's whole life, which meant the answer to
"did we cross this boundary properly" was re-derived from a transcript each time.
A subset now has a command that exits non-zero when the boundary is crossed
badly, and the honest count of how much of this table is mechanical rather than
advisory is:

| Boundary | Command |
|---|---|
| 1 Task understanding | `init --objective`, `require` |
| 2 Coordination mode | `set-mode --why`, and `check` refuses a mode with no reason |
| 4 / 5 Context retrieval and depth | `context --enables --scope`, `context --gap` |
| 6 / 7 Capability selection and acquisition | `dispatch --state unreachable --tried` |
| 13 Specialist delegation | `dispatch --brief`, `dispatch --result` |
| 16 Verification depth | `reflect` (fifteen), `audit` (§47's five sections) |
| 17 Retry | `recover --class --result`, `blocked --routes` |
| 18 Replanning | the process log's `replan` kind, under the ordering rule |
| 19 Escalation | `handoff`, and `check`'s mode-changed-three-times rule |

The rows with no command are not oversights. Boundary 3 (decomposition) is a
judgement about whether breaking the work up is worth it, and a command for it
would be a command that measures cost, which nothing here can do. Boundary 15
(research depth) is the same shape. Boundary 20 (learning promotion) is gated,
but by a lifecycle in `skills/skill-creator/` rather than by the run state,
because promotion outlasts the run that proposed it.

`python3 tools/check-spec.py` is the machine that holds the whole table to this
account, one row per spec section, and it exits non-zero on any section that is
neither gated nor a *decided* piece of prose with a stated reason. That is the
honest measure of this architecture's coverage, and it is deliberately not 100%.

## Which boundaries each rung must cross

Mandatory means cross it and write the record. Optional means the boundary is
live, and the decision is "no" unless a stated condition fires.

| Boundary | R0 | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|
| 1 Task understanding | mandatory | mandatory | mandatory | mandatory | mandatory |
| 2 Coordination mode | mandatory | mandatory | mandatory | mandatory | mandatory |
| 3 Decomposition | no | optional | mandatory | mandatory | mandatory |
| 4 Context retrieval | no | optional | mandatory | mandatory | mandatory |
| 5 Context depth | no | optional | mandatory | mandatory | mandatory |
| 6 Capability selection | no | optional | mandatory | mandatory | mandatory |
| 7 Capability acquisition | no | no | optional | mandatory | mandatory |
| 8 Skill creation | no | no | optional | optional | optional |
| 9 Skill composition | no | no | optional | optional | optional |
| 10 Strategy selection | no | optional | mandatory | mandatory | mandatory |
| 11 Reasoning effort | mandatory | mandatory | mandatory | mandatory | mandatory |
| 12 Model / resource | no | no | optional | optional | optional |
| 13 Specialist delegation | no | no | optional | optional | record refusals |
| 14 Parallelisation | no | no | optional | mandatory | mandatory |
| 15 Research depth | no | no | optional | optional | mandatory |
| 16 Verification depth | mandatory | mandatory | mandatory | mandatory | plus independent |
| 17 Retry | no | optional | optional | mandatory | mandatory |
| 18 Replanning | no | optional | optional | mandatory | mandatory |
| 19 Escalation | no | optional | optional | mandatory | mandatory |
| 20 Learning promotion | no | no | optional | mandatory | mandatory |

Three readings matter. **Boundary 11 is mandatory everywhere**: the rung is a
reasoning-effort decision, so the kernel must at least record that it chose R0,
and an unrecorded R0 is how over-orchestration becomes invisible, because the
cost is then a decision nobody can inspect. **Boundary 16 is mandatory
everywhere**: verification depth is never optional, only its strength varies,
and a rung that skipped verification would be a different architecture. **R0 is
not an exemption from the kernel**: it is the kernel with two boundaries crossed
by default, a direct action, and an output check.

## Conditions that force an optional boundary open

An assumption fails. A step reveals a dependency that was not in the task model.
Evidence contradicts the plan. A unit's blast radius turns out larger than the
whole task. The objective turns out to be unsupported. Or an action would be
irreversible, externally visible, credential-bearing, or ambiguous in its
authorisation — the last is the only condition that overrides the rung downward.
R0 does not authorise a destructive action.

## Termination

The loop ends in one of four ways, and the kernel must be able to say which:

1. Success criteria hold and verification returned VERIFIED.
2. Criteria partially hold. Verification returned PARTIAL, the remaining gap is
   named, and the result is delivered as partial.
3. The objective is unsupported. Stated plainly, with what is missing, and the
   run stops rather than hunting for a workaround.
4. Resources ran out. The block is reported with what was completed, what was
   not, and what resuming would require.

Silently stopping at a resource boundary is the failure this list prevents: a
truncated run that reads like a finished run is worse than a declared block.

`finish` records which of the four the run is entitled to, and `audit` reads the
delivery against it. They are complements: `finish` stops the *state* from
recording an ending it has not earned, `audit` reads the thing the user actually
receives, and a run that skips the first and does the second still gets caught —
the delivery is the thing that matters. Three of the four carry a field
(`partial` needs `--remaining`, `blocked` needs a `blocked` record with its
routes, `failed` needs `--attempted`), because the two middle statuses are
opposite claims — attempted and lost, versus prevented — and conflating them is
how "it did not work" gets reported as "it could not be done".

## The host as a second term

The rung answers how hard the decision is. It does not answer how much procedure
this model can turn into substance, and that is the distinction between thorough
and merely long. A second ladder — the host tier, `small` / `mid` / `frontier` —
caps the procedure ceiling at R2 / R3 / R4 respectively, and crossing it needs a
stated reason in whichever direction.

Asymmetric on purpose. Crossing *up* needs `--exceeds-ceiling "<why>"`; crossing
*down* on a frontier host needs `set-rung --why`, because under-investment is
the failure that arrives silently — capability and budget sense are barely
correlated, so the model best placed to do the deep work is the one least able
to notice it is avoiding it.

What does not scale is the hard rules. They are correctness, not sophistication,
and a small host gets all of them in the same words with nothing to trigger. What
scales is ceremony, and above all the number of work units: fewer and larger is
the whole difference between a small host doing two things properly and one
doing eight things shallowly. `references/model-adaptation.md` has the per-tier
table and the evidence.
