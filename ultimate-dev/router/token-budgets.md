# Token Budget Rules (compact)

## MODEL DETECTION (do FIRST)
Count context window. If unsure, assume SMALL.

| Context | Model Size | Path |
|---------|-----------|------|
| ≤8K | TINY | INLINE ONLY — no modules, no agents |
| ≤32K | SMALL | 1 module max, 1 agent max |
| ≤128K | LARGE | full system, up to 3 agents |
| >128K | HUGE | all features, unlimited |

## Budget Table
| Tier | Modules | Sub-agents | Context | Output |
|------|---------|------------|---------|--------|
| atomic | 0 | 0 | n/a | answer only |
| moderate | 1 (2 if security) | 0 | n/a | answer + 1-line rationale |
| complex | N (domains) | N (subtasks) | subtask-only | structured summary |

## Hard Rules
1. Never load Tier 1 without classification match.
2. Never re-load loaded module; cache/reuse.
3. Never pass more context than subtask requires.
4. Ambiguity blocks complex tasks until clarified.
5. Default compact; narrative opt-in.

## Recursion
- Max depth: 2 (sub-agent → sub-agent → escalate)

## Caching
- Loaded modules stay in context for task duration.
- Reference principles by number in sub-agent contracts.

## Sub-agent Context (pass only)
- Subtask contract
- Applicable numbered principles
- Relevant files/outputs

## Never Pass
- Full project history
- Unrelated modules
- Conversation transcript
- Entire Capability Index

## TINY Model Rules (≤8K)
```
IF task is simple:
  DO inline
  OUTPUT result
ELSE IF task needs multiple files:
  DO one file at a time
  OUTPUT each file separately
ELSE:
  OUTPUT "Task too complex for tiny model. Upgrade to small+."
```

## SMALL Model Rules (≤32K)
```
1. CLASSIFY task (atomic/moderate/complex)
2. IF atomic:
   DO inline
3. ELSE IF moderate:
   READ router/lite-mode.md
   FIND matching module
   READ that module
   APPLY patterns
   OUTPUT result
4. ELSE IF complex:
   DO best effort with 1 module
   LIST what you couldn't cover
   OUTPUT partial result + gaps
```

## LARGE Model Rules (≤128K)
```
1. CLASSIFY task
2. LOAD matching modules (up to 3)
3. IF complex:
   DECOMPOSE into subtasks
   SPAWN sub-agents (max 3)
   VERIFY results
4. OUTPUT structured result
```

## HUGE Model Rules (>128K)
```
1. Do everything in LARGE
2. ADD: deep analysis, multiple iterations
3. ADD: full test coverage, documentation
4. ADD: architecture decision records
```

## Fallback Chain
```
TINY → INLINE → if insufficient, report the bounded gap
SMALL → 1 SKILL/MODULE → universal-task for unknown work → list gaps
LARGE → SELECTED METHODS + OPTIONAL SPECIALISTS → escalate blocked decisions
HUGE → SAME PROMPT-FIRST METHODS WITH DEEPER VERIFICATION
```

A larger context does not authorize automatic tool execution, specialist
creation, or provider installation.
