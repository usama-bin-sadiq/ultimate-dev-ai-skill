Absolutely. The product should now be specified as **`ultimate-dev`**, with **`skill-creator` as a first-class capability for dynamically creating/extending skills**, while keeping the core itself compact, model-agnostic, and scalable.

`skill-creator` is a **sub-skill of `ultimate-dev`**, shipped inside it at `ultimate-dev/skills/skill-creator/`. It is not a sibling product and not a second entry point: only the kernel decides that a capability gap exists, and only the kernel hands the gap to the engine.

The key change is that `ultimate-dev` is **not a coding skill** despite the name. It is a universal problem-solving and engineering kernel capable of working on anything from a simple text task to an OS-scale engineering program.

# ULTIMATE-DEV — Production PRD

**Product name:** `ultimate-dev`
**Product type:** Universal Agent Skill / Cognitive-Execution Kernel
**Target maturity:** Production-grade, scalable, domain-agnostic
**Core principle:** One adaptive kernel, dynamically acquiring the context, capabilities, tools, skills, specialists, reasoning depth, and verification required by the objective.

---

# 1. Product Vision

`ultimate-dev` should behave as a **general-purpose autonomous engineering and problem-solving intelligence layer**.

A user should be able to provide:

> "Build an operating system."

and the system should not respond as though "OS" is a predefined workflow.

Instead:

```text
OBJECTIVE
   ↓
UNDERSTAND
   ↓
TRIAGE
   ↓
JEv
   ↓
DISCOVER REQUIRED KNOWLEDGE
   ↓
DISCOVER REQUIRED CAPABILITIES
   ↓
ACQUIRE / CREATE MISSING SKILLS
   ↓
DECOMPOSE
   ↓
ARCHITECT
   ↓
PLAN
   ↓
EXECUTE
   ↓
OBSERVE
   ↓
TEST
   ↓
VERIFY
   ↓
RECOVER / REPLAN
   ↓
ITERATE
   ↓
INTEGRATE
   ↓
VALIDATE
   ↓
DELIVER
   ↓
LEARN
```

The same kernel must be capable of applying this lifecycle to:

* software
* operating systems
* distributed systems
* scientific research
* mathematics
* engineering
* cybersecurity
* data science
* business
* finance
* writing
* education
* automation
* product development
* architecture
* hardware/software co-design
* unfamiliar disciplines
* cross-disciplinary problems

The system must **not require a pre-existing skill for every possible field**.

---

# 2. Core Product Thesis

The architecture is:

```text
                    ┌───────────────────────┐
                    │      USER OBJECTIVE   │
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │      TASK MODEL       │
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │        TRIAGE         │
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │     JEv DECISION      │
                    │        FABRIC         │
                    └───────────┬───────────┘
                                ↓
        ┌───────────────────────┼───────────────────────┐
        ↓                       ↓                       ↓
   CONTEXT                 CAPABILITY                STRATEGY
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ↓
                           REASONING
                                ↓
                            PLANNING
                                ↓
                           EXECUTION
                                ↓
                           OBSERVATION
                                ↓
                          VERIFICATION
                         ↙            ↘
                    VERIFIED        FAILED/PARTIAL
                       ↓                 ↓
                    RESULT           RECOVERY
                       │                 │
                       │              REPLAN
                       │                 │
                       └───────┬─────────┘
                               ↓
                            LEARNING
                               ↓
                              JEv
```

---

# 3. The Most Important Architectural Rule

`ultimate-dev` must **not become an enormous collection of agents**.

Instead:

```text
                     ULTIMATE-DEV
                           │
                           ▼
                    UNIVERSAL KERNEL
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
         Skills        Capabilities    Specialists
            │              │              │
            └──────────────┼──────────────┘
                           ↓
                         JEv
                           ↓
                       Objective
```

Skills, tools, specialists, references and external resources are **resources**.

The kernel remains the decision-maker.

---

# 4. Production Directory Structure

This is the structure I recommend as the canonical product repository.

