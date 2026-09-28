# Patterns

Reference for the `references/patterns.md` file inside a skill: the recurring
shapes a skill takes, and how to recognise which one you are writing.

> **Provenance.** Authored from this skill's `SKILL.md` and its sibling
> references; no original copy was recovered. The pattern names and the anti-pattern
> table are a reconstruction of what the skill's prose describes — treat the
> catalogue as a good-faith expansion, not a recovered list.

## What belongs in a patterns file

Patterns are the *reusable* decisions — the ones that come up in most skills and
are easy to get wrong in a way that is invisible until something breaks. A
pattern is not a tutorial and not a specification. It is "when you see this shape,
here is what it usually needs."

If a section would be true of only one skill, it belongs in that skill. If it is
true of most skills, it belongs here.

## The patterns

### Progressive disclosure

Three levels, loaded at different times:

1. **Metadata** — name and description, always in context, roughly a hundred
   words. This is what decides whether the skill loads at all.
2. **Body** — `SKILL.md`, loaded when the skill triggers, under about five
   thousand words.
3. **Bundled resources** — `references/`, `scripts/`, `assets/`, loaded or
   executed on demand. Effectively unlimited, because a script runs without its
   contents entering the context.

The practical consequence: anything a reader needs *every time* belongs in the
body, and anything they need *occasionally* must not.

### Resource classification

| Directory | Holds | Loaded into context? |
| --- | --- | --- |
| `references/` | Documentation meant to be read while working | Yes, when needed |
| `scripts/` | Executable utilities | No — executed, not read |
| `assets/` | Files used in the output, not read | No — copied or modified |
| `examples/` | Complete worked examples | Yes, when needed |

The distinction that gets confused: a script is *executed* so it costs almost
nothing in context; a reference is *read* so it costs the whole file. A
300-line script that replaces 300 lines of prose the agent would otherwise have
to reason about is a win even though the script is bigger.

### Writing a description that triggers

The description is the matching surface. It has to carry:

- **When** — the conditions under which the skill is the right answer.
- **What it produces** — the concrete artifact.
- **Trigger phrases** — the words a user actually types, including informal ones.

Weak: "Helps with data processing."
Strong: "Analyzes CSV exports, produces summary tables and charts, and flags
outliers. Use for 'summarise this spreadsheet', 'find the weird rows in this
export', or 'chart these numbers'."

The test: could someone match a real request against this description without
reading the body? If not, the skill will load too rarely or too often.

### The `> prose` frontmatter form

Multi-line descriptions use YAML folding. The rule that matters: `>` folds newlines
into spaces, `|` keeps them. A description with a list in it needs `|`, or the
list becomes one long run-on line that reads badly in the matching surface.

### Procedure-first bodies

The body is instructions, not an essay. Imperative form, present tense, addressed
to whoever is executing — usually "the agent", occasionally "the user" for
interview-style skills. Not second person: "you are..." presumes a reader who is
a person being told what to do, when the reader is an agent following a procedure.

Good:

```markdown
Run `scripts/build_counts_matrix.py --from salmon --quant-dir quant/` first.
The result must be `counts.csv` before differential expression can start.
```

Weak:

```markdown
You might want to start by building a counts matrix. It's generally a good idea
to do this before moving on to the next step, since you'll need it later.
```

### Failures that are invisible until they are expensive

Patterns worth stating explicitly, because nothing warns you:

- **The right port, the wrong deck.** Two devices that enumerate identically and
  take different firmware. If a choice cannot be detected, make it explicit and
  refuse to guess.
- **A silent no-op.** A control signal that is not wired. The operation appears
  to succeed and nothing happened. Check the ground truth, not the exit code.
- **A passing test that proves nothing.** A code path that runs without touching
  the hardware it claims to test. Test the thing, not the call.
- **Rounding that changes the answer.** Estimated counts rounded to integers is
  a documented approximation; rounding a currency amount is a bug.
- **The alias that looks like an absence.** In a fractional design, a main effect
  that looks null may be a two-factor interaction that cancels it.
- **Retry that hides the first failure.** A retry loop that reports only the
  last attempt makes an intermittent bug look like a persistent one.

Each of these is a real, recurring shape. Naming them in a patterns file is
cheaper than rediscovering them per skill.

### Progress and interruption

Long operations need three things, and a skill that omits them looks hung:

1. **A stage banner** before each phase, flushed.
2. **A heartbeat** during a silent phase, flushed.
3. **A prompt** when human input is required, stating exactly what to do.

Under a harness that buffers subprocess output until exit, silence is
indistinguishable from a hang. The fix is streaming semantics, not redirection:
progress must go to stderr *and* be flushed, and the caller must tail the log.

### Test seams

A skill that shells out needs its external calls injectable, or its tests are
integration tests that need a network and a clock. Dependency injection — a
transport object, a stub backend, a stub embedder — is what lets the same test
run offline.

### Recovery is a design decision

Decide, per skill, what happens on partial failure:

- **Idempotent rerun** — the best answer. Structure the skill so running it twice
  is safe, and say so in the body.
- **Checkpoint and resume** — for long pipelines. Record where each stage ended.
- **Report and stop** — when a partial state is dangerous. Name the failing
  stage and the paths, and do not substitute another path.

A skill with no stated recovery behaviour gets one invented at the worst moment.

## Anti-patterns

| Do not | Because |
| --- | --- |
| Put everything in `SKILL.md` | It is always loaded; a 10,000-word body is a 10,000-word tax on every request |
| Reference a file you did not create | The reader finds nothing and stops trusting the rest |
| Duplicate content between body and reference | One of the two goes stale, and the stale one is read |
| Write a "just in case" reference file | An unused reference is still an orphan the validator flags |
| Put a script's logic in prose | The script is the reusable artefact; prose about it is not |
| Ship a template with placeholder values left in | A shipped `TODO` is a note to yourself, not an instruction to the reader — do not ship one |
