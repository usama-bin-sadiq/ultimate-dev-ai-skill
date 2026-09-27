---
license: MIT
name: skill-creator
description: Internal sub-skill of ultimate-dev, selected by the kernel, not requested by a user. Handles the engine side of capability expansion once the kernel has already decided that no existing capability covers a real recurring gap — specification, generation, composition, security review, adversarial and negative-trigger testing, promotion, versioning, and deprecation. Produces a CANDIDATE skill that stays untrusted until the kernel promotes it on evidence. If the request is a user asking whether some repeated work should become a skill, that is the kernel's decision to make first, not this sub-skill's.
---

# skill-creator

The controlled capability-expansion mechanism. It exists so the kernel can grow
beyond the skills it shipped with, without self-improvement becoming
uncontrolled self-corruption.

Everything here serves one constraint:

> **A generated skill is a candidate until proven. It never becomes trusted
> behaviour because it was written.**

## The gap arrives here

The kernel calls this skill when capability resolution reaches step 4 or 5 — after
doing it directly, using an existing capability, and composing existing
capabilities have all genuinely failed. That ordering is not a formality. The
most common failure of this engine is being invoked when one of the first three
would have worked, which produces a proliferation of narrow skills that split the
trigger signal and teach the kernel nothing.

**Before generating anything, prove the gap is real:**

1. Is this needed again? A one-off is a step in a plan, not a skill.
2. Does an existing skill cover it? Search descriptions, not just names.
3. Can two existing skills be composed? Composition beats creation, nearly
   always.
4. Is the need *reusable capability* or just *this task*? Only the first is a
   skill.

If any of these resolves the gap, the answer is reuse or compose, and this engine
records that finding rather than producing a skill.

## Lifecycle

```text
OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → ACTIVE → DEPRECATED
```

Each transition is a gate with an entry condition. A candidate that fails a gate
returns to CANDIDATE with a record of why, or is rejected.

| State | What it means | What may use it |
|---|---|---|
| OBSERVED | A gap was noticed. No design yet. | Nothing. It is a note. |
| CANDIDATE | Designed, specified, written. Untested. | The creating run only, explicitly. |
| VALIDATING | Under test. | The test harness. |
| VALIDATED | Passed security and behavioural review. | Named tasks that match its scope. |
| PROMOTED | Reviewed and recorded. | Its declared scope. |
| ACTIVE | In normal service, being monitored. | Anything matching its description. |
| DEPRECATED | Superseded or harmful. | Nothing. Must be removable. |

The point of the ladder is reversibility. A promoted skill that turns out wrong
must be identifiable, attributable, and removable — which requires knowing when
it was promoted, on what evidence, and by which decision.

## The flow

```text
GAP
 ↓
Reuse?  →  compose?  →  design candidate        (stop here if any resolves it)
 ↓
SPECIFY      name, purpose, inputs, outputs, requirements, dependencies,
             constraints, security boundaries, verification criteria,
             failure modes
 ↓
GENERATE     content that does what the specification says
 ↓
SECURITY     what authority does this widen? what can it be made to do?
 ↓
TEST         behaviour · adversarial · interaction with existing skills
 ↓
VALIDATE     correctness · completeness · applicability · ambiguity ·
             failure behaviour
 ↓
JEv          promote, revise, or reject — and record which
 ↓
PROMOTED → ACTIVE
 ↓
DEPRECATED   when superseded, when it drifts, or when it was wrong
```

## Step 1 — specify before writing

A skill written before it is specified inherits whatever the author happened to
believe. The specification is the artifact that gets reviewed, and it is where
most of the value is.

Define, in this order:

- **name** — what it does, not what it is called. A name that describes a
  category will collide with its siblings.
- **purpose** — one sentence, and a test for when it must *not* fire.
- **inputs / outputs** — concrete, with types and formats.
- **requirements** — what must be true before it runs.
- **dependencies** — other skills, tools, permissions.
- **constraints** — what it must not do.
- **security boundaries** — what authority, if any, it widens.
- **verification criteria** — what a test must observe to call it correct.
- **failure modes** — what it does when its inputs are wrong, missing, or
  hostile.

The **negative trigger test** belongs in the specification, not as an
afterthought. A skill whose description matches everything will fire on requests
it cannot serve, and the cost of a false trigger is higher than the cost of a
miss: it burns the user's attention on a process they did not need.

See `references/skill-design.md` and `references/skill-contract.md`.

## Step 2 — generate

