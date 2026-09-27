# 0005. Measure before importing; bound the import to a named list

Status: Accepted
Date: 2026-09-27
Deciders: architecture maintainers
Supersedes: nothing. Constrains the intake described in
`research/skill-ecosystem/PLAN.md`.

## Context

Six surveys were run over roughly forty public repositories and directories. The
owner directed that all good agents and skills be cloned, deduplicated, and
adapted to this architecture, with tool-oriented ones made tool-neutral.

The survey results constrain what that instruction can mean in practice, and the
constraints were not known when it was given.

**The population has no stable referent.** Across a 191,846-entry public catalog,
171,470 distinct skill names — 95.6% — appear in exactly one repository. There
is no convergence to import in 96% of the catalog. One machine-generated
903-skill language-by-framework matrix outranked the entire hand-written
ecosystem in every search run. Two listed directories are broken outright: one is
a parked domain, one serves nine examples behind a "live search is unavailable"
notice. Two repositories named `superpowers` share a byte-identical commit, are
both marked `fork=false`, and rank on a public leaderboard purely by borrowing a
famous name.

"Clone all good skills" therefore has no enumerable target. It resolves to
importing farms and name-squats along with whatever is genuine.

**The bulk is redundant, and this was measured against our own files.** Of eleven
mechanisms the surveys independently identified as the best artifacts found, eight
are already present in this repository, several in more detailed form. The
`blast-radius` evidence ladder, quoted as the single best line about evidence
discipline in its survey, is materially the same as `references/evidence-system.md`,
which adds a "what it does not buy" column and an independence rule. Importing it
is churn.

**The value is concentrated in a small cross-cutting set.** Persona rates across
the agent-skill repositories are 2.4–10%, not the third of material that the
first survey implied. The consistent filter is tool-binding and domain
saturation: `sickn33/agentic-awesome-skills` is 85% substantive and only ~12%
cross-cutting; `TheQtCompanyRnD/agent-skills` is 85% substantive and 0%
cross-cutting. High quality proves nothing about portability.

**Two candidate sources are not collections at all.** `openai/skills` is
deprecated and its README advertises a directory that returns 404.
`vercel-labs/skills` is a package manager whose single skill is a registry
bootstrap funnel in which every no-result ends in "install a skill" or "create a
skill" and never in "do it directly" — the opposite of what a tool-neutral kernel
should do when a capability is absent.

## Decision

Adopt **per item, not per repository**, and place each item by what kind of thing
it is. The unit of adoption is a single skill or agent. Nothing obliges the
adoption of anything else in the repository it came from, and the owner's
instruction to clone good material is satisfied item by item rather than by
taking a source whole.

1. **The discriminator is which lifecycle the item needs.** An item that needs
   the gated creation lifecycle — specification, security review, held-out
   testing, promotion, deprecation — is a **sub-skill** and goes in
   `skills/<name>/SKILL.md` with its own `references/`, `scripts/`, and
   `assets/`. An item that needs only a procedure, an output contract, and a
   set of prohibitions is a **role** and goes in `agents/<name>.md`.
2. The test is therefore: *does this encode a judgement to be applied at a
   decision, or a procedure to be executed with its own gates?* Judgement →
   role. Procedure with lifecycle → sub-skill. A judgement wrapped in persona
   framing is still a judgement, and the framing is removed rather than being a
   reason to reject.
3. Every adopted item records its source repository and the path of the file it
   came from in its frontmatter, so any line can be traced and any defect
   re-checked against the original.
4. Every adopted item must pass the same reachability rule already enforced for
   roles: a role with no row in the dispatch table is unreachable and is an
   error. A sub-skill with no entry in the skill index and no trigger condition
   is unreachable by the same argument, and the check is extended to cover it.
5. Every adopted item carries at least one evaluation case. An item with no case
   is decoration, and decoration is how four roles went recommended and unshipped
   in this repository before.
6. After adoption, `tools/score-roles.py` scores the result and the redundancy
   ratio against the existing catalogue is written into `evaluation/RESULTS.md` as
   a measured number, reported whichever way it falls.
7. Items carrying a disqualifying defect are recorded as rejections in
   `VERDICTS.md` with the defect quoted, never silently dropped. The standing
   disqualifiers are: a `description` that advertises rules the file does not
   contain; a file instructing the model to assert its own excellence or to
   fabricate a user utterance; a file that writes instructions into the user's
   own agent configuration; a file whose self-certified completion token is not
   checkable by anything outside the model.

### Decision record

```text
DECISION
  question   capability acquisition: what is the unit of adoption, and where
             does an adopted item go
  selected   the individual skill or agent; classified by whether it needs the
             gated creation lifecycle, into skills/ or agents/ respectively;
             each traced to its source, reachable from a decision, and carrying
             an evaluation case
  rejected   (a) adopt per repository -- rejected because it couples adoption to
                 everything else in a source, and the sources are 95.6%
                 singletons plus generated farms; a repository is a search space,
                 not a unit of value
             (b) adopt per repository but only from a closed shortlist -- this
                 was the previous version of this record. It is superseded
                 because it still made the repository the decision unit, which
                 over-collects by construction
             (c) adopt nothing and hand-write every addition -- rejected because
                 genuine mechanisms exist elsewhere and re-deriving them wastes
                 effort and loses the provenance that makes them checkable
  rationale  the owner's instruction was to clone good material; the evidence
             says much of it is not good and the rest is tool-bound, but the
             per-item unit honours the instruction exactly while removing the
             temptation to take a source whole
  confidence high in the per-item unit being correct, because it is the only
             granularity at which the judgeable properties -- cross-cutting,
             tool-neutral, substantive -- are decidable at all;
             medium in the lifecycle split placing items correctly, because the
             discriminator is a judgement about a file's shape and will be
             contested at the boundary;
             low in the resulting trigger behaviour, which no survey evidence
             bears on
  cost       per-item provenance and evaluation work; buys a catalogue whose
             every entry is individually justified and individually removable
  evidence   OBS-001, OBS-002, OBS-003, OBS-004
  recovery   if the measured redundancy ratio over the adopted set exceeds 0.6,
             adoption is duplicating rather than deepening the catalogue;
             deprecate the duplicates by the same rule that made them, and record
             the ratio as the reason
```

## Consequences

The shortlist is the unit of review, not the individual file. A reviewer who
disagrees with one import can reject the repository without unpicking the rest.

The cost is that the catalogue will contain material this repository already
expresses. That is accepted deliberately, on the grounds that the owner asked for
depth over minimal diff, and it is bounded by the recovery condition above so it
cannot become permanent by neglect.
