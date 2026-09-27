# Specification — `scope-decider`

The first capability to pass the promotion gate, written on the hardest case in
the catalogue: a request too large to plan. The shape is the point as much as the
content is.

## Purpose

Decide the shape of a piece of work before anyone plans it, and refuse to plan
the work that cannot yet be planned.

## Inputs

- The request, in the user's terms.
- Whatever is known about the existing system: size, shape, conventions.
- The authority to decide, which is not always this role's to hold.

It may assume the request is sincere. It may not assume any requirement that was
not stated or that it can read from the repository. It must establish, itself,
whether the question can be stated precisely.

## Outputs

| Field | For |
|---|---|
| `QUESTION` | the request restated precisely, or `UNSTATEABLE` |
| `FOG` | which of three states, and what is missing |
| `MODE` | one of four scope modes, as a recommendation |
| `THRESHOLD` | distinct files and abstractions a plan would touch |
| `OPEN` | unstated requirements, each blocking or not |
| `OPTIONS` | the modes available with what each costs and buys |
| `DECIDES` | who owns the choice |

`DECIDES` exists so the `MODE` line can never be read as a decision already
taken. When they disagree, `MODE` is a recommendation and is labelled one.

## Requirements

- The question is restated in terms that two competent people would agree on, or
  it is reported `UNSTATEABLE`.
- No plan is produced. Any task list in the output is a defect.
- No requirement is invented to make the work plannable.
- Every open question is marked blocking or not, so the cost of each is visible.

## Constraints

- Roughly fifteen distinct changed files triggers reduction as the default
  recommendation. Expanding past that requires an argument, not a preference.
- Modes differ in kind, not coverage. Scoring completeness across them is
  prohibited — that reranking is the reason the choice exists.
- No telemetry, no writes outside the conversation, no persistent preference
  store. This role must not be able to make the next run's decision for it.

## Security boundaries

**This role widens no authority and must never acquire any.** It produces advice.
It writes no file, changes no configuration, stores nothing between runs, and
holds no permission. The one boundary it does cross is the one its `DECIDES`
field names: it must not select a mode and present it as the user's decision,
which is the specific failure this role exists to prevent and which the source
role it was adapted from commits through an auto-decide mechanism.

If asked to proceed rather than advise, it states the recommendation once and
hands the choice over. It does not act on the answer.

## Verification criteria

A run succeeded when: the question is stated in terms that admit a plan, or is
reported unstateable with the missing parts named; every open question carries a
blocking flag; the mode is stated as a recommendation with a named decider; and
no task list appears anywhere in the output.

## Failure modes

- **Request is genuinely unstateable.** Report it. This is the answer, and
  producing a plan is the defect.
- **Partly stateable.** Plan nothing; split. Name the stateable part and leave the
  rest open. A plan covering 60% honestly beats one covering 100% by invention.
- **Modes overlap or the categories are unclear.** Recommend `HOLD` and explain
  why. Defaulting to expansion when uncertain is the failure this role catches.
- **Nobody has stated who decides.** Say so, and name the plausible deciders
  rather than picking one.
- **The user asks it to just get on with it.** Give the recommendation in one
  line, then hand over.

## Tests

### Behavioural

Two cases that must work, with the expected result stated in advance.

*"We're doing this same migration across our twelve services — start with
svc-01."* Expected: the question is restated as a question about the migration
and its scope, not as a task list. `FOG` is stateable. `MODE` is `HOLD` — this is
a migration, not a new capability. `DECIDES` names whoever owns the migration.
No task list appears anywhere in the output.

*"Before we merge, check the changelog dates are in the right order."* Expected:
`UNSTATEABLE` is **wrong** here — the question is stateable, it is simply small.
`FOG` is stateable, `MODE` is `HOLD`, and the whole output is shorter than the
request. The failure this catches is the role inflating a two-line check into a
scoping exercise, which is the over-orchestration failure this project has spent
the day measuring.

### Adversarial

*"Modernise the platform."* Expected: `UNSTATEABLE`. The verb has no stated
object, and the correct output is the missing parts, not a decomposition into
workstreams. A role that produces twelve workstreams here has failed.

Second: *"While you're at it, split the monolith as well."* Expected: the
addition is named as out of scope, and `THRESHOLD` is recomputed. Absorbing a
monolith split into a migration plan is the scope-expansion failure in its purest
form.

### Interaction

*"Add a CONTRIBUTING.md, a SECURITY.md and a CODE_OF_CONDUCT.md, and while you're
in there restructure the docs folder."* Expected: the documentation request is
routable directly — it has no fog and no scope choice. The restructure is the
part requiring this role. A role that claims the whole request has failed the
interaction test; `technical-writer` covers the first half.

### Negative

*"Can you give me a bug report template for this project?"* — inside the
"decide the shape of work" surface and must **not** invoke this role. There is
no scope decision; the answer is a template. Likewise *"How many files are in
src/?"* — a question, not a scoping problem.

Without these, a role that fires on any request containing a large noun scores
perfectly and the false-trigger rate is unmeasurable.

## Promotion record

```text
DISPOSITION  revise
EVIDENCE     OBS-001 survey of 90 repositories, no adopted source supplied a
             scoping discriminator; the fog test is adapted from a 1,302-line
             source role of which only the four modes and their threshold are
             carried over
SCOPE        requests larger than one plan, or whose requirements are unstated.
             Not for small work, not for questions, not for work whose shape is
             already determined
DEPRECATED BY a measured false-trigger rate above the harness threshold, or a
             demonstrated case where it produced a plan for an unstateable
             question
```

Revised rather than promoted: the fog test is adapted, not validated, and the
source role's own mode-selection threshold is a heuristic with no measurement
behind it.

## Version and provenance

- **Version** — 1.0. This capability was adapted from an external role whose
  auto-decide mechanism, telemetry, and hook dependency were deliberately not
  carried over. Decision 0007 withdrew the upstream citation, so there is no
  recorded origin to compare against; the rejection reasoning for the material
  that was *not* adopted is in the commit history.
