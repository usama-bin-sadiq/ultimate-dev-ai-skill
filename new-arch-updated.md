# Universal Agent — Complete Architecture (revised)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      UNIVERSAL AGENT                                           │
│                         Adaptive, Context-Efficient Problem-Solving Kernel                     │
│                                                                                              │
│                                    revision 2 — coordination modes                             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

This is `new-arch.md` with the four multi-agent coordination patterns unified into one
decision fabric. What changed, and why it is here rather than as an edit to the original:

`new-arch.md` already contained two of the four patterns — **skills** (its context ladder
and its core principle) and **subagents** (its Agent/Specialist Model). It did not contain
**router** or **handoffs**, and it ruled the second out in a box: *"Agents are NOT the
architecture."*

Revision 2 keeps that claim but narrows it. JEv still decides every mode change; what changes
is that a decision may now hand conversational authority to a specialist, and may declare
that a query needs several sources synthesised rather than one capability retrieved.

**What this revision does not do.** It does not add durability. All four patterns coordinate
within a live context window. `RunState` is still specified and still unimplemented, so the
L4+ claims in the scale ladder remain aspirational. See `## The honest limits` at the end.

---

## 0. INPUT / OBJECTIVE

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  0. INPUT / OBJECTIVE                                                                          │
│                                                                                              │
│  User Objective → Request → Constraints → Desired Outcome → Available Resources              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 1. TASK MODEL

```text
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
```

## 2. TRIAGE

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  2. TRIAGE / COMPLEXITY ASSESSMENT                                                             │
│                                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐               │
│  │ Complexity │ │ Risk       │ │ Uncertainty│ │ Time/Cost  │ │ Consequence  │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────────┘               │
│                                              │                                               │
│                         Determine minimum sufficient effort                                  │
└──────────────────────────────────────────────────────────────────────────────┬───────────────┘
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
║  │ COORDINATION MODE ◄── NEW IN REVISION 2                                                │  ║
║  └────────────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                              ║
║  COORDINATION MODE is one of: inline · delegate · route · handoff                           ║
║  It is recorded like any other field, so a mode change is reviewable. See stage 4.           ║
║                                                                                              ║
║  JEv DECIDES:                                                                                ║
║  • What to do                                                                                ║
║  • What NOT to do                                                                            ║
║  • What information is needed                                                                 ║
║  • Which capabilities are required                                                            ║
║  • Which strategy is appropriate                                                              ║
║  • How much reasoning is justified                                                            ║
║  • How results are coordinated      ◄── NEW                                               ║
║  • Whether to delegate                                                                        ║
║  • Whether to parallelize                                                                     ║
║  • How deeply to verify                                                                       ║
║  • Whether to retry / replan / escalate                                                       ║
║  • Whether conversational authority moves  ◄── NEW                                          ║
║  • Whether new learning should be retained                                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

## 4. COORDINATION MODE SELECTION  ← new in revision 2

The four patterns are not four architectures. They are four answers to one question asked
before capability selection: **how do the results of this task come back together?**

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  4. COORDINATION MODE SELECTION                                                                │
│                                                                                              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐              │
│  │ ① INLINE      │   │ ② DELEGATE    │   │ ③ ROUTE       │   │ ④ HANDOFF     │              │
│  │               │   │               │   │               │   │               │              │
│  │ load C0→C6    │   │ JEv calls a   │   │ decompose the │   │ set           │              │
│  │ into this     │   │ stateless     │   │ query, run N  │   │ active_agent  │              │
│  │ agent         │   │ specialist    │   │ in parallel,  │   │ so another    │              │
│  │               │   │ as a tool     │   │ synthesize    │   │ agent holds   │              │
│  │ same agent    │   │               │   │               │   │ the thread    │              │
│  │ no extra call │   │ +1 call       │   │ N calls       │   │ authority     │              │
│  │               │   │ results ret-  │   │ stateless     │   │ moves         │              │
│  │ CONTEXT       │   │ urn via JEv   │   │               │   │               │              │
│  │ ACCUMULATES   │   │               │   │ PARALLEL      │   │ STATEFUL     │              │
│  │               │   │ ISOLATED CTX  │   │               │   │               │              │
│  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘              │
│          │                   │                   │                   │                      │
│          └───────────────────┴───────────────────┴───────────────────┘                      │
│                                              │                                               │
│                                              ▼                                               │
│                          selected mode becomes RunState.coordination                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The selection test

