# 0011. Audit findings, and what a validator that is wrong costs

Status: Accepted
Date: 2026-09-28
Deciders: architecture maintainers
Relates to: `SKILL.md` Step 7 (verification), `references/verification-system.md`, `references/evidence-system.md`

## Context

A full audit of the tree was run against its own kernel: Step 0 triage, then
measurement at each checkpoint rather than inspection of intent. Testing against
a real model was out of scope, so what follows is about the *system* — its
internal claims, its checks, and its structure.

The headline is uncomfortable and worth stating plainly. The largest error class
in the repository, for most of this audit's duration, was **the validator being
wrong about correct documents** — not the documents being unfinished.

This record necessarily contains every marker the unfilled-marker rule looks
for. That is the point of it: the marker vocabulary — the words that stand in
for a value rather than being one, such as the work marker `TODO`, its
neighbours `FIXME` and `TBD`, the redaction `XXX`, and the slot forms
`<angle brackets>` and `{{mustaches}}` — is discussed here as an object, so a
validator that scans this document will find them and report them. A document
that defines the marker rule is describing the rule, not violating it, and
`validate-skills.py` exempts such a document on that basis rather than on a list
of words.

| finding | count | verdict |
|---|---|---|
| unfilled markers reported inside ````markdown` template fences | 180 | validator wrong |
| lowercase `todo` reported as the `TODO` work marker | 44 | validator wrong |
| non-role files skipped by every agent check | 4 | validator blind |
| role count in prose, never verified against disk | 1 | validator blind |
| catalogue search returning all 2,397 entries for a 4-word query | 1 | tool wrong |

923 → 299 errors over the audit, and **224 of that reduction was the validator
correcting itself**, not the tree improving.

## Why this is worse than a wrong document

A wrong document is found and fixed. A validator that reports correct work as
broken has three properties that compound:

1. **It trains people to ignore the number.** 449 findings of which 180 were
   nonsense is not a to-do list, it is noise, and the response to noise is to
   stop reading. The 269 real findings were inside the number nobody trusted.

2. **It is self-concealing from outside.** A validator reporting fewer errors
   because it is checking less looks identical to one reporting fewer errors
   because the tree improved. The only way to tell them apart is a pinned
   baseline measured against a known commit — which is why
   `tools/baseline-check.sh` exists and why it prints both the raw and the
   content-attributable delta.

3. **The right instinct makes it worse.** Every individual exemption added here
   is defensible in isolation, and the sum is a checker that cannot fail. The
   `NOT_THIS_REPOSITORY` regex had already grown to `video_folder`,
   `imports? only`, `>\s*\./` and `\bcp "` — one marker per incident, each
   added to accommodate a single line. That is the whack-a-mole pattern, and it
   was in this codebase before the audit began.

## What the audit did instead

Where a rule was producing false positives, the question asked was not "what
exemption does this line need" but "is the rule's premise correct".

- Fenced code: the *premise* was wrong. A fence is a sample, and every other
  content check in the file already knew that. The placeholder check was the
  one reading raw lines. Fixed by making it consistent, not by exempting 180
  lines.
- `TODO` case: the *premise* was wrong. `// TODO` is a marker; "todo list" and
  `tasks/todo.md` are a noun and a filename. Case carries the distinction, and
  IGNORECASE discarded it.
- Catalogue search: the *premise* was wrong. Substring scoring cannot
  discriminate on a 1-character query word, and `a` is inside `abstract`. The
  fix is a length floor, not a stop-word list.
- Paragraph-scoped declarations: document scope was **measured and rejected**
  because it would have exempted 35 real links. A rule that was loosened was
  measured for what it would now let through before being loosened.

Two of the four bundled scripts the authoring agents produced were caught the
same way — the sibling-import check found 22 skills that imported a helper which
did not exist, and every prior verification had been `py_compile`, which cannot
see an unresolved import.

## Decision

Every fix in this audit ships with a self-test asserting **both directions**,
and every self-test asserts a clean-tree control.

This is the rule that generalises: a check that cannot be shown to fail is not
evidence. The single-word search bug survived because the command exited 0 and
printed plausible output; the fence bug survived for the same reason; the role
count survived because nobody compared prose to disk. All three were invisible
to "does the build pass", and all three are visible to "does this check reject a
tree I broke on purpose".

Where a check has no way to fail — because it asserts something static — the
audit added the ability to fail it: the role count is now compared to disk, the
fence exemption is asserted against a marker planted in prose, and the case
rule is asserted against a lowercase noun.

## Consequences

- The self-test suite is the real specification of what this repository
  guarantees. It is longer than the rule it tests, which is the correct ratio
  for a rule that has already been wrong twice.
- Three controls still fail on a clean tree, and that is honest: 299 findings
  remain. A control that passes while the tree is red is a control that has
  stopped meaning anything, so the failures are reported rather than relaxed.
- **The remaining 299 are not all real.** 62 are angle brackets in
  descriptions, 33 are sub-skills declaring a `references/` directory that does
  not exist, 26 are `*_*-automation` names, 13 are eval cases needing fixtures
  nobody generates, 8 are binary assets that cannot be honestly authored. Each
  needs a decision that is a content judgement, not a mechanical fix.
- Nothing here is evidence that the kernel *works*. Every check in the
  repository is the kernel agreeing with itself. The 128 evals have never run
  against a real model, and until they do, "verified" in this system means
  "consistent", which is a weaker claim and should be read as one.
