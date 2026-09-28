# Advanced Use

Reference for the `references/advanced.md` file inside a skill: the cases that go
beyond the basic create-and-validate loop, and the judgement calls that separate a
skill that works from one that works on the first try.

> **Provenance.** Authored from this skill's `SKILL.md` and its sibling
> references; no original copy was recovered. The situations below are a
> reconstruction of what the skill's prose describes, written to be useful rather
> than to match a recovered list.

## When a skill needs more than one file

Start with a single `SKILL.md`. Split only when one of these is true:

- The body exceeds about five thousand words.
- Detail is needed for some requests and not others, and carrying it always costs
  context for the requests that do not need it.
- Two audiences use the skill for genuinely different things, and the shared
  instructions are thin enough that the split buys more than it costs.

Those are the only three reasons. "The file is getting long" is a reason to split
prose from reference, not to split a skill in two.

## Multi-context repositories

A repo with several bounded contexts gets one `CONTEXT.md` per context and one
ADR directory per context, plus a root `CONTEXT-MAP.md` pointing at them:

```
/
├── CONTEXT-MAP.md
├── docs/adr/                    ← system-wide decisions
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/             ← context-specific decisions
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

The test for whether two things are one context: do they share vocabulary? Two
modules that both say "account" and mean different things are two contexts, and
the shared word is a defect in the glossary, not a fact about the system.

## ADRs: three tests, all three required

Write an ADR only when all three hold:

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will ask "why did they do it
   this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you
   picked one for reasons you can state.

Miss any one and skip the ADR. A directory of ADRs that does not reflect these
tests is a changelog with extra steps, and it is worse than nothing: an ADR
marked `accepted` after the decision was reversed will be cited as the reason for
a decision that no longer holds.

An ADR needs, at minimum, context, decision, and consequences. Consequences is
the one people skip and the one that matters: it is what tells the next person
what they have inherited.

## Interview-style skills

Some skills are a conversation, not a pipeline. The rules that make one work:

- **One question at a time.** A list of ten questions gets one answered.
- **Prefer exploring to asking.** If a question can be answered by reading the
  codebase or the docs, read them and do not spend the user's attention on it.
- **Always bring a recommendation.** An open question with no default stalls;
  an open question with a default that can be overridden moves.
- **Capture terms inline.** When a term is resolved, write it down immediately.
  Batching loses them.
- **Separate the record from the judgement.** A glossary says what a word means
  here. An ADR says why a decision was made. Mixing them makes both worse.

## Skills that maintain their own state

A skill that writes files needs three things stated up front, because a reader who
does not know them will either duplicate the work or destroy it:

- **Where the state lives**, and the exact path.
- **What is safe to delete** and what is not.
- **How to tell current from stale.** A version stamp, a checksum, a manifest.

For generated files, add the regeneration command and a check mode that exits
non-zero when the committed copy no longer matches. A generated file with no
freshness check is a file nobody can trust, and a digest that describes agents
which no longer exist is worse than no digest.

## Dependency and licensing constraints

A skill that vendors a dependency should record why:

- A pinned, permissive dependency (BSD, MIT, Apache) is often worth vendoring to
  make a fresh clone work with no install step.
- A copyleft dependency (GPL, AGPL) usually should not be vendored into a
  permissively licensed tree, even though it works. Keep the tree clean and let
  pip manage it, with a preflight that offers to install it.

Record the reasoning in `SKILL.md`. A future maintainer who cannot tell whether
a directory is missing by accident or by decision will restore it and break the
licence position.

## Runtime-dependent skills

Some capabilities are optional at runtime: a browser, an image service, a model
provider, network access. A skill that needs one should:

1. **Detect it**, explicitly, at the start.
2. **Say what is missing and what to install**, in the platform's own terms.
3. **Degrade to a documented alternative.** Deliver the HTML source and mark the
   PNG export as pending, rather than failing the whole task.
4. **Never assume the capability was present** because the skill ran yesterday.

The degradation path is the part people skip, and it is the difference between a
skill that is occasionally limited and one that is unusable on some machines.

## Security and safety boundaries

A skill that touches files, devices, or networks should state its boundary in the
body, not in a reference nobody loads:

- **What it reads and writes**, exactly.
- **What it refuses to do**, and why.
- **What it needs a human to confirm**, and at which point.
- **Where outputs must not be placed** — a live system, a production database, a
  user's home without consent.

The relevant property is that the boundary is *legible from the body alone*. A
safety rule in a reference that is only loaded sometimes is a safety rule that
sometimes does not apply.

## Publishing and versioning

- A skill version follows the package version, not the skill's own churn.
- A change to a skill's trigger surface is a **breaking** change: every user
  whose requests used to match it will stop matching.
- A change to a bundled reference file is a patch. A change to a bundled script's
  interface is a minor.
- Ship the reference and asset updates with the version they belong to. A skill
  that references a file which only exists in a later version is broken for
  everyone between the two.

## Testing a skill before shipping

1. **Structure** — directory layout, frontmatter present, name and description
   non-empty.
2. **Referential integrity** — every path in backticks resolves on disk. This is
   the check that catches the most common defect and it is mechanical.
3. **Triggers** — read the description as if you were the matcher. Would the
   requests you expect match? Would the ones you do not want to match also match?
   Over-triggering is as bad as under-triggering.
4. **Progressive disclosure** — body word count, and whether the moved detail is
   actually in a reference file.
5. **Placeholders** — grep the whole skill for `TODO`, `FIXME`, `TBD`, and
   literal `placeholder`. A shipped template with a placeholder in it is a
   defect, and it is invisible in review because the reader fills it in mentally.
6. **Examples** — run them. A broken example is worse than no example, because it
   is copied.
7. **Scripts compile** — `python -m py_compile` for Python, `bash -n` for shell,
   `node --check` for JavaScript, `tsc --noEmit` for TypeScript. A script that
   does not compile is worse than a missing one: it fails at the moment it is
   needed.
