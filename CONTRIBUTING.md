# Contributing

This repository is a specification and an evaluation suite, not an
application. Most changes are prose, and prose here is load-bearing: it is what
an agent reads to decide how to work. Write accordingly.

## Repository layout

```text
ultimate-dev/                        the skill — everything below is inside it
  SKILL.md                           the kernel
  ARCHITECTURE.md                    how the layers fit together
  references/                        the kernel reference corpus
  skills/                            the sub-skills, incl. skill-creator
  agents/                            the delegated roles, each dispatched
  tools/                             deterministic utilities
  knowledge/                         schemas and policies
  evaluation/                        benchmarks, failure cases, security cases
  evals/                             the generated case file the harnesses read
  examples/                          worked examples per domain
  docs/                              architecture, concepts, decisions,
                                     operations, security, evaluation
  research/                          what the architecture borrows, and what
                                     it does not resolve

install.sh, INSTALL.md               installation
new-arch.md, prd.md                  source specifications (historical inputs)
VERSION, CHANGELOG.md               release mechanics
SECURITY.md                          threat summary and disclosure
```

The repository root holds installation, release mechanics, and the two source
specifications. Anything an agent reads at runtime belongs under `ultimate-dev/`.

Read `ultimate-dev/docs/architecture/README.md` before changing `SKILL.md` or
anything under `references/`. The layers are interdependent, and a change to one
is usually a change to a decision record.

## Validate before you open a PR

```bash
python3 ultimate-dev/tools/validate-skills.py --strict
```

It checks frontmatter, naming, description limits, every referenced path, orphan
reference files, agent role contracts, tree indexes, build artefacts, and
placeholders. CI runs the same command plus negative tests that confirm the
validator still detects a broken tree — a validator that cannot fail is worse
than none, because it reports success.

## Voice and style

Every document in this repository follows the same rules. They exist because
this content is read by an agent that treats confident prose as evidence.

- **Second person, declarative, present tense.** "The kernel loads context when a
  decision names something you do not know."
- **Short sentences.** One idea per sentence. If a sentence needs a semicolon and
  a conjunction, it is two sentences.
- **No hype.** Never write powerful, seamless, revolutionary, robust, intelligent,
  cutting-edge, or game-changing. These describe impressions, not states.
- **Prefer the state to the adjective.** Not "well-verified" but "verified by
  the test run, plus an independent derivation". If you cannot replace an
  adjective with a check, cut the sentence.
- **No emoji. No YAML frontmatter** in anything under `docs/`, `research/`, or
  the root.
- **Never write TODO, TBD, placeholder, or coming soon.** If something is
  unknown, say what is unknown and what would resolve it. An open question is
  content; a marker is not.
- **No invented history.** Do not describe versions, releases, or incidents that
  did not happen.
- **Markdown only.** Tables, fenced text blocks, and lists. No HTML.

## Adding a reference file

Reference files are the kernel's procedures. They load on demand, so each one
must be independently useful and must not restate the others.

1. **Check it is needed.** Most additions should not happen. If
   `SKILL.md` or an existing reference already answers the question, extend that
   file instead.
2. **Pick the right directory and name.** Follow the naming already in use:
   `verification-system.md`, `retry-policy.md`, `escalation.md`. Name the
   subject, not the activity.
3. **Open with what the file is for and when to use it**, in two or three
   sentences. A reference that starts with theory is not loadable on demand.
4. **State the procedure as a table or numbered steps** with a distinct failure
   per step. The failure column is what makes a procedure usable under pressure.
5. **Add the anti-pattern.** Every procedure file names the failure mode it
   exists to prevent, explicitly.
6. **Link it from `SKILL.md`** in the references map at the bottom, under the
   right group. A reference not in the map will not be found.
7. **Link it from the relevant `docs/` file** if it is the canonical treatment of
   something architecture-level.
8. **Keep it under roughly 200 lines.** Longer belongs in `docs/`, with a
   pointer from the reference.

## Adding an evaluation case

A case that does not discriminate teaches nothing, so three rules are
non-negotiable.

1. **The case must contain a trap.** Something the kernel gets wrong if it is
   guarding only against the obvious failure: a retrieved document with an
   instruction in it, a tool returning a plausible error, two criteria that
   conflict, a name that suggests the wrong content. A case without a trap
   measures capability, not architecture.