> **Correction — `skill-creator` is a sub-skill, not a sibling.** An earlier
> revision of this tree placed `skill-creator/` beside `ultimate-dev/` under
> `skill/`, which made it a peer of the kernel. That is wrong, and wrong in a way
> that matters: as a sibling it would be a second entry point a user or an
> external indexer could select directly, bypassing the kernel's effort gate.
> Capability creation is a decision the kernel makes, not a request a user routes
> around it — which is the whole of §3. It now sits at
> `ultimate-dev/skills/skill-creator/`, and the kernel must reference it for the
> tree to be valid. The shipped implementation already had it in the right place;
> only this specification was wrong.

```text
ultimate-dev/
│
├── README.md
│   # Product overview and entry point.
│
├── LICENSE
│   # Product license.
│
├── PRD.md
│   # This complete product requirements document.
│
├── ARCHITECTURE.md
│   # Complete architecture and design decisions.
│
├── CHANGELOG.md
│   # Version history and behavioral changes.
│
├── CONTRIBUTING.md
│   # Contribution and engineering standards.
│
├── SECURITY.md
│   # Security model and threat model.
│
│
├── skill/
│   │
│   ├── ultimate-dev/
│   │   │
│   │   ├── SKILL.md
│   │   │   # ⭐ PRIMARY UNIVERSAL KERNEL
│   │   │   # The actual production skill.
│   │   │
│   │   └── references/
│   │       │
│   │       ├── operating-model.md
│   │       ├── task-model.md
│   │       ├── triage.md
│   │       ├── decision-fabric.md
│   │       ├── decision-ledger.md
│   │       │
│   │       ├── context-system.md
│   │       ├── context-compiler.md
│   │       ├── context-provenance.md
│   │       │
│   │       ├── capability-system.md
│   │       ├── capability-discovery.md
│   │       ├── capability-acquisition.md
│   │       ├── capability-validation.md
│   │       ├── capability-composition.md
│   │       │
│   │       ├── skill-system.md
│   │       ├── skill-discovery.md
│   │       ├── skill-selection.md
│   │       ├── skill-composition.md
│   │       │
│   │       ├── strategy-system.md
│   │       ├── reasoning-system.md
│   │       ├── model-adaptation.md
│   │       │
│   │       ├── planning-system.md
│   │       ├── execution-system.md
│   │       ├── observation-system.md
│   │       │
│   │       ├── verification-system.md
│   │       ├── evidence-system.md
│   │       ├── provenance-system.md
│   │       │
│   │       ├── recovery-system.md
│   │       ├── retry-policy.md
│   │       ├── escalation.md
│   │       │
│   │       ├── learning-system.md
│   │       ├── memory-system.md
│   │       ├── learning-safety.md
│   │       │
│   │       ├── state-system.md
│   │       ├── budget-system.md
│   │       ├── caching-and-reuse.md
│   │       │
│   │       ├── security-and-trust.md
│   │       ├── human-control.md
│   │       ├── deterministic-vs-agentic.md
│   │       │
│   │       ├── delegation.md
│   │       ├── parallelism.md
│   │       ├── multi-domain.md
│   │       ├── unknown-domain.md
│   │       │
│   │       ├── insufficient-capability.md
│   │       ├── insufficient-evidence.md
│   │       ├── output-contract.md
│   │       └── anti-patterns.md
│   │   │
│   │   └── skills/
│   │       │
│   │       └── skill-creator/
│   │           │
│   │           ├── SKILL.md
│   │           │   # ⭐ SKILL CREATION ENGINE
│   │           │   # A SUB-SKILL OF ultimate-dev, not a sibling.
│   │           │   # Creates, improves, composes and validates
│   │           │   # reusable skills when the kernel identifies
│   │           │   # a capability gap.
│   │           │
│   │           └── references/
│   │               │
│   │               ├── skill-design.md
│   │               ├── skill-contract.md
│   │               ├── skill-discovery.md
│   │               ├── skill-generation.md
│   │               ├── skill-composition.md
│   │               ├── skill-validation.md
│   │               ├── skill-testing.md
│   │               ├── skill-versioning.md
│   │               ├── skill-security.md
│   │               ├── skill-provenance.md
│   │               ├── skill-promotion.md
│   │               ├── skill-deprecation.md
│   │               └── skill-anti-patterns.md
│
│
├── knowledge/
│   │
│   ├── README.md
│   │
│   ├── schemas/
│   │   ├── task.md
│   │   ├── decision.md
│   │   ├── context.md
│   │   ├── capability.md
│   │   ├── skill.md
│   │   ├── evidence.md
│   │   ├── observation.md
│   │   ├── experience.md
│   │   └── learning.md
│   │
│   └── policies/
│       ├── freshness.md
│       ├── provenance.md
│       ├── validation.md
│       ├── promotion.md
│       └── retention.md
│
│
├── evaluation/
│   │
│   ├── README.md
│   ├── methodology.md
│   ├── metrics.md
│   │
│   ├── benchmark/
│   │   ├── simple/
│   │   ├── medium/
│   │   ├── complex/
│   │   ├── ambiguous/
│   │   ├── long-context/
│   │   ├── multi-step/
│   │   ├── cross-domain/
│   │   └── high-assurance/
│   │
│   ├── domains/
│   │   ├── software/
│   │   ├── systems/
│   │   ├── research/
│   │   ├── mathematics/
│   │   ├── science/
│   │   ├── engineering/
│   │   ├── data/
│   │   ├── business/
│   │   ├── finance/
│   │   ├── writing/
│   │   ├── education/
│   │   ├── planning/
│   │   └── security/
│   │
│   ├── failure-cases/
│   │   ├── context/
│   │   ├── capability/
│   │   ├── strategy/
│   │   ├── reasoning/
│   │   ├── execution/
│   │   ├── verification/
│   │   └── recovery/
│   │
│   ├── security-cases/
│   │   ├── prompt-injection/
│   │   ├── malicious-context/
│   │   ├── capability-poisoning/
│   │   ├── evidence-manipulation/
│   │   ├── authorization/
│   │   └── unsafe-actions/
│   │
│   └── regression/
│
│
├── examples/
│   │
│   ├── software-engineering/
│   ├── operating-system/
│   ├── distributed-system/
│   ├── research/
│   ├── mathematics/
│   ├── science/
│   ├── data-analysis/
│   ├── business/
│   ├── writing/
│   ├── planning/
│   ├── cross-domain/
│   ├── unknown-domain/
│   └── recovery/
│
│
├── docs/
│   │
│   ├── architecture/
│   ├── concepts/
│   ├── decisions/
│   ├── operations/
│   ├── security/
│   └── evaluation/
│
│
└── research/
    │
    ├── decision-making/
    ├── context-optimization/
    ├── capability-acquisition/
    ├── skill-generation/
    ├── reasoning/
    ├── verification/
    ├── recovery/
    └── learning/
```

