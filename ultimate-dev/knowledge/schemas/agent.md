# Agent

## Purpose

The agent record is the contract for a specialized reasoning role: what it must
be given, what it must return, which capabilities it may use, and when the
kernel selects it. An agent is **a role, not a model** — the same agent can be
executed by a tiny model, a frontier model, several model calls, a deterministic
process, or a human, and the contract does not change. The record exists so that
delegation is predictable: the kernel knows the price and the product before the
dispatch, and the result can be checked against something.

## Shape

```yaml
agent:
  id: string
  role: string                    # the specialized reasoning role, one sentence
  instructions: string            # path to the role file — the procedure, not a copy of it
  input:
    required: [string]            # artifact ids or context the role cannot start without
    optional: [string]
  output:
    type: string                  # the artifact type it returns (see artifact.md)
    contract: string              # the shape the output must satisfy
  capabilities:
    required: [string]            # provider-neutral ids from resources/capability-vocabulary.yaml
    optional: [string]
    denied: [string]
  constraints: [string]           # what the role must not do
  execution:
    parallel_safe: true | false
    writes: none | files | external
  dispatch:
    condition: string             # when the kernel selects this role
    fallback: string              # what happens when it is unreachable
```

## Fields

| Field | Type | Req | Meaning |
|---|---|---|---|
| `input.required` | list | yes | What must exist before dispatch. A role dispatched without its required input is a setup failure, not an agent failure. |
| `output.type` | enum | yes | An artifact type from `artifact.md`. "A good answer" is not a type. |
| `capabilities.required` | list | yes | Provider-neutral capability ids. Never a tool name, a server name, or a provider id — the runtime resolves those. |
| `capabilities.denied` | list | yes | Wins over `required` and `optional` on conflict. Capability-based, not server-based. |
| `constraints` | list | yes | The boundaries the role must hold even when the task tempts it past them. |
| `dispatch.condition` | string | yes | When this role is selected. A role with no dispatch condition is not available, however good it is. |
| `execution.writes` | enum | yes | `files` or `external` forces the write-scope checks in the security policy. |

## Field rules

- Capabilities are named from `resources/capability-vocabulary.yaml` and nothing
  else. A contract that names a provider has coupled the role to one
  implementation, and the fallback chain in `provider.md` cannot engage.
- `output.contract` names a checkable shape. If the result cannot be validated
  against it, the contract is decoration.
- `dispatch.condition` and `dispatch.fallback` are both required. The first
  prevents indiscriminate execution; the second prevents a missing role from
  ending a run that inline or another role could have finished.
- `execution.parallel_safe: false` excludes the role from every parallelism
  group in `workflow.md`. Roles that write to shared mutable state are never
  parallel-safe.
- The record carries no model field. A capability the role genuinely needs is
  recorded in `capabilities.required`; coupling the role to a model tier is the
  model-coupled-architecture anti-pattern.
- The role file at `instructions` is the procedure. The contract is what the
  kernel needs to dispatch and validate; it is not a summary of the procedure,
  and it is never a copy of it.

## Worked example

The `architect` role, whose instructions live at `agents/architect.md`:

```yaml
agent:
  id: architect
  role: Designs the security model — threat models, trust boundaries, secure-by-design architecture — and hands code-level findings to the AppSec Engineer.
  instructions: agents/architect.md
  input:
    required: [artifact://requirements, artifact://architecture]
    optional: [artifact://code-change]
  output:
    type: review
    contract: every finding carries severity, exploitability, and a concrete remediation; the trust boundaries of the system are named
  capabilities:
    required: [file_read, code_search]
    optional: [web_read]
    denied: [production_deploy, secrets_read]
  constraints:
    - Designs the security model; does not perform code-level SAST/DAST — that is the AppSec Engineer's role.
    - Every finding must be exploitable in principle, not theoretically concerning.
    - Modifies no files; the output is a review artifact.
  execution:
    parallel_safe: true
    writes: none
  dispatch:
    condition: system design, security review, or any change that moves a trust boundary
    fallback: inline — the kernel runs the threat-model questions itself and labels the review self-checked
```

## Validation

Mechanical:

- Every `capabilities.*` entry resolves to an id in
  `resources/capability-vocabulary.yaml`.
- `capabilities.denied` is applied after `required` and `optional`; a capability
  in both is denied.
- `output.type` is a declared artifact type.
- `dispatch.condition` and `dispatch.fallback` are non-empty.
- `execution.writes: none` ⟹ the role's instructions promise no file
  modification; a mismatch means the contract or the procedure is stale.

Judgement, not automatable:

- Whether `role` is a specialization or a second kernel. A role that triages,
  plans, verifies, and recovers is a god agent wearing a contract.
- Whether `input.required` is what the role needs or everything the run
  happens to hold. Context dumping into a contract is context dumping with a
  schema.
- Whether `dispatch.condition` declines the neighbouring request. A condition
  that fires on everything selects on nothing.

## Anti-patterns

- **The god agent.** One role whose contract covers requirements, architecture,
  coding, testing, and deployment. The contract is accurate and the
  specialization is gone.
- **Tool-coupled contract.** `capabilities.required` naming an MCP server or a
  product. The role now breaks when the provider changes, for no benefit.
- **Contract as summary.** Restating the instructions file in the contract
  fields. Two copies of the procedure drift; the contract holds the dispatch
  and validation surface only.
