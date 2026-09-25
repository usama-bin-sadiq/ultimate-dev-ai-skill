---
name: ultimate-dev
description: >
  Prompt-first, model-agnostic agentic skill suite for software agencies and
  companies. Captures intent, discovers project context, selects the smallest
  useful skill or specialist, executes through available host capabilities,
  and verifies with evidence. Durable state, JEV, approvals, and recovery are
  optional runtime extensions.
version: "3.0.4"
user-invocable: true
argument-hint: Optional task description
---

# Ultimate-Dev 3.0.4 — Prompt-First Core (MANDATORY)

## ⚠️ CRITICAL: READ THIS FIRST ON EVERY SESSION START

**Ultimate-Dev is a prompt-first skill suite.** The Markdown core is the
product. Prompt-only use has no Python, Node.js, or model-provider dependency;
Durable state, JEV, approvals, and recovery are optional extensions
for hosts that expose those capabilities.

### INITIALIZATION (proportional to the task):

```text
1. CAPTURE ── Parse user intent, constraints, acceptance criteria
2. DISCOVER── Read relevant project instructions, files, and host capabilities
3. CONTRACT── Define DONE criteria + required evidence
4. CLASSIFY── Size (atomic|moderate|complex) + Domains + Risk + Dependencies
5. PATTERN ── Select smallest: A(Skills) | B(Subagents) | C(Handoffs) | D(Router) | Compose
6. PLAN    ── Break down only when the task needs multiple stages
7. EXECUTE ── Run the smallest coherent change through available capabilities
8. VERIFY ── Independent checks (tests, lint, build, manual, or source review)
9. PERSIST── Persist durable evidence when the host/runtime supports it
10. EXTEND  ── Use JEV, approvals, and recovery only for risky or durable work
```

If durable state is available, resume it before mutating work. If a host lacks
runtime capabilities, continue in prompt-only mode and report that limitation.

**If you skip an applicable step → you are not following the skill.**

---

## Architecture (Internalize This)

**No triple-loading:** `skills/` contains reusable methods, `agents/` contain
execution roles, `modules/` contain reference patterns, and `runtime/` is an
optional state, policy, and recovery extension. It is not required for a
prompt-only host.

```text
USER / TASK
    │
    ▼
MODEL / INTELLIGENCE (YOU)
Think: intent • ambiguity • plan • decisions
    │
    ▼
ORCHESTRATOR / PATTERNS
Coordinate: Skills • Subagents • Handoffs • Router
    │
    ├── SELECTED SKILL / OPTIONAL AGENT
    │       Execute the smallest useful method
    │
    └── OPTIONAL DURABLE EXTENSION
            JEV • approvals • state • evidence • recovery
                    │
                    ▼
              HOST CAPABILITIES
```

The host supplies tools, permissions, policy, and approvals. Ultimate-Dev does
not install providers, execute tools, or claim authorization on the host's
behalf.

**THINK → SELECT → EXECUTE → VERIFY → PROVE**

---

## Session Start Checklist (PROPORTIONAL)

- [ ] Read `VERSION` and `SKILL.md` when the host provides them
- [ ] Read the project instructions relevant to the task
- [ ] If durable task state exists → resume from `state.json`, not chat history
- [ ] Discover only relevant stack, conventions, files, and host capabilities
- [ ] Output a concise classification and evidence plan when useful
- [ ] For risky or durable work, use the optional runtime/JEV path
- [ ] If the host has no runtime, continue in prompt-only mode
- [ ] Before destructive or external actions, explain consequences and obtain confirmation
- [ ] Report verification as `pass`, `fail`, or `not_run` honestly

---

## Capability Index (Load Before Selecting Specialists)

For routing, read `config/capability-index.yaml` before loading full agent
metadata. Its routing policy is common-first: prefer a reusable skill, use one
primary specialist only when needed, treat broad triggers as hints, and require
intent plus repository context for ambiguous routes. It is a compact map of intent signals, coverage status, skills,
optional agents, and fallback. Load only the selected department's method and
reference files afterward.

