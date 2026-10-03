# Capability Bridge — Runtime Dispatch Contract

Use `capability-registry.md` as the source-of-truth discovery contract and `dispatch-scheduler.md` for dependency-aware scheduling. `runtime-self-check.md` is the integrity gate.

This file defines the missing execution layer between the Ultimate Developer kernel and the host agent runtime.

## 1. Core rule

An agent file is a **dispatch specification**, not proof that an agent was executed.

A dispatch is successful only when:
- the host actually invoked a native subagent/task, or
- the host lacks native subagents and the kernel executed the agent prompt as a serial fallback.

Reading an agent file alone is `prepared`, not `executed`.

## 2. Runtime capability discovery

Before the first dispatch, inspect the host's exposed capabilities. Use the host's native discovery mechanism when one exists.

Build this logical map:

| Capability | Meaning |
|---|---|
| `subagent` | Can launch an independent specialist context |
| `skill` | Can discover/load another installed skill |
| `tool` | Can invoke a named runtime tool |
| `plugin` | Can invoke a connected external integration |
| `parallel` | Can run independent dispatches concurrently |
| `write` | Can modify/create files |
| `shell` | Can execute project commands |
| `web` | Can search/fetch web documentation |
| `review` | Can run/check a review workflow |

The exact host API names are implementation details. **Never invent an API name from this document.**

## 3. Agent resolution

For each selected `agents/<name>.md`:

1. Confirm the file exists.
2. Read its frontmatter.
3. Resolve each declared `tools:` entry against the runtime capability map.
4. Resolve the requested model tier against available model capabilities.
5. Load the agent prompt plus only the shared rules required by the kernel.
6. Dispatch using the strongest supported execution mode.

Resolution statuses:
- `native` — requested capability exists and was used.
- `fallback` — native capability is absent; equivalent serial execution was used.
- `partial` — agent ran but one or more optional tools were unavailable.
- `unavailable` — required capability is absent **and was looked for**: the host's
  capability map was inspected, a semantic equivalent was sought (a different tool
  with the same effect, a different execution mode, a narrower scope done for
  real), and the reason it substitutes nothing is written down.
- `skipped` — routing determined the agent was irrelevant.

`unavailable` is the one status a run reaches most easily and least defensibly,
because "I could not do that" and "I did not find a way to do that" produce the
same sentence and only one of them is a fact about the host. The map above is
built by *inspecting the host*, so an entry is an observation; a capability the
agent never went looking for is not an entry, it is an assumption. When the
capability is one the host actually lacks, say which mechanism reported it.

The failure this prevents is a run that opens with an accurate-sounding
capability map containing several `unavailable` rows it never tested, routes
around its own skills, and delivers a smaller result than the host was fully
able to produce. That is a self-inflicted limit, and it is worse than a real one
because it is invisible from the transcript: the report is accurate about a
capability set the run quietly shrank before using it. See
`references/retry-policy.md` for the routes to walk first.

## 4. Subagent execution

### Native subagent host

Use the host's real task/subagent mechanism. Pass:
- agent prompt
- task
- relevant file paths
- compact stack/rules context
- resolved tool set

Do not paste unrelated agent outputs into the child context.

### No native subagent host

Run the exact selected agent prompt in the current context as a focused serial turn. Preserve its output contract and clearly label the result `fallback`.

This makes the architecture functional on rule-only hosts without falsely claiming parallel subagents.

## 5. Skill/subskill execution

If the host exposes installed skills:
1. Discover them once per run.
2. Match task intent to relevant skills.
3. Load the selected skill instructions before execution.
4. Apply the skill as a capability, not merely as a document reference.
5. Avoid recursively loading the same skill.

If skill discovery is unavailable, do not claim that all installed skills were discovered. Continue with the available agent/tool path.

## 6. Tool execution

Agent frontmatter declares **requested tool classes**, not guaranteed host APIs.

The kernel must:
- map a requested tool to the host's actual equivalent;
- use the tool when needed by the agent's mission;
- never call a nonexistent tool;
- never replace a missing tool with fabricated output;
- distinguish "tool unavailable" from "tool not needed".

Equivalent examples:
- `Read` → host file-read capability
- `Grep` → host text-search capability
- `Glob` → host file-pattern search
- `Bash` → host shell/command execution
- `WebSearch`/`WebFetch` → host web capabilities

These are semantic mappings only; host-specific names must come from runtime discovery.

## 7. Parallel dispatch

If `parallel` exists:
- batch independent agents in one dispatch group;
- do not parallelize agents with write conflicts or ordering dependencies;
- cap concurrency by the phase token/agent budget.

If `parallel` does not exist:
- execute the same group serially;
- preserve the same selected roster and output contracts.

## 8. Result accounting

Maintain a compact dispatch ledger:

```text
agent                mode       tools              status
codebase-analyzer        native     Read,Grep,Glob     executed
security-auditor     fallback   Read,Grep          executed
database-optimizer  —          —                  skipped
```

The ledger is for orchestration and final reporting; do not dump raw child transcripts.

## 9. Failure behavior

- Missing optional tool → continue with `partial`.
- Missing required tool → try a semantically equivalent host capability.
- No equivalent → mark `unavailable`, explain the exact limitation, and do not fabricate results.
- Native subagent failure → retry once only if the host reports a transient failure; otherwise use serial fallback when safe.
- Skill load failure → continue with the closest applicable agent workflow and report the missing skill.
- Tool failure → preserve the real error and continue only where dependencies allow.

## 10. Bridge failure protocol

When a capability is reported absent or a dispatch fails, apply these steps in order before recording a result:

1. Record the gap in the capability map — name the missing capability class and the mechanism that reported it absent.
2. Attempt inline execution as a fallback — if the capability class has an inline-executable equivalent (e.g. a tool call, a direct file read, a web fetch), try it before marking anything unavailable.
3. Only report `unavailable` after inline was also tried, or after stating explicitly why inline is provably impossible for this capability class.

A capability reported unavailable without steps 1–3 is a hypothesis, not a finding.

## 11. What "use all" means

"Use all subskills/subagents/tools" must never mean indiscriminately running everything.

It means:
- every **relevant** capability is discoverable;
- every selected agent can actually execute or explicitly falls back;
- every required tool is resolved to a real host capability;
- irrelevant capabilities are intentionally marked `skipped`;
- unavailable capabilities are explicitly reported.

This prevents both silent omission and wasteful all-agent execution.
