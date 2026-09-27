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

Import **by literal clone from a named shortlist**, tool-neutralise what is
tool-bound, and **measure the redundancy ratio rather than assert it**.

1. The shortlist is fixed in `research/skill-ecosystem/SHORTLIST.md` with, for
   each repository, the file count, the cross-cutting proportion, and the
   disqualifying defects found. The shortlist is closed: a repository not on it
   is not imported, and adding one is a JEv record.
2. Cloning is literal. Files are taken as written, then adapted. Adaptation
   removes tool bindings and persona framing and rewrites the file into this
   repository's role contract; it does not replace content with a summary of
   content, because a summary is an extraction and extraction is what this
   decision rejected.
3. Every imported file records its source repository and the file it came from
   in its frontmatter, so any line can be traced and any defect re-checked
   against the original.
4. After adaptation, `tools/score-roles.py` scores the result and the redundancy
   ratio against the existing catalogue is written into `evaluation/RESULTS.md`
   as a measured number. The number is reported whichever way it falls.
5. Files carrying a disqualifying defect are recorded as rejections in
   `VERDICTS.md` with the defect quoted, never silently dropped. The standing
   disqualifiers are: a `description` that advertises rules the file does not
   contain; a file instructing the model to assert its own excellence or to
   fabricate a user utterance; a file that writes instructions into the user's
   own agent configuration; a file whose self-certified completion token is not
   checkable by anything outside the model.

### Decision record

```text
DECISION
  question   capability acquisition: how much external material to import, and
             from where
  selected   literal clone from a closed five-repository shortlist, adapted to
             the role contract, with the redundancy ratio measured and reported
  rejected   (a) clone every repository on the owner's list -- the population is
                 95.6% singletons plus generated farms and name-squats, so the
                 instruction has no enumerable target and the import would be
                 dominated by material with no cross-cutting content
             (b) extract only the three mechanisms found absent -- this was the
                 recommendation and the owner declined it; on the evidence it
                 discards genuine depth in the cross-cutting sources for a
                 smaller diff, and depth is what the owner asked for
             (c) import the full shortlist unadapted -- rejected because the
                 brief requires tool-neutral wording and role-contract
                 conformance, and because three shortlisted repositories ship
                 prompt-poisoning or self-modifying behaviour that must not be
                 executed
  rationale  the owner's goal is a deep, genuinely cross-cutting catalogue; the
             evidence says depth is available but only from a closed set, so
             clone deeply from that set rather than widely from all of them
  confidence high in the shortlist being the right set of repositories;
             medium in the adapted result being better than the original,
             because that depends on adaptation quality and is not yet measured;
             low in the resulting false-trigger behaviour, which no evidence
             from any survey bears on
  cost       roughly 120 files and one full measurement pass; buys a catalogue
             whose contents are traceable and whose redundancy is known rather
             than assumed
  evidence   OBS-001, OBS-002, OBS-003, OBS-004
  recovery   if the measured redundancy ratio exceeds 0.6, the import has
             duplicated rather than deepened the catalogue; revert to the
             shortlist's mechanisms-only form and record the ratio as the reason
```

## Consequences

The shortlist is the unit of review, not the individual file. A reviewer who
disagrees with one import can reject the repository without unpicking the rest.

The cost is that the catalogue will contain material this repository already
expresses. That is accepted deliberately, on the grounds that the owner asked for
depth over minimal diff, and it is bounded by the recovery condition above so it
cannot become permanent by neglect.
