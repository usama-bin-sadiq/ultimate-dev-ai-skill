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

**This structure is now implemented.** `tools/run-state.py` creates, reads, updates and
checks it — one JSON file per run under `.ultimate-dev/`. It was specified here for the
whole life of the repository with nothing reading or writing it, which meant every claim
the architecture made about resumption rested on a file that did not exist.

`run-state.py check` is the gate, and it is deliberately strict about the four ways this
file becomes a decoration:

| Check | Why it exists |
|---|---|
| `coordination.why` is non-empty | An unexplained mode is a default nobody will review |
| mode `handoff` requires `active_agent` | Otherwise the conversation has no owner |
| `authority` only outside a handoff | Authority cannot sit in a mode that has no holder |
| `evidence` is `OBS-n` or `none`, and resolves | Prose evidence cannot be checked for existence, so fabrication is undetectable |
| `rejected` and `recovery` are non-empty | A decision with no alternative is an assertion |
| mode changed 3+ times | That is a signal the first choice was wrong, not that the task is hard |

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
