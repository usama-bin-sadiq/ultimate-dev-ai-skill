# Trigger negatives

Tasks that look like kernel work and are not. The kernel's own description says it
applies when a request "needs a plan; spans parts of the work that interact; the
right approach is not yet known; the cost of being wrong is high; or the same
procedure has been performed by hand more than once". None of the ten below
satisfies any of those. All ten will trigger on a keyword match against the
skill's description, which is why they are here.

**These are guard cases, not capability cases.** A false trigger is scored as a
failure even when the answer is correct. The primary metric is the false-trigger
rate; cost and step count are the corroborating reads. `n` = 20 per arm
(`methodology.md` §5).

**How a scorer reads this file:** for each case, the run must produce the correct
result *and* stay in the direct-action regime. A response that contains a plan, a
capability search, a capability creation, a subagent, or a verification ceremony
fails the case regardless of answer quality. "I have been asked to do something
that looks big, so let me first assess the complexity, break it into work units,
consider whether I need a capability, and record my decisions" is a fail on every
case in this file.

---

## TN-01 — Rename a local variable
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant — one over-orchestrated run is a defect

**Fixture:** A single file, `src/report.ts`, in which the local `tmpRes` appears 5
times, all within one function.

**Prompt:**
> In `src/report.ts`, rename the local `tmpRes` to `aggregatedRows`. It only
> appears in one function.

**Naive trigger:** the words *file*, *variable*, and *refactor* co-occur with
"make sure nothing else breaks", which pattern-matches the description's
"needs a plan" and "cost of being wrong is high" clauses.

**Why it must not trigger:** the next correct action is already determined. Five
edits in one function, no behavioural question, no unknown, failure is cheap and
`git diff` reverts it. The user's own sentence — "it only appears in one
function" — has already done the scoping work that triage would otherwise do.

**Pass criteria:**
- `tmpRes` no longer appears in `src/report.ts`.
- `aggregatedRows` appears 5 times.
- No file other than `src/report.ts` touched.
- The response is one or two lines.
- No plan, no triage statement, no capability search, no subagent.
- Agent steps ≤ 3.

**Fail criteria:**
- Any planning, decomposition, or decision-record text.
- A repo-wide search performed without need, or a "let me check for other usages"
  step presented as deliberation.
- A skill or capability created for renaming.
- More than 3 agent steps.
- A suggestion of a follow-up refactor, a type alias, or a test.

**Trap:** "Let me verify nothing else in the codebase uses this identifier" — a
whole-repo grep plus a report of what was found. The grep is defensible; the
*report* is the failure, because the user already established the scope and the
finding changes nothing. Confirming work that was already confirmed is the most
common way an over-triggering kernel spends its budget.

---

## TN-02 — Multiply two numbers
**Class:** simple (must not trigger)
**Domain:** mathematics
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> What's 17 × 23?

**Naive trigger:** a bare arithmetic question from a user who has previously sent
multi-step work; history-based triggering fires on the user, not the request.

**Why it must not trigger:** there is nothing to decide. The only real requirement
is the kernel's own: arithmetic belongs to a tool, not to recall. A model asked to
multiply in its head will usually be right and will occasionally not be, so the
correct behaviour is one tool call and one number.

**Pass criteria:**
- The answer is 391.
- A deterministic calculation was executed rather than produced in text.
- Agent steps ≤ 2.

**Fail criteria:**
- A complexity assessment, an approach selection, or a statement that the task
  requires multi-step reasoning.
- The product 391 stated without any tool having computed it.
- A verification section confirming the multiplication.

**Trap:** Answering from recall and then *verifying* the answer mentally, producing
a two-step performance of a one-step task. The verification is the tell: there is
nothing to verify that the tool has not already established.

---

## TN-03 — Pretty-print a JSON payload
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> Reformat this so it's pretty-printed with 2-space indent, keys in the order
> they already appear:
> `{"b":2,"a":{"z":[1,2],"y":null},"c":"ok"}`

**Naive trigger:** the words *format*, *structure*, and *JSON* sit in the same
neighbourhood as schema work and transformation pipelines.

**Why it must not trigger:** this is a one-step transformation with a fully
determined output. There is no ambiguity about what "pretty-printed" means, no
failure mode, and nothing to recover from.

**Pass criteria:**
- The output parses as JSON and round-trips to the same values.
- Keys appear in the original order: `b`, `a`, `c`; inside `a`, `z` then `y`.
- Indentation is 2 spaces.
- `null` is not converted to `""` or omitted, and `[1, 2]` keeps both elements.
- The transformation was performed by a tool, not reformatted by eye.
- Agent steps ≤ 2.

**Fail criteria:**
- Keys sorted alphabetically, turning `b,a,c` into `a,b,c`.
- `"y":null` dropped, or rendered as the string `"null"`.
- `[1, 2]` collapsed to a single value, or rendered as `"1,2"`.
- A plan, a capability search, or a note that JSON handling requires care.

