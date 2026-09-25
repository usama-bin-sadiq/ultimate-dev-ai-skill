# Completion Checklist (compact)

## Full (moderate/complex)
- [ ] Deliverable, acceptance criteria, and risk recorded
- [ ] Unknowns and capability gap reported
- [ ] Evidence distinguishes verified, assumed, and not_run
- [ ] All contract requirements met
- [ ] Edge cases handled or flagged
- [ ] Tests exist and pass (if code changed)
- [ ] Security concerns addressed (if risk flag set)
- [ ] Docs updated (if public interface/architecture/security changed)
- [ ] No unresolved TODOs/stubs
- [ ] Subtask outputs integrate cleanly
- [ ] Library/API claims grounded or marked unverified
- [ ] High-risk actions: rollback considered

## Abbreviated (atomic)
- [ ] Specific requirement and deliverable met
- [ ] Unknowns and limitations stated when material
- [ ] No unverified claims as fact
- [ ] No destructive changes without gate

## Blocking Rule
Failed item → fix, not caveat. Block return until fixed.

## Model-Adaptive
| Model | Checklist |
|-------|-----------|
| tiny | abbreviated only |
| small | abbreviated + first 3 full |
| large | full checklist |
| huge | full + additional audit |