# Universal Agent — Complete Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      UNIVERSAL AGENT                                           │
│                         Adaptive, Context-Efficient Problem-Solving Kernel                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  0. INPUT / OBJECTIVE                                                                          │
│                                                                                              │
│  User Objective → Request → Constraints → Desired Outcome → Available Resources              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  1. TASK MODEL                                                                                 │
│                                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ Objective    │ │ Requirements │ │ Constraints  │ │ Unknowns     │ │ Success Criteria │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
│                                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │
│  │ Assumptions  │ │ Dependencies │ │ Risk         │ │ Verification │                        │
│  │              │ │              │ │              │ │ Criteria     │                        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘                        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  2. TRIAGE / COMPLEXITY ASSESSMENT                                                             │
│                                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐               │
│  │ Complexity │ │ Risk       │ │ Uncertainty│ │ Time/Cost  │ │ Consequence  │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────────┘               │
│                                              │                                               │
│                         Determine minimum sufficient effort                                  │
└──────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                               │
                                               ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  3. JEv DECISION FABRIC                                      ║
║                                                                                              ║
║  Central decision mechanism used at every meaningful decision boundary.                     ║
║                                                                                              ║
║  INPUT                                                                                       ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │ Objective │ State │ Evidence │ Candidates │ Constraints │ Risk │ Uncertainty │ Cost   │  ║
║  └────────────────────────────────────────────────────────────────────────────────────────┘  ║
║                                              │                                               ║
║                                              ▼                                               ║
║                                     ┌─────────────────┐                                      ║
║                                     │      JEv        │                                      ║
║                                     │ Decision Engine │                                      ║
║                                     └────────┬────────┘                                      ║
║                                              │                                               ║
║  DECISION                                                                                     ║
║  ┌────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │ Selected │ Alternatives │ Rationale │ Confidence │ Expected Cost │ Expected Value      │  ║
║  │ Context Needed │ Capability Needed │ Verification │ Escalation │ Recovery Conditions │  ║
║  └────────────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                              ║
║  JEv DECIDES:                                                                                ║
║  • What to do                                                                                ║
║  • What NOT to do                                                                            ║
║  • What information is needed                                                                 ║
║  • Which capabilities are required                                                            ║
║  • Which strategy is appropriate                                                              ║
║  • How much reasoning is justified                                                            ║
║  • Whether to delegate                                                                        ║
║  • Whether to parallelize                                                                     ║
║  • How deeply to verify                                                                       ║
║  • Whether to retry / replan / escalate                                                       ║
║  • Whether new learning should be retained                                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
                         │
          ┌──────────────┼──────────────────┬───────────────────┐
          │              │                  │                   │
          ▼              ▼                  ▼                   ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ 4. CONTEXT     │ │ 5. CAPABILITY  │ │ 6. STRATEGY    │ │ 7. REASONING   │
│    COMPILER    │ │    SYSTEM      │ │    SELECTION   │ │    CONTROL     │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │                  │
        ▼                  ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ CONTEXT        │ │ CAPABILITY     │ │ STRATEGY       │ │ EFFORT         │
│ REQUIREMENTS   │ │ REQUIREMENTS   │ │ CANDIDATES     │ │ SELECTION      │
│                │ │                │ │                │ │                │
│ What do we     │ │ What can solve │ │ Which solving  │ │ How much       │
│ actually need? │ │ this problem?  │ │ approach?      │ │ reasoning?     │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │                  │
        ▼                  ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Retrieval      │ │ Existing       │ │ Direct         │ │ R0 Minimal    │
