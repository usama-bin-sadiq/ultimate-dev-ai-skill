# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.6.0] — 2026-09-21

### Changed
- **SKILL.md completely rewritten**: Model-adaptive paths (TINY/SMALL/LARGE/HUGE)
- **Token budgets updated**: Explicit rules for each model size
- **Router/lite-mode.md**: Quick module lookup for small models
- **Path fix**: ~/.agent/skills/ → ~/.agents/skills/

### How It Works Now
| Model Size | Context | Behavior |
|------------|---------|----------|
| TINY | ≤8K | INLINE ONLY — no modules, single-file |
| SMALL | ≤32K | 1 module max, lite-mode router |
| LARGE | ≤128K | Full system, 3 agents max |
| HUGE | >128K | All features, unlimited |

## [1.5.0] — 2026-09-21

### Added
- **11 new specialized personas**: ml-engineer, data-pipeline-engineer, cloud-architect, event-architect, cache-engineer, search-engineer, sre-engineer, api-architect, test-architect, realtime-engineer, git-specialist
- **6 new pattern modules**: i18n-l10n, performance, accessibility, open-source, legacy-modernization, monorepo
- **All modules pattern-based**: no hardcoded technologies, works with ANY tool

### Changed
- **Complete persona coverage**: every module now has a corresponding persona
- **Updated skill-manifest.yaml**: 44 modules, 31 personas

## [1.4.0] — 2026-09-21

### Added
- **11 specialized modules**: api-patterns, testing-frameworks, real-time, blockchain, ai-ml, data-engineering, cloud, messaging, caching, search, observability
- **Blockchain/Web3 module**: smart contracts, DeFi, NFTs, gas optimization, security auditing
- **Git specialist persona**: conventional commits, conflict resolution, CI/CD
- **Git commit conventions template**: Conventional Commits v1.0.0
- **Git conflict resolution guide**: strategies, patterns, best practices
- **GitHub Actions workflows**: CI/CD pipeline, PR quality checks
- **Git hooks template**: pre-commit, commit-msg, pre-push hooks

### Changed
- **All modules converted to pattern-based**: removed hardcoded technologies
- **SKILL.md**: Added Best Practices section (mandatory for all tasks)
- **All triggers updated**: concept-based, not technology-specific

## [1.3.0] — 2026-09-21

### Optimized
- **SKILL.md**: 50% token reduction, model-adaptive tiers (tiny/small/large/huge)
- **router/token-budgets.md**: Compact format with model-adaptive limits
- **router/classification-rules.md**: Streamlined keyword matching
- **router/decomposition.md**: Compact algorithm with minimal version
- **router/invocation-template.md**: Minimal version for tiny models
- **router/completion-checklist.md**: Model-adaptive checklist levels
- **router/grounding-rules.md**: Compact 4-step process
- **router/precedence-rules.md**: Simplified conflict resolution
- **router/self-check.md**: Model-adaptive check levels
- **router/gap-promotion-rules.md**: Streamlined promotion process
- **modules/_emerging-tech-handler.md**: Compact 6-step process
- **modules/_universal-principles.md**: Essential principles only

### Added
- **Model adaptation table** in SKILL.md for all model sizes
- **Minimal versions** of templates for tiny models
- **Progressive loading** based on model capacity

## [1.2.0] — 2026-09-21

### Added
- **TUI installation scripts** with interactive option selection
- **Multi-tool detection** for 10+ agent tools (Claude, Codex, Cursor, Windsurf, Cline, Copilot, Aider, OpenCode, Continue, Tabnine, Codeium)
- **General installation paths** that all agents recognize (.agent/skills/, .claude/skills/, etc.)
- **Division selection** with meta division for system maintenance personas
- **Dry-run mode** for testing installation without changes
- **Verbose mode** for detailed detection output
- **JSON output** for tool detection results

### Changed
- Updated install.sh with TUI and comprehensive tool detection
- Updated install.ps1 with TUI and comprehensive tool detection
- Updated detect-tools.sh to support 10+ tools with detailed detection
- Updated verify.sh to check 9 router files and 22 personas
- Added gap-promotion-rules.md to router files verification
- Added meta personas to persona verification

