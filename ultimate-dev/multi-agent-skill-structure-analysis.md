# Multi-Agent Skill Directory Structure — Full Analysis

## Research Sources

- **Anthropic Agent Skills** (platform.claude.com) — Official spec for SKILL.md, progressive disclosure, 3-level loading
- **Anthropic Engineering Blog** — "Equipping agents for the real world with Agent Skills"
- **Addy Osmani** — "How to write a good spec for AI agents" (6 core areas, 3-tier boundaries)
- **GitHub Study** — Analysis of 2,500+ agent configuration files
- **CrewAI / LangGraph / AutoGen** — Framework-specific patterns
- **Red Hat ACE Team** — "Building skills for AI agents: pitfalls and best practices"
- **Microsoft Agent Architecture** — agent.yaml schema, registry patterns
- **Google Agent Development Kit** — A2A protocol, distributed agent systems

---

## Guide's Structure vs Enhanced Structure

The guide provides a **minimal viable structure**. Research shows each directory can contain significantly more files. Below is a comprehensive comparison.

---

### 1. `agents/` — Agent Definitions

**Guide has:** 5 flat files (orchestrator.md, researcher.md, coder.md, tester.md, reviewer.md)

**Can have:**

```text
agents/
├── _shared/                          # Reusable fragments (shared across agents)
│   ├── stack-detection.md            # How to detect project stack
│   ├── output-format.md              # Standard output format
│   ├── triage-rubric.md              # How to classify task size
│   ├── never-commits.md              # Things agents must never do
│   ├── tldr-output.md                # Short output format
│   ├── error-patterns.md             # Common error patterns & fixes
│   └── context-loading.md            # How to load context efficiently
│
├── _templates/                       # Agent definition templates
│   ├── base-agent.md                 # Template for new agents
│   ├── specialist-agent.md           # Template for domain specialists
│   └── review-agent.md               # Template for review agents
│
├── frontend/                         # Category subdirectories
│   ├── react-specialist.md
│   ├── vue-specialist.md
│   ├── css-architect.md
│   ├── perf-specialist.md
│   └── accessibility-engineer.md
│
├── backend/
│   ├── system-architect.md
│   ├── api-designer.md
│   └── microservices-architect.md
│
├── security/
│   ├── security-auditor.md
│   ├── threat-modeler.md
│   ├── incident-responder.md
│   └── compliance-engineer.md
│
├── devops/
│   ├── kubernetes-engineer.md
│   ├── terraform-engineer.md
│   ├── pipeline-engineer.md
│   ├── sre-engineer.md
│   └── reliability-engineer.md
│
├── database/
│   ├── postgres-specialist.md
│   ├── sql-optimizer.md
│   └── migration-auditor.md
│
├── testing/
│   ├── test-architect.md
│   ├── qa-engineer.md
│   └── e2e-specialist.md
│
├── performance/
│   ├── performance-engineer.md
│   └── bundle-analyzer.md
│
├── ai-ml/
│   ├── ml-engineer.md
│   ├── prompt-engineer.md
│   └── rag-architect.md
│
├── cloud/
│   ├── cloud-architect.md
│   └── cost-optimizer.md
│
├── observability/
│   ├── sre-engineer.md
│   └── monitoring-specialist.md
│
├── messaging/
│   └── event-architect.md
│
├── legacy/
│   └── modernizer.md
│
├── monorepo/
│   └── monorepo-architect.md
│
├── project-management/
│   ├── product-owner.md
│   ├── scrum-master.md
│   └── release-manager.md
│
├── design-handoff/
│   ├── ux-researcher.md
│   ├── motion-designer.md
│   └── design-spec.md
│
├── gis/
│   ├── spatial-analyst.md
│   └── cartographer.md
│
├── healthcare/
│   ├── clinical-data-analyst.md
│   ├── health-informaticist.md
│   └── biotech-researcher.md
│
├── sales/
│   ├── sales-engineer.md
│   ├── outbound-strategist.md
│   └── account-manager.md
│
├── git/
│   └── git-specialist.md
│
├── spatial-computing/
│   ├── xr-developer.md
│   └── spatial-ui-designer.md
│
├── specialized/
│   ├── iot-engineer.md
│   ├── blockchain-engineer.md
│   ├── quantum-computing.md
│   └── supply-chain.md
│
├── meta/
│   ├── auto-persona-generator.md
│   ├── gap-tracker.md
│   └── skill-maintainer.md
│
├── orchestrator.md                   # Core agents (flat)
├── codebase-investigator.md
├── cli-help.md
├── generalist.md
├── browser-agent.md
└── skill-creator.md
```

