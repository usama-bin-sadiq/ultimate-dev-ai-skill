# Gap Promotion Rules (compact)

## Threshold
- **3 occurrences** → promotion candidate

## Process
1. **Track**: emit gap note per emerging-tech-handler use
2. **Count**: verify occurrences in CHANGELOG.md
3. **Flag**: status → "Candidate" at 3 occurrences
4. **Notify**: coordinate with skill-maintainer
5. **Draft**: follow §25 skeleton exactly
6. **Validate**: full checklist
7. **Register**: SKILL.md, skill-manifest.yaml, CHANGELOG.md
8. **Bump**: minor version for new capability

## Validation Checklist
- [ ] Frontmatter complete (name, description, triggers, anti_triggers, last_verified)
- [ ] Principles section (imperative, checkable)
- [ ] Anti-Patterns section (paired examples)
- [ ] Current Tooling Notes section
- [ ] Output Contract section
- [ ] Escalation Triggers section
- [ ] No trigger conflicts with existing modules

## Rollback
1. Revert SKILL.md, skill-manifest.yaml
2. Update CHANGELOG.md status
3. Bump version
4. Document reason

## Metrics
- Gap note frequency
- Promotion rate
- Time to promotion
- Rollback rate
- Trigger accuracy