# Ultimate-Dev v2.5 Architecture

This is the canonical architecture. The four layers have strict ownership boundaries.

```text
                         USER / TASK
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                    MODEL / INTELLIGENCE                  │
│                                                          │
│  Reasoning • Planning • Decisions • Adaptation           │
│  Understand intent • Resolve ambiguity • Generate plans  │
│  Choose strategy • Interpret results                     │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                 LANGCHAIN PATTERNS                       │
│                                                          │
│  Skills • Subagents • Handoffs • Router                  │
│                                                          │
│  How should this work be orchestrated?                   │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                ULTIMATE-DEV RUNTIME                      │
│                                                          │
│  State • Context • Checkpoints • Execution               │
│  Verification • Recovery • Policy • Evidence             │
│                                                          │
│  How do we reliably execute and finish it?               │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
                    TOOLS / ENVIRONMENT
```

## JEV decision boundary

JEV is a deterministic policy kernel inside the Ultimate-Dev runtime boundary.
It does not introduce a fifth intelligence layer and it does not own execution:

```text
MODEL / ORCHESTRATION
    │ structured assessment + capability proposal
    ▼
JEV DECISION KERNEL
    │ validate → aggregate → guard → recommend route → slim capabilities
    ▼
DECISION PACKET
    │
    ▼
ULTIMATE-DEV RUNTIME
    │ persist → confirm → execute → observe → verify → recover
    ▼
HOST-NATIVE CAPABILITIES
```

The model owns intent, planning, and strategic pattern selection. The host owns
capability availability, isolation, policy, and approvals. JEV combines those
facts deterministically and returns an auditable recommendation. The runtime
remains authoritative for final policy enforcement, durable state, and evidence.

JEV uses three heads:

- **NOUL** — boolean safety and urgency facts.
- **CHOICE** — proposed orchestration path and task class.
- **SCORE** — normalized risk, complexity, confidence, and context pressure.

Scores are confidence/support values, not probabilities. Hard safety rules take
precedence over scores:

```text
deny > human_review > approve
```

A human-review packet exposes no executable capability IDs. Missing required
capabilities produce an explicit review result; JEV never installs a browser,
container, shell, model provider, or other dependency. Tool slimming is
intersection-only:

```text
selected = requested ∩ host_available ∩ policy_allowed
```

The language-neutral contract lives under `ultimate-dev/runtime/schemas/`.
`ultimate-dev/runtime/jev/engine.mjs` is a dependency-free reference engine;
hosts may implement the same contract natively. See
`docs/adr/0001-jev-host-native-decision-kernel.md`.

## Ownership boundaries

### 1. Model / Intelligence = THINK

The model owns:

- understanding user intent
- resolving ambiguity
- reasoning
- planning
- strategic decisions
- adapting the plan from observed results
- interpreting evidence and deciding what should happen next

The model does **not** own durable task state, checkpoints, proof of completion,
or recovery records.

### 2. LangChain Patterns = COORDINATE

Skills, Subagents, Handoffs, and Router are orchestration patterns. They organize
how model intelligence is applied:

- **Skills**: focused domain capability
- **Subagents**: isolated/parallel specialist work
- **Handoffs**: sequential transfer of task state
- **Router**: classification and dispatch

LangChain is a supported pattern/framework source, not the foundation of the
runtime. Ultimate-Dev remains framework-agnostic.

### 3. Ultimate-Dev Runtime = REMEMBER + EXECUTE + VERIFY + RECOVER

The runtime is the durable control plane. It owns:

- task state
- context assembly and budgets
- checkpoints
- execution lifecycle
- policy and permissions
- JEV packet persistence and execution gating
- verification
- evidence
- recovery and rollback records
- durable audit events

The runtime must not become a second model that invents strategy. It executes
structured model decisions, persists results, and returns compact state/evidence
for the model to interpret.

### 4. Tools / Environment = ACT

Concrete providers perform actions:

- filesystem
- shell/terminal
- browser
- Git
- APIs
- databases
- MCP
- IDE/host tools

Tools are capabilities, not the source of orchestration policy.

## Canonical control loop

```text
USER / TASK
    ↓
MODEL: understand → reason → plan → decide
    ↓
PATTERNS: Skills / Subagents / Handoffs / Router
    ↓
JEV: validate → aggregate → guard → recommend
    ↓
RUNTIME: checkpoint → execute → observe → verify → persist
    ↓
TOOLS / ENVIRONMENT
    ↓
RESULT + EVIDENCE
    ↓
RUNTIME persists durable state
    ↓
MODEL interprets result and adapts
```

The runtime-to-model boundary is intentionally compact:

```text
Model → structured plan/action → Runtime
Runtime → result/evidence + compact state → Model
```

**The model can forget. The runtime cannot.**

## Durable state

Task state is stored outside model context at:

```text
<project>/.memory/ultimate-dev/tasks/<task-id>/
├── state.json
├── context.json
├── progress.md
├── checkpoints/
├── handoffs/
└── evidence/
```

A new model/session must be able to resume safely without the previous chat
transcript.

## Progressive context

Context is loaded progressively:

```text
L0 Task
 ↓
L1 Current state
 ↓
L2 Relevant decisions
 ↓
L3 Relevant files/tests
 ↓
L4 Relevant skill/module
 ↓
L5 Relevant history/failures
 ↓
L6 Deep project knowledge
```

Only the minimum useful context is loaded. Small models therefore use compact
context, while larger models can receive deeper context without changing the
runtime architecture.

## Non-negotiable invariants

1. Model claims are not evidence.
2. Durable state lives outside the model context.
3. Every mutating execution step is persisted.
4. Completion requires the task contract and verification evidence.
5. Failed work is recorded and recoverable where practical.
6. Destructive operations require the applicable policy/confirmation.
7. Agents request capabilities, not vendor-specific tools.
8. LangChain patterns may be replaced or extended without replacing the runtime.
9. The same runtime contract works across tiny, small, medium, large, and huge models.
10. Context pressure must not erase the durable task state.
11. JEV decisions are side-effect-free recommendations; only the runtime may persist or execute.
12. A missing host capability is reported, never installed or silently substituted.
13. Human review is a blocking state, not a model-tier upgrade.
