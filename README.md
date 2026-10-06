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
├── LICENSE                MIT
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
git clone https://github.com/usama-bin-sadiq/ultimate-dev-ai-skill.git
cd ultimate-dev-ai-skill
./install.sh                      # copy the skill into your skills directory
./install.sh --target DIR --yes   # explicit destination, non-interactive
```

Or read [`INSTALL.md`](INSTALL.md) for the manual procedure and how to verify
the install.

## What is in the skill

| Path | What it is |
|---|---|
| `SKILL.md` | the router and execution discipline |
| `skills/` | the sub-skills, including `skill-creator` |
| `agents/` | the specialist roles |
| `tools/` | the structure validator and corpus-maintenance scripts |
| `evals/` | routing queries and the with/without-skill task suite |
| `TREE.json` | the capability index, regenerated with `tools/index-tree.py` |

### Measuring it

The corpus is large enough that its quality cannot be eyeballed, so three
harnesses report on it. All are reproducible from a clean checkout.

| Question | Command |
|---|---|
| Is the structure still valid? | `python ultimate-dev/tools/validate-skills.py --strict` |
| Do the skills route to the right one? | `python ultimate-dev/tools/eval-routing.py` |
| Do the graders actually discriminate? | `python ultimate-dev/evals/selftest_tasks.py` |
| Does a skill help an agent do the job? | `python ultimate-dev/tools/run-task-eval.py --agent opencode` |
| Are the internal references intact? | `python ultimate-dev/tools/check-links.py` |

## The one rule it serves

> Do not hand the agent everything. Hand it the ability to determine what it
> needs, acquire it, use it, check it, recover from failing, and keep only what
> has proven useful.

## Status, stated plainly

## Licence

MIT. See [`LICENSE`](LICENSE).
