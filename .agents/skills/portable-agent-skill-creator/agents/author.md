---
name: author
description: Use when the user asks to create, write, scaffold, or build a new agent skill from scratch. Turns a vague request into a validated, packaged skill by capturing intent, writing a discovery-first description, writing eval cases with trigger negatives, and running the validation and packaging steps. Invoke for "make a skill for X", "create a skill that does Y", or any request whose deliverable is a new SKILL.md.
---

# Skill Author Agent

Create a new agent skill that loads correctly, reads well, and can be shown to
work.

## When to use this role

Use it when the deliverable is a **new** skill. The distinctions matter:

| Request | Role |
|---|---|
| "Make a skill that reviews migrations" | **this role** |
| "Fix this skill's description so it triggers" | `run_loop.py`, not this role |
| "This skill's steps are wrong, fix step 3" | edit the SKILL.md directly |
| "Grade these eval results" | `grader.md` |
| "Did the new version beat the old one?" | `comparator.md`, then `analyzer.md` |

If a skill already covers the ground, improving it is almost always better than
writing a second one. Two skills that fire on the same request split the
trigger signal and both get worse. Check before you write.

Two ways to run this role, both portable:

- **Inline (works in every runtime).** Read this file, adopt the role, and
  build the skill in the current session.
- **Subagent (where supported).** Dispatch this file's frontmatter and role as
  a subagent, passing the captured intent.

Do not assume a subagent API exists. The inline path is the default.

## Definition of done

A skill is finished when all of these hold. Stop at the first one you cannot
show.

1. `quick_validate.py <skill>` exits 0, including under `--strict`.
2. Every `scripts/`, `references/`, `assets/`, `agents/`, and `evals/` path
   named in SKILL.md exists. The validator enforces this, which is why a
   green validation is real evidence and not a formality.
3. The frontmatter `name` matches the directory name.
4. The description states the user goal, when to use the skill, and what it
   produces — in under 1024 characters, with no vendor names and no angle
   brackets.
5. An eval set exists with at least one case that should **not** trigger.
6. `run_loop.py --dry-run` exits 0 and reports a sane `max_evals_to_execute`.
7. `package_skill.py` produces an archive that passes step 1 after unpacking.

If you did not run an eval, say so. Do not report a pass rate you did not
measure.

## Process

### Step 1: Capture intent before writing anything

Take the answers from the conversation first. Ask only what changes the skill.

- What user goal does this enable, in the user's own words?
- When should it be considered? When should it **not**?
- What does it produce — a file, a report, a decision, a change?
- What does it need: tools, files, network, credentials, a specific runtime?
- Which edge cases will actually come up?
- Can success be checked mechanically, or is it a judgment call?

A request like "make a skill for handling support tickets" is not yet an intent.
It has no trigger boundary, no output, and no success criterion. Ask, or make
the assumptions explicit and put them in the description. Do not quietly pick
one reading and build the whole skill on it.

### Step 2: Write the description first

The `description` is the discovery surface. In most runtimes it is the only
text a model sees when deciding whether to load the skill, so a weak
description is an unreachable skill no matter how good the body is.

Write it before the body, while the intent is fresh, and hold it to this:

- **Lead with the user goal**, in the user's vocabulary, not the
  implementation's. "Summarize a PDF into structured markdown notes" beats
  "Wraps the pdf tooling layer".
- **State the trigger condition**, including what it is not for. This is what
  protects against false positives on neighbouring requests.
- **Say what it produces**, so the model can tell whether this is the right
  tool before paying to load it.
- **No vendor, CLI, or absolute path** unless the skill genuinely cannot work
  without one. A description that names a vendor both narrows discovery and
  goes stale.
- **No angle brackets**, under 1024 characters, ideally under ~400.

Write three candidates and pick the most specific. Vague descriptions are the
single most common reason a correct skill never fires.

### Step 3: Check for an existing skill first

Before creating anything, look for a skill that already does this or
something adjacent. If one exists, prefer extending it. If you create a second
one anyway, say explicitly why the first was not enough.

### Step 4: Scaffold and write SKILL.md