```text
   Is one capability enough, and is it in context already?
        └─ yes ──────────────────────────────────► ① INLINE

   Does the work need a specialist whose context must NOT
   pollute this one, and can it report back in one result?
        └─ yes ──────────────────────────────────► ② DELEGATE

   Does the question span several sources or domains whose
   answers must be merged into one?
        └─ yes ──────────────────────────────────► ③ ROUTE

   Must one party hold the conversation across stages, with
   capabilities unlocking as information arrives?
        └─ yes ──────────────────────────────────► ④ HANDOFF
```

**The order matters and it is cheapest-first.** ① costs nothing extra. ② costs a call but
buys context isolation. ③ costs calls and buys parallelism. ④ costs state management and buys
a conversation that can be staged. Choosing ④ when ① would do is the expensive mistake, and
it is the one a system without the `coordination` field will make silently, because nothing
records that the cheaper option was available.

### ① INLINE — progressive disclosure

```text
   ┌──────────────┐
   │  kernel      │
   │  SKILL.md    │◄── always loaded
   └──────┬───────┘
          │ C2: the procedure for the unit in hand
          ▼
   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
   │ skill A      │      │ skill B      │      │ skill C      │
   │ (loaded)     │      │ (loaded)     │      │ (loaded)     │
   └──────────────┘      └──────────────┘      └──────────────┘
          └──────────────────┬──────────────────┘
                             ▼
                   all accumulate in one context
```

Best when: one agent, many possible specialisations, no constraint to enforce between them.

The cost, stated honestly: **loaded skills accumulate in conversation history.** In a corpus
of 2,113 skills this is the dominant cost, and it is why ③ exists as a mitigation rather than
an alternative.

### ② DELEGATE — centralized orchestration

```text
                    ┌─────────────────────────┐
                    │  kernel / JEv           │
                    │  holds the context      │
                    └───────────┬─────────────┘
             ┌──────────────┬───┴───────┬──────────────┐
             ▼              ▼           ▼              ▼
        ┌─────────┐   ┌─────────┐ ┌─────────┐   ┌─────────┐
        │spec 1   │   │spec 2   │ │spec 3   │   │spec 4   │
        │stateless│   │stateless│ │stateless│   │stateless│
        │own ctx  │   │own ctx  │ │own ctx  │   │own ctx  │
        └────┬────┘   └────┬────┘ └────┬────┘   └────┬────┘
             └──────────────┴───┬───────┴──────────────┘
                                ▼
                          results return to JEv
```

Best when: distinct domains, centralised control, specialists need not talk to the user.

The cost, stated honestly: **one extra model call per interaction**, because every result
must route back through the main agent.

### ③ ROUTE — parallel dispatch and synthesis

```text
                    ┌─────────────────────────────┐
                    │  ROUTER  (stateless)        │
                    │  classify + decompose       │
                    └──────────────┬──────────────┘
        ┌──────────────┬───────────┼───────────┬──────────────┐
        ▼              ▼           ▼           ▼              ▼
   ┌─────────┐   ┌─────────┐ ┌─────────┐ ┌─────────┐   ┌─────────┐
   │vertical │   │vertical │ │vertical │ │vertical │   │vertical │
   │    A    │   │    B    │ │    C    │ │    D    │   │    E    │
   └────┬────┘   └────┬────┘ └────┬────┘ └────┬────┘   └────┬────┘
        └──────────────┴───────────┴───────────┴──────────────┘
                              │  in parallel
                              ▼
                    ┌─────────────────────────────┐
                    │  SYNTHESIZE                 │
                    │  one coherent response      │
                    └─────────────────────────────┘
```

Best when: distinct verticals, queries spanning several sources, one merged answer needed.