**Why category subdirectories?**
- Agents working on the same domain share patterns and constraints
- Easier to discover all frontend agents, all security agents, etc.
- Prevents a flat directory with 50+ files
- Each category can have its own `_shared/` if needed

**Key insight from Anthropic:** Agent files should have YAML frontmatter (name, description) and be self-contained. The `definition` field in the registry points to these files.

---

### 2. `config/` — Centralized Configuration

**Guide has:** 3 files (agent_registry.yaml, workflow.yaml, permissions.yaml)

**Can have:**

```text
config/
├── agent_registry.yaml               # Central agent registry (required)
├── workflow.yaml                     # Global workflow config (required)
├── permissions.yaml                  # Permission policy (required)
├── models.yaml                       # Model configurations & fallbacks
├── tool_configs.yaml                 # Tool-specific configurations
├── environment.yaml                  # Environment variables & secrets refs
├── feature_flags.yaml                # Feature toggles for agents
├── rate_limits.yaml                  # Rate limiting per agent/tool
├── retry_policies.yaml               # Retry & backoff configurations
├── context_budgets.yaml              # Token budget allocations
├── security.yaml                     # Security policies & constraints
├── logging.yaml                      # Logging configuration
├── caching.yaml                      # Caching strategies
├── notification.yaml                 # Alert & notification rules
└── deployment.yaml                   # Deployment & environment targets
```

**What each adds:**

| File | Purpose | When to Load |
|------|---------|--------------|
| `models.yaml` | Model names, fallbacks, cost limits, temperature settings | Always (startup) |
| `tool_configs.yaml` | Tool-specific settings (API endpoints, timeouts, retries) | When tool is invoked |
| `environment.yaml` | Env vars, secret references, feature detection | Always (startup) |
| `feature_flags.yaml` | Toggle agent capabilities on/off without editing files | Always (startup) |
| `rate_limits.yaml` | Per-agent, per-tool rate limits and quotas | When dispatching |
| `retry_policies.yaml` | Exponential backoff, circuit breaker configs | On failure |
| `context_budgets.yaml` | Token allocation per agent, per workflow phase | When loading context |
| `security.yaml` | Allowed ops, blocked patterns, sandbox rules | Always (startup) |
| `logging.yaml` | Log levels, output formats, sinks | Always (startup) |
| `caching.yaml` | Cache TTL, invalidation rules, storage backends | On cache hit/miss |
| `notification.yaml` | Alert channels, escalation rules, thresholds | On event |
| `deployment.yaml` | Target environments, deploy strategies | On deploy |

---

### 3. `prompts/` — Reusable Prompt Components

**Guide has:** 3 files (system.md, delegation.md, handoff.md)

**Can have:**

```text
prompts/
├── system.md                         # Shared behavioral instructions
├── delegation.md                     # Task delegation format
├── handoff.md                        # Result handoff format
├── chain-of-thought.md               # CoT reasoning instructions
├── output-format.md                  # Standard output formatting
├── error-reporting.md                # How to report errors
├── context-loading.md                # How to request context
├── reflection.md                     # Self-reflection instructions
├── planning.md                       # Planning & decomposition
├── verification.md                   # Self-verification steps
├── safety.md                         # Safety guardrails
├── persona/                          # Persona definitions
│   ├── senior-engineer.md
│   ├── tech-lead.md
│   ├── junior-developer.md
│   └── qa-specialist.md
├── examples/                         # Few-shot examples
│   ├── good-delegation.md
│   ├── bad-delegation.md
│   ├── good-handoff.md
│   └── bad-handoff.md
├── context-templates/                # Context assembly templates
│   ├── code-review.md
│   ├── bug-investigation.md
│   ├── feature-implementation.md
│   └── architecture-design.md
└── output-specs/                     # Output format specifications
    ├── json-output.md
    ├── markdown-report.md
    ├── code-changes.md
    └── test-results.md
```