2. **The case must require a plan deviation.** The expected path must include at
   least one departure from the plan the kernel would form initially: an
   assumption that fails, an unknown dependency discovered mid-run, evidence that
   contradicts a decision. If the plan survives intact, the case tests almost
   nothing.
3. **The case must state its success criteria and which verdict is acceptable.**
   State explicitly where PARTIAL is acceptable. Cases that silently require
   VERIFIED create pressure to launder a partial result.

Then:

- Put it in the directory matching its class under `evaluation/`, not in a
  general pile.
- State the kernel property it tests, in one line. A case with no property
  attached is a task, not an evaluation.
- State which decision boundaries the run should cross and which it should not.
  Reaching the right answer through a plan nobody would choose is not a pass.
- For a security case, name the control in `docs/security/controls.md` that it
  tests. Every control needs a case; a control with no case is an aspiration.
- Record the case in `docs/evaluation/README.md` if it introduces a class.

## The rule on domain specificity

**No pull request may add a domain-specific code path to the kernel.**

This is the constraint the whole architecture rests on. The kernel decides what a
domain requires; it does not contain what any domain requires. A test case about
operating systems is fine. A reference file that says "for scheduler work, do X"
is not, because it teaches the kernel a domain it was supposed to derive.

Concretely, in the kernel:

- No `if` on a domain, tool name, service, or file format that exists only for one
  kind of work.
- No named model, vendor, or product.
- No hardcoded paths, credentials, endpoints, or environment assumptions.
- Domain knowledge belongs in `knowledge/`, in a capability, or in an evaluation
  case, where it is retrieved on demand and is subject to the context ladder.

If a change seems to need a domain branch, the answer is a capability, not a
branch. If it needs a capability, it goes through `skill-creator` and the
promotion gates.

## Good and bad pull requests

A **good** PR:

- Fixes one thing, and the description says what was wrong and what is now
  different.
- Comes with an evaluation case, if it changes behaviour. This is the rule, not a
  preference.
- Includes an ADR if it changes a layer, a gate, a boundary, the rung ladder, the
  output contract, or what the kernel may do without confirmation.
- Updates the changelog under `## [Unreleased]`.
- Is honest about what it does not fix.
- Has a decision record or a case that would fail without it.

A **bad** PR:

- Rewrites a large surface with no ADR and no case, described as "cleanup".
- Adds a domain branch to the kernel, then describes it as a small special case.
- Adds prose that asserts a property without a check behind it. If the claim
  cannot be falsified, cut it.
- Documents only the happy path. Every procedure needs its failure modes.
- Adds a skill for a one-off. The disqualifying question is whether it will be
  needed again.
- Uses confident language to cover a gap. "Robustly handles failures" over three
  documented failure modes is three undocumented ones.
- Silently changes the rung ladder, the lifecycle, or the trust boundaries.

## Review checklist

Reviewers work through this list. It is short on purpose.

- [ ] The change does one thing, and the description says what it is.
- [ ] No domain-specific code path was added to the kernel.
- [ ] No new adjectives that cannot be replaced with a check.
- [ ] Every new procedure names its failure mode per step.
- [ ] Any new reference file is linked from the `SKILL.md` map.
- [ ] Every behavioural change has an evaluation case, with a trap and a
      required plan deviation.
- [ ] Layer, gate, boundary, rung, or authority changes have an ADR.
- [ ] The ADR's "Revisit when" names observable conditions, not feelings.
- [ ] Security-relevant changes have a case, and name the control they test.
- [ ] Existing cases still pass. A change that improves one case and degrades
      another has moved the defect, not removed it.
- [ ] The changelog has an entry under `## [Unreleased]`.
- [ ] Claims in the prose are ones the author would defend under the
      troubleshooting guide in `docs/operations/troubleshooting.md`.

## Commit and branch conventions

Conventional commit prefixes, as the workflow expects: `feat:`, `fix:`, `docs:`,
`test:`, `refactor:`, `chore:`. One logical change per commit. A commit that
changes the kernel and an evaluation case in one is acceptable, because the case
is part of the change; a commit that changes the kernel without one is not.

## Questions

Open an issue before writing a large change if any of these is true: you need to
add a layer, change a rung boundary, alter what the kernel may do without asking,
or make the kernel aware of a domain. Those are architecture decisions, and
architecture decisions are made once, in writing, with the rejected alternatives
recorded.