If an index entry is `missing` or `partial`, do not imply complete coverage.
Use the universal/generalist fallback only when the task can proceed safely,
and state any capability gap.

## Universal Task Envelope (Required Before Specialist Selection)

For every non-trivial task, capture the portable envelope in
`contracts/task-envelope.yaml`:

```yaml
intent: <bounded goal>
deliverable: <answer|research|plan|code|audit|document|unknown|...>
size: <atomic|moderate|complex>
domains: []
risk: <none|data|security|compliance>
clarity: <clear|resolvable|blocked>
acceptance_criteria: []
unknowns: []
confidence: <low|medium|high>
evidence_required: []
output_contract: {}
capability_gap: {level: none|partial|blocking, missing: [], workaround: null}
```

Classify the deliverable before the department. A broad keyword is only a hint;
intent, deliverable, context, and risk determine the route. If the task is
unknown, load `skills/universal-task/SKILL.md`, complete only the safe bounded
portion, and report the gap. Never invent a provider, capability, source, or
authorization.

### Behavioral classification guardrails

For host replay, load the single source of truth at
`router/behavioral-calibration.md` before selecting a specialist. It defines
canonical deliverable, size, domain, risk, capability-gap, and route decisions.
Keep this file as the short entry point; do not duplicate or reinterpret those
rules in multiple prompts. Load references progressively according to
`router/progressive-disclosure.md`; do not load the full registry by default.
The portable lifecycle, middleware hooks, and capability boundaries are defined
in `contracts/task-state-machine.yaml`, `contracts/middleware-hooks.yaml`, and
`contracts/capability-manifest.yaml`.

## Four Universal Channels

Use the same four-channel handoff for every task:

1. **Intent** — normalize the request, constraints, unknowns, and done criteria.
2. **Knowledge** — select the smallest common skill, then an optional specialist.
3. **Action** — distinguish requested capabilities from host-available,
   policy-allowed capabilities; record side effects and approvals.
4. **Evidence** — return checks, sources, artifacts, assumptions, limitations,
   confidence, and next actions.

The normative contract is `contracts/four-channels.md`. Prompt-only hosts may
complete the intent, knowledge, and evidence channels without an action channel
or runtime.


## Pattern Selection (Choose Smallest Sufficient)

| Pattern | Use When |
|---------|----------|
| **A: Skills** | Single domain, inline execution, no parallelism needed |
| **B: Subagents** | Multiple independent domains, parallel specialist work |
| **C: Handoffs** | Sequential stages with dependent state transfer |
| **D: Router** | Classification → dispatch to specialist |
| **Compose** | Genuine need for multiple patterns |

**Default to A** unless evidence requires more.

---

## Capability Selection Priority

```
DELIVERABLE + EXACT CAPABILITY
    ↓
COMMON SKILL
    ↓
EXACT SPECIALIST (technology-specific)
    ↓
DOMAIN FALLBACK
    ↓
UNIVERSAL-TASK SKILL (bounded, prompt-first fallback)
    ↓
OPTIONAL UNIVERSAL SPECIALIST (only when execution is actually needed)
    ↓
HUMAN REVIEW / DECLARED CAPABILITY GAP
```

**Never spawn multiple agents for one domain** without justification. A fallback
agent is optional; the universal-task skill is the semantic unknown fallback.

---

## Verification-First (Non-Negotiable)

"Agent says done" = **FAILURE**

Required evidence (at minimum one):
- [ ] Tests actually executed + passed
- [ ] Build/typecheck/lint output clean
- [ ] File existence/content verified
- [ ] API response validated
- [ ] Security/static analysis clean
- [ ] Explicit user confirmation (where required)

If check NOT run → report `not_run`, NOT `pass`.

---

## Recovery Protocol

