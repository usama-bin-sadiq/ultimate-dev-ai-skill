# Ultimate-Dev — Canonical Architecture

> A prompt-first skill with an optional durable runtime.
> One contract. One gate. Two implementations.

```text
╔══════════════════════════════════════════════════════════════════════╗
║  THE PRINCIPLE                                                      ║
║                                                                      ║
║  A model decides.  A runtime remembers, and refuses.                 ║
║                                                                      ║
║  Neither replaces the other.  Absence is declared, never assumed.    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## The Format Rule

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   .md   .yml      WHAT A HUMAN READS OR AUTHORS                      │
│                                                                      │
│                    method · decision rule · contract · config        │
│                    editable by a person, reviewable by a person       │
│                                                                      │
│   ───────────────────────────────────────────────────────────────    │
│                                                                      │
│   .py   .mjs      WHAT A MACHINE EXECUTES                            │
│                                                                      │
│                    algorithm · enforcement · orchestration           │
│                    not authored by editing text                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

WHY THE SPLIT EXISTS

  A method that computes something cannot be expressed as prose.
  A rule that a person must judge cannot be expressed as code.

  Mixing them produces two failures:
    · prose that pretends to enforce     → not enforced
    · code that encodes a judgement      → unchangeable without a developer

  Keeping them apart makes each one honest about what it is.

  MD/YAML IS AUTHORITATIVE.  PY/MJS IS DERIVED FROM IT.
  A contract that code contradicts is a bug the doctor reports.
```

---

## The Two Planes

