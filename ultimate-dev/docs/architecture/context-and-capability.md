# Context and capability

Two ladders govern what the kernel has in hand: what it knows, and what it can
do. They are separate, they run in parallel, and they fail in opposite
directions.

The rule both ladders serve: acquire against a specific decision, and hold only
until that decision closes.

## The context ladder, C0 to C6

| Level | Content | Load when | Stop when |
|---|---|---|---|
| **C0** | the task and its state: objective, requirements, constraints, unknowns, assumptions, success criteria, decisions taken, units in flight | always; it is the floor | you can restate the live decision and where the work stands without rereading anything |
| **C2** | capability instructions for the unit in hand | the next action needs a procedure or convention you were not given | you can execute the unit correctly without guessing |
| **C3** | targeted references: the specific files, symbols, or passages the decision turns on | a decision names something whose current content you do not know | you hold the region that bears on the decision, not the whole artifact |
| **C4** | project material: the code, data, documents, and configuration actually in hand | the decision depends on the real state of the system, not its description | you can predict the effect of the change on the system as it is |
| **C5** | external evidence: what must be looked up beyond what you hold | a blocking unknown cannot be resolved from anything in hand | the unknown is answered, or recorded as a stated limit |
| **C6** | specialist depth: the long tail, the contested case, the expert treatment | the decision is novel, high-consequence, or contested and shallower context did not settle it | the residual uncertainty is named, bounded, and priced rather than closed |

### How to climb

One level, then ask whether the live decision changed. Stop when it did not.
C6 is not the goal; it is the fallback, reached when the answer is still
uncertain and the price of being wrong justifies it.

Skipping down is the common error. Jumping to C4 or C5 without C2 and C3 means
acting on material whose conventions you never checked, then debugging your own
misreading for several iterations.

Choosing depth is itself a decision, and it gets a record: the depth selected,
the depth rejected and why, the cost, the evidence, and the observation that
would send you one level deeper.

### Rung sets the floor, not the depth

| Rung | Typical ceiling | Reason |
|---|---|---|
| R0 | C0, sometimes C2 | the action is already determined; more context is delay, not safety |
| R1 | C3 | one or two dependent facts decide the step |
| R2 | C4 | parts interact; the real state of the material changes the plan |
| R3 | C5 | unfamiliar territory; blocking unknowns justify real cost |
| R4 | C6 | irreversible or high-consequence; expert depth is cheaper than a wrong action |

The rung is a ceiling that a condition may breach, not a hard limit. One
observation that contradicts the plan outranks the table.

## The context compiler

Loading is not compiling. Loading is retrieval plus hope: whatever arrived stays
and the decision is left to sort the pile. Compilation is a series of deletions.

| Stage | Does | Fails as |
|---|---|---|
| Requirements | writes what the live decision needs, as nouns and predicates | you retrieve by topic and get adjacent material |
| Retrieve | fetches only those, from the nearest rung of the ladder | you guess at content you could have read |
| Rank | orders by bearing on the live decision, not by size or availability | the loudest artifact decides |
| Filter | drops everything that cannot change the decision | load-everything |
| Resolve | follows what the kept items themselves require, to a fixed point | an item is used under a rule you never read |
| Deduplicate | collapses restatements into one entry with several sources | a fact repeated five times reads as five confirmations |
| Compress | rewrites at the smallest form that preserves what the decision uses | bloat, or a summary that quietly changes meaning |
| Freshness | compares retrieval time against the item's time to live | you act on an expired fact and never learn it expired |
| Budget | drops in a fixed, declared order until the set fits | arbitrary trimming |
| Provenance | stamps every surviving item before use | the claim cannot be traced later |
| Emit | assembles the set and records what was dropped and why | silence about what is missing |

Two tests make compression lossless, and both must hold:

1. **Recoverability** — every load-bearing element of what you dropped is still
   reconstructible, or is recorded with its source so it can be re-retrieved.
2. **Meaning invariance** — no surviving statement changed scope. Qualifiers,
   exceptions, thresholds, and negative cases survive intact.

A summary that drops the "except when" is not a compression. It is a new claim.

Deduplication matters more than it looks. Repetition is not corroboration. One
fact from three sources is one item with three attestations, and the strength of
corroboration is a judgement made at the evidence layer, not a side effect of
how many pages said it.

## The two opposed failures

| Failure | Appearance | Response |
|---|---|---|
| **Load-everything** | reading a whole subsystem to decide one constant; reasoning diluted across material that bears on nothing | cut back to C3. Keep the region, drop the artifact. Re-rank by bearing on the live decision |
| **Load-too-little** | deciding from a description of the system rather than the system; acting on assumptions never examined | escalate one rung. If you cannot state what you do not know, you are at the wrong depth |

