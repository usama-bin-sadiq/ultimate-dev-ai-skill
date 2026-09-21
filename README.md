# ultimate-dev

Master software-engineering orchestrator. Adapts to model size with **44 specialized modules** and **33 execution personas** covering engineering, business operations, research, domain-specific verticals, and system maintenance. Works with ANY technology — pattern-based, not hardcoded.

## When to Use

Use this skill for **any** engineering, business, research, or domain-specific task. It automatically adapts to your model's context window:
- **Tiny models (≤8K)**: Inline answers, no modules
- **Small models (≤32K)**: 1 module max, lite-mode router
- **Large models (≤128K)**: Full system, parallel agents
- **Huge models (>128K)**: All features, unlimited

## Departments Covered (19)

| Department | Module | Description |
|-----------|--------|-------------|
| **Engineering** | | |
| Backend | `engineering/backend.md` | API design, server architecture, microservices, performance |
| Frontend | `engineering/frontend.md` | UI components, rendering, browser APIs, accessibility |
| Architecture | `engineering/architecture.md` | System design, tech stack, scaling, service boundaries |
| Database | `engineering/database.md` | Schema design, query optimization, migrations |
| Security | `engineering/security.md` | Vulnerability assessment, auth, compliance |
| DevOps | `engineering/devops.md` | CI/CD, containers, infrastructure, monitoring |
| Mobile | `engineering/mobile.md` | iOS, Android, cross-platform, offline sync |
| Testing/QA | `engineering/testing-qa.md` | Test strategy, automation, E2E, quality gates |
| Documentation | `engineering/documentation.md` | API docs, ADRs, runbooks, user guides |
| **Agency & Business** | | |
| Project Management | `agency/project-management.md` | Sprints, backlog, estimation, retrospectives |
| Product | `agency/product.md` | Requirements, roadmaps, user stories, prioritization |
| Design Handoff | `agency/design-handoff.md` | Mockups, design tokens, component specs |
| Client Comms | `agency/client-communication.md` | Status updates, scope changes, stakeholder management |
| **Business Operations** | | |
| Marketing | `marketing/marketing.md` | SEO, content, social media, growth, email campaigns |
| Sales | `sales/sales.md` | Pipeline, prospecting, proposals, deal qualification |
| Finance | `finance/finance.md` | Budgeting, forecasting, unit economics, pricing |
| Support | `support/support.md` | Ticket management, knowledge base, CSAT, escalation |
| Paid Media | `paid-media/paid-media.md` | Google Ads, Meta Ads, ROAS optimization, retargeting |
| **Research & Knowledge** | | |
| Research | `research/research.md` | Competitive analysis, market research, data synthesis |
| Academic | `academic/academic.md` | Literature reviews, thesis structure, citation management |
| **Domain-Specific** | | |
| Healthcare | `healthcare/healthcare.md` | FHIR, HL7, HIPAA, EHR integration, clinical workflows |
| Game Dev | `game-dev/game-dev.md` | Game mechanics, player experience, monetization, balance |
| GIS | `gis/gis.md` | Spatial analysis, map design, geospatial databases |
| Spatial Computing | `spatial-computing/spatial-computing.md` | AR/VR/MR, 3D UI, hand tracking, immersive experiences |
| Specialized | `specialized/specialized.md` | Blockchain, IoT, scientific computing, HPC, robotics |
| **Meta & System Maintenance** | | |
| Skill Maintainer | `personas/meta/skill-maintainer.md` | Module/persona lifecycle, registration, validation |
| Gap Tracker | `personas/meta/gap-tracker.md` | Domain gap tracking, occurrence counting, promotion |

## Quick Install

### Interactive TUI Mode (Recommended)
```bash
# macOS/Linux - Interactive installation with visual menus
./scripts/install.sh --tui

# Windows - Interactive installation with visual menus
.\scripts\install.ps1 -TUI
```

