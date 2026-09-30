# State System

Every substantial task maintains a **RunState**: the single structure that lets
the kernel know where it is, what it believes, and what it has already done. Its
purpose is resumption. A task that cannot be resumed from its own state is not
under control, and a long task that cannot be resumed is a task that will be
restarted from nothing.

State is also what makes verification possible: you cannot check whether the
criteria hold if you did not record what you did.

## Shape

```text
RunState
  task               objective, requirements, criteria   (see task-model.md)
  objective           one sentence, user's terms
  requirements        numbered, checkable
  constraints         time, tools, data, permissions, prohibitions
  coordination        mode — why — until — changed[]      (see coordination-modes.md)
  active_agent        who holds the conversation          ◄── revision 2
  authority           inline | delegated                  ◄── revision 2
  assumptions         claim — if false: X — confidence — checked by: Y
  unknowns            item — blocking / non-blocking
  evidence            claim → evidence → source            (see evidence-system.md)
  context             what is loaded, its provenance and freshness
  capabilities        what is in use, and its validation status
  skills              which capabilities were selected, and why
  decisions           the decision ledger                  (see decision-ledger.md)
  strategy            the chosen approach, and its alternatives
  reasoning           current rung, scale, and why
  plan                work units, dependencies, schedule
  actions             what was attempted
  observations        what actually happened               (see observation-system.md)
  failures            classified, with responses          (see recovery-system.md)
  verification        criteria, verdicts, evidence
  learning_candidates patterns awaiting validation
  budget              effort spent and remaining
  provenance          origin and transformation chain
  result              the delivered outcome
```

**Part of this structure is implemented.** `tools/run-state.py` creates, reads, updates
and checks it — one JSON file per run under `.memory/`. It was specified here for the
whole life of the repository with nothing reading or writing it, which meant every claim
the architecture made about resumption rested on a file that did not exist.

The shape above is the design. What the tool actually carries today is a subset, and the
honest list matters more than the aspirational one, because a spec that claims more than
the code delivers is the same defect decision 0013 exists to prevent, one level up:

| Field | Status |
|---|---|
| `objective` `coordination` `active_agent` `authority` `assumptions` `verification` `result` | implemented and checked |
| `steps` `context` `deliverables` | implemented and checked (see below) |
| `rung` `scale` `rung_triggers` | implemented; constrained vocabularies, triggers required at R2+ |
| `decisions` `observations` | implemented and checked |
| `task` `requirements` `constraints` `unknowns` `capabilities` `skills` `strategy` `failures` `learning_candidates` `budget` `provenance` `evidence` | **not implemented** — no field is written, read, or checked |

Nothing in the table above is a promise that the missing fields will arrive. They are
named so that a reader knows which claims of this document are architectural and which
are tested.

### Working memory and deliverables are different things

State lives in `.memory/`, and that directory is the agent's private, disposable,
gitignored working memory. It is **not** where output goes.

`deliver --path <p> --what <w>` records a file the run produced, and refuses any path
inside `.memory/`. The refusal is the point. A deliverable filed in the memory directory
is invisible to the person who asked for it, uncommittable, and lost when the directory
is cleared — and because the directory is gitignored, nothing in the repository ever
notices the file existed. An agent that has run for a long time has the least context
left and the strongest incentive to file its work somewhere private and convenient, so
this is enforced by the tool rather than stated as a convention.

`init --deliverables <path>` records where the user asked output to go. Deciding that
once, at the start, from the request, is what stops it being re-guessed at the end.

### The step log answers "what is this agent doing right now"

`step --doing <what> --precondition <p> --expect <e>` opens a work unit; opening another
one supersedes the first, so at most one step is ever current. `show` prints that step
first, before the run header, because the question a human asks of a running agent is
"what is it doing" and the answer should not be the fourth line — a transcript answers
that question worse the longer the run gets.

`--precondition` and `--expect` are required, not optional. Step 5 defines a work unit as
independently verifiable, and a precondition is what makes it so: it is the condition a
resuming agent re-checks before repeating the work, and an expected result is the
observable condition that tells it the step is finished.

At R2 and above, `--capability` and `--verify` are required too, and those are the two
that get skipped — everybody writes the other three. A unit worked on with no named
capability cannot say whether that capability was reachable, and an `--expect` with no
`--verify` is a prediction rather than a check. §26 gives a work unit five fields; these
are the two whose absence is invisible, which is why nothing complained until the tool
asked. R0 and R1 are exempt for the same reason the step gate is: at those rungs a unit
is a sentence, and five fields of a sentence is the ceremony the kernel criticises.