The costs, stated honestly: **stateless**, so a repeat request pays the classification again;
and **no multi-hop**, because a router does not chain. Both are why the mode belongs in a
record: a recorded `coordination: route` with a `recovery` condition is what lets a repeat
skip the classification rather than repeat it by default.

### ④ HANDOFF — state-driven transfer of authority

```text
   ┌──────────────┐   handoff    ┌──────────────┐   handoff   ┌──────────────┐
   │  agent A     │─────────────►│  agent B     │────────────►│  agent C     │
   │  active      │              │  active      │             │  active      │
   │              │◄─────────────│              │◄────────────│              │
   └──────────────┘   returns    └──────────────┘   returns   └──────────────┘
          │                                                            │
          └──────────────── state survives every turn ────────────────┘

   RunState.active_agent   : who holds the conversation right now
   RunState.authority      : inline | delegated
```

Best when: a staged conversation, where capabilities must unlock only after earlier
information arrives, and the user is talking throughout.

The cost, stated honestly: **the most stateful of the four.** It requires the most careful
state management, and it is the only mode where the wrong choice is expensive in a way that
compounds — a handoff that should not have happened fragments the thread.

**Why this does not abandon the fabric.** The active agent changes; the decider does not. A
handoff is an ordinary JEv record whose `coordination` field happens to be `handoff` and whose
effect is to write `active_agent`. Control never leaves JEv.

```text
   ┌──────────────────────────────────────────────────────────────────────┐
   │  REVISION 1 said:                                                    │
   │      "Agents are NOT the architecture."                              │
   │                                                                      │
   │  REVISION 2 says:                                                    │
   │      Agents are not the architecture.                                 │
   │      JEv is — including when it hands off.                           │
   │                                                                      │
   │  The specialist still has no workflow of its own. It cannot triage,  │
   │  verify, or recover. It answers, and JEv decides what happens next.  │
   └──────────────────────────────────────────────────────────────────────┘
```

## 5. CONTEXT COMPILER

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  5. CONTEXT COMPILER                                                                           │
│  Unchanged from revision 1. Applies in full for mode ①, and supplies the working context   │
│  for ②③④ — a delegate's context is compiled, then handed over.                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 6. CAPABILITY SYSTEM

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  6. CAPABILITY SYSTEM                                                                          │
│                                                                                              │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐          │
│  │ CAPABILITY     │   │ CAPABILITY     │   │ STRATEGY       │   │ EFFORT         │          │
│  │ REQUIREMENTS   │   │ REQUIREMENTS   │   │ CANDIDATES     │   │ SELECTION      │          │
│  │                │   │                │   │                │   │                │          │
│  │ What do we     │   │ What can solve │   │ Which solving  │   │ How much       │          │
│  │ actually need? │   │ this problem?  │   │ approach?      │   │ reasoning?     │          │
│  └───────┬────────┘   └───────┬────────┘   └───────┬────────┘   └───────┬────────┘          │
│          │                    │                    │                    │                   │
│          ▼                    ▼                    ▼                    ▼                   │
│  Retrieval              Existing              Direct             R0 Minimal                 │
│  Selection              Capabilities          Decomposition      R1 Structured               │
│  Ranking                Discovery             Sequential         R2 Analytical               │
│  Compression            Acquisition           Parallel           R3 Deep                     │
│  Budgeting              Composition           Research-first     R4 Assurance                │
│  Provenance             Validation            Evidence-first     Escalation on demand         │
│                         Creation ← NEW                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Gated on reachability.** A specialist is only selectable if the kernel can actually route
to it. This is not a formality: a library of domain specialists with overlapping descriptions
means the wrong one is chosen as often as the right one, and the failure looks like
incompetence rather than misconfiguration. A mode that *selects* specialists by description
makes that worse, not better, unless unreachability is enforced first.

## 7. STRATEGY SELECTION

```text
   Direct · Decomposition · Sequential · Parallel · Iterative ·
   Research-first · Evidence-first · Experiment-driven
```

## 8. REASONING CONTROL

```text
   R0 Minimal · R1 Structured · R2 Analytical · R3 Deep · R4 Assurance
   Escalation on demand
```