**Why these matter:**
- `chain-of-thought.md` — Research shows CoT instructions improve reasoning accuracy by 15-30%
- `reflection.md` — Self-reflection prompts reduce hallucination and catch errors
- `persona/` — Different personas produce different quality outputs for different tasks
- `examples/` — Few-shot examples are the single most effective way to guide agent behavior
- `context-templates/` — Pre-assembled context patterns for common task types

---

### 4. `workflows/` — Execution Pipelines

**Guide has:** 4 files (default.yaml, research.yaml, implementation.yaml, review.yaml)

**Can have:**

```text
workflows/
├── default.yaml                      # Default workflow
├── research.yaml                     # Research-heavy tasks
├── implementation.yaml               # Implementation tasks
├── review.yaml                       # Independent review
├── debugging.yaml                    # Bug investigation & fix
├── refactoring.yaml                  # Behavior-preserving restructure
├── migration.yaml                    # Data/schema migration
├── optimization.yaml                 # Performance optimization
├── security-audit.yaml               # Security review pipeline
├── documentation.yaml                # Documentation generation
├── testing.yaml                      # Test creation & execution
├── deployment.yaml                   # Deployment pipeline
├── emergency.yaml                    # Emergency/hotfix workflow
├── onboarding.yaml                   # New developer onboarding
├── pipeline/                         # Reusable pipeline stages
│   ├── stage-discovery.yaml
│   ├── stage-planning.yaml
│   ├── stage-implementation.yaml
│   ├── stage-testing.yaml
│   ├── stage-review.yaml
│   └── stage-deployment.yaml
├── state-machines/                   # Complex state transitions
│   ├── task-lifecycle.yaml
│   ├── agent-lifecycle.yaml
│   └── error-recovery.yaml
├── triggers/                         # When workflows activate
│   ├── trigger-keywords.yaml
│   ├── trigger-patterns.yaml
│   └── trigger-schedules.yaml
└── templates/                        # Workflow templates
    ├── new-workflow.yaml
    └── custom-pipeline.yaml
```

**What each adds:**

| File | Purpose |
|------|---------|
| `debugging.yaml` | Structured debugging: reproduce → hypothesize → isolate → fix → verify |
| `refactoring.yaml` | Safe refactoring: analyze → plan → small steps → test → verify |
| `migration.yaml` | Zero-downtime migration: plan → backup → migrate → verify → rollback |
| `optimization.yaml` | Performance: profile → identify → optimize → benchmark → verify |
| `security-audit.yaml` | Security: threat model → scan → penetration test → report |
| `emergency.yaml` | Hotfix: triage → minimal fix → test → deploy → post-mortem |
| `pipeline/` | Reusable stages that compose into workflows |
| `state-machines/` | Formal state transitions for complex agent lifecycles |
| `triggers/` | Activation patterns (keyword, regex, schedule-based) |

---

### 5. `schemas/` — Data Contracts

**Guide has:** 3 files (task.yaml, result.yaml, message.yaml)

**Can have:**

```text
schemas/
├── task.yaml                         # Task structure
├── result.yaml                       # Result structure
├── message.yaml                      # Inter-agent messages
├── agent_config.yaml                 # Agent configuration schema
├── workflow_config.yaml              # Workflow configuration schema
├── tool_input.yaml                   # Tool input schemas
├── tool_output.yaml                  # Tool output schemas
├── error.yaml                        # Error structure
├── metadata.yaml                     # Metadata structure
├── context.yaml                      # Context window structure
├── feedback.yaml                     # Feedback/review structure
├── handoff.yaml                      # Handoff packet structure
├── resource.yaml                     # Resource/file reference schema
├── constraint.yaml                   # Constraint definition schema
├── acceptance_criteria.yaml          # Acceptance criteria schema
└── examples/                         # Schema examples
    ├── task-example.yaml
    ├── result-example.yaml
    └── error-example.yaml
```

**Why more schemas?**
- `error.yaml` — Structured error reporting enables automated retry/recovery
- `context.yaml` — Defines what context an agent receives (file list, code snippets, history)
- `feedback.yaml` — Review feedback structure (severity, location, suggestion)
- `handoff.yaml` — When one agent hands off to another, the packet structure matters
- `constraint.yaml` — Formal constraint definitions prevent agent violations