`check` refuses an R2-or-higher run with no steps at all, and refuses two steps open at
once. R0 and R1 are exempt: the kernel calls recording at those rungs ceremony, and a
gate that fires there is the thing it criticises.

### The process log is the one structure that can contradict the state

Everything else in this file is a record, and a record cannot assert — which is why the
rung, the mode, the evidence pointers, the dispatch chain and the criteria are all
enforceable. The process log is prose, so it can say something the ledger contradicts,
and a run can satisfy every gate above and still write `P07 — DELEGATE` for a delegation
that never happened.

```sh
python3 tools/run-state.py log --kind <stage> --what "<what happened>" [--under P03]
python3 tools/run-state.py log --list
```

`log` is the gate for that. Entries are numbered `P01`, `P02`, …, never reset — including
across a recovery, because a number that restarts at 1 after a failure produces a log that
cannot be read to find out what had already been tried, which is the only reason to
number it at all. Substeps hang off a parent as `P03.1` and the top-level count is
unaffected, so a log reads `P01 … P03.1, P04` rather than fragmenting.

The vocabulary is closed, and each kind that claims something *about the work* is checked
against the work: `--kind delegate` is refused unless the dispatch ledger has a capability
at `invoked` or beyond, and `--kind verify` is refused unless a capability reached
`verified` or an acceptance criterion is met. `--kind complete` is refused until `finish`
has recorded a status. A run that did its work inline is not penalised — it uses the
kinds that claim nothing about the ledger, which is the honest description of what
happened. The third check is ordering: a stage is refused unless the log has already
been where that stage comes from, so `verify` needs an `observe` and `observe` needs an
`execute`. That is what stops a log from being written forwards at the end. The full
predecessor table is in `references/execution-system.md`.

`execute-inline` exists because of a gap this found on real work. A run that did the
job itself has no honest way to record that, since `execute` claims a dispatch is
running and the dispatch ledger correctly says nothing was dispatched. The alternative
was to write nothing, and a log with a hole where the execution happened is the exact
failure the log exists to catch.

`check` re-reads the same three things, because a state file can also be hand-edited and
because a criterion can be reopened by a later `require` after the run claimed completion.

### Acceptance criteria: what must be true when the run ends

A step says what the agent is *doing*. A criterion says what must be *true* when it
is finished, and only the second one tells you when to stop. The two are not
interchangeable and a run needs both: “add retry logic” is a step, “the retry header
is three attempts and the error is logged once” is a criterion.

```sh
python3 tools/run-state.py require  --what "<what must be true>"
python3 tools/run-state.py satisfy  --what "<verbatim>" --evidence OBS-n
python3 tools/run-state.py blocked  --what "<the blocked part>" --reason "<why>" \
                                --tried "<a route walked>" [--next-action "<what next>"]
```

`check` refuses an R2-or-higher run that ends with any criterion `open`, and refuses
an R2-or-higher run that has steps but no criteria at all — work with no stopping
condition stops when the work *looks* finished, which is the failure where a precise
account of the unfinished work is delivered in place of the work.

This is the one gate that answers *whether the objective was met*, and it is
deliberately mechanical rather than a matter of judgement. Prose does not work here:
an explicit “do not give up” line in a system prompt does not change paired success,
and a model asked whether its own run is complete scores it complete regardless of
what happened (AUROC ≤ 0.65 across five judge models) because it anchors on
confident closing language. So the question is not put to the model; it is answered
by a script over state the model wrote earlier.

`satisfy` requires `--evidence` to resolve to a recorded observation, exactly as
decision evidence does. A criterion met by restating the criterion is not met.

`blocked` is the exit, and it is the expensive one. `--tried` is mandatory and must
be non-empty, because a capability you did not find is a hypothesis rather than a
fact, and the declaration has to name the routes walked before it can stand. The
same block cannot be declared twice for the same reason unless `--next-action`
records what will be executed — the analogue of a harness-level self-reference
guard, so a run that has already written “this is blocked” cannot end on the
same words. The bound is structural, which is what keeps it from being a plea.