---

# 5. `ultimate-dev` Core

The core skill should operate according to:

```text
RECEIVE
  ↓
UNDERSTAND
  ↓
MODEL
  ↓
TRIAGE
  ↓
DECIDE
  ↓
ACQUIRE
  ↓
PLAN
  ↓
EXECUTE
  ↓
OBSERVE
  ↓
VERIFY
  ↓
RECOVER / REPLAN
  ↓
SYNTHESIZE
  ↓
SELF-EVALUATE
  ↓
LEARN
  ↓
DELIVER
```

Every major transition can return to JEv.

---

# 6. JEv Decision Fabric

JEv is the central control mechanism.

It decides:

* whether decomposition is necessary
* whether more context is necessary
* what context is relevant
* whether research is required
* which capability is required
* whether a capability exists
* whether a new skill should be created
* whether skills should be composed
* whether specialists are justified
* whether work should be parallelized
* which strategy to use
* how much reasoning is justified
* whether a model/tool/resource should change
* whether verification should be shallow or exhaustive
* whether an action should be retried
* whether strategy should change
* whether the plan should be rebuilt
* whether the user needs to be asked
* whether the objective is currently impossible
* whether a discovered pattern should become learning

JEv must optimize:

```text
Expected Outcome
────────────────────────────
Cost + Risk + Uncertainty
```

rather than blindly minimizing tokens or tool calls.

---

# 7. Skill Creator

This is an important addition.

`skill-creator` is a **sub-skill of `ultimate-dev`**, invoked by the kernel and
not selectable directly. Its description must say so, because the failure mode it
guards against is a user or an external indexer routing straight to it and
skipping triage — which is precisely the capability proliferation §3 prohibits.

`skill-creator` should **not mean "generate Markdown whenever something is missing."**

It is a controlled capability-generation subsystem.

