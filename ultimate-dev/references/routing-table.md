# Routing Table

Only agents with a file in `agents/` are reachable. Reachability requires four
conditions simultaneously: the runtime exposes the agent, the kernel can invoke
it, it can receive the context, and it can return a result. A file that exists
but fails any of these conditions is an unreachable description, not a dispatch
target.

## Agent clusters

| Cluster | Agents (file-backed, confirmed) |
|---|---|
| **Engineering** | `architect` · `backend-architect` · `api-platform-engineer` · `appsec-engineer` |
| **Analysis** | `ai-generated-code-auditor` · `ai-data-remediation-engineer` · `analyst` |
| **AI / ML** | `ai-engineer` |
| **Testing** | `api-tester` |

## Task-type to agent mapping

| Task type | First choice | Second choice | Fallback |
|---|---|---|---|
| System design | `architect` | `backend-architect` | inline |
| API design | `api-platform-engineer` | `architect` | inline |
| ML / AI | `ai-engineer` | `backend-architect` | inline |
| Security review | `architect` | `appsec-engineer` | inline |
| API testing | `api-tester` | `appsec-engineer` | inline |
| Code audit | `ai-generated-code-auditor` | `appsec-engineer` | inline |
| Data remediation | `ai-data-remediation-engineer` | `analyst` | inline |

## Reachability test

Before selecting an agent from this table, confirm all three:

1. **File exists** — `agents/<name>.md` is present in the skill install.
2. **Runtime exposes it** — the host's capability registry shows the agent as
   invocable (not merely listed).
3. **Dispatch path is open** — a `run-state.py dispatch` call for it does not
   return `unreachable`.

If any check fails, move to the second choice; if that also fails, fall back to
inline. Record the outcome with `dispatch --state unreachable --tried "<what was checked>"`.

## Do not name these

Do not name the specific runtime, tool, or host product that exposes or blocks an
agent. Reachability is a property of the current run's capability registry, not of
a product version. The registry is queried at bootstrap; this table is the static
map it resolves against.
