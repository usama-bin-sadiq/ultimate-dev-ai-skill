# Skill Versioning

Version a skill so that behaviour can be attributed to a specific set of
instructions, and so that a revision can be evaluated rather than merely shipped.

## When a version is required

- The body changes in any way.
- The trigger changes — a widened or narrowed `fires_when`.
- A dependency changes behaviour.
- A failure mode is added or resolved.
- A security finding is resolved.

A description-only change is a version when it changes which requests the skill
claims, because that is a behavioural change even though the body is identical.

## Semantic versioning for skills

Interpret the numbers as behaviour, not as source compatibility:

- **MAJOR** — the trigger changed substantially, a failure mode was removed, or
  the output shape changed. Existing callers may break.
- **MINOR** — new capability within the existing trigger. Existing callers
  continue to work.
- **PATCH** — a clarification, a corrected example, a typo that changes
  understanding. No behavioural change intended.

The commonest real change — narrowing a trigger that was too broad — is MINOR if
the skill still serves everything it claimed to serve for its own callers. It is
MAJOR if narrowing means some previously-handled request is now unhandled, and
something else has to take it.

## Changelog

```text
## [1.2.0] — 2026-09-26
Added
  - Handles the case where the migration runner is already mid-transaction.
Changed
  - fires_when now excludes single-tenant tables (they use plain migrations).
Fixed
  - Batch size was computed after the first batch, not before.
Security
  - advisory: reads a config file the user did not name; documented in boundaries.
```

Record what a user would observe, not what a diff shows. "Refactored helper
function" is not a changelog entry; "handles mid-transaction runners" is.

## Attribution

Every behavioural difference between versions is attributable to a version. This
is what makes "it used to work" diagnosable: the run that fails is running
version *N*, and the change between *N* and *N-1* is in the changelog.

Without versions, a skill that quietly became worse is indistinguishable from one
that was always bad, and the fix is guesswork.

## Compatibility

A change is compatible if a run that would have succeeded still succeeds and
produces an equivalent result. Test that, do not assume it:

- Re-run the regression suite from `skill-testing.md` against the new version.
- Re-run the negative cases. A narrowed trigger is the most common accidental
  breaking change, because the removed case simply stops being exercised.
- If a case can no longer be handled, it must be handled by something. A gap
  created by a revision is a regression, not a simplification.

## Not editing in place

A promoted skill is changed through a revision, never edited silently. "Editing
in place" means changing the body without a version, a changelog entry, and a
regression run — which makes the change unreviewable and the resulting behaviour
unattributable.

The cost of versioning is a few minutes. The cost of not versioning is a skill
that cannot be safely improved and therefore never is.