---

### 6. `tools/` — Tool Integrations

**Guide has:** 1 file (README.md)

**Can have:**

```text
tools/
├── README.md                         # Tool overview & requirements
├── tool_registry.yaml                # Available tools registry
├── tool_configs/                     # Per-tool configurations
│   ├── filesystem.yaml
│   ├── terminal.yaml
│   ├── web_search.yaml
│   ├── browser.yaml
│   ├── git.yaml
│   └── database.yaml
├── mcp_servers/                      # MCP server configurations
│   ├── README.md
│   ├── servers.yaml                  # MCP server registry
│   └── configs/                      # Per-server configs
│       ├── github.yaml
│       ├── postgres.yaml
│       └── slack.yaml
├── integrations/                     # External service integrations
│   ├── README.md
│   ├── api-specs/                    # OpenAPI specs for consumed APIs
│   │   ├── github-api.yaml
│   │   └── stripe-api.yaml
│   └── sdk-refs/                     # SDK reference docs
│       ├── prisma.md
│       └── express.md
├── restrictions/                     # Tool restrictions per agent
│   ├── read-only-agents.yaml
│   ├── write-agents.yaml
│   └── admin-agents.yaml
└── examples/                         # Tool usage examples
    ├── file-operations.md
    ├── terminal-commands.md
    └── git-workflow.md
```

---

### 7. `templates/` — Reusable Templates

**Guide has:** 2 files (task.md, report.md)

**Can have:**

```text
templates/
├── task.md                           # Task template
├── report.md                         # Report template
├── adr.md                            # Architecture Decision Record
├── prd.md                            # Product Requirements Document
├── spec.md                           # Technical specification
├── code_review.md                    # Code review template
├── bug_report.md                     # Bug report template
├── feature_spec.md                   # Feature specification
├── runbook.md                        # Operations runbook
├── postmortem.md                     # Incident post-mortem
├── rfc.md                            # Request for Comments
├── changelog.md                      # Changelog entry
├── readme.md                         # README template
├── api_doc.md                        # API documentation
├── test_plan.md                      # Test plan template
├── deployment_checklist.md           # Deployment checklist
├── onboarding.md                     # New developer onboarding
├── handoff_doc.md                    # Knowledge transfer doc
├── decision_log.md                   # Decision logging template
├── risk_assessment.md                # Risk assessment template
└── examples/                         # Filled-in examples
    ├── adr-example.md
    ├── prd-example.md
    └── code-review-example.md
```

**Why so many templates?**
- Each template ensures consistent output format across agents
- Templates reduce hallucination by providing structure
- Pre-filled examples show agents exactly what "good" looks like
- Templates can be versioned and evolved independently

---

### 8. `rules/` — Operational Constraints

**Guide has:** 3 files (delegation.md, validation.md, error-handling.md)

**Can have:**

```text
rules/
├── delegation.md                     # Delegation rules
├── validation.md                     # Validation rules
├── error-handling.md                 # Error handling rules
├── security.md                       # Security rules & constraints
├── coding-standards.md               # Coding style & standards
├── naming-conventions.md             # Naming conventions
├── git-workflow.md                   # Git branching & commit rules
├── testing-strategy.md               # Testing approach & coverage
├── performance-guidelines.md         # Performance rules
├── accessibility-guidelines.md       # WCAG compliance rules
├── documentation-standards.md        # Documentation requirements
├── api-design-rules.md               # API design principles
├── database-rules.md                 # Database design rules
├── deployment-rules.md               # Deployment safety rules
├── monitoring-rules.md               # Observability requirements
├── i18n-rules.md                     # Internationalization rules
├── three-tier-boundaries.md          # Always/Ask-first/Never boundaries
├── cost-constraints.md               # Token & API cost limits
├── privacy-rules.md                  # Data privacy rules
└── compliance/                       # Compliance-specific rules
    ├── gdpr.md
    ├── hipaa.md
    ├── soc2.md
    └── pci-dss.md
```

**Key insight from GitHub study:** The three-tier boundary system (Always/Ask-first/Never) is the single most effective constraint pattern. `three-tier-boundaries.md` formalizes this.

---

### 9. `scripts/` — Automation Scripts