### Command-Line Mode
```bash
# macOS/Linux
./scripts/install.sh --tool claude-code

# Windows
.\scripts\install.ps1 -Tool claude-code

# Install specific divisions only
./scripts/install.sh --tool claude-code --division engineering,security,marketing

# Dry run (see what would be installed)
./scripts/install.sh --tool generic --dry-run
```

### Auto-Detection
```bash
# Auto-detect installed tools and install
./scripts/install.sh

# Detect all installed agent tools
./scripts/detect-tools.sh --verbose
```

## How It Works

### Model-Adaptive Behavior
The skill automatically adapts to your model's context window:

| Model Size | Context | Behavior |
|------------|---------|----------|
| **TINY** | ≤8K | Inline only — no modules, single-file changes |
| **SMALL** | ≤32K | 1 module max, uses lite-mode router |
| **LARGE** | ≤128K | Full system, up to 3 parallel agents |
| **HUGE** | >128K | All features, unlimited agents |

### Classification (automatic, before any action)
Every task is classified on four axes:
- **Size**: atomic (single change), moderate (one feature), complex (multi-domain)
- **Domains**: which of the 44 modules apply
- **Risk**: none, data, security, compliance
- **Clarity**: clear or ambiguous (ambiguous blocks complex tasks)

### Tier Selection
- **Atomic**: answer inline, no module loaded
- **Moderate**: load exactly the matched domain module(s)
- **Complex**: decompose into subtasks, assign owners, execute in dependency order

### Token Budget
Token spend scales with task size, not package size. The full module library is never loaded for a single task.

---

## Usage Guide

### Basic Usage (After Installation)

Once installed, the skill activates automatically when you use your agent tool.

#### Example 1: Simple Task (Atomic)
```
User: "Write a function to calculate Fibonacci numbers"
Agent: [tier: tiny | work: inline]
       function fibonacci(n) { ... }
```

#### Example 2: Feature Task (Moderate)
```
User: "Add user authentication with JWT"
Agent: [tier: small | module: security]
       Loads: modules/engineering/security.md
       Implements: JWT auth with proper patterns
```

#### Example 3: Complex Task (Decomposed)
```
User: "Build a full-stack e-commerce platform"
Agent: [tier: large | modules: backend, frontend, database | agents: 3]
       Decomposes into:
       1. Backend API (sub-agent 1)
       2. Frontend UI (sub-agent 2)
       3. Database schema (sub-agent 3)
```

### Task Types & Expected Behavior

| Task Type | Expected Response |
|-----------|-------------------|
| "Fix this bug" | Atomic — inline fix |
| "Add feature X" | Moderate — loads relevant module |
| "Build system Y" | Complex — decomposes, spawns agents |
| "Review this code" | Moderate — loads testing-qa module |
| "Optimize performance" | Moderate — loads performance module |
| "Set up CI/CD" | Moderate — loads devops module |

### Force a Specific Tier

If you want to override the automatic classification:

```
# Force inline (even for complex tasks)
"Use Tier 0 only: fix this bug"

# Force module loading
"Load backend module: design REST API"

# Force decomposition
"Decompose this into subtasks: build full-stack app"
```

### Check What's Loaded

Ask the agent:
```
"What tier are you operating at?"
"Which modules are loaded?"
"What's your token budget?"
```

### Manual Module Access

You can explicitly request a module:
```
"Load the security module and audit this code"
"Use the performance module to optimize this function"
"Apply the database module to design this schema"
```

### Project Memory

The skill remembers across sessions:
```
"Remember: we use PostgreSQL, not MySQL"
"Store this architecture decision"
"What did we decide about authentication?"
```

Stored in: `.ultimate-dev/project-memory.md`

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent doesn't load modules | Check model size — tiny models work inline only |
| Agent does everything inline | Model may be too small — upgrade or use `Load module X` |
| Agent spawns too many agents | Check token budget — large models max 3 agents |
| Agent ignores best practices | Add explicit: "Follow best practices from SKILL.md" |

### Advanced Usage

#### Custom Workflows
```
"Follow the operating loop from SKILL.md:
1. Capture requirements
2. Detect stack
3. Classify task
4. Execute
5. Verify"
```

