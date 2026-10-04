# Token Budget — Efficient Agent Selection

Goal: accomplish the task with the fewest tokens while maintaining quality.

## Agent Count Guidelines

| Complexity | Exploration | Design | Implementation | Review | Verify |
|------------|-------------|--------|----------------|--------|--------|
| Trivial | 0 | 0 | direct | 1 | 1 |
| Small | 1 | 0-1 | direct | 2 | 1 |
| Medium | 2 | 1-2 | direct | 3-4 | 1 |
| Large | 3-4 | 2-3 | direct | 5-8 | 1-2 |
| Epic | 4-5 | 3-4 | direct | 8-12 | 2-3 |

## Dynamic Model Selection

Model tiers are NOT hardcoded. Each agent declares a suggested tier in frontmatter, but the orchestrator adapts:

1. **If running a small-tier host** (`small` in `references/model-adaptation.md`) — Use all agents at their default tier. Small hosts benefit from focused, single-purpose prompts with ≤5 work units.
2. **If running a mid-tier host** (`mid` in `references/model-adaptation.md`) — Can combine thin agents (merge accessibility-auditor+i18n-engineer into frontend-developer).
3. **If running a frontier-tier host** (`frontier` in `references/model-adaptation.md`) — Can run more agents in parallel, use deeper analysis passes.

Tier definitions and enforcement: `references/model-adaptation.md`. Record
the tier at run init: `python3 tools/run-state.py init --host <tier>`.

The frontmatter `model:` field is advisory. The orchestrator picks based on available compute, not hardcoded names.

## Smart Dispatch Rules

1. **Never run an agent that returns nothing useful.** If no database, skip database-optimizer.
2. **Never run redundant agents.** If performance-reviewer already covers N+1, skip database-optimizer.
3. **Share context efficiently.** Pass stack-detection output once, reference in all agents.
4. **Parallel when possible.** Independent agents run simultaneously, not sequentially.
5. **Skip phases that add no value.** Trivial tasks skip exploration, design, and planning.

## Context Injection Pattern

When dispatching an agent, inject only:
1. Detected stack (~10 lines, not 30)
2. Rules sheet (~5 lines)
3. Task description (~3-5 lines)
4. Relevant file paths (~3-5 paths)

Do NOT inject full file contents, other agents' outputs, or conversation history.