**Guide has:** `...` (placeholder)

**Can have:**

```text
scripts/
├── install.sh                        # Install skill (Unix)
├── install.ps1                       # Install skill (Windows)
├── verify.sh                         # Verify installation
├── uninstall.sh                      # Uninstall skill
├── validate_config.sh                # Validate YAML configs
├── validate_schemas.sh               # Validate schemas
├── validate_agents.sh                # Validate agent definitions
├── run_tests.sh                      # Run skill tests
├── generate_docs.sh                  # Auto-generate documentation
├── benchmark.sh                      # Performance benchmarks
├── lint.sh                           # Lint all files
├── build.sh                          # Build/package skill
├── deploy.sh                         # Deploy skill
├── migrate.sh                        # Migrate skill versions
├── health_check.sh                   # Health check
├── setup_dev.sh                      # Development environment setup
└── utils/                            # Utility functions
    ├── common.sh                     # Shared shell functions
    ├── colors.sh                     # Terminal colors
    └── logging.sh                    # Logging functions
```

---

### 10. `tests/` — Skill Tests

**Guide has:** `...` (placeholder)

**Can have:**

```text
tests/
├── README.md                         # Test overview
├── conftest.py                       # Python test config (if using pytest)
├── unit/                             # Unit tests
│   ├── test_agent_registry.py
│   ├── test_workflow_routing.py
│   ├── test_permission_check.py
│   ├── test_schema_validation.py
│   └── test_prompt_loading.py
├── integration/                      # Integration tests
│   ├── test_agent_delegation.py
│   ├── test_workflow_execution.py
│   ├── test_tool_integration.py
│   └── test_end_to_end.py
├── e2e/                              # End-to-end tests
│   ├── test_simple_task.yaml
│   ├── test_complex_feature.yaml
│   └── test_emergency_fix.yaml
├── fixtures/                         # Test data
│   ├── sample_task.yaml
│   ├── sample_result.yaml
│   ├── sample_agents/
│   └── sample_workflows/
├── mocks/                            # Mock data
│   ├── mock_agent_responses.md
│   ├── mock_tool_outputs.yaml
│   └── mock_api_responses.json
└── evals/                            # Evaluation test cases
    ├── correctness/
    ├── security/
    ├── performance/
    └── edge_cases/
```

---

### 11. `examples/` — Usage Demonstrations

**Guide has:** 5 directories (simple-task, backend-feature, bug-fix, architecture-review, research-task)

**Can have:**

```text
examples/
├── README.md                         # Examples overview
├── simple-task/                      # Simple task example
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── backend-feature/                  # Backend feature
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   ├── workflow.yaml
│   └── walkthrough.md
├── bug-fix/                          # Bug fix
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── architecture-review/              # Architecture review
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── research-task/                    # Research task
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── security-audit/                   # Security audit
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── performance-optimization/         # Performance optimization
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── database-migration/               # Database migration
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
├── full-stack-feature/               # Full-stack feature
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   ├── workflow.yaml
│   └── walkthrough.md
├── emergency-hotfix/                 # Emergency hotfix
│   ├── README.md
│   ├── task.yaml
│   ├── expected-result.yaml
│   └── walkthrough.md
└── multi-agent-parallel/             # Parallel agent execution
    ├── README.md
    ├── task.yaml
    ├── expected-result.yaml
    ├── workflow.yaml
    └── walkthrough.md
```

---

### 12. Additional Directories (Not in Guide)