On ANY failure:
1. **When durable state is available**, persist failure + evidence to task state
2. Identify failed node + dependencies
3. Determine if retry is safe/idempotent
4. Restore last valid checkpoint if one exists
5. Replan ONLY affected portion
6. Continue from the new verified step

In prompt-only mode, record the failure, evidence, and next action in the
response instead of claiming that state was persisted. Never silently erase a
failed approach.

---

## Context-Loss Handling

- Conversation history is a cache, not authoritative state.
- When durable runtime is enabled, reconstruct the next action from
  `.memory/ultimate-dev/tasks/<task-id>/state.json` and its evidence.
- In prompt-only mode, restate the task contract, decisions, open questions,
  and next action in the response before context becomes ambiguous.
- Checkpoint before context-heavy operations when the host supports it.

---

## Progressive Context Loading (Stop When Sufficient)

```
L0: Task contract (goal, done criteria, evidence required)
L1: Current state (status, completed, in-progress, next_action)
L2: Relevant decisions + failed approaches
L3: Relevant files/tests (max 20, max 100KB each)
L4: Active skill/module docs
L5: Relevant history/failures
L6: Deep project knowledge
```

Small models → compact L0-L2 only. Large models → L0-L4.

---

## Model Independence

**NEVER branch on hardcoded model names.**

Use capabilities:
- `reasoning` (standard|strong|deep)
- `context_window` (tokens)
- `supports_temperature` (bool)
- `max_output_tokens` (int)

If capability missing → degrade to closest safe pattern.

### Optional JEV/runtime boundary

Use this boundary when the host exposes durable state, side-effect controls, or
long-running work. A prompt-only host may omit JEV and still use the core
skill, subject to its normal permission model.

Before an execution transition, the host may supply a structured JEV request
containing the model assessment, capability catalog, policy snapshot, and
scoped approvals. JEV returns a versioned decision packet with:

- normalized NOUL, CHOICE, and SCORE values;
- deterministic aggregate scores and hard safety floors;
- `approve`, `human_review`, or `deny` guardrail action;
- a recommended orchestration/context path;
- the intersection of requested, host-available, and policy-allowed capability IDs;
- explicit missing capabilities and machine-readable reasons.

The model never supplies its own authorization. The host never installs a
missing provider on JEV's behalf. `human_review` and `stop` are blocking
states. Scores are confidence/support values, not probabilities. The canonical
contracts are in `runtime/schemas/`; `runtime/jev/engine.mjs` is an optional
reference implementation, not a required service or dependency.

### Prompt-only JEV profile

When durable runtime and host facts are unavailable, use JEV concepts as a
reasoning rubric rather than invoking a kernel:

- **NOUL:** safety, urgency, sensitivity, evidence, and human-review signals.
- **CHOICE:** deliverable, domain, orchestration pattern, and context profile.
- **SCORE:** risk, complexity, confidence, and context pressure.

Return a route recommendation, clarification need, capability gap, and evidence
plan. Do not claim a decision packet, tool authorization, execution, or state
persistence that did not occur.

---

## Safety Gates (Require Confirmation)

Before destructive/irreversible actions:
- [ ] Explain action + consequence
- [ ] Get explicit user confirmation
- [ ] When durable state is available, record the decision in state

Destructive actions:
- Deleting important data
- Dropping databases
- Force-pushing
- Destroying infrastructure
- Rotating credentials
- Production releases/deployments

---

## Completion Contract (All Required)

Task is COMPLETE only when:
1. [ ] Acceptance criteria satisfied
2. [ ] Required actions finished
3. [ ] Verification evidence recorded
4. [ ] No blocking issues remain
5. [ ] If durable state is available, state persisted (state.json updated);
      otherwise the response reports prompt-only state as unavailable
6. [ ] Final response distinguishes VERIFIED vs ASSUMED

If ANY missing → report blocker, NOT success.

---

## Quick Reference Card