#### Multi-Domain Tasks
```
"Build a healthcare app with:
- HIPAA compliance (healthcare module)
- REST API (backend module)
- React frontend (frontend module)
- PostgreSQL database (database module)"
```

#### Learning & Adaptation
```
"Log this decision to project memory"
"What conventions have we established?"
"Update the project memory with our tech stack"
```

## Directory Structure

```
ultimate-dev/
├── SKILL.md                     # Tier 0 — entry point, always loaded
├── skill-manifest.yaml          # Complete module/persona registry
├── VERSION                      # Current version (1.6.0)
├── .gitignore                   # Git ignore rules
├── router/                      # Classification and routing rules
│   ├── classification-rules.md  # Task classification
│   ├── decomposition.md         # Complex task breakdown
│   ├── token-budgets.md         # Model-adaptive budgets
│   ├── grounding-rules.md       # Library/tool verification
│   ├── completion-checklist.md  # Deliverable verification
│   ├── invocation-template.md   # Sub-agent contract
│   ├── precedence-rules.md      # Conflict resolution
│   ├── self-check.md            # Process compliance
│   ├── gap-promotion-rules.md   # Domain gap lifecycle
│   └── lite-mode.md            # Quick router for small models
├── modules/                     # 44 domain modules
│   ├── engineering/             # 9 engineering modules
│   ├── agency/                  # 4 agency modules
│   ├── business/                # 5 business modules
│   ├── research/                # 2 research modules
│   ├── domain/                  # 5 domain-specific modules
│   ├── specialized/             # 17 specialized modules
│   └── cross-cutting/           # 2 cross-cutting modules
├── personas/                    # 33 execution specialists
│   ├── engineering/             # 8 engineering personas
│   ├── specialized/             # 11 specialized personas
│   ├── agency/                  # 4 agency personas
│   ├── business/                # 5 business personas
│   ├── domain/                  # 5 domain personas
│   ├── meta/                    # 2 system maintenance personas
│   └── git/                     # 1 git specialist
├── scripts/                     # Installer and verification
├── adapters/                    # Tool-specific mappings
├── evals/                       # Test cases
├── templates/                   # Reusable templates
├── .github/                     # CI/CD workflows
├── README.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## Adding a New Domain Module

1. Create `modules/<category>/<domain>.md` following the template in `CONTRIBUTING.md`
2. Register it in SKILL.md's Capability Index
3. Add trigger keywords to `router/classification-rules.md`
4. Add entry to `skill-manifest.yaml`
5. Run `./scripts/verify.sh` to confirm all files are present

## Supported Tools (10+)

| Tool | Installation | Auto-Detect |
|------|-------------|-------------|
| Claude Code | `./scripts/install.sh --tool claude-code` | ✅ |
| Codex CLI | `./scripts/install.sh --tool codex` | ✅ |
| Cursor | `./scripts/install.sh --tool cursor` | ✅ |
| Windsurf | `./scripts/install.sh --tool windsurf` | ✅ |
| Cline | `./scripts/install.sh --tool cline` | ✅ |
| GitHub Copilot | `./scripts/install.sh --tool copilot` | ✅ |
| Aider | `./scripts/install.sh --tool aider` | ✅ |
| OpenCode | `./scripts/install.sh --tool opencode` | ✅ |
| Continue | `./scripts/install.sh --tool generic` | ✅ |
| Tabnine | `./scripts/install.sh --tool generic` | ✅ |
| Codeium | `./scripts/install.sh --tool generic` | ✅ |
| Any CLI | Use `--tool generic` | — |

See `adapters/` for tool-specific configuration details.

## Known Limitations

- Enforcement depends on the host tool loading and respecting system instructions
- New domains with fewer than 3 occurrence notes are not automatically promoted to modules
- Domain-specific modules (healthcare, GIS, game-dev) require domain expertise to validate

## Versioning

Uses semver. Routing-affecting changes (Capability Index, classification algorithm) are minor version bumps.

## License

MIT