The mirror failure is not fixed by this. A run that blocks when it could have
answered fails the same gate, because a decline does not satisfy a criterion and
produces no deliverable. Both directions are gated; neither is a stylistic
preference.

### The terminal status: which of the two conditions of §55 holds

A run ends one of two ways and the record has to say which, because the delivery is
written by the same judgement that wrote the state and they will agree by default.

```sh
python3 tools/run-state.py finish --status completed|partial|blocked|failed \
        [--remaining "<what is outstanding>"] [--attempted "<what was tried>"] \
        [--recovery "<what recovery was tried>"] [--next-action "<what next>"] \
        [--replace --why "<what changed the recorded ending>"]
```

`completed` is the only status that asserts the objective was met, so it is the only one
gated on §35's four conditions, and all four are reported separately because each fails on
its own: every work unit closed, at least one acceptance criterion and all of them met,
the verification behind them passed, and no capability in flight. Each has a distinct
failure and a distinct repair, so collapsing them into one message would hide which one
you are looking at.

The other three each carry the field the spec gives them, and the asymmetry is the point.
`partial` needs `--remaining`, because a partial report with no remainder is a complete
one with a caveat; it also needs work to have actually happened, so a run that never
opened a step cannot claim it. `blocked` needs a `blocked` record whose routes were
walked. `failed` needs `--attempted`, because `failed` and `blocked` are opposite claims
— attempted and lost, versus prevented — and a run that conflates them has not decided
which one occurred.

A second ending is refused unless `--replace --why` records what changed. Retracting a
verdict is a decision, and the whole point of recording one is that changing it is visible.

`audit` is the complement. Every gate on this page reads the state; `audit` reads the
delivery, because a run can satisfy all of them and still hand the user a report
describing work it did not do.

### The dispatch contract: a capability that was chosen and not run

The kernel has an over-delegation guard — “delegation is a cost, not a default” —
and until this was added, no rule at all pushing the other way. That asymmetry is
not neutral. With a cost stated and no benefit stated, a run quietly stops loading
the capability it was built around and does the work with whatever is already in
context; and because doing the work inline *always* feels compliant, no rule about
dispatch quality catches it. The mirror is the under-delegation failure, and it is
invisible from the transcript for the same reason every other one of these gates is:
a precise account of the work reads exactly like the work.

```sh
python3 tools/run-state.py dispatch --for "<capability, as the host names it>" \
                                    --state selected|invoked|running|observed|verified
python3 tools/run-state.py dispatch --for "<capability>" --state invoked \
                                    --brief "<objective, input, constraints, expected \
                                             output, success criteria, verification, \
                                             available context>"
python3 tools/run-state.py dispatch --for "<capability>" --state observed \
                                    --result-status completed|partial|failed \
                                    --result "<what came back>"
python3 tools/run-state.py dispatch --for "<capability>" --state unreachable \
                                    --tried "<a route looked for>"
python3 tools/run-state.py dispatch --for "<capability>" --state skipped \
                                    --why "<the reason>"
```

Six rules, all structural:

1. **`selected`, `invoked` and `running` are not terminal.** `check` refuses an
   R2-or-higher report while any capability sits in one. A capability chosen and
   never observed is a delegation described rather than performed.
2. **`invoked` needs a brief naming all seven of §11's fields.** A delegate given
   three of them returns a guess about the other four, and the guess is
   indistinguishable from an answer in the final report. The fields are a closed
   list rather than prose precisely so that "I described the objective" cannot
   stand in for naming it.
3. **`observed` needs `--result-status` and `--result`.** A capability that
   returned with nothing attached is indistinguishable from one never invoked,
   and `completed` is a claim about the *capability*, not about the run — a
   specialist that says "Done" has returned, which is the thing being recorded.
4. **`unreachable` needs `--tried`, non-empty.** `NOT_INVOKED` and `UNREACHABLE`
   are different states: one is an action not taken, the other is a capability
   proved absent. Only the second is a finding about the host, and the first is
   what a run writes when it stops looking.
5. **`skipped` needs `--why`.** A deliberate pass-over is a decision with a
   recorded reason. An unnamed one is indistinguishable from having forgotten the
   capability existed.
6. **The chain does not run backwards.** A state that un-observes itself is a
   rewrite of history, which is worse than the omission it papers over.

`verified` additionally needs `--evidence OBS-n`, because a capability reported as
checked with nothing recording what was checked is an assertion wearing the word for
a finding.