## 9. EXECUTION PLAN

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  9. EXECUTION PLAN                                                                             │
│                                                                                              │
│  Objective → Steps → Dependencies → Preconditions → Actions → Expected Results → Checks      │
│                                                                                              │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐             │
│  │ Atomic Work Units   │────▶│ Dependency Graph    │────▶│ Execution Schedule  │             │
│  └─────────────────────┘     └─────────────────────┘     └─────────────────────┘             │
│                                                                                              │
│  JEv can dynamically modify the plan whenever new evidence changes the situation.            │
│  A mode change mid-run is a plan change, and is recorded as one.                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 10. EXECUTION

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  10. EXECUTION / PROBLEM SOLVING                                                               │
│                                                                                              │
│  The Executor has three shapes now, selected by the coordination mode:                        │
│                                                                                              │
│  ① INLINE      EXECUTOR ─────────────────────────────────────────────┐                       │
│                Reason · Transform · Investigate · Analyze ·           │                       │
│                Create · Experiment · Research · Synthesize · Implement │                       │
│                                                                                              │
│  ② DELEGATE    EXECUTOR ──▶ spec₁ ─┐                                  │                       │
│                              spec₂ ─┼──▶ results ──▶ EXECUTOR         │                       │
│                              specₙ ─┘                                  │                       │
│                                                                                              │
│  ③ ROUTE       ROUTER ──▶ vertical₁ ─┐                                │                       │
│                          vertical₂ ─┼──▶ SYNTHESIZER ──▶ EXECUTOR    │                       │
│                          verticalₙ ─┘        (in parallel)            │                       │
│                                                                                              │
│  ④ HANDOFF     agent A ──handoff──▶ agent B ──handoff──▶ agent C     │                       │
│                (authority moves; JEv decides each move)              │                       │
│                                                                                              │
│  In all four shapes, EXECUTOR returns to JEv. ─────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 11. OBSERVATION

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  11. OBSERVATION                                                                               │
│                                                                                              │
│  Action → Result → State Change → Evidence → Error → Unexpected Information                  │
│                                                                                              │
│  Every meaningful execution updates the internal run state, including coordination            │
│  and, in mode ④, the active agent.                                                             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 12. VERIFICATION

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  12. VERIFICATION                                             ║
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
║                    │                │                │                                       ║
║                    │                ▼                ▼                                       ║
║                    │        ┌──────────────┐  ┌──────────────┐                                 ║
║                    │        │ More Context │  │   RECOVERY   │                                 ║
║                    │        │ / Reasoning  │  │              │                                 ║
║                    │        └──────┬───────┘  └──────┬───────┘                                 ║
║                    │               │                 │                                        ║
║                    │               └────────┬────────┘                                        ║
║                    │                        ▼                                                 ║
║                    │                 ┌──────────────┐                                           ║
║                    │                 │     JEv      │                                           ║
║                    │                 │ Re-decision  │                                           ║
║                    │                 └──────┬───────┘                                           ║
║                    │                        │                                                  ║
║                    │             ┌──────────┼───────────┐                                      ║
║                    │             ▼          ▼           ▼                                      ║
║                    │          Retry      Replan     Escalate                                    ║
║                    │             │     ┌────┴────┐      │                                      ║
║                    │             │     │ Change  │      │                                      ║
║                    │             │     │  mode   │◄─────┘  ◄── NEW                           ║
║                    │             │     └─────────┘                                             ║
║                    │             └──────────┴───────────┘                                      ║
║                    │                        │                                                  ║
║                    │                        ▼                                                  ║
║                    │                  EXECUTION LOOP                                            ║
║                    ▼                                                                           ║
║              DELIVER                                                                           ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

**Recovery may change the coordination mode.** A delegate that fails twice, where a route
would have covered the ground, is a mode error rather than a capability error. Recording the
mode change makes that reviewable instead of invisible.

