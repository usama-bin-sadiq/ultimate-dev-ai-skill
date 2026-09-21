# Decomposition Algorithm (compact)

## Steps (complex tier only)
1. **Restate goal** — 1-2 lines, becomes "done" definition
2. **List domains + risk** — from classification block
3. **Split subtasks** — smallest set, clean interfaces, bounded-context
4. **Write contracts** — inputs, output shape, constraints, done criteria, out-of-scope
5. **Build dependency order** — sequential vs independent
6. **Assign owners** — per Owner Decision table
7. **Execute** — structured results (decisions, files, risks)
8. **Integrate** — reconcile against done definition
9. **Return** — compact working list

## Rules
- Each subtask → single owner
- No subtask spans >1 domain unless inseparable
- Explicit inputs/outputs — no "figure it out"
- Independent subtasks parallel (if tool supports)
- Sequential subtasks in dependency order

## Owner Decision Table
| Condition | Owner |
|-----------|-------|
| Different lens, shared context, low isolation | Mode-switch |
| Isolation needed, no sub-agent support | Mode-switch, sequential |
| Isolation + parallelism + sub-agent support | Real sub-agent |
| Sub-agent's subtask is complex | Re-classify, spawn (max depth 2) |

## Sub-agent Contract (compact)
```
<role>{domain} specialist</role>
<task_contract>
  <goal>1-2 lines</goal>
  <inputs>exact files/data</inputs>
  <constraints>conventions, risk flags</constraints>
  <definition_of_done>checkable criteria</definition_of_done>
  <out_of_scope>what NOT to do</out_of_scope>
</task_contract>
<context>minimum files/outputs only</context>
<applicable_principles>numbered principles only</applicable_principles>
<output_format>structured result</output_format>
<escalation_rule>stop if high-risk or unclear</escalation_rule>
```

## Output Format
```markdown
## Subtask: [name]
- **Owner**: [mode-switch|sub-agent]
- **Inputs**: [files/data]
- **Outputs**: [structured result]
- **Decisions**: [list]
- **Files touched**: [list]
- **Open risks**: [list]
```