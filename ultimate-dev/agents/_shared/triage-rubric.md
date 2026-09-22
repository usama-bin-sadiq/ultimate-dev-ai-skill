---
name: triage-rubric
description: Task classification rubric for determining required agent pipeline depth
---

# Triage Rubric (Phase 0)

Classify EVERY task before spawning agents:

| Class | Definition | Pipeline | Agents |
|-------|------------|----------|--------|
| **A** | Trivial: typo, single-line fix, config tweak | Inline only | 0 |
| **B** | Simple: one file, one concern, known pattern | Explore → Implement → Verify | 1-2 |
| **C** | Moderate: 2-5 files, single feature, some unknowns | Explore → Design → Implement → Review → Verify | 3-5 |
| **D** | Complex: 5+ files, multi-domain, architectural impact | Full pipeline + bootstrap | 6+ |

**Decision Tree:**
1. How many files touched? ≤1 → A/B; 2-5 → C; 5+ → D
2. Cross-domain? (frontend+backend, DB+API, etc.) → bump one class
3. Unknown codebase? → bump one class
4. Security/auth/data-migration involved? → minimum C
5. Production deploy/release? → minimum D

**Never run Class D pipeline for Class A task. Never run Class A pipeline for Class D task.**