# Changelog

## [Unreleased]

## [3.2.0] - 2026-09-26

### Added
- `provision-host-instructions.py` and `contracts/host-instruction-provisioning.yaml`: writes the skill's operating method into the tool's own root instruction file, which that tool reads on every session. Detects the tool from live environment variables first and marker files second, supports claude-code, codex, opencode, cursor, windsurf, cline, copilot, gemini, and a generic `AGENTS.md`, and never rewrites content outside its own markers.
- `router/trigger-mechanism.md`: the four activation channels in reliability order, why auto-discovery fails silently on very large prompts, the persona-versus-method precedence rule, and a five-step diagnosis for a trigger failure.

### Fixed
- **The skill had no activation contract.** Nothing told the model what to do when a request assigns its own role, such as "You are an autonomous senior game-development agent", and nothing detected that the skill had never been loaded. A large prompt could therefore be worked with none of the skill's discipline and no visible sign that anything was missing. SKILL.md and AGENTS.md now state that an active skill announces itself, that a persona is kept while the method still applies, and that a non-loaded skill says so and offers the explicit invocation.
- Provisioning writes a marked block, so a file the user already maintains is preserved. Re-running replaces only what is between the markers, which is covered by a test.
- Tool detection ranked marker files above live environment signals, so a project carrying both `CLAUDE.md` and `AGENTS.md` always resolved to the wrong tool. Environment signals now outrank file presence.
- `tests/test_consistency.py` compared the manifest contract list against a hardcoded literal, which broke on every contract addition including a sort-order slip. It now compares against the files on disk, so it is self-maintaining.

### Changed
- SKILL.md's entrypoint budget rose from 2400 to 2500 words to accommodate the Activation and Precedence section, with the reason recorded in `measure-entrypoint.py`. The gate stays active. The Quick Reference Card was rewritten as compact prose because the ASCII diagram consumed visual space without reducing the word count.

## [3.1.2] - 2026-09-26

### Fixed
- **Skill activation was unreliable.** The frontmatter `description` described what the skill is but carried no trigger conditions, while the sub-skills all ended with an explicit "Use for ..." clause. Hosts match on the description, so the top-level control plane under-triggered relative to its own sub-skills. It now leads with "Use for any request that asks to build, fix, refactor, review, audit, debug, migrate, design, plan, research, document, optimize, test, or deploy", names the @ultimate-dev and /ultimate-dev invocation forms, and declares an explicit `triggers` list. `argument-hint` also now matches the value used by AGENT.md and AGENTS.md.
- An installed copy predating v3.1.0 opened with "You do NOT need to be 'loaded' - you ARE the active orchestrator from the first token", which granted blanket pre-authorization and caused exactly the reported behaviour: starting the task immediately and skipping initialization. That sentence was already removed in 3.1.0; reinstalling propagates the fix.

### Changed
- Reinstall guidance is now part of the release checklist, because a stale global install silently keeps old behaviour regardless of what is in the repository.

## [3.1.0] - 2026-09-26

### Added
- Portable control-plane contracts: task state machine, middleware hooks, capability manifest, subagent, handoff, memory provenance, and HITL interrupt. All host-neutral, none requiring a runtime.
- `validate-routing-decision.py`: lints a decision record for vocabulary, route resolution against shipped skills and agents, risk justification, unfamiliar-domain gap coherence, and a bounded one-pass self-check.
- `measure-entrypoint.py`: budgets always-loaded entrypoints so context cost cannot silently grow; wired into `verify.sh`.
- `replay-gate.py`: fails a recorded replay on regression, pass-rate drop, forbidden-domain activation, or missing predictions.
- `validate-task-state.py`: confirms durable task state is a single parseable JSON document, catching YAML-written-as-JSON and concatenated documents.
- `reference/agentic-security-checklist.md`: OWASP Agentic Top 10 and NIST mapped to controls this package can enforce or verify.
- `router/progressive-disclosure.md` and `router/context-projection.md` for context cost control.
- Calibration and holdout fixtures with declared oracle limits; `--fields` scoring in the comparison tool.

### Fixed
- **Automated releases had been failing since v3.0.2.** `sync-version.py` did not write `SKILL.md`, which `validate-consistency.py` version-checks, so every release bumped `VERSION` and then failed validation. `SKILL.md` is now synced, and its `# Ultimate-Dev X.Y.Z` title moves with the version instead of going stale.
- Durable task state was unparseable in three places, silently breaking the context-loss guarantee: one state file had an unquoted JSON key, one was YAML written with a `.json` extension, and one held two concatenated JSON documents. All repaired, and the class is now caught mechanically.
- Routing vocabulary was duplicated between `classification-rules.md` and the calibration contract, which biased classification. The vocabularies now live in one place.

### Changed
- Measured replay 32 improved from 16/32 to a mean of 29.8/32 across 11 recorded rounds, with deliverable, risk, and size agreement at 0.99 or better. This is a same-model host-context diagnostic, not an independent model benchmark.
- Two replay gold labels were corrected on independent evidence from `config/capability-index.yaml` signals. A third correction was made and reverted because it aligned the labels to model output rather than to evidence.
- Documented that accuracy falls as the calibration contract grows past roughly 2400 words, because added rules collide rather than stack.

### Added
- Universal task envelope, deliverable-first capability index, unknown/unclassified fallback, and four-channel contracts.
- Provider-free routing benchmark with 154 golden cases, forbidden-route checks, and explicit non-model provenance.
- Read-only project-context recipe generator and optional company-context templates.
- Progressive reference splits for `self-evolve` and `task-observer`.

### Changed
- Prompt-only JEV profile is explicit; durable state/JEV requirements are conditional on host support.
- Fallback and evolution paths now produce reviewed candidates instead of automatically writing package files.
- Generated manifest, agent catalog, README, and consistency gates include the new contracts and skill.
- Installers now exclude local development caches, report staged payload size, and document prompt-only versus development dependencies in `INSTALLATION.md`.
- Added pinned `requirements-dev.txt` and a reproducible `measure-install.py` check.

## [3.0.0] - 2026-09-24

### Major release

- Hardened the durable runtime with strict JEV binding, policy/capability enforcement, evidence-gated completion, idempotent operations, cancellation, leases, and recovery.
- Added canonical workflow/catalog execution, optional MCP integration seams, provenance-aware memory, governed self-evolution, and provider-neutral evaluation.
- Synchronized release metadata to the root `VERSION` source of truth.

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
