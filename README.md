# ultimate-dev

A universal adaptive problem-solving kernel, packaged as an installable agent
skill.

The skill lives in [`ultimate-dev/`](ultimate-dev/). Everything at this level is
installation and repository mechanics.

```text
.
├── ultimate-dev/          the skill — this is what you install
├── install.sh             installer
├── INSTALL.md             installation and verification
├── VERSION                canonical version
├── CHANGELOG.md           version history
├── CONTRIBUTING.md        how to contribute
├── SECURITY.md            threat model summary and disclosure
├── new-arch.md            source specification (historical input)
├── prd.md                 source requirements (historical input)
├── LICENSE                MIT
└── .github/               CI
```

`new-arch.md` and `prd.md` are the specifications this architecture was built
from. They are historical inputs, not maintained documents; where they disagree
with `ultimate-dev/docs/`, the latter reflects what was actually built.

## What the skill does

It takes an objective, works out what that objective actually requires, acquires
what is missing, does the work, checks the work, admits what it could not
establish, and retains only what has proven useful.

It is not a coding skill despite the name. It is domain-independent by
construction: there is no medical path, no finance path, no operating-system
path. It contains the machinery for working out what a domain needs.

```text
"Build an operating system."

 → not a workflow lookup
 → not "I do not have a skill for that"
 → triage → decompose → acquire capabilities → plan → execute → observe
   → verify → integrate → deliver a staged, scoped, honest first increment
```

## Install

```bash
git clone https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill.git
cd ultimate-dev-ai-skill
./install.sh                      # install to run it: prune to the runtime tree
./install.sh --bundle             # build a distributable copy, pruned and zipped
```

The file count and the size are reported by the installer, not fixed here. Run
`./install.sh --check-bundle` to print the current figures without writing
anything.

Or read [`INSTALL.md`](INSTALL.md) for the manual procedure, the two install
paths, and how to verify the install.

## What is in the skill

| Path | What it is |
|---|---|
| `SKILL.md` | the kernel: the effort gate, the decision fabric, verification, recovery, delivery |
| `references/` | the corpus, loaded on demand — `references/README.md` is the index |
| `skills/` | the sub-skills, including `skill-creator`, which creates and retires the others |
| `agents/` | the delegated roles, each with a row in `references/delegation.md` |
| `tools/` | the structure validator, the bundler, the doc auditor, and the evaluation harnesses |
| `knowledge/` | data contracts and the policies governing them |
| `evaluation/` | benchmark, domain, failure, security, and regression cases |
| `evals/` | the generated case file those harnesses read |
| `examples/` | worked kernel runs, organised by domain |
| `docs/` | architecture, concepts, decision records, operations, security |
| `research/` | what the architecture borrows, and what it does not resolve |
| `ARCHITECTURE.md` | how the layers fit, and what breaks if one is absent |

## The one rule it serves

> Do not hand the agent everything. Hand it the ability to determine what it
> needs, acquire it, use it, check it, recover from failing, and keep only what
> has proven useful.

## Status, stated plainly

The architecture is written and the evaluation suite is defined. **The
with-versus-without measurements have not been run.** Treat this as a hypothesis
with a documented test plan, not a validated result. `ultimate-dev/evaluation/`
specifies how to measure it; the numbers do not exist yet.

There is also no independent security audit. `ultimate-dev/evaluation/security-cases/`
contains the cases such an audit would run — they have been written, not
externally executed.

## Licence

MIT. See [`LICENSE`](LICENSE).
