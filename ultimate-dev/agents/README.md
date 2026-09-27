# Agents

Roles the kernel may delegate work to. Each is an execution resource, not a
capability, and each is optional at every rung.

## The test for delegating

**Does the work need a different kind of attention than the run is currently
giving it?**

That is almost always because the run produced the thing being checked, and a
separate derivation is the point. It is occasionally because the work needs a
kind of attention the run cannot currently supply — an unfamiliar domain, or an
adversarial reading.

It is never "the work is large". Size is a reason to decompose, not to
delegate; a work unit handed to a fresh context loses the reasoning that produced
it and has to reconstruct it.

## Contents

| Role | Use when | Produces |
|---|---|---|
| [verifier](verifier.md) | A result must survive being derived a different way | `VERIFIED` / `PARTIAL` / `FAILED` with independent evidence |
| [investigator](investigator.md) | The domain is unfamiliar or the cause of a symptom is unknown | Ranked candidates plus the cheapest discriminating observation |
| [critic](critic.md) | Work is expensive to reverse, or a plan is defending itself against evidence | Fatal / serious / cosmetic defects, ranked |
| [grader](grader.md) | An output needs scoring against criteria written in advance | Per-criterion verdicts, undecidable ones as `null` |
| [comparator](comparator.md) | A pass rate cannot explain why one version is better | Blind A/B verdict and the differences that decide it |
| [author](author.md) | `skill-creator` has decided a new capability is warranted | A **candidate** skill, never an installed one |

## The rules that apply to all of them

- **The delegate gets the context it needs and nothing more.** Over-briefing costs
  the delegate's attention on material that does not bear on the task.
- **A delegate that finds its scope was wrong says so** rather than widening it.
  Scope creep by delegation is how a five-minute check becomes a project.
- **A delegate does not fix.** It reports. A role that repairs what it found
  destroys its own independence, and the caller cannot tell its changes from its
  preferences.
- **Undecidable is `null`, not `false`.** A guessed verdict becomes a number, and
  the number is then indistinguishable from a measurement.

## The characteristic misuse

Delegating verification to the context that produced the work. It costs a round
trip, reproduces the author's blind spot exactly, and produces a check that
cannot fail — which is worse than no check, because the check is reported.

`verifier.md` is therefore written around a single rule: re-derive, do not
re-read. And it reports `INDEPENDENCE` explicitly, including when the answer is
`none`, so the caller can discount a verdict that was not actually independent.

## Why these are not skills

Giving a role a user-facing description would make it compete with `SKILL.md`
for the same requests, and a user asking for verification is usually asking the
kernel to verify, not to spin up a verifier. Roles are selected at a decision
boundary; skills are selected by description. `../skills/README.md` covers the
distinction in full.

## One naming hazard

`agents/` means two incompatible things in this ecosystem.

Inside a skill, it means plain Markdown role prompts with no required frontmatter
— which is how the major public skill collections use it. At a plugin root, it
means registered subagents with `name`, `description`, `model`, and `tools`
frontmatter.

This directory uses the in-skill meaning, which is the correct precedent. But if
these files are ever lifted to a plugin root, all seven silently change meaning
and gain fields that were never written. The validator here requires frontmatter
on every role, which is stricter than the in-skill convention requires and is
deliberate: it makes a role self-describing, and it means a lift to a plugin root
would mostly work rather than silently not.

Verified against the public collections in `../research/skill-ecosystem/`.