```text
├── personas/                         # Agent persona definitions
│   ├── README.md
│   ├── senior-backend-engineer.md
│   ├── frontend-lead.md
│   ├── devops-engineer.md
│   ├── security-analyst.md
│   ├── qa-engineer.md
│   ├── tech-lead.md
│   ├── product-owner.md
│   └── scrum-master.md
│
├── reference/                        # Reference documentation
│   ├── README.md
│   ├── api-patterns/
│   │   ├── rest.md
│   │   ├── graphql.md
│   │   ├── grpc.md
│   │   └── websocket.md
│   ├── design-patterns/
│   │   ├── creational.md
│   │   ├── structural.md
│   │   ├── behavioral.md
│   │   └── concurrency.md
│   ├── frameworks/
│   │   ├── react.md
│   │   ├── vue.md
│   │   ├── angular.md
│   │   ├── nextjs.md
│   │   ├── express.md
│   │   ├── fastapi.md
│   │   └── spring-boot.md
│   └── databases/
│       ├── postgres.md
│       ├── mysql.md
│       ├── mongodb.md
│       └── redis.md
│
├── memory/                           # Persistent memory
│   ├── README.md
│   ├── project-memory.md             # Learned project conventions
│   ├── decision-log.md               # Past decisions
│   ├── error-patterns.md             # Known error patterns & fixes
│   └── performance-notes.md          # Performance observations
│
├── evals/                            # Evaluation framework
│   ├── README.md
│   ├── rubrics/
│   │   ├── correctness.md
│   │   ├── security.md
│   │   ├── performance.md
│   │   └── maintainability.md
│   ├── benchmarks/
│   │   ├── task-completion.yaml
│   │   ├── response-quality.yaml
│   │   └── cost-efficiency.yaml
│   └── reports/
│       └── .gitkeep
│
├── changelog/                        # Version history
│   ├── README.md
│   ├── CHANGELOG.md
│   └── MIGRATION.md                  # Upgrade guide
│
├── docs/                             # Additional documentation
│   ├── architecture.md               # Architecture overview
│   ├── contributing.md               # Contribution guide
│   ├── troubleshooting.md            # Common issues & fixes
│   ├── faq.md                        # Frequently asked questions
│   └── glossary.md                   # Terminology definitions
│
└── .github/                          # GitHub-specific
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Summary: Files Per Directory

| Directory | Guide Files | Enhanced Files | Increase |
|-----------|-------------|----------------|----------|
| `agents/` | 5 | 50+ (with categories) | 10x |
| `config/` | 3 | 14 | 4.7x |
| `prompts/` | 3 | 20+ (with subdirs) | 6.7x |
| `workflows/` | 4 | 20+ (with subdirs) | 5x |
| `schemas/` | 3 | 16 (with examples) | 5.3x |
| `tools/` | 1 | 15+ (with configs) | 15x |
| `templates/` | 2 | 21 | 10.5x |
| `rules/` | 3 | 22 (with compliance) | 7.3x |
| `scripts/` | `...` | 17 (with utils) | — |
| `tests/` | `...` | 20+ (with fixtures) | — |
| `examples/` | 5 | 11 (with walkthroughs) | 2.2x |
| **New dirs** | 0 | 6 (personas, reference, memory, evals, changelog, docs) | — |

**Total: ~235+ files vs ~20 files in guide = 12x more comprehensive**

---

## Key Research Findings

### 1. Progressive Disclosure (Anthropic)
- Level 1: Metadata (~100 tokens, always loaded)
- Level 2: SKILL.md body (<5K tokens, loaded when triggered)
- Level 3+: Bundled files (0 tokens until accessed)
- **Implication:** More files = better progressive disclosure, not more context usage

### 2. Three-Tier Boundaries (GitHub Study)
- ✅ Always do / ⚠️ Ask first / 🚫 Never do
- "Never commit secrets" was #1 most helpful constraint
- **Implication:** `rules/three-tier-boundaries.md` is essential

### 3. Curse of Instructions (Research)
- Too many instructions in one prompt → performance drops
- Decompose into sequential, simple instructions
- **Implication:** Modular prompts > monolithic prompts

### 4. Spec-Driven Development (GitHub Spec Kit)
- 4 phases: Specify → Plan → Tasks → Implement
- Specs as executable artifacts, not just prose
- **Implication:** Templates + workflows + schemas work together

### 5. Agent Registry Pattern (Microsoft/Google)
- Central YAML registry maps agent identity → definition → capabilities → permissions
- Prevents hard-coding agent configuration
- **Implication:** `config/agent_registry.yaml` is the backbone

### 6. Few-Shot Examples (Research)
- Single most effective way to guide agent behavior
- Good/bad examples are more powerful than rules
- **Implication:** `prompts/examples/` is high-value

### 7. Self-Reflection (Research)
- Agents that reflect on their output catch 15-30% more errors
- **Implication:** `prompts/reflection.md` and `prompts/verification.md` are essential

### 8. Context Engineering (Anthropic)
- Organize prompts into distinct sections
- Minimal does not mean short — be detailed where it matters
- **Implication:** `prompts/context-templates/` enables smart context assembly

---

## LangChain Multi-Agent Architecture Patterns (January 2026)

Source: https://www.langchain.com/blog/choosing-the-right-multi-agent-architecture

### The 4 Patterns

LangChain identifies **4 foundational multi-agent patterns**. Our `ultimate-dev` skill primarily uses **Pattern 2 (Skills)** but can leverage all 4:

| Pattern | Description | Our Skill Uses? |
|---------|-------------|-----------------|
| **1. Subagents** | Supervisor orchestrates specialized subagents via tool calls. Centralized control, stateless subagents, parallel execution. | ✅ YES — via `subagent` tool |
| **2. Skills** | Progressive disclosure — agent loads specialized prompts/knowledge on-demand. Quasi-multi-agent through prompt-driven specialization. | ✅ YES — core pattern |
| **3. Handoffs** | Active agent changes dynamically based on context. Stateful transitions, sequential workflows. | ⚡ PARTIAL — via workflow state |
| **4. Router** | Classify input → dispatch to specialized agents in parallel → synthesize results. Stateless per-request. | ✅ YES — `router/` directory |

### Pattern Comparison Matrix

| Capability | Subagents | Skills | Handoffs | Router |
|-----------|-----------|--------|----------|--------|
| Distributed development | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | — | ⭐⭐⭐ |
| Parallelization | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | — | ⭐⭐⭐⭐⭐ |
| Multi-hop | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | — |
| Direct user interaction | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### Performance Characteristics

**Single request (e.g., "buy coffee"):**
- Subagents: 4 model calls (results flow back through main agent)
- Skills: 3 calls (direct execution)
- Handoffs: 3 calls (direct execution)
- Router: 3 calls (direct execution)

**Repeat request (same task twice):**
- Subagents: 8 calls total (stateless — no savings)
- Skills: 5 calls total (40% efficiency gain — stateful)
- Handoffs: 5 calls total (40% efficiency gain — stateful)
- Router: 6 calls total (25% efficiency gain)

**Multi-domain query (e.g., "Compare Python, JS, Rust"):**
- Subagents: 5 calls, ~9K tokens (parallel, context isolation)
- Skills: 3 calls, ~15K tokens (fewer calls but context accumulation)
- Handoffs: 7+ calls, ~14K+ tokens (sequential, can't parallelize)
- Router: 5 calls, ~9K tokens (parallel execution)

**Key insight:** Subagents process **67% fewer tokens** than Skills for multi-domain tasks due to context isolation. Each subagent works only with relevant context.

### Key Takeaways for Our Structure

1. **Skills are validated as a quasi-multi-agent pattern** — LangChain explicitly confirms Skills share benefits with multi-agent systems (distributed development, context control) through lighter-weight prompt-driven method.

2. **Context accumulation is the Skills weakness** — As skills load into conversation history, token usage grows. Our `config/context_budgets.yaml` and `config/caching.yaml` can mitigate this.

3. **Subagents add 1 model call overhead** — Results must flow back through orchestrator. Worth it for centralized control and context isolation.

4. **Handoffs need careful state management** — Our `workflows/state-machines/` directory is the right place for this.

5. **Router is best for parallel multi-domain** — Our `router/` directory already implements this pattern.

6. **Start simple, graduate to multi-agent** — "Start with a single agent and good prompt engineering. Add tools before adding agents. Graduate to multi-agent patterns only when you hit clear limits."

### Recommended Directory Additions (Based on LangChain)

```text
workflows/
├── state-machines/                   # For Handoffs pattern
│   ├── agent-handoff.yaml           # State-driven agent transitions
│   ├── conversation-flow.yaml       # Multi-turn conversation states
│   └── precondition-gates.yaml      # Sequential capability unlocking

config/
├── context_budgets.yaml              # Mitigate Skills token accumulation
├── parallel_execution.yaml           # Subagent/Router parallel config
└── handoff_rules.yaml                # When to handoff between agents

router/
├── classification-rules.md           # Input classification (already exists)
├── parallel-dispatch.md              # How to dispatch to multiple agents
├── synthesis.md                      # How to combine parallel results
└── fallback-rules.md                 # What to do when no agent matches
```
