---
name: emerging-tech-handler
description: >
  Fallback for tasks matching no domain module. Borrows principles from adjacent domains, applies universal principles, discloses gaps transparently.
triggers: [unrecognized technology, unknown domain, new framework, unfamiliar pattern]
anti_triggers: [any task matching existing Capability Index module]
last_verified: 2026-09-21
---

# Emerging Tech Handler (compact)

## Role
Fallback for unmatched tasks. Transparent about gaps, borrows principles.

## Process (6 steps)
1. **Nearest-neighbor**: borrow 1-2 adjacent domain principles (labeled as analogy)
2. **Universal baseline**: apply _universal-principles.md (correctness, security, maintainability, testability)
3. **Research**: WebSearch/WebFetch if available; otherwise reason from steps 1-2
4. **Disclose**: state no module exists, answer is best-effort
5. **Session scaffold**: hold ad-hoc knowledge for session (discarded at end)
6. **Gap note**: emit {domain, date, description, count} for CHANGELOG.md

## Rules
1. Never fake expertise
2. Borrow principles, not prescriptions
3. Research before reasoning
4. Disclose confidence level
5. Session scope only
6. Gap notes mandatory

## Gap Note Format
```
| Domain | Date | Description | Occurrences | Status |
|--------|------|-------------|-------------|--------|
| [name] | YYYY-MM-DD | [one-line] | [1/2/3+] | Gap note |
```

## Response Format
```markdown
## Domain Gap: [Name]
**No module exists.** Response based on:

### Borrowed Principles (from [adjacent])
- [Principle 1] — analogy
- [Principle 2] — analogy

### Universal Principles Applied
- Correctness: [how]
- Security: [how]
- Maintainability: [how]
- Testability: [how]

### Confidence
- Verified docs: [yes/no]
- Borrowed principles: [yes/no]
- General reasoning: [yes/no]
```

## Escalation
- This IS the escalation target for unmatched tasks
- At 3+ occurrences → flag for promotion to real module