```text
╔══════════════════════════════════════════════════════════════════════╗
║  PLANE A — PROMPT CORE                                               ║
║                                                                      ║
║  .md + .yml only        no code        no dependencies                ║
║                                                                      ║
║  PURPOSE    be the product on its own, on any host, with nothing      ║
║             installed                                                   ║
║  FUNCTION   carry every judgement: what good looks like, what to      ║
║             check, when to stop, what may be claimed                  ║
║  REACH      a host with no runtime, no network, no package manager    ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║  PLANE B — DURABLE RUNTIME                    optional extension      ║
║                                                                      ║
║  .py + .mjs             host supplies tools and the model            ║
║                                                                      ║
║  PURPOSE    make work survive a session, and make claims checkable    ║
║  FUNCTION   keep state, schedule work, gate effects, prove outcomes  ║
║  REACH      long-running, resumable, multi-agent, auditable work     ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Plane A — Layers

```text
┌──────────────────────────────────────────────────────────────────────┐
│ L1  ENTRY                                                            │
│                                                                      │
│   PURPOSE   become active and be believed present                    │
│   FUNCTION   state activation, precedence, session start             │
│   FORM      AGENTS.md · SKILL.md · AGENT.md                          │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L2  DETECTION                                                       │
│                                                                      │
│   PURPOSE   know which plane this host is in                         │
│   FUNCTION   probe capabilities; choose evidence grade               │
│   FORM      a probe script + a required field in the status block    │
│   WHY       an undeclared capability surfaces as a crash, not a gap  │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L3  ROUTING                                                          │
│                                                                      │
│   PURPOSE   turn an objective into the smallest sufficient structure  │
│   FUNCTION   classify deliverable, size, risk; select pattern        │
│   FORM      router/ rule documents + config/capability-index.yaml    │
│   RULE      a common method before a specialist, always              │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L4  METHOD                                                          │
│                                                                      │
│   PURPOSE   carry reusable ways of working                           │
│   FUNCTION   skills/ = method · agents/ = role · modules/ = knowledge │
│   FORM      Markdown only                                            │
│   RULE      load only what the task requires, never the whole library│
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L5  CONTRACT                                                        │
│                                                                      │
│   PURPOSE   one vocabulary both planes speak                         │
│   FUNCTION   INTENT · KNOWLEDGE · ACTION · EVIDENCE                 │
│   FORM      contracts/*.yaml                                         │
│   RULE      portable; must not require the runtime to be read        │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L6  ACTING                                                          │
│                                                                      │
│   PURPOSE   change the outside world                                │
│   FUNCTION   the model uses host tools; the host runs the model      │
│   FORM      host capability, outside both planes                    │
│   RULE      a claimed change is not yet an observed change           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Plane B — Layers

```text
┌──────────────────────────────────────────────────────────────────────┐
│ L1  DECISION                                                         │
│                                                                      │
│   PURPOSE   choose among alternative paths                           │
│   FUNCTION   weigh safety, objective, complexity; return a packet    │
│   FORM      engine.mjs — pure, deterministic, no I/O                 │
│   RULE      recommends only; never grants authority                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼  decision packet, produced by the host
┌──────────────────────────────────────────────────────────────────────┐
│ L2  STATE                                                            │
│                                                                      │
│   PURPOSE   make work survive beyond one conversation                │
│   FUNCTION   four channels, versioning, provenance, checkpoints     │
│   FORM      state.py                                                 │
│   RULE      state is authoritative over what a model remembers       │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L3  ORCHESTRATION                                                    │
│                                                                      │
│   PURPOSE   the single place work is sequenced                       │
│   FUNCTION   build a graph, order it, parallelise, gate, cancel      │
│   FORM      task_graph.py + contracts/task-graph.yaml               │
│   RULE      one orchestrator; every mode is a graph shape            │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L4  ABILITY                                                          │
│                                                                      │
│   PURPOSE   separate permission from capability                     │
│   FUNCTION   policy.py = may it?   capabilities.py = can it?        │
│   FORM      policy.py · capabilities.py                             │
│   RULE      never name a vendor tool directly; request a capability  │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L5  EXECUTION GATE                                                   │
│                                                                      │
│   PURPOSE   make a claimed effect provable                           │
│   FUNCTION   stamp an observation; grade it; refuse completion       │
│   FORM      attestation.py                                          │
│   RULE      only the runtime may attest; absence is detected         │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L6  EVIDENCE + VERIFICATION                                         │
│                                                                      │
│   PURPOSE   decide whether the objective was actually met            │
│   FUNCTION   record provenance, inspect evidence, issue a verdict    │
│   FORM      verification.py + the evidence ledger in state           │
│   RULE      a verdict is derived from evidence, never from confidence │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L7  RECOVERY + LEARNING                                              │
│                                                                      │
│   PURPOSE   continue after failure, and improve without guessing     │
│   FUNCTION   diagnose, replan, checkpoint, stage a candidate         │
│   FORM      lifecycle.py · evolution.py · memory.py · retention.py   │
│   RULE      a failure re-enters the decision layer, not a retry loop │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Gate

```text
                        ONE GATE, TWO GRADES

        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
   PROMPT CORE                                    DURABLE RUNTIME
   no runtime detected                            runtime detected
        │                                               │
   produces claims                                produces observations
        │                                               │
        └───────────────────────┬───────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │      ATTESTATION      │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
    SELF_REPORTED            no effect              TOOL_ATTESTED
        │                  (read-only work)               │
        ▼                       │                          ▼
   PROVISIONAL              PROVISIONAL               ATTESTED
   may NOT complete         may NOT complete          MAY complete
```

---

## Flow

```text
   OBJECTIVE
      │
      ▼
   DETECT ──────────────► absent capability ──► declare the gap
      │                                            report not_run
      ▼
   DECIDE ──────────────► human review ──────► ask, do not guess
      │                              deny
      ▼
   PLAN ────────────────► graph: nodes, edges, order, gates
      │
      ▼
   SELECT ──────────────► method · role · capability
      │
      ▼
   ACT ─────────────────► host runs the effect
      │
      ▼
   OBSERVE ─────────────► the runtime records what came back
      │
      ▼
   GATE ────────────────► no observation ──► refuse to call it done
      │
      ▼
   VERIFY ──────────────► evidence, not confidence
      │
      ├──── met ──────────► COMPLETE  (attested only)
      │
      └──── not met ──────► DECIDE again ──► recover · replan · ask
```

---

## Invariants

```text
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   ONE ORCHESTRATOR      every mode lowers to one graph               │
│                                                                      │
│   ONE GATE              two grades, one decision                     │
│                                                                      │
│   CLAIMED ≠ OBSERVED   a report is not a record                      │
│                                                                      │
│   REQUESTED ≠ EXECUTED asking for a capability is not having it      │
│                                                                      │
│   ASSUMED ≠ DETECTED   absence is probed, never inferred             │
│                                                                      │
│   NO PROVIDER CLIENT   the host's model is the only intelligence      │
│                                                                      │
│   NO MODEL NAMES       capabilities, never vendor strings            │
│                                                                      │
│   MD/YAML AUTHORITATIVE   the code implements, it does not define    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Why Two Planes and Not One

```text
   MERGING THEM WOULD REQUIRE

     · a mandatory interpreter on every host          → breaks portability
     · the reasoning model to run inside our process   → duplicates the host
     · a provider client inside the runtime           → reads the user's keys
     · one component to trust for judgement and state → couples them

   KEEPING THEM SPLIT COSTS

     · two implementations of one contract            → the price paid
     · a handshake between them                       → detection, §0

   THE SPLIT IS THE FEATURE
   The runtime is optional; the honesty is not.
```
