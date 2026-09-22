# ultimate-dev v2.1.0

**Master software-engineering orchestrator** — a single, adaptive skill that replaces dozens of specialized skills. Works with ANY model (tiny to huge) and ANY technology stack.

## Quick Start

1. Install the skill in your agent's skills directory
2. Start working — the orchestrator handles routing automatically

## How It Works

```
User Task → Capture → Detect → Classify → Pattern → Route → Execute → Verify → Review
                                         ↓
                                   Decision Tree
                                   /     |     \     \
                                 A       B      C     D
                              Skills  Subagents Handoffs Router
```

### The 4 Architecture Patterns (LangChain)

| Pattern | When | How |
|---------|------|-----|
| **A: Skills** | Single domain | Load skill on-demand, execute directly |
| **B: Subagents** | Multi-domain parallel | Spawn stateless agents, synthesize results |
| **C: Handoffs** | Sequential workflow | Pass state between agents in sequence |
| **D: Router** | Classify + dispatch | Classify task, dispatch to specialists, merge |

### Tier-Based Execution

Adapts to your model's context window automatically:

| Tier | Context | Behavior |
|------|---------|----------|
| **TINY** | ≤8K | Inline only, max 500 words |
| **SMALL** | ≤32K | 1 module, 1 agent, max 2000 words |
| **LARGE** | ≤128K | 3 modules, 3 agents |
| **HUGE** | >128K | Everything, unlimited agents |

## What's Inside

### 120 Agents across 34+ Categories

```
agents/
├── frontend/      (6)  react, vue, css, accessibility, perf, generic
├── backend/       (10) node, python, go, rust, java, csharp, graphql, api, generic
├── security/      (4)  auditor, threat-modeler, incident-responder, compliance
├── devops/        (7)  k8s, terraform, pipeline, sre, reliability, observability, generic
├── testing/       (6)  playwright, jest, pytest, quality, test-automator, generic
├── database/      (4)  postgres, sql-optimizer, data-engineer, generic
├── ai-ml/         (4)  ml-engineer, data-scientist, nlp-engineer, generic
├── marketing/     (7)  growth, content, seo, social, email, brand, affiliate
├── finance/       (5)  analyst, compliance, pricing, revenue, fintech
├── specialized/   (6)  blockchain, iot, quantum, xr, supply-chain, edtech
├── ...30+ more categories
└── codebase-investigator.md  (built-in)
```

### 17 Meta-Cognitive Sub-Skills

Each teaches HOW to think about a domain — technology-agnostic:

| Skill | Purpose |
|-------|---------|
| `self-evolve` | Auto-generates new skills from experience |
| `research` | Learn anything |
| `coding` | Build anything |
| `testing` | Verify anything |
| `review` | Evaluate anything |
| `architecture` | Design anything |
| `security` | Protect anything |
| `devops` | Deliver anything |
| `debugging` | Fix anything |
| `documentation` | Communicate anything |
| `performance` | Optimize anything |
| `monitoring` | Observe anything |
| `data` | Work with any data |
| `api-design` | Connect anything |
| `migration` | Transition anything |
| `mobile` | Build for any device |
| `ai-ml` | Build intelligent systems |

### Self-Evolution

When the system encounters a task with no matching sub-skill:
1. Researches how to do it
2. Executes the task
3. Extracts patterns
4. Auto-generates a new sub-skill
5. Persists in `skills/_learned/` for future use

## Usage Examples

### Simple Task (Tier: SMALL)
```
User: "Fix the login bug"
→ Pattern A: Skills (debugging)
→ Load skills/debugging/SKILL.md
→ Spawn codebase-investigator
→ Fix the bug
→ Verify
```

### Multi-Domain Task (Tier: LARGE)
```
User: "Build a React feature with API and tests"
→ Pattern B: Subagents (multi-domain)
→ Spawn react-specialist (frontend)
→ Spawn api-designer (backend)
→ Spawn test-architect (testing)
→ Parallel execution
→ Synthesize results
```

### Sequential Pipeline (Tier: LARGE)
```
User: "Deploy to production"
→ Pattern C: Handoffs (sequential)
→ Plan (system-architect) → handoff state
→ Implement (auto) → handoff state
→ Test (test-architect) → handoff state
→ Review (code-reviewer) → handoff state
→ Deploy (pipeline-engineer)
```

### Unknown Technology (Tier: SMALL)
```
User: "Use Bun for the backend"
→ No dedicated Bun specialist exists
→ Spawn generic-backend-specialist
→ Web research: Bun documentation
→ Apply universal backend patterns
→ Complete the task
→ Auto-generate bun-specialist for future use
```

## Validation

```bash
# Run all checks
python3 scripts/validate.py

# Auto-generate manifest from disk
python3 scripts/generate-manifest.py

# Install pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Structure

```
ultimate-dev/
├── SKILL.md                    ← Orchestrator (218 lines)
├── skill-manifest.yaml         ← Auto-generated registry
├── agents/                     ← 120 specialized agents
├── skills/                     ← 17 meta-cognitive sub-skills
├── modules/                    ← 45 internal pattern modules
├── config/                     ← Configuration files
├── prompts/                    ← Shared prompt components
├── workflows/                  ← Execution pipelines (with agent refs)
├── schemas/                    ← Data contracts
├── rules/                      ← Operational constraints
├── router/                     ← Classification & routing logic
├── templates/                  ← Reusable templates
├── scripts/                    ← validate.py, generate-manifest.py, pre-commit
├── tools/                      ← Tool integrations
├── tests/                      ← Validation tests
├── examples/                   ← Usage examples
├── evals/                      ← Evaluation cases
├── reference/                  ← Reference documentation
├── memory/                     ← Persistent memory
└── changelog/                  ← Version history
```

## License

MIT