Between the two, load-too-little is more dangerous. Load-everything announces
itself as confusion, which is visible and correctable. Load-too-little
produces a confident wrong answer, which is invisible until it costs something.
Neither is fixed by a larger budget.

The single rule that avoids both: load the narrowest thing that would change
the decision, and no more. The second clause is where under-loading comes from,
and the first is where over-loading comes from. Hold both.

A third failure sits between them: loading the right material at the wrong
freshness. A correct answer about a stale artefact is a wrong answer.

## The capability ladder

A capability is any means of making progress: a skill, a tool, a command, a
person, a document, a model, a deterministic operation, or something that does
not exist yet.

Resolve in this order, and stop at the first rung that works:

1. **Do it directly.** No capability required. Most tasks end here.
2. **Existing capability.** A skill, tool, or reference that already covers it.
3. **Compose.** Combine what exists. Composition beats creation.
4. **Acquire.** Fetch or install one, then validate it.
5. **Create.** Build one, and only when 1 to 4 genuinely fail.

### The disqualifying question

Before creating: *will this be needed again?*

A one-off is not a skill. It is a step in the plan. Minting a skill per task is
proliferation, and proliferation is a failure mode, not a feature: nothing gets
reused, and the trigger signal splits until the library matches nothing. See
`../decisions/0002-skills-are-resources-not-agents.md`.

### Validation is not optional

A capability is validated before use. Three questions, in order:

1. **Existence** — is it actually there, and does it load?
2. **Behaviour** — does it do what it claims, on a case you can check?
3. **Output shape** — is the result what you think it is? A capability that
   returns something other than what its name implies will corrupt every
   decision downstream.

An unvalidated capability produces confident nonsense, which is more expensive
than an honest gap because it removes the signal that something is missing.
Composition and creation belong to `skill-creator`, which owns specification,
validation, security review, and promotion. Hand it the gap. Do not hand-author
a skill inline, and never let a generated skill become trusted behaviour
immediately. The lifecycle is in `skills/skill-creator/SKILL.md` and the
gates are recorded in `../decisions/0003-gated-learning-lifecycle.md`.

## How the two ladders interact

They are not sequential. They are driven by the same decisions, and each one
constrains the other.

**Context gates capability.** You cannot tell whether an existing capability
covers the work until you hold the material it operates on. Choosing between two
skills usually requires reading the thing they would act on, which is a context
decision first.

**Capability gates context.** Once you know you will use a specific tool, the
context budget is no longer open-ended. The tool's requirements, its input
format, and its error modes become the relevant material, and unrelated
material is now provably irrelevant.

**Both are budgeted from one budget.** Context consumes tokens, calls, and
attention. Capability consumes tokens for discovery and validation, plus real
cost for acquisition. Splitting them into separate budgets invites spending
both.

**Both stop at the same place.** The narrowest context that settles the
decision, the cheapest capability that closes the gap. When neither is available
at acceptable cost, the correct move is the same in both cases: report the
block, with what is missing and what resuming would require.

### Worked example

Objective: change a retry policy in a client library. C0 names the requirement
and the success criterion; C2 pulls the retry convention for this codebase; C3
pulls the retry module and its test file. The decision is now changeable, so stop
at C3 — reading the whole client library is load-everything, and skipping the
convention is load-too-little. Capability resolves at rung 1: the project's own
test runner, confirmed to exist and to be the command this project uses. The
interaction is visible: the runner's error output told the capability ladder that
C3 needed one more file, the fixture, so context depth moved because of a
capability result.

### Worked example, opposite direction

Objective: build an operating-system kernel subsystem. Context runs C0, then C2
for the architecture conventions, then C5, because the blocking unknown is the
hardware interface and nothing in the repository answers it. C6 is reached only
for the interrupt and memory-model questions where the C5 sources disagree.
Capability resolves at rung 3: an assembler toolchain and emulator exist, a
memory model design capability does not, and that gap goes to `skill-creator` as
a specification entering the lifecycle as a candidate. The interaction runs the
other way: the acquired emulator is what made the C5 evidence checkable, and the
C6 material selected which emulator features to demand.

## Anti-patterns, in this subsystem

- Loading C5 before C3 because the material is interesting.
- Treating repetition across sources as corroboration.
- Summarising away a qualifier and carrying the summary forward as a fact.
- Creating a skill for a one-off step.
- Composing two capabilities when the first rung would do.
- Using a capability because validating it would take longer than doing the work
  manually, when the manual work is not deterministic.
- Deciding depth once at the start and never revisiting it after evidence
  arrives.
