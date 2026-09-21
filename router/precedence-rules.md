# Precedence Rules (compact)

## Order (highest wins)
1. Explicit user instruction (if safe)
2. Security module (if risk flag set)
3. Architecture module (if structural impact)
4. Most specific domain module
5. _universal-principles.md (tiebreaker)

## Rules
- Lower layer never weakens higher
- Note conflicts in output (not invisible)
- Same level → conservative default (security > speed, correctness > convenience)

## Common Conflicts
| Conflict | Resolution |
|----------|-----------|
| Security validate vs Backend skip | Security wins if risk flag |
| Architecture event-driven vs Backend sync | Architecture if structural |
| Frontend loading vs Performance no-render | Ask if ambiguous |
| DevOps pin vs Backend latest | DevOps wins |
| Testing integration vs Security auth first | Security wins |