```text
Capability Gap
      ↓
Determine whether reusable
capability is actually needed
      ↓
Search existing skills
      ↓
Search existing capabilities
      ↓
Compose existing resources?
      │
   YES ─────────→ Compose
      │
      NO
      ↓
Design candidate skill
      ↓
Generate skill specification
      ↓
Generate implementation/instructions
      ↓
Security analysis
      ↓
Capability tests
      ↓
Behavior tests
      ↓
Adversarial tests
      ↓
Validation
      ↓
JEv decision
      ↓
CANDIDATE
      ↓
VALIDATED
      ↓
PROMOTED
```

### Critical rule

A newly generated skill must **not automatically become trusted core behavior**.

Its lifecycle is:

```text
OBSERVED
   ↓
CANDIDATE
   ↓
VALIDATING
   ↓
VALIDATED
   ↓
PROMOTED
   ↓
ACTIVE
   ↓
DEPRECATED
```

This prevents self-improvement from becoming uncontrolled self-corruption.

---

# 8. Skill Creator Responsibilities

`skill-creator` should be able to:

### Discover

Find whether an existing capability already solves the problem.

### Analyze

Determine the actual capability gap.

### Specify

Define:

```text
name
purpose
inputs
outputs
requirements
dependencies
constraints
security boundaries
verification criteria
failure modes
```

### Generate

Create the skill content.

### Compose

Combine existing skills rather than generating redundant ones.

### Validate

Test:

* correctness
* completeness
* applicability
* security
* ambiguity
* failure behavior
* interaction with other skills

### Version

Maintain:

```text
candidate
validated
active
deprecated
```

### Regress

Ensure a new skill doesn't break existing behavior.

---

# 9. Capability Architecture

Capabilities should be dynamically acquired.

```text
                    Capability Registry
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
          Existing      Discover       Create
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                       Validate
                           ↓
                       Compose
                           ↓
                         Use
```

A capability may come from:

* existing skill
* newly generated skill
* available tool
* external resource
* specialist
* model capability
* deterministic operation
* domain reference
* user-provided material

---

# 10. OS-Scale Example

For:

> Build an operating system.

`ultimate-dev` should recognize this as a **large program of work**, not one prompt.

Possible decomposition:

```text
OS PROJECT
│
├── Requirements
│
├── System Architecture
│
├── ISA / Hardware Assumptions
│
├── Boot Process
│
├── Bootloader
│
├── Kernel
│   ├── Memory Management
│   ├── Process Management
│   ├── Scheduling
│   ├── IPC
│   ├── Interrupts
│   ├── Device Model
│   └── System Calls
│
├── Drivers
│
├── Filesystem
│
├── Networking
│
├── Security
│
├── Runtime
│
├── User Space
│
├── Shell
│
├── Toolchain
│
├── Build System
│
├── Testing
│
├── Debugging
│
├── Documentation
│
└── Release / Packaging
```

But this decomposition is **not hard-coded into `ultimate-dev`**.

JEv derives the appropriate decomposition from the actual objective.

For a different operating system objective, the plan may be completely different.

---

# 11. Arbitrary Domain Architecture

The system must not have:

```text
if task == "medical":
    use medical-agent

if task == "finance":
    use finance-agent

if task == "OS":
    use os-agent
```

Instead:

```text
OBJECTIVE
    ↓
What must be known?
    ↓
What must be done?
    ↓
What capabilities are necessary?
    ↓
What capabilities exist?
    ↓
What capabilities are missing?
    ↓
Acquire / create
    ↓
Execute
    ↓
Verify
```

This makes the architecture domain-independent.

---

# 12. Adaptive Reasoning

Reasoning should scale dynamically:

```text
R0 — Immediate
     Simple deterministic task

R1 — Structured
     Moderate reasoning

R2 — Analytical
     Multi-step reasoning

R3 — Deep
     Complex dependencies / uncertainty

R4 — High Assurance
     Critical, novel, highly coupled or
     verification-heavy work
```

The system can move:

```text
R1 → R2 → R3
```

when reality becomes more complicated than expected.

Likewise:

```text
R3 → R1
```

when additional complexity is no longer justified.

---

# 13. Context Architecture

Context is treated as a managed resource.

```text
C0  Task
 ↓
C1  State
 ↓
C2  Capability Instructions
 ↓
C3  Targeted References
 ↓
C4  User / Project Material
 ↓
C5  External Evidence
 ↓
C6  Specialist / Deep Context
```