Write the skill so that its description is discoverable and its body is
executable. Body before description: if the body does not work, a beautiful
description only makes the failure easier to find.

A generated skill must contain:

- A description that states the user goal, when it applies, and what it
  produces — and does not name a vendor, CLI, or path unless it genuinely
  depends on one.
- A body with the decision procedure, not just the happy path.
- Named failure modes and what to do in each.
- An explicit statement of what it must not do.

If the specification cannot be expressed as a procedure, it is not a skill. It is
a document.

See `references/skill-generation.md`.

## Step 3 — security review

A generated skill is **untrusted content that the kernel wrote itself**, and it is
treated exactly like content fetched from the internet. The exception would be
that a self-authored skill can be assumed benign, and that exception is the whole
attack surface.

Ask, before any promotion:

- Does it widen authority? Can it cause effects outside the task?
- Can its instructions be subverted by its *inputs*? A skill that reads a file
  and then follows instructions in that file is an injection vector with extra
  steps.
- Does it exfiltrate, transmit, or persist anything it should not?
- Does it claim capabilities it does not have, so a future run trusts a fiction?
- Does it tell the reader to disable a check, bypass a confirmation, or skip
  verification? This is the single most reliable marker of a poisoned skill.
- Can it be induced to do something its author would not have sanctioned?

Any finding blocks promotion until resolved. Findings are recorded, not
summarised away. See `references/skill-security.md`.

## Step 4 — test

Three kinds, and all three are required.

1. **Behavioural** — does it do what the specification says, on the cases the
   specification names? Including a positive case that *must* work.
2. **Adversarial** — hostile inputs, missing inputs, contradictory inputs,
   inputs designed to make it do the wrong thing. A skill that has never been
   attacked is not tested.
3. **Interaction** — does it collide with an existing skill? Two skills that
   fire on the same request split the trigger signal, and the user gets two
   half-processes instead of one.

Plus the case everyone forgets: **the negative**. A request that resembles the
skill's domain but must not trigger it. Without a negative, false-positive rates
are unmeasurable and a skill that fires on everything scores perfectly.

See `references/skill-testing.md` and `references/skill-validation.md`.

## Step 5 — decide, and record

Promotion is a JEv decision like any other. It gets a record: what was promoted,
on what evidence, what alternatives were considered, and what would deprecate it.

The disposition is one of three:

- **Promote** — evidence of generalisation beyond the instance that produced it,
  plus a stated scope.
- **Revise** — a specific, named defect, and a re-test plan. Not "needs work".
- **Reject** — the gap was not real, or the design cannot be made safe, or an
  existing skill covers it after all.

Rejecting is a normal, successful outcome. A run that produces a skill every
time it hits an unfamiliar problem is misbehaving, not learning.

See `references/skill-promotion.md`.

## Step 6 — maintain

A skill that is never revised becomes wrong. Its description drifts from its
body, its assumptions expire, and it keeps firing on requests it now handles
badly.

- **Version** — record what changed and why, so behaviour can be attributed to a
  version. See `references/skill-versioning.md`.
- **Attribute** — record provenance: which gap, which run, which decisions. A
  skill with no provenance cannot be evaluated. See `references/skill-provenance.md`.
- **Deprecate** — when superseded, when it drifts, or when it was wrong. Removal
  must be as easy as installation. See `references/skill-deprecation.md`.

## What this engine refuses to do

- Write a skill for a single task.
- Write a second skill that fires on the same request as an existing one.
- Promote a skill that has not been attacked.
- Promote a skill whose author was the thing under test.
- Generate a skill that disables a check, bypasses a confirmation, or instructs
  the reader to trust it.
- Rewrite an existing skill in place without a version and a regression check.

See `references/skill-anti-patterns.md`.

## References

- `references/skill-design.md` — what makes a skill worth creating
- `references/skill-contract.md` — the specification format, field by field
- `references/skill-discovery.md` — finding out what already exists
- `references/skill-generation.md` — writing the candidate
- `references/compose-or-create.md` — combining instead of creating
- `references/skill-validation.md` — the seven validation questions
- `references/skill-testing.md` — behavioural, adversarial, interaction, negative
- `references/skill-versioning.md` — versions, attribution, compatibility
- `references/skill-security.md` — the security review
- `references/skill-provenance.md` — where it came from and who to blame
- `references/skill-promotion.md` — the promotion gate
- `references/skill-deprecation.md` — removal, and why it must be easy
- `references/skill-anti-patterns.md` — how this engine fails