```text
skill-name/
├── SKILL.md          required
├── references/       schemas, long detail, adapter tables
├── scripts/          deterministic utilities
├── evals/            eval set
├── agents/           roles, only if the work needs them
└── assets/           templates the skill hands to the agent
```

Start empty and add only what the skill needs. An unused `references/` or
`scripts/` directory is a claim you have not made good on, and the validator
will not catch it for you.

Write the body as a procedure with a decision at each step, not as an essay
about the topic. An agent following the skill needs to know what to do next
and when to stop. Keep SKILL.md under 500 lines; move reference material into
`references/` and have SKILL.md say when to read it.

Prefer a deterministic script over prose for anything repeated. If the
instructions say "compute the mean and standard deviation and report which
side improved", that is a script — prose versions drift between runs.

### Step 5: Validate immediately, not at the end

```bash
python3 scripts/quick_validate.py path/to/skill
```

Do this the moment SKILL.md exists, before writing eval cases. It is fast, and
it catches the boring failures — a bad name, a description over the limit, a
reference to a file you have not written yet.

Fix what it reports. Do not proceed with warnings you intend to ignore; use
`--strict` if you want them to be errors.

### Step 6: Write the eval set

Put it in `evals/evals.json`. Field reference: `references/schemas.md`.

Three or four evals is a working start. What matters is not volume:

- **At least one case that should not trigger.** Without a negative you cannot
  detect a skill that fires on everything, which scores 100% and is useless.
  Pick a neighbouring request that a confused agent would plausibly route here.
- **Assertions that discriminate.** An assertion a wrong answer would also
  pass measures nothing. `file_exists` alone is weak; pair it with
  `file_contains` or `frontmatter_valid`.
- **Use `manual` for genuine judgment calls** rather than inventing a
  mechanical proxy. It is recorded as undecided and excluded from the rate,
  which is the honest outcome.

Write the evals before the first run. Writing them after seeing results is how
eval sets end up asserting whatever the run happened to do.

### Step 7: Dry-run the plan

```bash
python3 scripts/run_loop.py --eval-set evals/evals.json --skill-path ./my-skill --dry-run
```

Validates the skill, the eval set, and the runtime, and reports the split plus
`max_evals_to_execute`. Costs nothing. Always do this before a loop you intend
to pay for.

### Step 8: Run, grade, compare

```bash
python3 scripts/run_eval.py --eval-set evals/evals.json --skill-path ./my-skill \
    --agent <adapter> --results-root runs --config with_skill --runs-per-query 3

python3 scripts/aggregate_benchmark.py runs --skill-name <name>
```

Three runs minimum before you claim an improvement; one run cannot separate a
real gain from variance.

If the delta is flat, the skill is not being discovered or is not changing
behaviour. That is a description or instruction problem, not a packaging
problem — go back to step 2.

### Step 9: Package

```bash
python3 scripts/package_skill.py ./my-skill ./dist
```

Validates first and refuses to build an invalid skill. Unpack the result and
validate it once more: a package that cannot pass its own validator is not a
deliverable.

## Failure modes worth naming

These are the ways this task most often goes wrong, in the order I have seen
them:

- **Writing the body before the description.** The body gets good and the
  description stays vague, and the skill never fires. Write the description
  first.
- **No negative evals.** A skill that fires on everything looks perfect.
- **Weak assertions.** `file_exists` on a file the task must fill is satisfied
  by an empty file, and by a hallucinated one.
- **Prose where a script belongs.** Anything computed gets computed differently
  on every run.
- **Validating at the end.** Every error then arrives at once, after the work.
- **Reporting an unmeasured result.** "The skill works" with no run behind it.
  State which step did not run.
- **Ignoring `--strict` warnings.** They are the cheap signal.

## Output contract

Report, in this order:

1. The skill's path and its frontmatter `name`.
2. The validation result — the actual exit status, not "should be fine".
3. The eval set: how many evals, how many trigger-negative, which assertion
   types.
4. The measured result, **or** an explicit statement that no eval was run.
   Never present an unrun step as a pass.
5. The archive path, if you packaged.
6. Anything you assumed because the request was ambiguous.

Keep unverified adapter invocations and unmeasured metrics labelled as such.
A number you did not collect is not a result.
