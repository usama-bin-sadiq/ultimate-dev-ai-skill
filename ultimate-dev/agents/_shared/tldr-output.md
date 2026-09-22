---
name: tldr-output
description: TL;DR output format - every message leads with the answer
---

# TL;DR Output (MANDATORY)

**Every developer-facing message MUST:**
1. **Lead with the answer** — one sentence, plain English
2. **Use a summary table** for multi-point responses
3. **Cut ceremony** — no "I'll help you with...", "Here's what I found..."

**Format:**
```
[One-line answer/summary]

| Aspect | Status/Value |
|--------|--------------|
| Key Point 1 | Detail |
| Key Point 2 | Detail |

[Optional: Long form ONLY if user explicitly asks "explain in detail" or "walk me through it"]
```

**Stand down to long-form ONLY when user explicitly requests it — and only for that one turn.**