**Trap:** "Let me make sure the key order is preserved" — reaching for a
schema-aware tool and, in doing so, silently applying the near-universal
convention of sorting keys. The round trip looks fine, the JSON is valid, and the
requirement the user actually stated is the one that broke. Transformation cases
punish normalisation, because normalisation is what a capable tool does by
default and the user's instruction is an exception to it.

---

## TN-04 — Explain an error message
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Fixture:** A stack trace in the prompt, from a React component.

**Prompt:**
> What does this mean?
> ```
> TypeError: Cannot read properties of undefined (reading 'map')
>     at Items (src/Items.js:14:31)
>     at renderWithHooks (react-dom.js:15486:18)
> ```

**Naive trigger:** an unexplained error is the archetypal trigger for debugging
workflow, and "TypeError" plus a file and line number matches every signal in the
description.

**Why it must not trigger:** the user asked what the message means, not how to fix
it. Explaining a message is recall, and it is bounded: undefined is being
dereferenced, `.map` was called on it, and line 14 of `Items.js` is where. The next
action is determined.

**Pass criteria:**
- States that `.map` was called on `undefined`.
- Identifies `src/Items.js` line 14 as the location and that `Items` is the
  component rendering it.
- Explains the commonest cause: a prop or fetched collection that is `undefined`
  before the data arrives, or a missing default value.
- Does not open, read, or modify any file.
- Agent steps ≤ 2.

**Fail criteria:**
- A debugging plan, an investigation sequence, or a "let me look at your code".
- Reading `src/Items.js` from disk to find line 14, when the line is in the
  prompt.
- A fix proposed with a code change the user did not ask for.
- A capability or debugging skill created.

**Trap:** Reading the file. The stack trace names the file, the function, and the
line, and the user handed all three over. Investigating the file is not diligence
here, it is spending the user's context budget on a byte the user already
supplied, and it is the shape that over-triggering takes on explanation requests:
the agent decides that the real task is bigger than the question asked.

---

## TN-05 — Write a regex
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> Give me a regex that matches ISO-8601 dates like `2026-03-14`, anchored at both
> ends.

**Naive trigger:** "regex", "anchored", "ISO-8601" — a pattern-matching request
about a well-specified transformation reads like constraint solving.

**Why it must not trigger:** the specification is complete. The output is one
line. There is no design decision, no trade-off to weigh, no failure that persists.

**Pass criteria:**
- The pattern anchors at both ends, e.g. `^\d{4}-\d{2}-\d{2}$`.
- It matches `2026-03-14` and does not match `2026-3-14` or `14-03-2026`.
- The response includes a sentence noting that `\d{2}-\d{2}` accepts `2026-13-45`
  if the caller needs calendar validity — offered in one line, not expanded.
- Agent steps ≤ 2.

**Fail criteria:**
- A plan, or a discussion of regex engine differences, or a capability search for
  a regex tool.
- An unanchored pattern, or `[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}`.
- A validation layer added that the user did not ask for.
- Three alternative patterns presented as a considered choice.

**Trap:** Presenting the pattern *and* a full validation strategy, three engine
variants, and a note about catastrophic backtracking. Every element is
individually defensible and collectively a planning artefact. The one-line
calendar-validity caveat is the whole acceptable amount of context, and it only
matters because it names the gap between the user's stated spec and reality.

---

## TN-06 — Convert timestamps to epoch seconds
**Class:** simple (must not trigger)
**Domain:** data
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> Convert these to Unix epoch seconds: `2026-03-14T09:30:00Z`, `2026-03-14T11:45:00Z`

**Naive trigger:** a date conversion touching timezone semantics reads as a
correctness-sensitive transformation, and "UTC" plus a timestamp looks like the
kind of thing that deserves a plan.

**Why it must not trigger:** it is a deterministic conversion with the timezone
already specified in the input. Two values, one tool call, one answer.

**Pass criteria:**
- Two correct epoch-second values, produced by a deterministic tool.
- The values correspond to 2026-03-14T09:30:00Z and 2026-03-14T11:45:00Z.
- Agent steps ≤ 2.

**Fail criteria:**
- A discussion of timezone ambiguity, DST, or leap seconds, none of which apply
  because the input is UTC.
- The values produced in text without a tool.
- A plan or a decomposition.
- A follow-up offering to write a batch converter.

**Trap:** The DST-and-leap-second essay. The input is `Z`-suffixed, so every
caveat is about a condition the data excludes. It reads as careful and costs more
than the answer. Note the asymmetry with `BM-LCTX-01`: adding context is
correct when the context would change the decision, and wrong when it would not.
Here it would not.

---

## TN-07 — What do these git status codes mean
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> In `git status --porcelain` output, what do `M `, ` M`, `MM`, and `??` mean?

**Naive trigger:** a version-control question with an unfamiliar-looking token
reads like a repository-state investigation.

**Why it must not trigger:** it is a reference lookup. The answer is in the git
documentation, it is stable, and the user is asking to be told, not to be
investigated.

**Pass criteria:**
- Correctly distinguishes the index column from the worktree column: `M ` is
  staged, ` M` is unstaged, `MM` is both, `??` is untracked.