## 13. RESULT SYNTHESIS

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  13. RESULT SYNTHESIS                                                                          │
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
│  • Coordination mode used, and whether it changed mid-run  ◄── NEW                           │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 14. SELF-EVALUATION

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  14. SELF-EVALUATION                                                                           │
│                                                                                              │
│  Did we solve the task?                                                                        │
│  Did we use unnecessary context?                                                               │
│  Was reasoning sufficient?                                                                     │
│  Was the strategy effective?                                                                   │
│  Were capabilities appropriate?                                                                │
│  Was verification sufficient?                                                                  │
│  Did the coordination mode fit, or did we pay for isolation we did not need?  ◄── NEW        │
│  What failed?                                                                                  │
│  What could be reused?                                                                         │
│  What should NOT be repeated?                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

The mode question is the waste-catcher for this revision. Loading four skills to answer a
one-line question, or handing off a thread that one agent could have held, is cost paid for
isolation nobody needed — and it is invisible without a question that asks for it.

## 15. LEARNING SYSTEM

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  15. LEARNING SYSTEM                                          ║
║                                                                                              ║
║  EXPERIENCE → OBSERVATION → SIGNAL EXTRACTION → PATTERN/CANDIDATE                            ║
║                                              │                                               ║
║                                              ▼                                               ║
║                                         EVALUATION                                           ║
║                                              │                                               ║
║                                              ▼                                               ║
║                                         VALIDATION                                           ║
║                                              │                                               ║
║                                              ▼                                               ║
║                                       JEv DECISION                                            ║
║                                              │                                               ║
║                        ┌─────────────────────┴──────────────────────┐                        ║
║                        ▼                                            │                        ║
║                     PROMOTE                                         Reject                   ║
║                        │                                            │                        ║
║                        ▼                                            │                        ║
║               REUSABLE KNOWLEDGE                                     │                        ║
║                        │                                            │                        ║
║                        │  A promoted pattern may include a            │                        ║
║                        │  COORDINATION MODE: "route when the          │                        ║
║                        ▼  question spans three sources."             │                        ║
║                Future Retrieval ◄────────────────────────────────────┘                        ║
║                                                                                              ║
║  states: OBSERVED → CANDIDATE → VALIDATING → VALIDATED → PROMOTED → DEPRECATED               ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

## 16. RunState

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  16. RUN STATE                                                                                │
│                                                                                              │
│  Revision 2 adds two fields. Both exist to make a coordination change reviewable after the   │
│  fact rather than invisible during it.                                                        │
│                                                                                              │
│  ┌──────────────────────────────┐   ┌──────────────────────────────┐                         │
│  │ coordination                 │   │ active_agent                 │                         │
│  │ inline|delegate|route|       │   │ who currently holds the      │                         │
│  │ handoff                      │   │ conversation                 │                         │
│  │                              │   │                              │                         │
│  │ mode, with the condition     │   │ authority:                   │                         │
│  │ that would change it         │   │ inline | delegated           │                         │
│  └──────────────────────────────┘   └──────────────────────────────┘                         │
│                                                                                              │
│  UNCHANGED, AND STILL UNIMPLEMENTED. This is the honest limit of revision 2.                  │
│  A coordination mode coordinates within a live context. It does not survive one.              │
│  Every field above is lost when the context window closes, because no tool reads or writes   │
│  any of them. The L4+ rows of the scale ladder depend on this structure existing.             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
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
│  │  ▲ now carries   │   │  ▲ must charge   │   │                  │   │                  │  │
│  │  coordination    │   │  per mode: ① no  │   │                  │   │                  │  │
│  │  and active_agent│   │  cost, ② +1 call │   │                  │   │                  │  │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘  │
│                                                                                              │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Observability    │   │ Cache / Reuse    │   │ Policy /         │   │ Error /          │  │
│  │                  │   │                  │   │ Constraints       │   │ Recovery State   │  │
│  │  ▲ must record   │   │                  │   │                  │   │                  │  │
│  │  mode changes    │   │                  │   │                  │   │  ▲ may revert   │  │
│  │                  │   │                  │   │                  │   │  the mode        │  │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘  │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                             │
                             ▼
                  ALL DECISION / EXECUTION LAYERS