│ Selection      │ │ Capabilities   │ │ Decomposition  │ │ R1 Structured │
│                │ │                │ │                │ │ R2 Analytical │
│ Relevance      │ │ Discovery      │ │ Sequential     │ │ R3 Deep       │
│ Ranking        │ │                │ │ Parallel       │ │ R4 Assurance  │
│                │ │ Acquisition    │ │ Iterative      │ │                │
│ Compression    │ │                │ │ Research-first │ │ Escalation    │
│                │ │ Composition    │ │ Evidence-first │ │ on demand     │
│ Budgeting      │ │                │ │ Experiment     │ │                │
│                │ │ Validation     │ │ Driven         │ │                │
│ Provenance     │ │                │ │                │ │                │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  8. EXECUTION PLAN                                                                             │
│                                                                                              │
│  Objective → Steps → Dependencies → Preconditions → Actions → Expected Results → Checks      │
│                                                                                              │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐             │
│  │ Atomic Work Units   │────▶│ Dependency Graph    │────▶│ Execution Schedule  │             │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘             │
│                                                                                              │
│  JEv can dynamically modify the plan whenever new evidence changes the situation.            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  9. EXECUTION / PROBLEM SOLVING                                                                │
│                                                                                              │
│                    ┌──────────────────────────────────────┐                                  │
│                    │             EXECUTOR                 │                                  │
│                    └──────────────────┬───────────────────┘                                  │
│                                       │                                                      │
│             ┌─────────────────────────┼─────────────────────────┐                            │
│             ▼                         ▼                         ▼                            │
│      ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                      │
│      │ Reason       │         │ Transform    │         │ Investigate  │                      │
│      └──────────────┘         └──────────────┘         └──────────────┘                      │
│             │                         │                         │                            │
│      ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                      │
│      │ Analyze      │         │ Create       │         │ Experiment   │                      │
│      └──────────────┘         └──────────────┘         └──────────────┘                      │
│             │                         │                         │                            │
│      ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                      │
│      │ Research     │         │ Synthesize   │         │ Implement    │                      │
│      └──────────────┘         └──────────────┘         └──────────────┘                      │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  10. OBSERVATION                                                                                │
│                                                                                              │
│  Action → Result → State Change → Evidence → Error → Unexpected Information                  │
│                                                                                              │
│  Every meaningful execution updates the internal run state.                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  11. VERIFICATION                                             ║
║                                                                                              ║
║                         What must be true for this result to be trusted?                     ║
║                                                                                              ║
║      ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                          ║
║      │ Evidence       │    │ Validation     │    │ Independent    │                          ║
║      │ Check          │    │ Check          │    │ Check          │                          ║
║      └───────┬────────┘    └───────┬────────┘    └───────┬────────┘                          ║
║              │                     │                     │                                   ║
║              └─────────────────────┼─────────────────────┘                                   ║
║                                    ▼                                                         ║
║                           ┌──────────────────┐                                                ║
║                           │ Verification     │                                                ║
║                           │ Decision         │                                                ║
║                           └────────┬─────────┘                                                ║
║                                    │                                                         ║
║                   ┌────────────────┼────────────────┐                                        ║
║                   ▼                ▼                ▼                                        ║
║                VERIFIED        PARTIAL          FAILED                                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
                   │                │                │
                   │                │                │
                   │                ▼                ▼
                   │        ┌──────────────┐  ┌──────────────┐
                   │        │ More Context │  │   RECOVERY   │
                   │        │ / Reasoning  │  │              │
                   │        └──────┬───────┘  └──────┬───────┘
                   │               │                 │
                   │               └────────┬────────┘
                   │                        │
                   │                        ▼
                   │                 ┌──────────────┐
                   │                 │     JEv      │
                   │                 │ Re-decision  │
                   │                 └──────┬───────┘
                   │                        │
                   │             ┌──────────┼───────────┐
                   │             ▼          ▼           ▼
                   │          Retry      Replan     Escalate
                   │             │          │           │
                   │             └──────────┴───────────┘
                   │                        │
                   │                        ▼
                   │                  EXECUTION LOOP
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  12. RESULT SYNTHESIS                                                                          │
│                                                                                              │
│  Verified Findings → Answer / Artifact / Action / Recommendation / Deliverable                │
│                                                                                              │
│  Result contains, where applicable:                                                           │
│  • Outcome                                                                                     │
│  • Evidence                                                                                    │
│  • Assumptions                                                                                 │
│  • Limitations                                                                                 │
│  • Confidence                                                                                  │
│  • Verification status                                                                         │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  13. SELF-EVALUATION                                                                           │
│                                                                                              │
│  Did we solve the task?                                                                        │
│  Did we use unnecessary context?                                                               │
│  Was reasoning sufficient?                                                                     │
│  Was the strategy effective?                                                                   │
│  Were capabilities appropriate?                                                                │
│  Was verification sufficient?                                                                  │
│  What failed?                                                                                  │
│  What could be reused?                                                                         │
│  What should NOT be repeated?                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  14. LEARNING SYSTEM                                          ║
║                                                                                              ║
║  EXPERIENCE                                                                                   ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  OBSERVATION                                                                                  ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  SIGNAL EXTRACTION                                                                            ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  PATTERN / CANDIDATE                                                                           ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  EVALUATION                                                                                   ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  VALIDATION                                                                                   ║
║      │                                                                                       ║
║      ▼                                                                                       ║
║  JEv DECISION                                                                                 ║
║      │                                                                                       ║
║      ├─────────────── Reject ────────────────────────────────────────┐                      ║
║      │                                                               │                      ║
║      ▼                                                               │                      ║
║  PROMOTE                                                                                     ║
║      │                                                               │                      ║
║      ▼                                                               │                      ║
║  REUSABLE KNOWLEDGE                                                                          ║
║      │                                                               │                      ║
║      └────────────────────── Future Retrieval ◀──────────────────────┘                      ║
║                                                                                              ║
║  Learning states: OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → DEPRECATED      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │ FUTURE TASKS          │
                         │                      │
                         │ Reuse proven         │
                         │ knowledge/capability │
                         │ and strategies       │
                         └──────────┬───────────┘
                                    │
                                    └───────────────┐
                                                    │
                                                    ▼
                                            JEv / TASK MODEL
