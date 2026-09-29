# Documentation

Engineering documentation for the kernel: how it is built, what its terms mean,
which decisions were taken and why, how to operate it, and how it is secured and
evaluated.

Read in this order if you are new.

## Contents

| Section | What it answers |
|---|---|
| [architecture/](architecture/) | How the system is put together, and what breaks if a layer is absent |
| [concepts/](concepts/) | What the vocabulary means, and what each term is not |
| [decisions/](decisions/) | Which choices were made, what was rejected, and when to revisit |
| [operations/](operations/) | How to run it, what to do when it misbehaves, how to bound cost |
| [security/](security/) | The threat model, the controls, and what to do when a control fails |
| [evaluation/](evaluation/) | Which kernel property each test class exercises |
| [tool-integration/](tool-integration/) | Per-agent setup guides (Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others) and how to author a skill |
| [PERSONAS.md](PERSONAS.md) | The persona format specification. Describes a tree this repository does not ship |

## Start here

- **[architecture/README.md](architecture/README.md)** — the narrative
  architecture. What each of the fourteen layers is *for*, in the order a run
  passes through them.
- **[architecture/kernel.md](architecture/kernel.md)** — the execution model:
  the lifecycle, the JEv fabric, and the twenty decision boundaries.
- **[architecture/scalability.md](architecture/scalability.md)** — how the same
  kernel operates from L1 to L7. This is the load-bearing claim of the whole
  repository, so it gets the most careful treatment.
- **[concepts/README.md](concepts/README.md)** — the glossary. Read it before
  reading anything else; most disagreements about this architecture turn out to
  be disagreements about a term.

## For a specific job

**I want to change the kernel's behaviour.**
Read `architecture/kernel.md`, then `decisions/README.md`. A behaviour change
usually invalidates a decision record, and the record has to be superseded rather
than quietly edited.

**I want to add a reference file.**
`CONTRIBUTING.md` has the rules. The short version: it must be reachable from
`SKILL.md`, and `tools/validate-skills.py` will fail the build if it is not.

**Something went wrong in a run.**
[operations/troubleshooting.md](operations/troubleshooting.md) lists the
symptoms of a misbehaving kernel — over-orchestration, fabricated tool results,
unnecessary skill creation — with cause and fix for each.

**I want to add or change a skill.**
`skills/skill-creator/references/` owns that procedure, and it is stricter than
anything in this directory.

**I am worried about safety.**
[security/threat-model.md](security/threat-model.md) for the analysis,
[security/controls.md](security/controls.md) for what the kernel actually does
about it, and the root `SECURITY.md` for the posture stated honestly, including
what has not been tested.

## Conventions

These documents are read by an agent that treats confident prose as evidence, so:

- No unfilled placeholders. A gap is stated as a gap, in the section that has it.
- No emoji. They carry no information here and they date quickly.
- Decisions live in `decisions/`, not in prose. If you find yourself explaining
  *why* in a README, the explanation belongs in an ADR.
- Claims about behaviour point at a file or a trace. "The kernel does X" is
  weaker than "`references/delegation.md` says X, and
  `examples/recovery/` shows it".

`new-arch.md` and `prd.md` at the repository root are the **source
specifications**. They are historical inputs to this architecture rather than
maintained documents, and they are exempt from the conventions above. Where they
disagree with `docs/`, `docs/` reflects what was actually built.
