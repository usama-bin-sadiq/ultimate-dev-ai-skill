# 0007. Adopted capabilities carry no upstream citation

Status: Accepted
Date: 2026-09-27
Deciders: architecture maintainers
Amends: 0005, clause 3

## Context

Decision 0005 set the adoption unit at the individual skill and required, in its
clause 3, that every adopted item record its source repository and file path in
its frontmatter "so any line can be traced and any defect can be re-checked
against the original". Nineteen capabilities were adopted under that clause and
carried `source_repo`, `source_file`, and `adapted`.

The owner directed that the upstream citation be removed: no reference to the
repository a capability was compiled from.

The direction is recorded here rather than applied silently, because it reverses
a clause this repository wrote and because the cost is real and specific.

## What is lost

**Defects in an adopted capability can no longer be re-checked against the
original.** When `unknowns-mapper` behaves wrongly, there is no recorded origin to
compare it against, and the only way to recover one is to search for it again. The
18 hours of survey work that produced the shortlist become unrepeatable from the
repository alone.

That cost is acceptable under three conditions, all of which currently hold. The
capabilities have been rewritten rather than copied — procedure, output contract,
and prohibitions are in this repository's shape, not the source's. The
disqualifying defects that caused four candidates to be rejected are recorded in
the commit history, so the *rejection* reasoning survives even though the
*acceptance* citation does not. And the underlying material is public and
unpublished material cannot be uniquely identified by its ideas.

## What is kept

- **Version**, on every adopted capability, so behaviour is attributable to a
  revision. This is what decision 0005's clause 3 was actually protecting, and it
  is retained.
- **Rejection reasoning**, in the commit history, including the quoted defects
  that disqualified each candidate.
- **The substance scorer**, `tools/score-roles.py`, which measures the adapted
  text on its own terms and needs no citation.

## Decision

1. `source_repo` and `source_file` are removed from every capability. `version`
   replaces them.
2. `validate-skills.py` no longer accepts the repository keys.
3. The promotion gate's `provenance` requirement is satisfied by a version alone.
4. A capability may cite a source in prose where the citation is *load-bearing* —
   that is, where the argument cannot be stated without it. The line is that a
   reader must be able to follow the reasoning from what is in front of them.

### Decision record

```text
DECISION
  question   provenance: whether an adopted capability records where it came from
  selected   version only; no upstream repository citation in any capability
  rejected   (a) keep the citations -- rejected by the owner, who directed their
                 removal; the preference is theirs and the reasoning does not
                 outweigh it
             (b) keep the citation in a separate ledger outside the capability --
                 rejected because it preserves the citation in the repository,
                 which is what was directed, and only relocates it
  rationale   a capability is judged on its text; a citation to a repository is a
             claim about origin, not about behaviour, and origin does not change
             what the file says
  confidence high in the removal being correct as a product decision, since the
             owner stated it directly;
             medium in the survey work not being needed again, since that work was
             expensive and its output is now unrepeatable from the repository;
             low in the absence of citation reducing the chance of a defect being
             traced back, which is the cost being accepted rather than avoided
  cost       the ability to re-check an adapted capability against its original
             without re-running the survey
  evidence   none -- this is a preference, not a finding, and it is recorded as
             one rather than argued for
  recovery   if an adopted capability later shows a defect that can only be fixed
             by consulting its original, add the citation for that capability
             only, under clause 4
```