Never load everything by default.

The Context Compiler should:

```text
requirements
     ↓
retrieve
     ↓
rank
     ↓
filter
     ↓
dependency resolution
     ↓
deduplicate
     ↓
compress
     ↓
freshness check
     ↓
budget
     ↓
provenance
     ↓
final context
```

---

# 14. Execution Architecture

Execution must support:

```text
Sequential
Parallel
Conditional
Iterative
Recursive
Checkpointed
Interruptible
Recoverable
```

The plan is mutable.

New information can invalidate an assumption:

```text
Plan
 ↓
Execute
 ↓
Observe
 ↓
Unexpected result
 ↓
JEv
 ↓
Replan
 ↓
Continue
```

---

# 15. Verification Architecture

Verification must be proportional to:

```text
Risk
+
Consequence
+
Uncertainty
+
Novelty
+
Evidence quality
```

Therefore:

```text
Simple task
→ lightweight verification

Complex task
→ multi-stage verification

High-impact task
→ independent / redundant verification

Large engineering project
→ continuous verification + integration testing
```

---

# 16. Recovery Architecture

Failures become structured information.

```text
FAILURE
   ↓
CLASSIFY
   │
   ├── Missing Context
   ├── Wrong Capability
   ├── Wrong Strategy
   ├── Bad Assumption
   ├── Execution Failure
   ├── Resource Failure
   ├── Verification Failure
   └── Unsupported Objective
```

Then:

```text
Retry
Change Strategy
Acquire Context
Acquire Capability
Increase Reasoning
Reduce Scope
Replan
Escalate
Ask User
Stop
```

**Blind retry is prohibited.**

---

# 17. State Architecture

Every substantial task maintains conceptual state:

```text
RunState
│
├── task
├── objective
├── requirements
├── constraints
├── assumptions
├── unknowns
├── evidence
├── context
├── capabilities
├── skills
├── decisions
├── strategy
├── reasoning
├── plan
├── actions
├── observations
├── failures
├── verification
├── learning_candidates
├── budget
├── provenance
└── result
```

---

# 18. Evidence and Provenance

Important conclusions must be traceable.

```text
RESULT
  ↓
CLAIM
  ↓
EVIDENCE
  ↓
SOURCE
  ↓
TRANSFORMATION
  ↓
VERIFICATION
```

The system must distinguish:

```text
Known
Inferred
Assumed
Unverified
Uncertain
Contradicted
```

This is essential for a universal system operating across domains.

---

# 19. Security Model

The system must assume that external information can be hostile.

Untrusted content must not automatically become instructions.

Security boundaries include:

```text
User instruction
      ≠
Retrieved document
      ≠
External website
      ≠
Tool output
      ≠
Generated skill
      ≠
Trusted system policy
```

The kernel must defend against:

* prompt injection
* malicious documents
* malicious tool output
* capability poisoning
* fabricated evidence
* unauthorized actions
* credential exposure
* unsafe generated skills
* untrusted instructions
* accidental destructive operations

---

# 20. Human Control

Autonomy does not mean uncontrolled action.

The system should request confirmation when required by:

```text
high impact
irreversibility
sensitive information
ambiguous authorization
external side effects
financial consequences
destructive operations
security-sensitive operations
```

---

# 21. Self-Improvement

The system can improve, but not through uncontrolled rewriting.

```text
Experience
   ↓
Observation
   ↓
Signal
   ↓
Pattern
   ↓
Candidate Learning
   ↓
Validation
   ↓
JEv
   ↓
Promotion
```

One failed task must not permanently rewrite the system.

---

# 22. Scalability Model

The architecture must scale in **complexity**, not merely file count.

### Small task

```text
Task
 ↓
JEv
 ↓
Execute
 ↓
Verify
 ↓
Done
```

### Medium task

```text
Task
 ↓
Triage
 ↓
Context
 ↓
Capability
 ↓
Plan
 ↓
Execute
 ↓
Verify
```

### Complex task

```text
Task
 ↓
Decomposition
 ↓
Multiple work units
 ↓
Dynamic capabilities
 ↓
Parallel execution
 ↓
Integration
 ↓
Verification
 ↓
Recovery
```