## [1.1.1] — 2026-09-21

### Fixed
- Added gap-promotion-rules.md reference to SKILL.md operating loop
- Added 2 additional anti-pattern examples to skill-maintainer persona
- Added 2 additional anti-pattern examples to gap-tracker persona
- Added 6 edge-case test cases to evals/golden-cases.yaml

## [1.1.0] — 2026-09-21

### Added
- **2 meta system personas**: skill-maintainer, gap-tracker for lifecycle management
- **Gap promotion rules**: router/gap-promotion-rules.md for formal promotion process
- **Meta & System Maintenance department**: new department in Capability Index

### Changed
- Updated SKILL.md Capability Index with meta personas
- Updated skill-manifest.yaml with new personas and stats
- Bumped total personas from 12 to 14
- Bumped total router files from 8 to 9
- Bumped departments covered from 18 to 19

## [1.0.0] — 2026-09-21

### Added
- **Tier 0 Core Router** (`SKILL.md`) with Capability Index, classification algorithm, operating loop, non-negotiable rules, and self-check
- **8 router files**: classification-rules, decomposition, token-budgets, grounding-rules, completion-checklist, invocation-template, precedence-rules, self-check
- **9 engineering domain modules**: backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation
- **4 agency domain modules**: project-management, product, design-handoff, client-communication
- **5 business operations modules**: marketing, sales, finance, support, paid-media
- **2 research & knowledge modules**: research, academic
- **5 domain-specific modules**: healthcare, game-dev, gis, spatial-computing, specialized
- **2 cross-cutting modules**: universal-principles, emerging-tech-handler
- **12 execution personas**: api-designer, database-tuner, perf-specialist, threat-modeler, pipeline-engineer, test-automator, tech-writer, scrum-master, growth-hacker, outbound-strategist, fintech-analyst, health-informaticist
- **Installer scripts**: install.sh (POSIX), install.ps1 (Windows), detect-tools.sh, verify.sh
- **Tool adapters**: claude-code, codex, cursor, generic-cli
- **skill-manifest.yaml** — machine-readable module/persona registry
- **CONTRIBUTING.md** — module, persona, and adapter authoring templates
- **ARCHITECTURE.md** — maintainer documentation for tier system, decomposition, and extension

### Credits
- **msitarzewski/agency-agents** — The repo that prompted this PRD. Its per-specialist persona files (engineering, design, marketing, sales, etc.) are a useful content source for populating Tier 2 personas. The domain expertise and voice in those files were adapted rather than written from scratch. It is explicitly not the structural model for this system: it ships ~300+ standalone files with no shared router, no capability map, no token-budget logic, and no built-in mechanism for deciding when a persona is actually needed. This skill's Tier 0/1/2 split, classification step, and budget rules exist specifically to avoid that pattern.

### Resolved Domain Gaps

| Domain | Date | Resolution |
|--------|------|------------|
| WebAssembly | 2026-09-21 | Covered by `specialized` module |
| Blockchain/EVM | 2026-09-21 | Covered by `specialized` module |
| AR/VR/XR | 2026-09-21 | Covered by `spatial-computing` module |
| Game Development | 2026-09-21 | Covered by `game-dev` module |
| GIS | 2026-09-21 | Covered by `gis` module |
| Healthcare | 2026-09-21 | Covered by `healthcare` module |
| Marketing | 2026-09-21 | Covered by `marketing` module |
| Sales | 2026-09-21 | Covered by `sales` module |
| Finance | 2026-09-21 | Covered by `finance` module |
| Support | 2026-09-21 | Covered by `support` module |
| Paid Media | 2026-09-21 | Covered by `paid-media` module |
| Research | 2026-09-21 | Covered by `research` module |
| Academic | 2026-09-21 | Covered by `academic` module |

### Unresolved Domain Gaps

| Domain | Date | Description | Occurrences | Status |
|--------|------|-------------|-------------|--------|
| — | — | No unresolved gaps at v1.0.0 | — | — |
