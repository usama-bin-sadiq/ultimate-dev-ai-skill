<!-- Moved verbatim from design-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 7: Triage

Sort all discovered findings by impact, then decide which to fix:

- **High Impact:** Fix first. These affect the first impression and hurt user trust.
- **Medium Impact:** Fix next. These reduce polish and are felt subconsciously.
- **Polish:** Fix if time allows. These separate good from great.

Mark findings that cannot be fixed from source code (e.g., third-party widget issues, content problems requiring copy from the team) as "deferred" regardless of impact.

Detector findings carry their `[rule-id]`; a deferred one ends with its `handoff=` command when `IMPECCABLE_SKILL: present` (Phase 0 lists them), and nothing when the detector did not run.

---
