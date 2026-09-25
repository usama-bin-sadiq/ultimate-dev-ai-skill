# Changelog

## [3.2.0] — 2026-09-25

### Added
- feat: provision host root instruction files so the skill activates reliably Reported symptom: a large engineering prompt was worked with none of the skill's discipline, and nothing indicated the skill (commit 5a172be61ce9)


# Changelog

## [3.1.2] — 2026-09-25

### Documentation
- docs: warn that a stale install keeps old behaviour, and how to check it The installed copy is what the host loads, so repository changes have no effect until a reinstall. A copy left a full version b (commit 4d2a9ffc2222)


# Changelog

## [3.1.1] — 2026-09-25

### Fixed
- fix: skip recorded-benchmark check when project-local evidence is absent test_external_benchmark_evidence reads from the project-local .memory tree, which is intentionally untracked and is not part of (commit 63a703036198)


# Changelog

## [3.1.0] — 2026-09-25

### Changed
- Manual release (manual)


# Changelog

## [3.0.4] — 2026-09-25

### Fixed
- fix: stage every versioned file in the release commit The previous fix made releases succeed but left the pushed main branch broken. The release commit staged only VERSION, config/, the manifest, READ (commit c67a7798b8f9)


# Changelog

## [3.0.3] — 2026-09-25

### Fixed
- fix: repair the automated release pipeline, failing since v3.0.2 Every release run since v3.0.2 failed at the same step. The workflow bumps VERSION, runs sync-version.py, regenerates the manifest and  (commit fedb8d1909a2)


# Changelog

## [3.0.2] — 2026-09-24

### Fixed
- fix: make installers interactive and copy-only (commit 88f3aae95126)


# Changelog

## [3.0.1] — 2026-09-24

### Fixed
- fix: use configured CICD release environment (commit cb8f8ced5846)


# Changelog

## [3.0.0] — 2026-09-24

### breaking
- Major runtime/platform release: strict JEV-bound execution, durable operations, optional MCP seam, canonical workflow/catalog authority, provenance memory, governed self-evolution, and provider-neutral evaluation.

### added
- Dependency-free runtime platform components with host-injected adapters and no mandatory provider dependency.

### fixed
- Corrected release workflows and installers to use the root `VERSION` source of truth.

## [2.8.0] — 2026-09-24

