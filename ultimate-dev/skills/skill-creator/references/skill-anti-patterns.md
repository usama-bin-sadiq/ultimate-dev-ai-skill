# Skill anti-patterns

Each failure below is a real failure of this engine, not a style preference. For
each: what you see, why it happens, what to do. Every one is caught by a gate
that already exists, so the skipped gate is the diagnosis.

| Symptom | Mechanism | Fix | Gate |
|---|---|---|---|
| A new skill per task | The disqualifying question was never asked | Answer it with named recurrences | `skill-design.md` |
| Engine invoked when reuse would work | Designing before searching descriptions | Record a discovery entry first | `skill-discovery.md` |
| An untested skill reached ACTIVE | The validation gate was treated as a formality | Run all four test kinds | `skill-testing.md` |
| The description matches everything | No negative trigger in the contract | Write three near-miss queries | `skill-contract.md` |
| The rationale was written after the result | The decision was fitted to its outcome | Record it at the boundary | `skill-provenance.md` |
| A validator pass reported as correctness | A real result read as the judgement it supports | Ask the seven questions | `skill-validation.md` |
| A self-authored skill skipped review | The author was accepted as the reviewer | Read it as if fetched from outside | `skill-security.md` |

## Proliferation

**Symptom** — the skills directory grows by one per unfamiliar problem, and every
new description competes with the rest for every selection.
**Mechanism** — the engine was reached for a hard task, which is exactly when it
is most tempting, and the disqualifying question was skipped.
**Fix** — more skills than distinct recurring procedures is a defect, not a
portfolio. Answer the question with named recurrences.

## Premature invocation

**Symptom** — a composition or an existing skill would have produced the result,
and a new narrow skill was created instead.
**Mechanism** — steps 1–3 of capability resolution were assumed to have failed
rather than tried.
**Fix** — record what was tried and the evidence it failed on. If you cannot name
the evidence, the earlier rungs were not exhausted.

## Untested promotion

**Symptom** — the skill works, so it is promoted. No adversarial case was run.
**Mechanism** — the producing instance was treated as evidence. It is not: it
passed by construction, because the author built it from that instance.
**Fix** — a skill that has never been attacked is not tested. A promotion with no
adversarial case and no negative is refused, not deferred.

## Total trigger surface

**Symptom** — the skill fires on neighbouring requests, and the user gets two
half-processes instead of one.
**Mechanism** — the description states what the skill does and omits when it must
not fire, and no negative was ever measured.
**Fix** — put the near-miss in the contract, then measure it. A skill that fires
on everything scores 100% on pass rate, so the score will never tell you; only
the negative set will.

## Post-hoc justification

**Symptom** — the design note explains why the skill was needed, the explanation
is convincing, and it was written after the skill worked.
**Mechanism** — provenance fitted to a known outcome. It will always read well,
which is exactly why it is worthless.
**Fix** — record the decision at the boundary. A rationale that could have been
written for any outcome is not provenance.

## Mechanical pass mistaken for validation

**Symptom** — the validator is clean, the run is green, and the skill is promoted
as "validated".
**Mechanism** — a real result was mistaken for the judgement it supports.
**Fix** — a structural pass proves well-formedness, nothing more. Ask the seven
questions. The validator cannot tell you a skill is correct, safe, or worth
having, and will certify one that tells the reader to ignore it.

## Self-authored exemption

**Symptom** — the security review is skipped or softened because the kernel wrote
the skill.
**Mechanism** — the author was accepted as the reviewer. This exception *is* the
attack surface, not a shortcut past it.
**Fix** — treat a generated skill exactly like fetched content. Read the whole
package, eval fixtures included, as if it arrived from outside. The run that
designed the skill cannot clear it.

## Also

- **Unremovable capability** — removal needs an edit elsewhere. One deletion, or
  the design was wrong. `skill-deprecation.md`
- **Spec written after the body** — the skill inherited whatever the author
  happened to believe. `skill-contract.md`
- **Invisible edit** — a live skill changed with no version and no regression run.
  `skill-versioning.md`
- **Flat delta called success** — a benchmark showing no change reported as an
  improvement. `skill-testing.md`
- **The engine as escape hatch** — invoked to avoid a hard decision. It is a
  governance path; a hard decision still needs a record.