Two counts are compared rather than asserted, because §40 is about synthesis and
synthesis is the one thing two specialists' outputs cannot be assumed to have done
between them. `check` refuses a run that observed two or more capabilities and
recorded no comparison, and it refuses a run that dispatched-and-observed while
every work unit named `inline` — §38's over-delegation in its narrow, checkable
form: isolation was paid for and the work happened here anyway.

### One gate before you stop, and the routes it walks

If the objective is not met, walk the fifteen routes in
`references/completion-law.md` in order and take the first `yes`, then name the
one you took:

```sh
python3 tools/run-state.py blocked --what "<the blocked part>" --reason "<why>" \
  --tried "<what you actually looked for>" --routes <one of fifteen>
```

A block is what is left *after* that list, never the first thing noticed, and
`--routes` is what makes the walk a record rather than a claim. `--routes` is the
checkable half and `--tried` is the evidence; they fail in opposite directions,
because a block with a route and no detail asserts a category without showing any
work, and a block with detail and no route asserts that nothing systematic was
tried — the claim that most needs support and is least often given it.

The list is not restated here. Two copies of a fifteen-item list is one more
thing to keep in sync, and `tools/test-run-state.py` already holds
`completion-law.md` to the `ROUTES` constant, so the two cannot drift silently —
which is the whole reason the list is written down at all.

### Recovery names the failure, because "it failed" is not a class

`recover` records the failure reason, the recovery action, the previous and new
mode, the previous and new capability, and the result — and §28's nine classes are
a closed vocabulary rather than free text:

```sh
python3 tools/run-state.py recover --class <one of nine> --action "<what was done>" \
  --result "<what it produced>" [--from-mode M --to-mode M]
```

The classes are `capability`, `context`, `tool`, `input`, `execution`,
`verification`, `coordination`, `dependency`, `resource`. `--result` is required
rather than optional because a recovery with no recorded outcome has not been
evaluated, and a re-plan against an unevaluated recovery is a blind retry with a
longer log in front of it. Each recovery is numbered and none is ever reset, so a
run that failed four times says so rather than recording one recovery four times.

### Self-evaluation is recorded, not remembered

`references/self-evaluation.md` has §45's fifteen questions in prose, and
`reflect` is the same fifteen in state:

```sh
python3 tools/run-state.py reflect --list
python3 tools/run-state.py reflect --answer "<question>=<answer>" --answer ...
```

All fifteen or none. A question may be abbreviated to any prefix that is unique
among the fifteen, and a prefix that matches two is refused by name rather than
guessed at — two questions agreeing for eighteen characters is exactly how one
answer silently answers the wrong question.

`reflect` also has a floor on content. An answer counts when a reader who
disagrees could show it wrong, and the check refuses fifteen answers that name
no fault. Two conditions, and each exists because its absence broke the check in
one direction or the other: a finding opens on a negation *or* on a concession
(`but`, `however`, `although`, `except`, `under-delegated`), and in both cases at
least eight words have to follow the marker. The eight-word floor is what stops
fifteen bare "no"s — fifteen verdicts and not one finding — and the concession
list is what stops the check refusing "Yes, but the count of the gated rows was
self-reported", which is the shape an honest review actually takes. `--why` skips
the floor, for the run that looked and found nothing and would rather say so than
manufacture a fault. `references/self-evaluation.md` has the reasoning.

### Context is recorded as loads, drops, and acknowledged gaps

`context --ref <r> [--level C0..C6]` records what entered the context;
`context --ref <r> --drop --why <w>` records what was deliberately left out. Both
halves are required, and they fail in opposite directions — a record of loads
alone is a shopping list that never says what was omitted, so the next agent
cannot tell an intentional omission from an oversight. `check` refuses a drop with
no reason.

A load also names what it enables and its minimum scope, and a gap is a load that
turned out not to be answerable:

```sh
python3 tools/run-state.py context --ref "references/foo.md" --level C3 \
  --why "<why>" --enables "<the action this enables>" --scope "<minimum scope>"
python3 tools/run-state.py context --gap "<what is missing>"   # refuses check at R2+
python3 tools/run-state.py context --closed "<gap>" --how "<what resolved it>"
```