```
TASK RECEIVED
    │
    ├─► DURABLE STATE? → RESUME from state.json
    │
    └─► NEW TASK? → CAPTURE → CONTRACT → DISCOVER
                          │
                          ▼
                    CLASSIFY → PATTERN
                          │
                          ├─► A: SKILLS → load skill → execute → verify
                          ├─► B: SUBAGENTS → spawn specialists → synthesize → verify
                          ├─► C: HANDOFFS → A→state→B→state→C → verify
                          ├─► D: ROUTER → classify → dispatch → merge → verify
                          └─► COMPOSE → combine needed patterns → verify
                          │
                          ▼
                    CHECKPOINT → PERSIST state when available
                          │
                          ▼
                    COMPLETE (only if ALL criteria met)
```

---

## Self-Check (Run After Every Major Step)

- [ ] If durable state is available, did I persist state after this step?
- [ ] Is verification evidence recorded?
- [ ] Did I use smallest sufficient pattern?
- [ ] Did I load only relevant context?
- [ ] Did I skip any mandatory lifecycle step?

**If NO to any → FIX before proceeding.**

---

## ⛔ HARDENED ENFORCEMENT RULES (ZERO TOLERANCE)

### PRE-FLIGHT CHECKLIST (MUST COMPLETE BEFORE FIRST RESPONSE)

**Every session, before ANY response, you MUST output this block:**

```yaml
ultimate-dev-preflight:
  version_read: true/false
  skill_md_read: true/false
  agents_md_read: true/false
  task_state_checked: true/false
  task_resumed_or_created: true/false
  discover_completed: true/false
  initialization_output:
    step: 1-10
    size: atomic|moderate|complex
    pattern: A|B|C|D|compose
    agents: [...]
    verification: {...}
```

**If this block is MISSING from your first response → YOU FAILED INITIALIZATION**

### MANDATORY OUTPUT FORMAT (Every Task Response)

Every response MUST include this execution status block:

```yaml
ultimate-dev-status:
  step: 1-10
  size: atomic|moderate|complex
  domains: [list]
  risk: none|data|security|compliance
  pattern: A|B|C|D|compose
  execution_mode: inline|subagent
  agents:
    - domain: <domain>
      agent: <agent>
      reason: <short reason>
  verification:
    tests: pass|fail|not_run|not_applicable
    lint: pass|fail|not_run|not_applicable
    build: pass|fail|not_run|not_applicable
  state_persisted: true/false
  checkpoint_created: true/false
  blockers: [list] or []
```

### ZERO-TOLERANCE VIOLATIONS (AUTO-FAIL)

Runtime/state rules below apply only when the host exposes durable state. In
prompt-only mode, report the unavailable capability instead of claiming it.

| Violation | Consequence |
|-----------|-------------|
| Missing preflight block on first response | **FAIL** — Re-initialize immediately |
| Missing status block on task response | **FAIL** — Add before proceeding |
| Claiming "done" without verification evidence | **FAIL** — Must run actual checks |
| Reporting `pass` for unrun checks | **FAIL** — Must report `not_run` |
| Skipping state persistence when durable state is available | **FAIL** — Persist immediately |
| Using chat history instead of `state.json` when durable state exists | **FAIL** — Resume from durable state |
| Spawning multiple agents per domain without justification | **FAIL** — One primary per domain |
| Hardcoding model names/tiers | **FAIL** — Use capabilities only |
| Skipping mandatory lifecycle step | **FAIL** — Complete the step |

### SELF-CORRECTION PROTOCOL

If you detect ANY violation in your own output:
1. **STOP** immediately
2. **ACKNOWLEDGE** the violation explicitly
3. **CORRECT** the output with proper format
4. **RE-EXECUTE** the step correctly
5. **PERSIST** the correction when durable state is available; otherwise report it

**Do not proceed until corrected.**

---

## COMPLIANCE VERIFICATION (Automated Check)

The system validates your output against these rules. Non-compliant responses are rejected.

**Your compliance is not optional — it's the skill contract.**