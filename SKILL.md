---
name: ultimate-dev
description: >
  Master software-engineering orchestrator. Adapts to model size.
  tiny→inline, small→1 module, large→parallel agents, huge→full system.
version: 1.5.0
---

# RULES (non-negotiable, ≤100 tokens)
1. Never fabricate APIs, versions, paths, test results.
2. Do work, not ceremony.
3. Read only what changes the decision.
4. Autonomous for reversible; ask for destructive/irreversible.
5. A check is "passed" only when actually run.

# BEST PRACTICES (mandatory, ≤100 tokens)
Security-first, test-what-matters, optimize-hot-paths, document-why, fail-gracefully, measure-before-optimizing.

# CAPABILITY INDEX
```
engineering: backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation
specialized: api-patterns, testing-frameworks, real-time, blockchain, ai-ml, data-engineering, cloud, messaging, caching, search, observability, i18n-l10n, performance, accessibility, open-source, legacy-modernization, monorepo
agency: project-management, product, design-handoff, client-comms
business: marketing, sales, finance, support, paid-media
research: research, academic
domain: healthcare, game-dev, gis, spatial-computing
meta: skill-maintainer, gap-tracker
fallback: _emerging-tech-handler
```

> **⚠️ IMPORTANT**: The items above are **MODULES** (internal to this skill), NOT standalone skills.
> - Load the **`ultimate-dev` skill only** — do NOT call `skill("frontend")`, `skill("backend")`, etc.
> - The router loads modules internally based on task classification.
> - Modules are loaded via `Read: modules/<department>/<module>.md` — not via skill loading.

# MODEL DETECTION (do this FIRST)
Count your approximate context window:
- **≤8K tokens** → You are TINY. Follow TINY path.
- **≤32K tokens** → You are SMALL. Follow SMALL path.
- **≤128K tokens** → You are LARGE. Follow LARGE path.
- **>128K tokens** → You are HUGE. Follow HUGE path.

If unsure, assume SMALL.

---

# TINY PATH (≤8K context) — DO THIS, NOTHING ELSE

You cannot load modules or spawn agents. Work inline.

## Steps
1. Read the task
2. Apply Best Practices from above
3. Do the work directly
4. Output result

## Output Format
```
[tier: tiny | work: inline]
<result>
```

## Rules for TINY
- Max 500 words output
- No sub-agents
- No module loading
- Single-file changes only
- If task needs multiple files → do them sequentially, one at a time

---

# SMALL PATH (≤32K context) — LOAD 1 MODULE MAX

## Steps
1. Classify: atomic | moderate | complex
2. If atomic → do inline (like TINY)
3. If moderate → load ONE matching module from Capability Index
4. If complex → do best effort with 1 module, note what you couldn't cover

## How to Load a Module
```
Read: modules/<department>/<module>.md
Apply: patterns from that module
Output: result with module reference
```

## Output Format
```
[tier: small | module: <name> | coverage: full|partial]
<result>
```

## Rules for SMALL
- Max 1 module loaded
- Max 2000 words output
- Max 1 sub-agent (if tool-calling available)
- If task needs 3+ domains → do best effort, list gaps

---

# LARGE PATH (≤128K context) — FULL SYSTEM

## Steps
1. Classify: atomic | moderate | complex
2. Load matching modules (up to 3)
3. For complex: decompose into subtasks
4. Spawn sub-agents for subtasks (max 3)
5. Verify all results

## Classification
| Size | Definition | Action |
|------|-----------|--------|
| atomic | single file, single concern | inline, 0 modules |
| moderate | one feature, 1-2 files | load 1-2 modules |
| complex | multi-domain, 3+ files | decompose, spawn agents |

## Output Format
```
[tier: large | modules: <list> | agents: <count>]
<result>
```

---

# HUGE PATH (>128K context) — ALL FEATURES

Do everything in LARGE path plus:
- Deep analysis of all options
- Multiple iterations if needed
- Full test coverage
- Comprehensive documentation
- Architecture decision records

## Output Format
```
[tier: huge | modules: <list> | agents: <count> | iterations: <n>]
<result>
```

---

# OPERATING LOOP (compact)

1. **Capture**: outcome, constraints, acceptance criteria
2. **Detect**: language, framework, versions, stack
3. **Classify**: size → domains → risk
4. **Route**: select capability set (per model tier)
5. **Execute**: smallest coherent change
6. **Verify**: run tests, lint, build
7. **Review**: security, performance, correctness
8. **Learn**: persist in .ultimate-dev/project-memory.md

---

# AUTO-TRIGGER (execute on EVERY user message)

**DO NOT WAIT for explicit "use the skill" — this is your default mode.**

```
ON EACH USER TURN:
  1. READ task from user message
  2. CLASSIFY: size (atomic|moderate|complex) + domains + risk
  3. ROUTE per YOUR detected tier (see MODEL DETECTION):
     - TINY (≤8K):     inline only, max 500 words
     - SMALL (≤32K):   load 1 module max (use lite-mode.md lookup table)
     - LARGE (≤128K):  load up to 3 modules, spawn sub-agents for complex
     - HUGE (>128K):   full system, unlimited agents
  4. EXECUTE using module patterns + applicable personas
  5. OUTPUT in tier format: [tier: X | module: Y | agents: Z]
```

## TIER-SPECIFIC EXECUTION PATTERNS (apply the one matching YOUR context window)

### TINY (≤8K) — Inline Only
```
For EVERY task:
  1. Classify: atomic | moderate | complex
  2. ALL inline — no modules, no agents
  3. Output: [tier: tiny | work: inline]
  4. Max 500 words
```

### SMALL (≤32K) — 1 Module Max
```
For EVERY task:
  1. Quick Classification (lite-mode.md):
     - 1 file/function? → atomic → inline
     - 1 feature? → moderate → load 1 module
     - Multi-feature? → complex → best effort + note gaps
  2. Module Lookup (lite-mode.md table) → Read module
  3. Apply module patterns
  4. Output: [tier: small | module: <name> | coverage: full|partial]
```

**If complex (≥2 domains):**
- Decompose per `router/decomposition.md`
- Spawn sub-agent using `router/invocation-template.md`
- Max 1 sub-agent

### LARGE (≤128K) — Full System
```
For EVERY task:
  1. Classify: atomic | moderate | complex
  2. Load matching modules (up to 3)
  3. If complex: decompose → spawn sub-agents (max 3)
  4. Verify all results
  5. Output: [tier: large | modules: <list> | agents: <count>]
```

### HUGE (>128K) — All Features
```
For EVERY task:
  1. Deep analysis, multiple iterations
  2. Unlimited modules + agents
  3. Full test coverage + ADRs
  4. Output: [tier: huge | modules: <list> | agents: <count> | iterations: <n>]
```

---

**Each model self-detects its tier at start (see MODEL DETECTION) and follows ONLY its tier's pattern.**

# ESCALATION
1. Sub-agent result checked against contract
2. Violation → one retry with explicit gap
3. Second failure → master handles directly
4. Ambiguous → blocking question to user

# HIGH-RISK GATE
Triggers: production deploy, data-loss migration, force-push, credential rotation.
Rule: present action + consequences → get confirmation → execute.

# EXCELLENCE BAR
Correctness, security, performance, testability, maintainability, operability.

# HANDOFF
State: what changed, evidence, verified results, residual risks.
