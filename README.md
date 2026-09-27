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
└── .github/               CI
```

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
git clone https://github.com/<you>/ultimate-dev.git
cd ultimate-dev
./install.sh                      # install to run it: 75 files, 395 KB
./install.sh --bundle             # build a distributable copy: 84% smaller
```

Or read [`INSTALL.md`](INSTALL.md) for the manual procedure, the two install
paths, and how to verify the install.

## What is in the skill

| | |
|---|---|
| `SKILL.md` | the kernel: the effort gate, the decision fabric, verification, recovery, delivery |
| `references/` | 47 references, loaded on demand |
| `skills/skill-creator/` | the sub-skill that creates, validates, and retires other skills |
| `agents/` | six delegated roles: verifier, investigator, critic, grader, comparator, author |
| `tools/` | the structure validator |
| `knowledge/` | data contracts and the policies governing them |
| `evaluation/` | 101 benchmark, domain, failure, and security cases |
| `examples/` | 27 worked kernel runs across 13 domains |
| `docs/` | architecture, concepts, decision records, operations, security |
| `research/` | what the architecture borrows, and what it does not resolve |
| `new-arch.md`, `prd.md` | the source specifications |

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