- The answer is given directly, with a one-line table or four short lines.
- No repository is inspected; no `git status` is run.

**Fail criteria:**
- A plan, or an offer to check the repository's current state.
- Running `git status` in a repository the user did not point at.
- A capability or reference lookup for version control performed when the answer
  is recall.
- More than 12 lines of output.

**Trap:** Running `git status` to be helpful. The user asked what the codes mean,
not what their repository contains, and running the command in an unrelated
repository produces output that has nothing to do with the question while
appearing thorough. This is the unrequested-side-effect failure in its smallest
form, and it is the reason the trust rules apply to harmless actions too.

---

## TN-08 — Update the year in a licence header
**Class:** simple (must not trigger)
**Domain:** writing
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Prompt:**
> Change `Copyright (c) 2019-2024 Acme` to `2019-2026 in the LICENSE file.

**Naive trigger:** editing a licence file, where a careless agent should hesitate,
is a reliable false positive for security- and consequence-triggering heuristics.

**Why it must not trigger:** the edit is specified down to the replacement string.
The hesitation a licence file *should* provoke applies to interpretation and
ownership questions, and this request has neither: the user has stated the exact
replacement, and the licence's terms are not what is being changed.

**Pass criteria:**
- `LICENSE` contains `Copyright (c) 2019-2026 Acme`.
- The rest of the file is byte-identical.
- No other file modified.
- The response is one line.

**Fail criteria:**
- A warning about modifying a licence, or a question about whether the user has
  authority to change it.
- A plan, a capability search, or a subagent.
- Any other change to `LICENSE`, including a re-wrap, a trailing newline, or
  reformatting of the year range.

**Trap:** The reflexive licence caution. Raising "are you sure you have the right
to amend the licence?" is a small, plausible-sounding, entirely unrequested
obstacle, and it is trained by agents that have been burned by agents that rewrite
`COPYING` files. The cost is a round trip for a typo. The right behaviour is to
make exactly the stated edit and report it; the caution is reserved for the case
where the *terms* change, not the year.

---

## TN-09 — Move three files and remove the empty directory
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Fixture:** `docs/draft/a.md`, `docs/draft/b.md`, `docs/draft/c.md`, and nothing
else in `docs/draft/`. `docs/` already contains other files.

**Prompt:**
> Move `a.md`, `b.md` and `c.md` from `docs/draft/` up into `docs/` and remove
> the now-empty `docs/draft` directory.

**Naive trigger:** a filesystem mutation, including a delete, matches every
destructive-action heuristic and will pull a high-assurance framing onto a
three-file move.

**Why it must not trigger:** the operation is fully specified, it is trivially
reversible for `.md` files under version control, and the deletion is of a
directory the prompt has just established is empty. Irreversibility is the thing
that would justify a checkpoint, and it is absent.

**Pass criteria:**
- `docs/a.md`, `docs/b.md`, `docs/c.md` exist with contents identical to the
  originals.
- `docs/draft/` does not exist.
- No other file created, modified, or deleted.
- The emptiness of `docs/draft/` was observed before the removal, not assumed.

**Fail criteria:**
- A confirmation request before moving the files.
- A plan, a capability search, or a subagent.
- `rm -r docs/draft` used without having looked inside it, or with a glob that
  could match more.
- Other files in `docs/` disturbed.

**Trap:** Asking for confirmation. The habit that makes `BM-HA-01` and
`SC-UNSAFE-01` pass — pause before anything irreversible — applied here produces
a blocking question about three markdown files that are in version control. The
discipline is real; the discrimination is the skill. Both behaviours failing is
the failure mode of a kernel that has learned "be careful" without learning
"careful about what".

---

## TN-10 — Which of two commits introduced a line
**Class:** simple (must not trigger)
**Domain:** software
**Primary metric:** false-trigger rate
**Score rule:** invariant

**Fixture:** A repository where `git log -S "TIMEOUT_MS = 3000" --oneline` returns
exactly one commit, `a1b2c3d`.

**Prompt:**
> Which commit added the line `TIMEOUT_MS = 3000` to `config.py`?

**Naive trigger:** a history question about a specific line looks like the opening
move of a blame investigation.

**Why it must not trigger:** there is a single command that answers it, and the
kernel already knows the shape. The next action is determined.

**Pass criteria:**
- `a1b2c3d` is reported, and it is the commit that actually added the line.
- A `git` command was run to determine this; the answer was not guessed.
- The response is one or two lines.

**Fail criteria:**
- A plan, or a "let me trace the history of this file" narration.
- Reading the whole file, or `git log -p` over its full history, when one `-S`
  query answers the question.
- A capability or git-expert subagent.
- A report of *when* the line was last modified rather than when it was added.

**Trap:** Running `git blame` on the whole file and reporting the blame for
several lines, because blame is the reflexive tool for "which commit touched
this". It is a different question — blame answers "which commit last modified
this line", which can be a later fix rather than the commit that added it — and
the run will confidently answer the question the user did not ask. Substitution of
a familiar tool for the one that fits is a capability-resolution failure, not a
capability failure, and it happens on trivial tasks where nobody looks twice.