### changed
- chore: release v2.7.0 (minor) (#3)

# Changelog

## [2.6.0] — 2026-09-24

### changed
-  (#)

# Changelog

## [2.5.3] — 2026-09-24

### changed
-  (#)

# Changelog

All notable changes to the ultimate-dev skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2026-09-22

### Fixed
- **install.sh**: global scope crash (`mkdir /.memory: Read-only file system`) — now sets `PROJECT_DIR=$HOME` so memory seeds to `~/.memory/ultimate-dev/`
- **install.ps1**: global scope crashes (`$Project` empty → `Join-Path` error), missing `.memory` seeding, managed `.gitignore` for global installs (bash only does project scope)
- **verify.sh**: computed `SKILL_DIR` from its own location (repo root) instead of `ultimate-dev/` — 44 false errors; now derives all counts from file lists; replaced deleted `personas/` check with agents count
- **detect-tools.sh**: footer advertised nonexistent `--tool` and `--tui` flags — now prints real install commands
- **validate.py**: hardcoded `>= 15` skills check → reads `total_skills` from manifest
- **pre-commit**: broken path resolution when installed as git hook (ran `scripts/sync-docs.py` from repo root where it doesn't exist) — now resolves `ultimate-dev/` correctly in both hook and direct modes
- **SKILL.md**: stale header `# Ultimate Developer v2.0` → versionless `# Ultimate Developer`; removed stale "Don't run all 120" count

### Added
- **LICENSE** (MIT, 2026, usama-bin-sadiq) at repo root
- Dynamic badges only on both READMEs (release, workflow, license, models, tools) — zero drift
- Mermaid flowchart for 4 LangChain patterns, collapsible module departments, emoji-first TOC anchors, alert callouts
- `pip install pyyaml` note in inner README (required for `validate.py` / `generate-manifest.py`)

### Changed
- Outer README: memory wording covers both global (`~/.memory`) and project (`<project>/.memory`) scopes; `verify.sh` description → "check package integrity"
- Inner README: preserves all 7 inline managed facts + 2 `ud:` blocks (sync-docs passes); real pre-commit install path (`ultimate-dev/scripts/pre-commit`)

## [2.1.0] - 2026-09-22

### Added
- Three-Layer Architecture documentation (Skills → Agents → Modules) with clear loading rules
- Agent Selection Tiebreaker in `router/classification-rules.md` (exact match → technology → domain generic → universal)
- Max 1 agent per domain rule to prevent token waste
- Framework-specific anti_triggers on all frontend agents (react excludes vue/angular/svelte, etc.)
- Validation script now checks: anti_triggers, three-layer architecture, agent selection rules, router completeness
- 49 total validation checks (up from 36)

### Changed
- `router/classification-rules.md`: Added Step 4 (Agent Selection) with tiebreaker logic and anti-trigger exclusion
- `SKILL.md`: Replaced "Module Loading" section with "Three-Layer Architecture" section clarifying Skills vs Agents vs Modules
- `SKILL.md`: Updated Selection Priority to include technology match and max-1-per-domain rule
- All frontend agent `anti_triggers` expanded to exclude other frameworks (prevents 4-agent overlap on single task)
- Version bumped to 2.1.0 across all files (SKILL.md, VERSION, README, manifest, configs)

### Fixed
- Frontend agent trigger overlap: react-specialist, vue-specialist, css-architect, accessibility-engineer, perf-specialist all had generic anti_triggers — now each excludes other frameworks
- Module vs Skill confusion: SKILL.md now explicitly states "No triple-loading" — an agent that references a module does NOT also load the parent skill
- Validation script hardcoded version check — now reads from VERSION file dynamically

## [2.0.0] - 2026-09-22

### Added
- 120 agents across 34+ categories (up from 50 personas)
- 17 meta-cognitive sub-skills (technology-agnostic)
- 45 internal pattern modules
- 5 shared agent fragments in `agents/_shared/`
- LangChain 4 patterns wired into mandatory Operating Loop (Step 4: Pattern Selection)
- Decision Tree for pattern selection (Skills, Subagents, Handoffs, Router)
- Tier-Based Execution system (TINY/SMALL/LARGE/HUGE) with token budgets
- Self-evolution capability (`skills/self-evolve/`) — auto-generates new skills from experience
- Auto-generated manifest via `scripts/generate-manifest.py` (never hand-edit)
- Pre-commit hook with 36 validation checks
- Install scripts for Mac/Linux (`install.sh`) and Windows (`install.ps1`)
- 6 workflows referencing actual agents (default, research, implementation, review, debugging, emergency)
- `config/` with models, workflow, permissions, security, context_budgets, agent_registry
- `router/` with classification-rules, token-budgets, precedence-rules, decomposition, grounding-rules, etc.
- README.md with usage examples (4 scenarios: simple, multi-domain, sequential, unknown technology)

### Changed
- SKILL.md rewritten from 516 to 218 lines — pure orchestrator, no reference docs
- Personas directory fully migrated to agents (deleted `personas/`)
- Agent format unified to 10 YAML frontmatter fields
- 3 duplicate agents removed (sre-engineer kept in devops/, ml-engineer kept in ai-ml/, cloud-architect kept in architecture/)
- All module paths fixed (old `modules/specialized/` → actual `modules/<category>/`)
- All versions synced to 2.0.0

### Removed
- `personas/` directory (migrated to `agents/`)
- 3 duplicate agent definitions
- Hardcoded model names from tier system (now uses runtime-provided context window)

## [0.1.0] - 2026-01-01

### Added
- Initial release of ultimate-dev skill
- Core directory structure
- README.md with project overview
- SKILL.md with skill definition
- skill-manifest.yaml with metadata
- VERSION file tracking releases
- Basic agent framework
- Module system
- Router for agent selection

---

## Versioning

- **Major** (X.0.0): Breaking changes to the skill interface
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible
