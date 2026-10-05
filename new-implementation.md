# PRD: Ultimate Dev — Model-Agnostic Agentic Skill Architecture

**Status:** Proposed
**Version:** 1.0
**Type:** Architecture / Platform PRD
**Primary Component:** `ultimate-dev`
**Architecture Goal:** Model-agnostic, tool-neutral, MCP-compatible, runtime-driven agentic development system

---

# 1. Executive Summary

`ultimate-dev` is a general-purpose software development skill designed to coordinate requirements analysis, architecture, implementation, testing, review, documentation, and related development workflows.

The current architecture has become difficult to operate because too many responsibilities are concentrated inside a large skill containing numerous subskills and subagents without a sufficiently clear separation of:

* orchestration
* domain workflows
* specialized reasoning
* capabilities
* tools
* state
* external integrations
* validation
* execution

This PRD defines a new architecture for `ultimate-dev` from first principles.

The architecture must **not be constrained by the existing implementation**. The current implementation should be treated only as a migration source.

The new architecture must work across the entire model spectrum:

```text
Tiny → Small → Medium → Large → Huge / Frontier
```

A huge model may improve planning and reasoning quality, but a huge model must **not be required for the architecture to function**.

The system must also support MCP as a first-class integration mechanism while avoiding direct coupling between skills and MCP servers.

The fundamental design principle is:

> **Build the system so that a tiny model can execute it correctly, while a huge model can execute it intelligently.**

---

# 2. Problem Statement

The existing `ultimate-dev` architecture has accumulated too many responsibilities.

Typical problems include:

* unclear boundaries between skills and agents
* too many subagents
* too many subskills
* orchestration logic mixed with execution logic
* tool-specific assumptions inside skills
* model-specific assumptions
* excessive context passed between agents
* implicit dependencies
* unclear ownership of state
* MCP/tool integrations becoming coupled to workflows
* child agents deciding too much about global workflow
* root skill becoming a "god skill"
* agents becoming "god agents"
* difficulty determining which components should run
* unnecessary execution of unrelated agents
* poor failure handling
* weak validation boundaries
* difficult migration and testing

The new architecture must solve these structurally rather than simply rewriting the existing prompts.

---

# 3. Goals

## 3.1 Primary Goals

The system must:

1. Provide a clean architecture for `ultimate-dev`.
2. Separate orchestration from execution.
3. Separate reusable workflows from specialized reasoning roles.
4. Separate capabilities from concrete tools.
5. Support MCP without depending on MCP.
6. Remain independent of any specific model provider.
7. Support tiny through frontier models.
8. Keep state outside the model.
9. Use artifacts as the primary mechanism for passing important information.
10. Dynamically select only relevant skills and agents.
11. Validate outputs between workflow stages.
12. Support retries, fallback, escalation, and graceful failure.
13. Support multiple tool providers for the same capability.
14. Allow runtime-level model routing.
15. Allow deterministic workflows where possible.
16. Allow model-generated plans where necessary.
17. Make the system observable and debuggable.
18. Be easy to extend without creating architectural chaos.

---

# 4. Non-Goals

The following are explicitly outside the scope of the architecture:

* requiring a particular LLM provider
* requiring a particular model size
* requiring MCP
* requiring a specific agent framework
* requiring autonomous agents everywhere
* requiring every workflow to be model-generated
* putting all tools directly into the root skill
* putting MCP server implementations inside `ultimate-dev`
* exposing every available tool to every model
* building a deeply nested agent hierarchy
* optimizing exclusively for frontier models
* preserving the current implementation architecture

---

# 5. Core Architectural Principles

## 5.1 Separation of Concerns

Each layer must have one primary responsibility.

```text
Skill
  ↓
Workflow
  ↓
Agent / Subskill
  ↓
Capability
  ↓
Provider
  ↓
Tool / MCP / API / CLI
```

---

## 5.2 Model Independence

The architecture must not assume:

* large context windows
* native tool calling
* structured output
* JSON mode
* reasoning models
* autonomous multi-agent execution
* parallel tool calls
* a specific tokenizer
* a specific provider API

The runtime must adapt the execution mechanism to the model.

---

## 5.3 Runtime Is the Operating System

The model should not become the operating system of the agent framework.

The runtime owns:

* discovery
* scheduling
* state
* dependencies
* workflow execution
* artifact routing
* capability resolution
* tool execution
* permissions
* retries
* limits
* validation
* observability
* model adaptation

The model owns:

* reasoning
* interpretation
* planning when appropriate
* specialized judgment
* generating proposed decisions

---

# 6. Conceptual Architecture

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │ ultimate-dev│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Orchestrator│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Workflow  │
                    │    Engine   │
                    └──────┬──────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Subskill       Agent        Subskill
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    ┌─────────────┐
                    │ Capability  │
                    │   Layer     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Native         MCP          API
           Adapter       Adapter      Adapter
              │            │            │
              └────────────┼────────────┘
                           ▼
                    External Systems
```

---

# 7. Architectural Entities

## 7.1 Skill

A skill is a reusable domain capability or workflow.

A skill answers:

> "What reusable capability does this component provide?"

Examples:

* requirements analysis
* architecture design
* frontend development
* backend development
* testing
* documentation

A skill should have:

* purpose
* scope
* inputs
* outputs
* contract
* dependencies
* workflow
* constraints

A skill should **not** contain every implementation detail.

---

# 7.2 Subskill

A subskill is a smaller reusable workflow within a larger skill.

Example:

```text
frontend
├── component-development
├── state-management
├── accessibility
└── visual-testing
```

A subskill should exist only when its workflow is meaningfully reusable.

Do not create a subskill for every tiny operation.

---

# 7.3 Agent

An agent is a specialized reasoning/execution role.

Examples:

```text
architect
frontend-developer
backend-developer
tester
reviewer
```

An agent consists conceptually of:

```text
Role
+ Instructions
+ Input Contract
+ Output Contract
+ Allowed Capabilities
+ Constraints
```

An agent is **not a model**.

The same agent can be executed by:

* a tiny model
* a medium model
* a frontier model
* multiple model calls
* a deterministic process
* a human

---

# 7.4 Capability

A capability is an abstract ability required by a workflow or agent.

Examples:

```text
file_read
file_write
code_search
repository_read
repository_write
execute_tests
web_read
database_read
browser_automation
```

The capability describes **what can be done**, not how it is done.

---

# 7.5 Provider

A provider implements a capability.

Possible providers include:

```text
Native tool
MCP server
API
CLI
Remote service
Database connector
IDE integration
```

Multiple providers can implement the same capability.

---

# 7.6 Tool

A tool is a concrete executable operation.

Examples:

```text
read_file
write_file
git_diff
run_tests
search_code
```

Tools are implementation details from the skill's perspective.

---

# 7.7 Workflow

A workflow defines:

* sequence
* dependencies
* branching
* parallelism
* validation
* recovery
* completion criteria

Example:

```text
Requirements
    ↓
Architecture
    ↓
Implementation
    ↓
Testing
    ↓
Review
```

---

# 7.8 Artifact

An artifact is a persistent structured output produced during execution.

Examples:

```text
requirements
architecture
implementation-plan
code-change
test-results
review
documentation
```

Artifacts are preferred over passing huge conversational contexts between agents.

---

# 8. Ultimate Dev Responsibilities

`ultimate-dev` should coordinate software-development work.

It should be able to handle tasks such as:

* understanding requirements
* planning work
* designing architecture
* implementing frontend code
* implementing backend code
* modifying existing systems
* writing tests
* running tests
* reviewing changes
* debugging
* documentation
* refactoring
* repository analysis

It should dynamically select the minimum necessary components.

---

# 9. Ultimate Dev Package Structure

The target package structure is:

```text
.agents/
└── skills/
    └── ultimate-dev/
        │
        ├── SKILL.md
        ├── manifest.yaml
        ├── orchestrator.md
        │
        ├── skills/
        │   ├── requirements/
        │   │   ├── SKILL.md
        │   │   └── manifest.yaml
        │   │
        │   ├── architecture/
        │   │   ├── SKILL.md
        │   │   └── manifest.yaml
        │   │
        │   ├── frontend/
        │   │   ├── SKILL.md
        │   │   └── manifest.yaml
        │   │
        │   ├── backend/
        │   │   ├── SKILL.md
        │   │   └── manifest.yaml
        │   │
        │   ├── testing/
        │   │   ├── SKILL.md
        │   │   └── manifest.yaml
        │   │
        │   └── documentation/
        │       ├── SKILL.md
        │       └── manifest.yaml
        │
        ├── agents/
        │   ├── architect/
        │   │   ├── AGENT.md
        │   │   └── contract.yaml
        │   │
        │   ├── frontend-developer/
        │   │   ├── AGENT.md
        │   │   └── contract.yaml
        │   │
        │   ├── backend-developer/
        │   │   ├── AGENT.md
        │   │   └── contract.yaml
        │   │
        │   ├── tester/
        │   │   ├── AGENT.md
        │   │   └── contract.yaml
        │   │
        │   └── reviewer/
        │       ├── AGENT.md
        │       └── contract.yaml
        │
        └── resources/
            ├── schemas/
            ├── templates/
            ├── examples/
            └── policies/
```

---

# 10. Root SKILL.md

The root skill should remain concise.

It should define:

* identity
* purpose
* scope
* inputs
* outputs
* high-level constraints
* delegation policy
* reference to orchestrator

It should not contain:

* every tool
* every MCP server
* every agent's instructions
* implementation-specific workflows
* massive examples
* entire repository knowledge

---

# 11. Manifest

The manifest is the declarative composition layer.

Example:

```yaml
name: ultimate-dev
version: 1.0.0
type: skill

description: >
  General-purpose software development orchestration skill.

orchestrator:
  path: orchestrator.md

skills:
  - id: requirements
    path: skills/requirements

  - id: architecture
    path: skills/architecture

  - id: frontend
    path: skills/frontend

  - id: backend
    path: skills/backend

  - id: testing
    path: skills/testing

  - id: documentation
    path: skills/documentation

agents:
  - id: architect
    path: agents/architect

  - id: frontend-developer
    path: agents/frontend-developer

  - id: backend-developer
    path: agents/backend-developer

  - id: tester
    path: agents/tester

  - id: reviewer
    path: agents/reviewer
```

The manifest should be intentionally boring and predictable.

---

# 12. Orchestrator

The orchestrator is the central coordinator.

Its responsibility is:

```text
Understand
    ↓
Plan
    ↓
Delegate
    ↓
Execute
    ↓
Validate
    ↓
Recover
    ↓
Synthesize
```

It decides:

* what needs to happen
* when it happens
* which component should do it
* what inputs it receives
* what output is required
* whether the output is valid
* what happens next

It does **not** perform every specialized task itself.

---

# 13. Orchestrator Rules

The orchestrator must:

### Dynamically select components

A documentation task should not invoke:

```text
frontend
backend
database
tester
```

unless required.

### Prefer minimal execution

Use the smallest workflow that can correctly solve the problem.

### Maintain shallow delegation

Preferred:

```text
ultimate-dev
    ↓
workflow
    ↓
agent
```

Avoid:

```text
ultimate-dev
 ↓
agent A
 ↓
agent B
 ↓
agent C
 ↓
agent D
 ↓
agent E
```

Target typical depth:

```text
2–4 meaningful levels
```

---

# 14. Agent Contracts

Every agent should have an explicit contract.

Example:

```yaml
id: backend-developer

input:
  required:
    - requirements
    - architecture

output:
  type: implementation-result

capabilities:
  required:
    - file_read
    - file_write
    - code_search

constraints:
  - modify only relevant files
  - preserve existing behavior unless explicitly required
  - report unresolved issues
```

Contracts make agent execution predictable.

---

# 15. Artifact-First Communication

Agents should communicate through artifacts wherever practical.

Example:

```text
requirements
      ↓
architecture
      ↓
implementation-plan
      ↓
implementation
      ↓
test-results
      ↓
review
```

Instead of:

```text
Agent A conversation
      ↓
entire conversation
      ↓
Agent B
      ↓
entire conversation
      ↓
Agent C
```

This reduces:

* context usage
* accidental instruction leakage
* token consumption
* model dependency
* ambiguity

---

# 16. State Management

State must live outside the model.

The runtime should own:

```text
Task State
Workflow State
Artifact State
Dependency State
Execution History
Errors
Decisions
Provider State
```

Example:

```yaml
task:
  id: T123
  status: running

workflow:
  current_stage: implementation

artifacts:
  - requirements
  - architecture

completed:
  - requirements
  - architecture

pending:
  - implementation
  - testing
```

A model should never be required to remember the entire workflow.

---

# 17. Model Adapter

The runtime must provide a model adapter layer.

Conceptually:

```text
Model Router
    │
    ├── Tiny
    ├── Small
    ├── Medium
    ├── Large
    └── Huge
```

The architecture must remain unchanged regardless of model size.

---

# 18. Model Capability Profiles

Models can have different profiles.

Example:

```yaml
model:
  id: model-x

capabilities:
  reasoning: medium
  context: small
  tool_calling: false
  structured_output: false
  parallelism: false
```

Another model might support:

```yaml
model:
  id: model-y

capabilities:
  reasoning: very_high
  context: huge
  tool_calling: true
  structured_output: true
  parallelism: true
```

The skill definition does not change.

---

# 19. Tiny Model Support

Tiny models should be able to execute the architecture through:

* smaller prompts
* one task at a time
* explicit state
* explicit schemas
* deterministic workflows
* runtime-managed tools
* frequent validation
* limited branching

Example:

```text
Task
 ↓
Small prompt
 ↓
One capability
 ↓
Validate
 ↓
Next task
```

The model does not need to understand the entire `ultimate-dev` ecosystem.

---

# 20. Large / Frontier Model Support

Larger models may receive:

* richer context
* multiple related artifacts
* more complex planning
* broader reasoning tasks
* parallel execution opportunities

However, these are optimizations.

The architecture must never require them.

---

# 21. Runtime Planning

There should be two valid planning modes.

## Deterministic planning

For known workflows:

```text
Requirements
 → Architecture
 → Implementation
 → Testing
```

The runtime executes the predefined workflow.

## Model-assisted planning

For unknown or highly variable tasks:

```text
User Request
     ↓
Model proposes plan
     ↓
Runtime validates plan
     ↓
Runtime executes plan
```

The model proposes.

The runtime controls.

---

# 22. Capability Layer

Skills and agents must request capabilities instead of specific providers.

Example:

```yaml
requires:
  capabilities:
    - file_read
    - file_write
    - code_search
    - execute_tests
```

They should not say:

```yaml
requires:
  mcp:
    - filesystem
    - github
```

This keeps the architecture provider-neutral.

---

# 23. MCP Integration

MCP is a first-class provider mechanism.

The architecture is:

```text
Capability
    ↓
Provider Resolver
    ├── Native
    ├── MCP
    ├── API
    └── CLI
```

MCP is therefore supported without becoming a core dependency.

---

# 24. MCP Registry

The runtime should maintain MCP provider configuration.

Example:

```yaml
mcp:
  servers:

    - id: filesystem
      capabilities:
        - file_read
        - file_write

    - id: git
      capabilities:
        - repository_read
        - repository_write

    - id: terminal
      capabilities:
        - command_execute
```

This configuration belongs to the runtime/environment, not the skill package.

---

# 25. MCP Adapter

The runtime translates MCP functionality into internal capabilities.

Conceptually:

```text
MCP Server
    ↓
MCP Adapter
    ↓
Capability Registry
    ↓
Capability Resolver
    ↓
Agent
```

The agent does not need to know the MCP tool name.

---

# 26. MCP Example

Agent requests:

```text
file_read
```

Runtime resolves:

```text
file_read
   ↓
MCP filesystem
   ↓
read_file
```

Alternatively:

```text
file_read
   ↓
native filesystem
```

or:

```text
file_read
   ↓
remote repository API
```

The agent remains unchanged.

---

# 27. MCP Security

MCP servers must not automatically become available to every agent.

Permissions should be capability-based.

Example:

```yaml
agent: backend-developer

capabilities:
  allow:
    - file_read
    - file_write
    - code_search
    - execute_tests

  deny:
    - production_deploy
    - secrets_read
```

The runtime enforces these permissions.

---

# 28. MCP Tool Exposure

Do not expose every MCP tool to every model.

Instead:

```text
All Providers
      ↓
Capability Resolver
      ↓
Relevant Capabilities
      ↓
Current Task
      ↓
Minimal Tool Set
```

This is particularly important for tiny and medium models.

---

# 29. MCP Failure Handling

MCP errors should be normalized.

Examples:

```text
MCP_UNAVAILABLE
MCP_CONNECTION_FAILED
MCP_TOOL_NOT_FOUND
MCP_PERMISSION_DENIED
MCP_TIMEOUT
MCP_INVALID_RESPONSE
```

The runtime determines whether to:

```text
Retry
Fallback
Ask user
Skip
Stop
```

---

# 30. Provider Fallback

A capability can have multiple providers.

Example:

```text
file_read
    │
    ├── Native filesystem
    ├── MCP filesystem
    └── Remote API
```

The runtime chooses based on:

* availability
* permissions
* compatibility
* reliability
* latency
* cost
* task requirements

---

# 31. Tool Execution Modes

The runtime must support environments with different model/tool capabilities.

Supported modes may include:

### Native tool calling

```text
Model
 ↓
Tool Call
 ↓
Runtime
```

### Structured action

```text
Model
 ↓
Structured Action
 ↓
Runtime Parser
 ↓
Tool
```

### Text action

```text
Model
 ↓
Text
 ↓
Runtime Parser
 ↓
Tool
```

### Runtime-driven execution

```text
Model
 ↓
Decision
 ↓
Runtime
 ↓
Tool
```

The skill does not depend on one mechanism.

---

# 32. Progressive Disclosure

The system must avoid loading the entire skill ecosystem into the model.

Instead:

```text
Task
 ↓
Discover relevant skill
 ↓
Load relevant instructions
 ↓
Load relevant artifacts
 ↓
Resolve relevant capabilities
 ↓
Execute
```

For example, a frontend task should not automatically load:

* backend instructions
* deployment instructions
* database administration
* unrelated MCP tools
* all agents
* all resources

---

# 33. Context Management

Context should be treated as a managed resource.

The runtime should provide only:

* relevant instructions
* required artifacts
* current task
* allowed capabilities
* necessary constraints

Example model invocation:

```yaml
task:
  id: T123
  objective: Fix failing authentication tests

role:
  id: backend-developer

context:
  required_artifacts:
    - artifact://requirements
    - artifact://architecture

capabilities:
  available:
    - code_read
    - code_write
    - code_search
    - execute_tests

output:
  schema: implementation-result

constraints:
  - do not modify unrelated files
```

---

# 34. Validation

Validation is a runtime responsibility.

The model should not be the only judge of its own work.

Validation can include:

* schema validation
* artifact validation
* test execution
* type checking
* linting
* dependency checks
* policy checks
* file scope checks
* output contract validation

---

# 35. Recovery

Every meaningful workflow should define recovery behavior.

Example:

```text
Agent fails
   │
   ▼
Retry?
   │
   ├── Yes → retry with adjusted context
   │
   └── No
       ↓
Alternative agent?
       │
       ├── Yes → fallback
       │
       └── No
           ↓
Ask user / stop
```

---

# 36. Failure Boundaries

Failures should be isolated.

A failed testing agent should not necessarily invalidate the entire workflow.

Example:

```text
Requirements ✓
Architecture ✓
Implementation ✓
Testing ✗
Review pending
```

The runtime records the failure and decides the next action.

---

# 37. Parallelism

Parallel execution should be allowed only when dependencies permit it.

Example:

```text
Architecture
     │
     ├── Frontend implementation
     │
     └── Backend implementation
```

can potentially execute in parallel.

But:

```text
Implementation
     ↓
Testing
```

must respect the dependency.

Parallelism is an optimization, not a requirement.

Tiny models may use sequential execution.

Large models may benefit from parallel workflows.

---

# 38. Dependency Graph

Workflows should conceptually form a dependency graph.

Example:

```text
Requirements
      │
      ▼
Architecture
   ┌──┴──┐
   ▼     ▼
Frontend Backend
   └──┬──┘
      ▼
   Testing
      ▼
   Review
```

The runtime should manage these dependencies.

---

# 39. Observability

The runtime should record:

* task ID
* workflow ID
* agent ID
* model used
* capabilities requested
* providers selected
* MCP calls
* artifacts created
* validation results
* retries
* failures
* duration
* final result

This makes debugging possible without reconstructing model conversations.

---

# 40. Security

Security must be enforced outside model instructions wherever possible.

The runtime should control:

* filesystem access
* command execution
* repository modification
* network access
* MCP access
* secrets
* deployment capabilities
* destructive operations

Prompt instructions alone must not be treated as a security boundary.

---

# 41. Human Escalation

The runtime must be able to stop and request user input when:

* requirements are ambiguous
* destructive action requires approval
* credentials are required
* conflicting architectural choices exist
* no provider can satisfy a required capability
* validation repeatedly fails
* confidence is insufficient

---

# 42. Balance Rules

The architecture must avoid both under-engineering and over-engineering.

## Create a Skill When

Create a skill when the behavior:

* represents a meaningful domain workflow
* is reusable
* has a clear contract
* has independent value

---

## Create an Agent When

Create an agent when:

* specialized reasoning is useful
* a distinct role exists
* separate context is useful
* separate capabilities are required
* independent validation is useful

---

## Use a Capability When

The concept describes:

> "What can the system do?"

Examples:

```text
file_read
code_search
execute_tests
```

---

## Use a Tool When

The operation is a concrete implementation.

Examples:

```text
read_file
run_pytest
git_diff
```

---

## Keep It Local When

The operation is trivial and not reusable.

Do not create:

```text
skills/
  read-single-file/
  check-one-variable/
  format-one-line/
```

---

# 43. Anti-Patterns

## God Skill

```text
ultimate-dev
 └── contains everything
```

Avoid.

---

## God Agent

```text
ultimate-agent
 └── requirements
 └── architecture
 └── coding
 └── testing
 └── deployment
```

Avoid.

---

## Micro-Skill Explosion

```text
skill-a
skill-b
skill-c
skill-d
...
```

for trivial operations.

Avoid.

---

## Tool-Coupled Skill

Bad:

```text
frontend skill
  → use specific MCP server
```

Preferred:

```text
frontend skill
  → browser_automation
```

Runtime chooses provider.

---

## Model-Coupled Architecture

Bad:

```text
requires frontier reasoning model
```

Preferred:

```text
runtime adapts execution to available model
```

---

## Context Dumping

Bad:

```text
load entire ultimate-dev
load all agents
load all skills
load all tools
load all repository context
```

Preferred:

```text
discover
→ select
→ load
→ execute
```

---

# 44. Decision Tree

Use this decision process when designing new components:

```text
Is this the overall development workflow?
        │
        └── Yes → Orchestrator

Is this a reusable domain workflow?
        │
        └── Yes → Skill

Does it require specialized reasoning/role?
        │
        └── Yes → Agent

Is it an abstract ability?
        │
        └── Yes → Capability

Is it a concrete external operation?
        │
        └── Yes → Tool / Provider

Otherwise
        │
        └── Keep it local
```

---

# 45. Example End-to-End Workflow

User:

> Add OAuth login to the application and make sure it is tested.

Runtime starts:

```text
User
 ↓
ultimate-dev
 ↓
Understand task
```

Discover:

```text
requirements
architecture
backend
frontend
testing
```

Create workflow:

```text
Requirements
     ↓
Architecture
     ↓
   ┌─┴─┐
   ▼   ▼
Backend Frontend
   └─┬─┘
     ▼
  Testing
     ↓
  Review
```

Resolve capabilities:

```text
code_read
code_write
code_search
execute_tests
```

Provider resolution:

```text
code_read
 → native filesystem

code_write
 → MCP filesystem

execute_tests
 → MCP terminal
```

Artifacts:

```text
requirements
architecture
backend-change
frontend-change
test-results
review
```

Final synthesis:

```text
Implementation complete
Tests passed
Review completed
```

---

# 46. Example Small-Model Execution

For a small model, the runtime may execute:

```text
Task 1:
Understand requirements

Validate
↓

Task 2:
Generate architecture

Validate
↓

Task 3:
Implement backend change

Validate
↓

Task 4:
Run tests

Validate
```

The model never needs to reason about the entire workflow simultaneously.

---

# 47. Example Frontier Execution

A frontier model may receive:

```text
requirements
architecture context
repository structure
test constraints
```

and propose:

```text
parallel frontend/backend implementation
```

The runtime validates dependencies and executes the plan.

Thus:

```text
Small model → correct execution
Large model → better optimization
```

---

# 48. Migration Strategy

The existing implementation should not determine the target architecture.

Migration should happen in stages.

## Phase 1 — Define Contracts

Define:

* skill contract
* agent contract
* capability contract
* provider contract
* artifact contract
* workflow contract

---

## Phase 2 — Extract Responsibilities

Identify current functionality and classify it as:

```text
Skill
Agent
Capability
Tool
Provider
Resource
Workflow
```

Do not preserve incorrect boundaries merely because they exist today.

---

## Phase 3 — Build Runtime Abstractions

Implement:

* discovery
* state
* scheduler
* workflow engine
* capability resolver
* artifact store
* model adapter
* provider adapters

---

## Phase 4 — Add MCP Adapter

Implement:

```text
MCP
 ↓
MCP Adapter
 ↓
Capability Registry
```

Do not couple skills directly to MCP.

---

## Phase 5 — Rebuild Ultimate Dev

Construct the new:

```text
SKILL.md
manifest.yaml
orchestrator.md
skills/
agents/
resources/
```

from the new contracts.

---

## Phase 6 — Add Compatibility Adapters

Existing implementation components may temporarily run behind adapters.

```text
New Runtime
     ↓
Legacy Adapter
     ↓
Existing Implementation
```

This is transitional only.

---

## Phase 7 — Remove Legacy Coupling

Once the new architecture is stable:

* remove direct tool coupling
* remove model assumptions
* remove implicit dependencies
* remove duplicated orchestration
* remove obsolete agents
* remove obsolete subskills

---

# 49. Testing Strategy

The architecture should be tested at multiple levels.

## Unit Tests

Test:

* capability resolution
* artifact validation
* manifest parsing
* dependency resolution
* provider selection

## Workflow Tests

Test:

* successful workflows
* branching
* retries
* failures
* fallbacks
* parallel execution

## Model Compatibility Tests

Test with:

```text
Tiny
Small
Medium
Large
Huge
```

The same skill definitions should be used.

## Provider Tests

Test:

```text
Native
MCP
API
CLI
```

providers for equivalent capabilities.

---

# 50. Compatibility Matrix

The target behavior is:

| Model  | Structured Output | Native Tools | Complex Planning | Expected  |
| ------ | ----------------: | -----------: | ---------------: | --------- |
| Tiny   |                No |           No |              Low | Supported |
| Small  |          Optional |     Optional |              Low | Supported |
| Medium |      Yes/Optional | Yes/Optional |           Medium | Supported |
| Large  |               Yes |          Yes |             High | Supported |
| Huge   |               Yes |          Yes |        Very High | Supported |

No model tier should require changes to the skill definitions.

---

# 51. Definition of Done

The new `ultimate-dev` architecture is complete when:

### Architecture

* [ ] Root skill is an orchestrator, not a god skill.
* [ ] Skills have clear contracts.
* [ ] Agents have clear contracts.
* [ ] Capabilities are provider-neutral.
* [ ] Tools are implementation details.
* [ ] State lives in the runtime.
* [ ] Artifacts are first-class.
* [ ] Workflow dependencies are explicit.

### Model Independence

* [ ] No specific model provider is required.
* [ ] Tiny models are supported.
* [ ] Small models are supported.
* [ ] Medium models are supported.
* [ ] Large models are supported.
* [ ] Frontier models are supported.
* [ ] Model capabilities can be detected/configured.
* [ ] Skill definitions remain model-independent.

### MCP

* [ ] MCP is supported.
* [ ] MCP is optional.
* [ ] MCP servers are runtime configuration.
* [ ] Skills do not depend on MCP server names.
* [ ] MCP tools map to capabilities.
* [ ] MCP permissions are enforced.
* [ ] MCP failures are recoverable.
* [ ] Alternative providers can replace MCP.

### Orchestration

* [ ] Components are dynamically selected.
* [ ] Irrelevant agents are not invoked.
* [ ] Workflow dependencies are explicit.
* [ ] Parallel execution is supported where appropriate.
* [ ] Sequential execution works.
* [ ] Retry/fallback exists.
* [ ] Human escalation exists.
* [ ] Runtime validation exists.

### Context

* [ ] Progressive disclosure is implemented.
* [ ] Relevant artifacts are selectively loaded.
* [ ] Entire skill ecosystems are not dumped into model context.
* [ ] Agent communication is artifact-first where practical.

### Operations

* [ ] Execution is observable.
* [ ] Failures are traceable.
* [ ] Provider selection is traceable.
* [ ] Model selection is traceable.
* [ ] Artifacts are traceable.
* [ ] Workflow state is recoverable.

---

# 52. Target Architecture

The final architecture can be summarized as:

```text
                              USER
                                │
                                ▼
                       ┌────────────────┐
                       │  ultimate-dev  │
                       └───────┬────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │  Orchestrator  │
                       └───────┬────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │ Workflow Engine│
                       └───────┬────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
                 Subskill     Agent     Subskill
                    │          │          │
                    └──────────┼──────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │  Capabilities  │
                       └───────┬────────┘
                               │
                   ┌───────────┼───────────┐
                   ▼           ▼           ▼
                Native        MCP         API
                Provider    Provider    Provider
                   │           │           │
                   └───────────┼───────────┘
                               ▼
                         External Systems


                ┌──────────────────────────┐
                │          RUNTIME         │
                │                          │
                │ Discovery                │
                │ Scheduler                │
                │ State                    │
                │ Dependency Resolver      │
                │ Workflow Engine          │
                │ Artifact Store           │
                │ Capability Resolver      │
                │ Provider Resolver        │
                │ Validation               │
                │ Security                 │
                │ Observability            │
                │ Model Adapter             │
                └────────────┬─────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
            Tiny           Medium          Huge
            Model           Model          Model
```

---

# 53. Fundamental Design Rules

The implementation team must preserve these rules.

### Rule 1

> **Skills describe reusable behavior, not tools.**

### Rule 2

> **Agents describe specialized roles, not models.**

### Rule 3

> **Capabilities describe what can be done, not how.**

### Rule 4

> **Providers implement capabilities.**

### Rule 5

> **MCP is a provider, not the architecture.**

### Rule 6

> **The runtime owns state and execution.**

### Rule 7

> **The model reasons; the runtime controls.**

### Rule 8

> **Artifacts are preferred over conversation dumping.**

### Rule 9

> **Only relevant context and capabilities should be exposed.**

### Rule 10

> **Use the smallest architecture that correctly solves the problem.**

### Rule 11

> **Strong models should improve execution, not be required for execution.**

### Rule 12

> **The current implementation is a migration source, not an architectural constraint.**

---

# 54. Final Product Principle

The purpose of this architecture is not to create the most complicated multi-agent system possible.

The purpose is to create a system that remains understandable while scaling from simple tasks to complex software engineering.

The desired relationship is:

```text
                    SAME SKILL
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Tiny Model    Large Model   Frontier Model
          │             │             │
          ▼             ▼             ▼
      Sequential     Adaptive       Intelligent
       execution      planning       planning
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                   SAME RUNTIME
                        │
                        ▼
                 SAME CAPABILITIES
                        │
               ┌────────┼────────┐
               ▼        ▼        ▼
             Native    MCP       API
```

The architecture should therefore optimize for **correctness, composability, observability, portability, and graceful degradation**, rather than maximizing the number of agents, skills, tools, or model calls.

The ultimate objective is:

> **A tiny model should be able to execute `ultimate-dev` correctly. A large model should execute it efficiently. A frontier model should execute it intelligently. None of them should require a different skill architecture.**
