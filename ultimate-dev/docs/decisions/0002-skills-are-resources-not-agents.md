# 0002. Skills are resources, not agents

Status: Accepted
Date: 2026-09-26
Deciders: architecture maintainers

## Context

The kernel has to work on domains it has never seen. There are two obvious ways
to get capability into an unfamiliar domain, and the industry has largely picked
different ones at different times.

The first is a **library of domain agents**: a finance agent, a security agent, a
scientific-writing agent, each with its own prompt, its own tools, and its own
partial workflow. The user or a router picks one. This is how the 2023 to 2025
agent ecosystem grew, and it delivers capability quickly for domains that were
anticipated.

The second is a **decision kernel with a resource library**: the kernel works out
what the domain requires, then selects or acquires means. Capability arrives
during the run, not before it.

The first has three costs that compound.

**Trigger signal split.** Every domain agent's description competes for the same
attention during discovery. Thirty skills with broad, overlapping descriptions
means the wrong one is selected as often as the right one, and the failure looks
like incompetence rather than misconfiguration.

**Proliferation.** Because creating an agent is cheap, agents are created. Each
run that meets a gap mints a new specialist. Within weeks the library is large,
the descriptions overlap, and selection accuracy falls. Nothing is reused,
because the new specialist was easier to make than to find.

**Architecture by accretion.** With per-domain agents, each one tends to grow its
own mini-workflow: its own triage, its own verification, its own recovery. The
architecture is then the union of those workflows, and no single description of
the system is possible. The kernel stops being a kernel and becomes a
convention.

There is also a subtler cost. When a specialist is an agent, the decision about
what to do passes to it, and the reason for that decision leaves the kernel. The
architecture can no longer answer "why did it do that", which breaks
[0001](0001-jev-as-decision-fabric.md).

A fourth consideration is control. An agent carries its own authority assumptions
and its own notion of what is permitted. Many agents means many authority
surfaces, and the security model in `../security/` depends on the kernel being
the only place where an action is authorised.

## Decision

Adopt the **resource model**:

1. A skill is a **resource**: a documented means of making progress, with
   declared inputs, outputs, constraints, failure modes, and verification
   criteria. It is selected by the kernel at a decision boundary, and the
   selection is recorded.
2. A skill is **not** a decision-maker. It does not triage, does not choose its
   own strategy, and does not authorise anything. It runs under the kernel's
   authority and returns a result the kernel verifies.
3. There is **no router and no domain table**. The kernel does not contain
   `if domain == finance`. Routing is a conclusion derived from the task model,
   and it is revisable when evidence arrives.
4. Composition beats creation. Before any capability is created, the kernel
   must attempt direct action, then existing capabilities, then composition.
5. Creation is **delegated** to `skill-creator`, which owns specification,
   validation, security review, and promotion. A skill is never hand-authored
   inline and never becomes trusted behaviour on creation.
6. Before creation, the kernel asks the disqualifying question: **will this be
   needed again?** A one-off is a step in the plan, not a skill.
7. Every skill carries a **trigger negative**: an explicit statement of what it
   does not do, so that selection does not depend on a broad positive
   description alone.
8. Every capability is **validated** before first use: it exists, it does what
   it claims, and its output is what its name implies.

## Consequences

**Easier.** One place decides, so one place audits. The architecture stays
describable in one document because no skill is allowed to grow its own
workflow. Adding a domain requires a resource, not a branch, and the branch is
the part that would have broken the universality claim. Trigger signals stay
sharp because skills have narrow descriptions and explicit negatives. Security
has a single authorisation point.

**Harder.** Capability is slower to arrive. When the kernel meets a gap, it must
synthesise, acquire, and validate, which costs more than instantiating a
pre-written specialist. Skill quality now constrains kernel quality: a vague
reference file produces a vague run, and there is no framework to catch it
automatically. Composition requires skills to have compatible contracts, which is
real interface design and is not free. The single authorisation point also
becomes a bottleneck, and a kernel that spends its time on authorisation
decisions is a kernel doing over-orchestration.

**New failure modes this makes more likely.** Resource framing invites
**capability hoarding**: accumulating skills on the theory that they will be
useful, which reproduces proliferation with more steps. **Composition
overreach** — chaining three mediocre capabilities because composition is
officially preferred to creation — can be worse than one clear new skill.
**Validation theatre**, where a skill is checked once for existence and then
trusted for its lifetime, converts the validation gate into a formality. And
**deferred expertise**: the resource model makes it structurally easy to say "a
capability exists" and never examine whether it fits the decision at hand. The
trigger negative is the control for the last one, and it must be enforced, not
merely recommended.

## Alternatives considered

**Domain agent library with a router.** Rejected. Router maintenance becomes the
product, domain coverage is bounded by the library, and per-agent workflows make
the architecture undescribable. It also makes the failure mode of a misroute
silent: a wrong agent produces a plausible answer from the wrong domain.

**Model-driven dynamic specialist, synthesised per task.** Rejected. It looks
like the resource model without the cost, and the cost is the point. Per-task
specialists have no validation, no contract, and no regression history, so each
use is a first use. Rejected for the same reason we reject creating a skill per
task: the learning is discarded, so the system never improves.

**Hierarchical agent tree: a manager over domain agents over tools.** Rejected.
Each level adds coordination overhead and a place where the reason for a
decision is lost. The decision point is the same at every level in our design, so
the extra levels add cost without adding capability.

**One large skill containing all domains as sections.** Rejected. This is
load-everything as an architecture. Context becomes unbounded, selection
disappears because everything is already loaded, and editing one domain risks
another. It also cannot satisfy the C0 to C6 ladder, since all domains are at
the same depth.

**Skills that may propose plans but never execute.** Rejected. It creates two
kinds of resource with different contracts, doubles the validation surface, and
buys little: the kernel already separates planning (layer 8) from execution
(layer 9), and a plan-proposing skill is just a capability whose output is a
plan.

**Keep agents, but require each to run the full kernel internally.** Rejected as
strictly worse: it duplicates the kernel per domain, guaranteeing divergence in
rung discipline and verification between domains, and it recreates the routing
problem at the next level up.

## Revisit when

- A skill's trigger description is observed to be selected for the wrong work in
  the evaluation suite, repeatedly, and the cause is description overlap rather
  than a missing negative.
- The cost of capability acquisition (synthesise, acquire, validate) exceeds the
  cost of the work it enables in more than a small fraction of runs, which would
  mean the ladder's order is wrong.
- Interface composition of skills turns out to dominate creation cost in
  practice, and the ladder should be reordered to try creation second.
- A use case appears where a genuinely independent decision-maker is required
  with its own authority, such as an external compliance reviewer. Then the
  resource model is right for skills and wrong for that actor, and the exception
  should be recorded as a new ADR rather than smuggled in as a special skill.
- Proliferation metrics show a rising count of skills whose sole use is a single
  past run, which means the disqualifying question is not being asked.