```

## Cross-Cutting Systems

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                CROSS-CUTTING CONTROL PLANE                                     │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ State Management │   │ Budget Manager   │   │ Evidence /       │   │ Security /       │  │
│  │                  │   │                  │   │ Provenance        │   │ Trust            │  │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘  │
│                                                                                              │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Observability    │   │ Cache / Reuse    │   │ Policy /         │   │ Error /          │  │
│  │                  │   │                  │   │ Constraints       │   │ Recovery State   │  │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘  │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                             │
                             ▼
                  ALL DECISION / EXECUTION LAYERS
```

## Context Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  CONTEXT ON DEMAND                                             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

C0 ── Task
 │
 ▼
C1 ── Task Metadata / State
 │
 ▼
C2 ── Required Capability Instructions
 │
 ▼
C3 ── Targeted References / Knowledge
 │
 ▼
C4 ── User / Project Material
 │
 ▼
C5 ── External Evidence
 │
 ▼
C6 ── Specialist / Deep Context

                  ▲
                  │
                  │ JEv determines whether deeper context is justified
                  │
                  └─────────────────────────────────────────────┐
                                                                │
                                                                ▼
                                                     ┌──────────────────┐
                                                     │ Context Compiler │
                                                     └────────┬─────────┘
                                                              │
                         ┌────────────────────────────────────┼─────────────────────────────┐
                         ▼                                    ▼                             ▼
                  Relevance Ranking                     Deduplication                 Compression
                         │                                    │                             │
                         └────────────────────────────────────┼─────────────────────────────┘
                                                              ▼
                                                       Budget Enforcement
                                                              │
                                                              ▼
                                                    Provenance / Freshness
                                                              │
                                                              ▼
                                                        Model Context
```

## Capability Architecture

```text
                              CAPABILITY SYSTEM
                                      │
                                      ▼
                           ┌────────────────────┐
                           │ Capability Registry│
                           └─────────┬──────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
          Existing Capability    Discover             Acquire
                 │                   │                   │
                 │                   │                   ├── External
                 │                   │                   ├── Generated
                 │                   │                   └── User-provided
                 │                   │
                 └───────────────────┼───────────────────┘
                                     ▼
                              Validate Capability
                                     │
                                     ▼
                              Compose Capability
                                     │
                       ┌─────────────┼──────────────┐
                       ▼             ▼              ▼
                   Sequential     Parallel       Iterative
                       │             │              │
                       └─────────────┼──────────────┘
                                     ▼
                                   JEv
                                     │
                                     ▼
                                  Execute
