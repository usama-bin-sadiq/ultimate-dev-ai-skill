---
name: output-format
description: Standard output format for agent-to-orchestrator communication
---

# Agent Output Format

Every agent MUST structure its response for the orchestrator:

```markdown
## TL;DR
One-line summary of findings/result.

## Details
- **Key Finding 1**: Evidence (file:line)
- **Key Finding 2**: Evidence (file:line)
- **Risk/Opportunity**: Description

## Files to Review
- `path/to/file1.ts:123` — reason
- `path/to/file2.py:45` — reason

## Recommendations
1. **Immediate**: Action with rationale
2. **Short-term**: Action with rationale
3. **Long-term**: Action with rationale

## Blast Radius (if applicable)
- Direct callers: X files
- Test files affected: Y files
- Config consumers: Z files
```

**Rules:**
- Lead with the answer (TL;DR first)
- Use specific file:line references
- Distinguish critical vs. minor
- Never say "it should work" — show evidence