§15 names four things about a context request and two were being recorded, so
`--enables` and `--scope` are asked for at R2+: a request with no named action it
enables is an open-ended read, and one with no scope has not said what it will not
read. `--gap` is the other direction — a run that knows it is missing something
and has stopped is the failure §16 is about, so an open gap refuses `check` at
R2+ and only `context --closed` clears it. Gaps are how a run reports
incompleteness without claiming a blocker, and the distinction matters: a blocker
says the work cannot proceed, a gap says it has not yet.

`run-state.py check` is the gate, and it is deliberately strict about the ways this
file becomes a decoration:

| Check | Why it exists |
|---|---|
| `coordination.why` is non-empty | An unexplained mode is a default nobody will review |
| mode `handoff` requires `active_agent` | Otherwise the conversation has no owner |
| `authority` only outside a handoff | Authority cannot sit in a mode that has no holder |
| `evidence` is `OBS-n` or `none`, and resolves | Prose evidence cannot be checked for existence, so fabrication is undetectable |
| `rejected` and `recovery` are non-empty | A decision with no alternative is an assertion |
| mode changed 3+ times | That is a signal the first choice was wrong, not that the task is hard |
| R2+ has at least one step | At R2 and above the current work unit, its precondition, and what is about to happen are stated at every boundary; a run that never says what it is doing cannot be steered or resumed |
| at most one step is open | "What is the agent doing" with two answers gets answered from the transcript, which is what this file replaces |
| every step has a precondition and an expected result | A work unit without those is not independently verifiable, so it can only be re-run blind |
| a context drop has a reason | The next agent cannot otherwise tell an intentional omission from an oversight |
| a context load names `--enables` and `--scope` | A request with no named action it enables is an open-ended read; one with no scope has not said what it will not read |
| no open context gap at R2+ | A run that knows it is missing something and has stopped is the failure §16 is about |
| a recovery names its class and its result | "It failed" is not a class, and a recovery with no outcome has not been evaluated |
| a block names a walked route | A block asserted without a route claims nothing systematic was tried |
| an invoked capability has a brief | §11's seven fields; a delegate given three of them returns a guess |
| an observed capability has a result | A capability that returned with nothing attached is indistinguishable from one never invoked |
| dispatch and observation counts agree | Two capabilities observed and none compared is concatenation, not synthesis |
| dispatched-and-observed while every unit is `inline` | Paid for isolation and did the work here anyway (§38) |
| an open `execute` entry is not claimed complete | The ledger must be reconciled against the plan |
| no deliverable sits inside `.memory/` | A file filed in gitignored memory is invisible to whoever asked for it and lost when the directory is cleared |
| a requested deliverable location has something in it | The user named a path; nothing was written there |
| every §18 field is mapped or enumerated | Coverage is reported as a ratio, and only mapped-and-missing fields fail — a gate on a field the run never claimed to track would be enforcing something the spec did not ask for |

## The fields that earn their keep

Most of these are useful; four are load-bearing.

- **`assumptions`** — because a false assumption invalidates work that already
  looks finished, and nothing else reveals that.
- **`observations`** — because the gap between what was expected and what
  happened is the only input to recovery, and an unrecorded surprise silently
  corrupts the model of the situation.
- **`verification`** — because a verdict with no criteria attached cannot be
  re-checked, and "looks right" is not a status.
- **`budget`** — because without it, de-escalation never happens. Effort spent
  is what tells you the cheap path has stopped being cheap.

## Durability and resumption

Write state at every boundary crossing, not at the end. A run interrupted at
unit 14 of 20 must resume at 14, not at 1.

What makes a unit resumable:

- its **precondition** is stated, so it can be re-checked on resume;
- its **expected result** is stated, so partial completion is detectable;
- its **side effects** are identified, so a half-applied change is found.

That last one is the one usually missed. A unit that writes three of five files
and is interrupted has left the workspace in a state that is neither the old one
nor the new one. Record what was being changed so resume can finish or reverse it.

## State is per-run; memory is not

RunState is scoped to one task and discarded when the task ends. It is **not**
memory. What may persist between tasks is governed by `memory-system.md`, and what
may become durable behaviour by `learning-safety.md` — which is a much higher bar
and a separate decision.

Conflating the two is how a scratch assumption from one task becomes a permanent
rule, and how one project's specifics contaminate another's behaviour.

## Trust state

RunState records what has been *observed*, and observations are only as good as
their provenance. When writing an entry:

- mark its epistemic status — **Known**, **Inferred**, **Assumed**, **Unverified**,
  **Uncertain**, **Contradicted** (`provenance-system.md`);