```

## Agent / Specialist Model

```text
                   UNIVERSAL AGENT
                         │
                         ▼
                       JEv
                         │
                 Is specialization
                    justified?
                    /       \
                  NO         YES
                  │           │
                  ▼           ▼
             Direct solve   Specialist
                              │
                              ▼
                       Temporary / selected
                       capability context
                              │
                              ▼
                           Execute
                              │
                              ▼
                         Return result
                              │
                              ▼
                             JEv
```

```text
Agents are NOT the architecture.

Agents are optional execution resources selected by the architecture
when specialization provides sufficient expected value.
```

## Decision Boundaries

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      JEv BOUNDARIES                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Task Understanding ────────────────► JEv                                                     │
│  Decomposition ─────────────────────► JEv                                                     │
│  Capability Selection ──────────────► JEv                                                     │
│  Capability Acquisition ────────────► JEv                                                     │
│  Context Retrieval ─────────────────► JEv                                                     │
│  Context Depth ─────────────────────► JEv                                                     │
│  Strategy Selection ────────────────► JEv                                                     │
│  Workflow Selection ────────────────► JEv                                                     │
│  Reasoning Effort ──────────────────► JEv                                                     │
│  Specialist Delegation ─────────────► JEv                                                     │
│  Parallelization ───────────────────► JEv                                                     │
│  Research Depth ────────────────────► JEv                                                     │
│  Verification Depth ────────────────► JEv                                                     │
│  Retry ─────────────────────────────► JEv                                                     │
│  Replanning ────────────────────────► JEv                                                     │
│  Escalation ────────────────────────► JEv                                                     │
│  Learning Promotion ────────────────► JEv                                                     │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## State Model

```text
                                      ┌──────────────┐
                                      │    RECEIVE   │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │  UNDERSTAND  │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │    TRIAGE    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │    DECIDE    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   CONTEXT    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │     PLAN     │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   EXECUTE    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   OBSERVE    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   VERIFY     │
                                      └──────┬───────┘
                                      ┌──────┴──────┐
                                      ▼             ▼
                                ┌───────────┐  ┌────────────┐
                                │ DELIVER   │  │  RECOVER   │
                                └─────┬─────┘  └─────┬──────┘
                                      │              │
                                      │              └──────► JEv
                                      ▼
                                ┌───────────┐
                                │  LEARN    │
                                └─────┬─────┘
                                      │
                                      └──────────────► FUTURE TASKS
```

## Core Principle

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                         DO NOT GIVE THE AGENT EVERYTHING.                                    │
│                                                                                              │
│                    GIVE IT THE ABILITY TO DETERMINE WHAT IT NEEDS,                           │
│                    ACQUIRE IT, USE IT, VERIFY IT, RECOVER FROM FAILURE,                     │
│                    AND RETAIN ONLY WHAT HAS BEEN PROVEN USEFUL.                             │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Final System Boundary

```text
                         ┌───────────────────────────────┐
                         │        UNIVERSAL AGENT        │
                         │                               │
                         │  Task Model                   │
                         │       ↓                       │
                         │  JEv Decision Fabric          │
                         │       ↓                       │
                         │  Context + Capability         │
                         │       ↓                       │
                         │  Strategy + Reasoning         │
                         │       ↓                       │
                         │  Execution                    │
                         │       ↓                       │
                         │  Observation                  │
                         │       ↓                       │
                         │  Verification                 │
                         │       ↓                       │
                         │  Recovery                     │
                         │       ↓                       │
                         │  Self-Evaluation              │
                         │       ↓                       │
                         │  Controlled Learning           │
                         │                               │
                         └───────────────┬───────────────┘
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
       ┌───────────┐              ┌────────────┐              ┌────────────┐
       │  Model    │              │ Capabilities│              │  Resources │
       │ / Reasoner│              │ / Knowledge │              │ / Context  │
       └───────────┘              └────────────┘              └────────────┘
                                         │
                                         ▼
                                  VERIFIED RESULT
```
