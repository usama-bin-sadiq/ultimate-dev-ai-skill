# Workflow Bridge — Host-Native Primitive Mapping

When the host exposes workflow or subagent primitives, the kernel can use them as
implementation vehicles for the four coordination modes. This file defines that
mapping, the degradation contract, and how to detect the primitives at bootstrap.

The principle:

> The coordination mode is chosen first, by the cheapest-adequate rule in
> `references/coordination-modes.md`. A host-native primitive is the
> implementation vehicle, not the driver. The logical outcome is identical
> whether or not the primitive is available; what changes is efficiency.

## The five capability labels

Detect these at bootstrap (Step 0), after the capability registry is built.
Each label is a semantic description of what the host can do — never a product
name.

| Label | What it means |
|---|---|
| `parallel-dispatch` | The host can launch N independent agent/tool contexts concurrently and collect all results before continuing. |
| `sequential-dispatch` | The host can run agents in a declared pipeline — each step receives the prior step's output — without the calling context holding intermediate state. |
| `stateful-handoff` | The host can transfer a conversation thread with its accumulated state to a new agent, preserving history and tool context. |
| `review-loop` | The host can run an implement→review cycle with a declarative stop condition, iterating automatically until the condition is met or a bound is exceeded. |
| `background-run` | The host can start a long-running task asynchronously and notify the caller on completion, without blocking the calling context. |

## Mode mapping table

| Coordination mode | Primitive available | Behaviour | Primitive absent |
|---|---|---|---|
| `route` | `parallel-dispatch` | Dispatch N specialists concurrently; synthesize on join. | Run the same specialists serially; synthesize identically. |
| `delegate` chain | `sequential-dispatch` | Run the chain as a declared pipeline; no intermediate state in the calling context. | Execute each delegate in series, passing output forward explicitly. |
| `handoff` | `stateful-handoff` | Transfer the thread natively; history and tool context survive the handoff. | Embed the relevant state in the next agent's prompt and continue. |
| R3/R4 verify cycle | `review-loop` | Declare the stop condition; the host iterates automatically. | Implement the loop inline with explicit re-entry via JEv on each iteration. |
| Long/async work | `background-run` | Start the task asynchronously; continue other work; handle the completion notification. | Run synchronously; block until complete; record the latency cost. |

## Degradation contract

A run that could not use a native primitive is not a partial result. The kernel
produces the same logical outcome regardless of which primitives were available.
What changes:

- **Efficiency** — parallel-dispatch reduces wall-clock time; its absence raises
  it. The result is the same.
- **Context isolation** — sequential-dispatch and stateful-handoff keep
  intermediate state out of the calling context; their absence means that state
  accumulates inline. The result is the same, the context cost is higher.
- **Latency** — background-run frees the calling context during long work; its
  absence serialises everything. The result is the same.
- **Loop overhead** — review-loop offloads iteration management to the host;
  its absence means the kernel manages re-entry explicitly at each JEv boundary.
  The result is the same.

Record the degradation in one line, placed with the limitations in the delivery:

```text
LIMITATION  parallel-dispatch unavailable: specialists ran serially.
            Result is equivalent; wall-clock time was higher.
```

Do not omit the limitation line. An efficiency gap the reader cannot see is a
gap they cannot account for when deciding how much to trust the timing claims.

## Detection guidance

Detection is empirical (runtime-self-check), never a product-name lookup.
Do not check for a named product. Check for the capability:

- **`parallel-dispatch`** — can the host accept a batch of independent
  invocations in one call and return all results before continuing? Detect by
  attempting it on two trivially independent units; if the host rejects the
  batch or serialises it, the capability is absent.
- **`sequential-dispatch`** — does the host expose a pipeline primitive where
  step N receives step N−1's output without the calling context holding it?
  Detect by reading the host's task/workflow API, if one is documented; otherwise
  assume absent and fall back to serial inline.
- **`stateful-handoff`** — does the host preserve conversation history and tool
  state across an agent transfer? Detect by whether the host's handoff mechanism
  documents state continuity; an undocumented claim is treated as absent.
- **`review-loop`** — does the host expose a loop primitive with a declarative
  stop condition (a file check, a value match, or a sentinel in output)? Detect
  by reading the host's workflow API; if no such primitive is documented, absent.
- **`background-run`** — does the host support async task launch with a
  completion notification to the calling context? Detect by whether the host's
  run/task API documents an async or background mode; if not, absent.

Record each label as `available`, `unavailable`, or `unknown` in the capability
registry. `unknown` means detection was not possible (the host has no documented
API and no empirical probe succeeded); treat it as `unavailable` for planning.

## Relationship to capability-bridge.md

The five labels above are an extension of the capability map in
`agents/_shared/capability-bridge.md`. Where that file records `parallel` as a
boolean, this file gives it a semantic role in mode selection. The two must stay
consistent: if `capability-bridge.md` records `parallel: available`, this file
records `parallel-dispatch: available`.

The entries here are never the authority on what the host can do — that is always
the runtime-self-check and the live capability registry. These labels are the
vocabulary the kernel uses when recording mode decisions and limitations.
