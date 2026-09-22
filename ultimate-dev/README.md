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

### 118 Agents across 36 Categories

<!-- ud:begin agent-tree -->
```
agents/ — 118 agents, 36 categories, 7 root-level
├── academic/            ( 1)  research-methodologist
├── ai-ml/               ( 4)  generic-ai-ml-specialist, ml-engineer, prompt-engineer, rag-architect
├── api-patterns/        ( 1)  api-architect
├── architecture/        ( 2)  microservices-architect, system-architect
├── backend/             (12)  api-designer, csharp-engineer, database-tuner, generic-backend-specialist, generic-shell-specialist, go-engineer, graphql-engineer, java-engineer, nodejs-architect, python-engineer, rust-engineer, tui-specialist
├── blockchain/          ( 1)  smart-contract-developer
├── caching/             ( 1)  cache-engineer
├── cloud/               ( 3)  cloud-architect, cost-optimizer, generic-cloud-specialist
├── data-engineering/    ( 1)  data-pipeline-engineer
├── database/            ( 4)  data-engineer, generic-database-specialist, postgres-specialist, sql-optimizer
├── design-handoff/      ( 3)  design-spec, motion-designer, ux-researcher
├── devops/              ( 7)  generic-devops-specialist, kubernetes-engineer, observability-engineer, pipeline-engineer, reliability-engineer, sre-engineer, terraform-engineer
├── documentation/       ( 2)  devrel-engineer, tech-writer
├── finance/             ( 5)  compliance-officer, financial-analyst, fintech-analyst, pricing-strategist, revenue-operations
├── frontend/            ( 6)  accessibility-engineer, css-architect, generic-frontend-specialist, perf-specialist, react-specialist, vue-specialist
├── game-dev/            ( 3)  game-designer, game-programmer, level-designer
├── gis/                 ( 2)  cartographer, spatial-analyst
├── git/                 ( 1)  git-specialist
├── healthcare/          ( 3)  biotech-researcher, clinical-data-analyst, health-informaticist
├── legacy/              ( 1)  modernizer
├── marketing/           ( 7)  affiliate-marketer, brand-strategist, content-strategist, email-marketing, growth-hacker, seo-specialist, social-media-manager
├── messaging/           ( 1)  event-architect
├── meta/                ( 4)  agent-generator, auto-persona-generator, gap-tracker, skill-maintainer
├── mobile/              ( 3)  mobile-android, mobile-flutter, mobile-ios
├── monorepo/            ( 1)  monorepo-architect
├── paid-media/          ( 2)  ads-optimizer, programmatic-buyer
├── performance/         ( 1)  performance-engineer
├── project-management/  ( 3)  product-owner, release-manager, scrum-master
├── real-time/           ( 1)  realtime-engineer
├── sales/               ( 3)  account-manager, outbound-strategist, sales-engineer
├── search/              ( 1)  search-engineer
├── security/            ( 4)  compliance-engineer, incident-responder, security-auditor, threat-modeler
├── spatial-computing/   ( 2)  spatial-ui-designer, xr-developer
├── specialized/         ( 6)  blockchain-engineer, edtech-designer, iot-engineer, legal-tech, quantum-computing, supply-chain
├── support/             ( 3)  customer-success, support-ops, technical-support-engineer
├── testing/             ( 6)  generic-testing-specialist, performance-tester, qa-engineer, quality-engineer, test-architect, test-automator
└── root-level           ( 7)  browser-agent, cli-help, codebase-investigator, generalist, orchestrator, skill-creator, universal-technology-specialist
```
<!-- ud:end agent-tree -->

### 17 Meta-Cognitive Sub-Skills

Each teaches HOW to think about a domain — technology-agnostic:

<!-- ud:begin skills-table -->
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
<!-- ud:end skills-table -->

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

# Re-sync README numbers (version, counts, agent tree) with the repo
python3 scripts/sync-docs.py

# Verify README is in sync without rewriting (pre-commit/CI)
python3 scripts/sync-docs.py --check

# Install pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Structure

```
ultimate-dev/
├── SKILL.md                    ← Orchestrator (271 lines)
├── skill-manifest.yaml         ← Auto-generated registry
├── README.md                   ← User documentation (this file)
├── VERSION                     ← Version number (source of truth)
├── AGENT.md / CLAUDE.md        ← Agent entry-point docs for other harnesses
├── adapters/                   ← Harness adapters (claude-code, codex, cursor, generic-cli)
├── agents/                     ← 118 specialized agents
├── skills/                     ← 17 meta-cognitive sub-skills
├── modules/                    ← 45 internal pattern modules
├── config/                     ← Configuration files
├── prompts/                    ← Shared prompt components
├── workflows/                  ← Execution pipelines (with agent refs)
├── schemas/                    ← Data contracts
├── rules/                      ← Operational constraints
├── router/                     ← Classification & routing logic
├── templates/                  ← Reusable templates
├── scripts/                    ← validate.py, generate-manifest.py, sync-docs.py, pre-commit
├── tools/                      ← Tool integrations
├── tests/                      ← Validation tests
├── examples/                   ← Usage examples
├── evals/                      ← Evaluation cases
├── reference/                  ← Reference documentation
├── memory/                     ← Memory templates (runtime .memory/ lives at project root)
└── changelog/                  ← Version history
```

## License

MIT