- never write an expected result into an observation field;
- never write a tool result into state that was not actually observed.

The state file is the most-copied artefact in a run, because every later stage
reads it and trusts it. **Never report a tool result you did not observe.** A
fabricated entry here is invisible downstream, which makes it the single most
damaging failure in the system.

## Size discipline

RunState grows with the task, and at L5–L7 it can dwarf the work. Keep entries
append-only and prune what later work has superseded — but prune *derivations*,
never *evidence*. The observation that a dependency was discovered is
superseded; the observation that the tool returned exit code 2 is not.

If state is too large to be useful it has stopped being state and become a log.
Summarise the plan; do not summarise the evidence.

See `budget-system.md` for effort accounting, `observation-system.md` for what
qualifies as an observation, and `caching-and-reuse.md` for what may be
recomputed instead of stored.

## Why the record is written before the work, and not after

The kernel's central claim is that the coordination mode and the effort rung
follow the complexity of the task. That is a claim about a decision, and a
decision nobody can read back is not a capability — it is an assertion.

So the rung and the mode are recorded at the moment they are chosen:

```sh
python3 tools/run-state.py init --rung R1 --objective "<one line>"
python3 tools/run-state.py set-mode --mode delegate --why "<what justified isolation>"
python3 tools/run-state.py set-rung  --rung R2 --why "<what was discovered>"
```

The path is `tools/run-state.py`, relative to the skill root. It was written
without that prefix here and in the kernel, and every run that followed the
instruction literally wrote no state file — so the harness, which reads the file
rather than the transcript, scored each of those runs `undecided`. An
instruction that cannot be executed as written is not a soft version of the
instruction; it is a different one.

**This was not being asked for, and the measurement caught it.** The first real
run of the task corpus loaded the kernel, did the work correctly, and recorded
nothing — 0 of 8 rows decidable, every one `undecided`. The transcripts showed
`Skill "ultimate-dev"` loading, the right tool run, the right files read, and no
`run-state.json` anywhere. The kernel mentioned `set-mode` exactly once, in a
sentence explaining what the tool *does*, and nothing told a run *when* to call
it. Every step where the mode is decided was silent on recording.

The lesson is the shape of the defect rather than the missing line: a tool can be
documented accurately and still never be invoked, because describing a
mechanism is not instructing anyone to use it. The fix was in the kernel, as an
imperative with the command in it.

**Then the placement was wrong too, and that needed a second pass.** The first
fix put `init` in Step 1, where the task model is written. A run that has the
imperative in context still did not call it — and Step 0, thirty lines earlier, is
where the rung is actually chosen. Two things were wrong: the record was not an
instruction, and then the instruction was not adjacent to the decision it records.
A record a screen away from its own decision reads as a different topic, and a
model given a task does the task.

So the command now sits inside Step 0, immediately after the rung ladder it
records, and before the four triage questions are even answered. That is the
whole redesign: the rung decision and its record are one statement, not two
topics thirty lines apart. Whether it works is a measurement, not an assertion —
and `testbed/run-tasks.py --ask-record` exists to measure the adjacent thing, which
is whether a model asked explicitly to record will. Two numbers, and they are
allowed to disagree.

**The R0 case is the one that gets argued about.** A task model at R0 is one line
by design, and `references/decision-ledger.md` calls recording ceremony at the
lower rungs. The reconciliation is that the *rung* is not ceremony. It is a
single field, set once, and it is the only thing that makes an escalation
visible: a run that treated an R0 task as R3 and wrote nothing has left no
evidence that it did, so the failure is invisible rather than correctable. What
is forbidden at R0 is elaboration — plans, ledgers, verification ceremony — and
a rung is not elaboration. An unrecorded R0 is precisely the case that would
otherwise pass silently.

**Undecided is a real outcome, not a soft pass.** A run that recorded nothing is
scored `undecided` and excluded from every rate, because nothing is known about
what it would have chosen. Scoring it zero would be a false accusation: the run
might have chosen correctly and failed to say so. Scoring it one would convert an
absence into a measurement. Both were available, and the difference between them
is the whole discipline.

**Nothing here grades the run.** The recorded mode is read by a grader and
compared against an oracle. That comparison is the only thing in the system that
speaks about whether the chosen architecture was the warranted one, and it cannot
exist unless the run wrote something down first.