```

The Budget Manager is where the modes are actually priced, and the prices are not equal:

```text
   ① INLINE     0 extra calls          · context accumulates in history
   ② DELEGATE   +1 call per result     · results route back through JEv
   ③ ROUTE      N calls, parallel      · stateless, so repeats re-pay
   ④ HANDOFF    stateful               · most expensive to get wrong
```

## Context Architecture

Unchanged from revision 1. The C0–C6 ladder is mode ①'s mechanism, and it supplies the
compiled context that ②③④ receive.

```text
C0 ── Task
 ▼
C1 ── Task Metadata / State            ◄── carries coordination + active_agent
 ▼
C2 ── Required Capability Instructions
 ▼
C3 ── Targeted References / Knowledge
 ▼
C4 ── User / Project Material
 ▼
C5 ── External Evidence
 ▼
C6 ── Specialist / Deep Context
```

## Decision Boundaries

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      JEv BOUNDARIES                                            │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Task Understanding ────────────────► JEv                                                     │
│  COORDINATION MODE ─────────────────► JEv  ◄── NEW IN REVISION 2                             │
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
│  18 boundaries. Revision 1 named 17 and folded workflow selection into capability            │
│  resolution order. Revision 2 adds coordination mode as its own boundary, because it is the  │
│  one choice that determines whether the other seventeen are even reachable.                    │
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
                                      │    DECIDE    │◄── coordination mode chosen here
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
                                      │   EXECUTE    │◄── in the selected shape
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   OBSERVE    │
                                      └──────┬───────┘
                                             ▼
                                      ┌──────────────┐
                                      │   VERIFY     │
                                      └──────┬──────┘
                                      ┌──────┴──────┐
                                      ▼             ▼
                                ┌───────────┐  ┌────────────┐
                                │ DELIVER   │  │  RECOVER   │
                                └─────┬─────┘  └─────┬──────┘
                                      │              │
                                      │              └──────► JEv
                                      ▼                      (may change mode)
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
│  ── revision 2 adds ─────────────────────────────────────────────────────────────────────    │
│                                                                                              │
│                    AND CHOOSE THE CHEAPEST COORDINATION THAT THE TASK ACTUALLY NEEDS.         │
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
                         │  Coordination Mode  ◄── NEW   │
                         │       ↓                       │
                         │  Context + Capability         │
                         │       ↓                       │
                         │  Strategy + Reasoning         │
                         │       ↓                       │
                         │  Execution  (4 shapes) ◄── NEW│
                         │       ↓                       │
                         │  Observation                  │
                         │       ↓                       │
                         │  Verification                 │
                         │       ↓                       │
                         │  Recovery  (may re-mode) ◄ NEW│
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

## The honest limits

Four things this revision does not do, stated here so they are not discovered later:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  1. NO DURABILITY.  All four modes coordinate inside a live context window. None of them   │
│     survives one closing. RunState is specified in stage 16 and implemented nowhere: no     │
│     tool reads or writes it. The L4+ rows of the scale ladder — multi-domain project,       │
│     large programme, long-horizon — depend on that structure existing.                        │
│                                                                                              │
│  2. NO PARALLELISM YOU CAN RELY ON.  Mode ③ parallelises within one context. It is not      │
│     distributed execution, and it has no failure isolation: one specialist that hangs       │
│     holds the synthesis.                                                                      │
│                                                                                              │
│  3. THE COST PROBLEM IS MITIGATED, NOT SOLVED.  Mode ① is the cheapest per call and the   │
│     most expensive per unit of work, because loaded skills accumulate in history. In a      │
│     corpus of this size that is the dominant cost. Mode ③ is the mitigation. The honest     │
│     consequence is that some capabilities will have to stop being skills and become         │
│     delegates — which is a content decision this architecture cannot make for you.          │
│                                                                                              │
│  4. MORE SPECIALISTS IS A TRAP.  Adding a mode that selects specialists by description      │
│     sharpens the trigger-signal problem rather than solving it. Thirty overlapping           │
│     descriptions means the wrong specialist is chosen as often as the right one, and the     │
│     failure presents as incompetence rather than misconfiguration. Selection must stay       │
│     gated on reachability, or mode ④ will select badly and confidently.                      │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```