### Massive project

```text
Program
│
├── Architecture
├── Subsystems
│   ├── Workstream
│   │   ├── Tasks
│   │   ├── Skills
│   │   ├── Evidence
│   │   └── Verification
│   └── ...
│
├── Integration
├── System Verification
├── Release
└── Continuous Learning
```

The **same kernel** operates at every level.

That is one of the most important properties of `ultimate-dev`.

---

# 23. Evaluation

Production readiness cannot be established by "it works on a few examples."

Evaluation must include:

### Task classes

```text
Simple
Medium
Complex
Ambiguous
Long-context
Multi-step
Cross-domain
Novel-domain
High-assurance
Failure-prone
```

### Metrics

```text
Task success
Correctness
Completeness
Reliability
Verification quality
Recovery effectiveness
Context efficiency
Reasoning efficiency
Capability efficiency
Cost
Latency
Learning effectiveness
Security robustness
```

### Comparison

Evaluate:

```text
Same model without ultimate-dev
             VS
Same model + ultimate-dev
```

The objective is to determine whether the architecture produces better outcomes/resource tradeoffs across representative workloads.

---

# 24. Production Maturity Levels

## Level 0 — Concept

Architecture defined.

## Level 1 — Functional Kernel

The kernel reliably performs:

```text
Task → Decide → Execute → Verify
```

## Level 2 — Adaptive Kernel

Adds:

```text
Dynamic context
Dynamic capabilities
Adaptive reasoning
Recovery
```

## Level 3 — Universal Kernel

Adds:

```text
Cross-domain operation
Skill creation
Capability composition
Deep verification
Learning
```

## Level 4 — Production System

Adds:

```text
Security
Provenance
Regression testing
Budget management
Reliability testing
Failure recovery
Observability
```

## Level 5 — Scalable Intelligence Platform

Adds:

```text
Large project execution
Hierarchical planning
Dynamic skill ecosystem
Continuous evaluation
Validated learning
Capability evolution
Large-scale coordination
```

---

# 25. MVP Acceptance Criteria

`ultimate-dev` is not MVP-ready until it can:

* correctly model arbitrary objectives
* distinguish simple vs complex tasks
* dynamically decide whether decomposition is useful
* dynamically retrieve context
* dynamically select capabilities
* detect capability gaps
* use `skill-creator`
* construct multi-step plans
* execute and observe work
* verify results
* recover from failures
* replan when assumptions fail
* maintain state
* track evidence
* respect trust boundaries
* avoid hallucinating tool/evidence results
* produce useful results without unnecessary orchestration

---

# 26. Production Acceptance Criteria

Production release additionally requires:

* broad cross-domain evaluation
* regression suite
* security testing
* adversarial testing
* failure recovery testing
* capability validation
* skill-generation validation
* evidence/provenance checks
* resource-budget controls
* deterministic-operation separation
* learning safety
* reproducible evaluation
* documented limitations
* robust behavior under incomplete information
* graceful handling of unsupported objectives
* no uncontrolled skill proliferation
* no uncontrolled learning
* no blind retry loops
* no unnecessary delegation

---

# 27. Final Architecture

The complete system can ultimately be understood as:

```text
                         ┌──────────────────────────┐
                         │       USER OBJECTIVE     │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       TASK MODEL         │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │          TRIAGE           │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────┐
                    │              JEv                    │
                    │         DECISION FABRIC             │
                    └──────┬────────┬────────┬───────────┘
                           │        │        │
                           ▼        ▼        ▼
                       CONTEXT  CAPABILITY STRATEGY
                           │        │        │
                           └────────┼────────┘
                                    ▼
                               REASONING
                                    │
                                    ▼
                                PLANNING
                                    │
                                    ▼
                               EXECUTION
                                    │
                                    ▼
                               OBSERVATION
                                    │
                                    ▼
                              VERIFICATION
                           ┌────────┴────────┐
                           │                 │
                           ▼                 ▼
                       VERIFIED           FAILURE
                           │                 │
                           │              RECOVERY
                           │                 │
                           │              REPLAN
                           │                 │
                           └────────┬────────┘
                                    │
                                    ▼
                               SYNTHESIS
                                    │
                                    ▼
                             SELF-EVALUATION
                                    │
                                    ▼
                                 LEARNING
                                    │
                                    ▼
                                   JEv
                                    │
                                    ▼
                                  RESULT
```

And when the kernel discovers that it lacks a capability:

```text
                  CAPABILITY GAP
                        │
                        ▼
                Existing Skill?
                  /          \
                YES           NO
                 │             │
              Reuse       Compose Existing?
                              /      \
                            YES       NO
                             │         │
                          Compose   Skill Creator
                                       │
                                       ▼
                                  Generate Candidate
                                       │
                                       ▼
                                    Validate
                                       │
                                       ▼
                                    Security
                                       │
                                       ▼
                                     Test
                                       │
                                       ▼
                                      JEv
                                       │
                              ┌────────┴────────┐
                              ▼                 ▼
                           Promote           Reject
                              │
                              ▼
                         New Capability
                              │
                              ▼
                             JEv
```

That gives us the fundamental product:

> **`ultimate-dev` is a universal adaptive cognitive kernel that can acquire, create, compose, execute, verify, recover, and learn whatever capabilities are necessary to solve an objective—without requiring the architecture to know every domain in advance.**

And `skill-creator` is not a side utility. It is the **controlled capability-expansion mechanism** that lets the system grow beyond the skills initially shipped with it.

The important constraint is that **"OS-scale capable" should mean the architecture can manage and solve the work through decomposition, acquisition, execution, integration, and verification—not that a single model magically generates an entire operating system in one pass.** That distinction is what makes the design technically credible and scalable.


Exactly. **“Build an OS” is the stress-test metaphor, not a literal product requirement.**

The requirement should be:

> If `ultimate-dev` can reliably handle an extremely complex, unfamiliar, long-horizon, multi-domain engineering problem such as building an operating system, then its architecture is strong enough to generalize to most other difficult problem classes.

So the PRD should frame OS-building as a **capability benchmark**, not as the product's primary purpose.

### Revised core requirement

```text
ULTIMATE-DEV
     │
     │  Must handle
     ▼
┌─────────────────────────────────────────────┐
│ EXTREME PROBLEM COMPLEXITY                  │
│                                             │
│ • enormous scope                            │
│ • many dependencies                         │
│ • unfamiliar domain                         │
│ • incomplete information                    │
│ • long execution horizon                    │
│ • changing requirements                     │
│ • multiple capabilities                     │
│ • multiple verification layers              │
│ • failures and recovery                     │
│ • cross-domain reasoning                    │
│ • high uncertainty                          │
│ • substantial context                       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
                 ULTIMATE-DEV
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    DISCOVER         REASON          EXECUTE
       │               │                │
       ▼               ▼                ▼
    ACQUIRE          PLAN           OBSERVE
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                   VERIFY
                       │
                ┌──────┴──────┐
                ▼             ▼
             SUCCESS       RECOVER
                              │
                              ▼
                            REPLAN
```

### The actual ambition

`ultimate-dev` should be designed for problems ranging roughly from:

```text
Level 1
Simple question / transformation

        ↓

Level 2
Multi-step task

        ↓

Level 3
Complex professional task

        ↓

Level 4
Large multi-domain project

        ↓

Level 5
Novel research / engineering problem

        ↓

Level 6
Extremely complex long-horizon problem

        ↓

Level 7
OS-scale / civilization-scale complexity
```

The kernel shouldn't have a special `"Level 7 = OS"` mode.

It should use the **same fundamental machinery** at every level, with more resources, deeper planning, stronger verification, and more sophisticated capability composition as complexity increases.

### Therefore, the strongest product definition is

> **`ultimate-dev` is a universal adaptive problem-solving skill designed to handle arbitrary objectives—from simple tasks to extremely complex, unfamiliar, long-horizon, multi-domain problems—by dynamically acquiring context and capabilities, selecting appropriate strategies and reasoning depth, executing and verifying work, recovering from failure, and learning from validated experience.**

And the architecture should be judged against the question:

> **“Can this kernel scale from a trivial task to the hardest class of problems without requiring a completely different architecture?”**

If the answer is yes, then we've actually built the **universal kernel** you're aiming for.

That also means I would rename some of the PRD language from **“OS-scale execution”** to **“extreme-complexity execution”**, with OS construction listed as one representative benchmark rather than the defining use case.
