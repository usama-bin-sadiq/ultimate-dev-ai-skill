# Ultimate-Dev Prompt-Skill Audit

**Audit date:** 2026-09-25
**Scope:** portable Markdown prompt skill only
**Explicitly out of scope:** external providers, host APIs, browsers, containers, MCP servers, operating-system claims, production infrastructure, and real execution authorization

## Executive verdict

Ultimate-Dev is now a credible **prompt-first, cross-department skill suite**.
It is stronger than a flat collection of prompts because it has a capability
index, common skills, optional specialist agents, explicit verification rules,
and host-neutral adapters.

It is not yet a 10/10 prompt product because prompt quality is only partly
measured. The repository now has 154 golden classification cases, 33 skills,
20 capability domains, a portable task/four-channel contract, and a
provider-free fixture benchmark. It still has no independent model/host
behavioral benchmark showing that agents select the right common skill, avoid
false activation, and produce better answers than a minimal prompt.

**Current evidence-bounded prompt-only estimate: 8.6/10.**
**10/10 status:** not claimed.

This is a modest post-implementation estimate, not a model benchmark. The
previous 8.5 estimate was raised because all 154 fixtures now declare
deliverables/clarity, broad legacy trigger collisions are removed, and the
cache-free measured installer is reproducible. Independent model/host behavior
is still required before a 9–10 claim.

The current deterministic audit reports **0 structural errors** across 119 agents,
33 skills, 46 modules, 20 capability domains, and 154 golden cases. The fixture
benchmark reports 62 negative/near-miss cases (40.3%) and explicitly labels
itself `fixture_audit_pass`, not a model benchmark.

## Scorecard

| Dimension | Score | Evidence / remaining gap |
|---|---:|---|
| Prompt architecture | 9.0 | Universal task envelope, four channels, deliverable-first routing, and optional runtime/JEV boundary |
| Common-skill coverage | 8.7 | 33 skills cover requirements, planning, communications, business, data, finance, legal, people, procurement, audit, artifacts, project context, evaluation, and universal fallback |
| Capability discoverability | 8.7 | Capability index includes deliverable types, unknown fallback, contract cross-checks, and generated metadata |
| Routing precision | 8.1 | 154 cases, forbidden-route fixtures, 62 negative/near-miss cases, and zero broad-trigger collisions; real model precision remains unmeasured |
| Context efficiency | 8.5 | Long skills are split into references; installer excludes development caches; capability index is loaded first |
| Output/evidence contracts | 8.5 | Portable envelope, four channels, capability-gap reports, and standardized high-use contracts are present |
| Portability | 8.8 | Copy-only installation, measured 3,472 KiB payload, host-neutral contracts, optional JEV, adapters, and provider-free benchmark |
| Maintainability | 8.7 | Generated inventory, contract validation, candidate-only evolution, reference tests, normalized trigger metadata, and CI/pre-commit gates |
| Evaluation | 8.1 | All 154 cases declare deliverables; provider-free fixture benchmark passes; three same-model smoke iterations range from 4/32 to 17/32 with the final comparison policy; no independent model/host outcome benchmark or calibrated judge |
| Prompt-only safety | 8.3 | Explicit uncertainty, human review, capability gaps, no automatic package writes, and honest `not_run` semantics |
| **Overall** | **8.6** | Strong prompt and packaging foundation; behavioral model/host evidence and organization-specific evaluation remain the main gaps |

## What the repository currently does well

### Common-first coverage

The suite now has common methods for:

- requirements and discovery
- planning and execution
- internal communication
- business analysis and strategy
- data analysis/BI
- accounting and finance
- project context and repository recipes
- legal/privacy/contracts
- people operations
- procurement/vendors
- office artifacts
- audit/controls
- prompt evaluation

These are reusable across software agencies and companies. They are more
valuable than adding one narrow agent for every framework or job title.

### Portable packaging

- The inner skill is copied as Markdown and supporting files.
- `skill-manifest.yaml` is generated.
- `config/agent-catalog.yaml` is generated from concrete agent frontmatter.
- `config/agent_registry.yaml` now explicitly contains abstract workflow roles.
- `config/capability-index.yaml` provides a compact department-to-skill map.
- Skill names now conform to the Agent Skills convention and match directories.
- Runtime/JEV/state are optional in the core prompt.

### Evidence discipline

The repository has:

- verification-first instructions
- task contracts and acceptance criteria
- human-review boundaries for finance, legal, people, audit, and external actions
- 154 golden routing cases, including unknown, multilingual, and forbidden-route cases
- provider-free fixture benchmark with honest non-model provenance
- static prompt-suite auditing
- host-neutral output and completion contracts

## Post-implementation evidence update

The latest implementation pass adds the following measurable packaging and
prompt-quality evidence:

- staged install: **3,492 KiB**, **421 files**, zero symlinks, zero local cache
  directories, and zero protected local bridges;
- prompt-only dependencies: **none** beyond the host;
- development dependencies: Python 3.11+, PyYAML 6.0.2, pytest 8.3.5, and
  optional requests 2.32.3; Node.js 20+ is optional for JEV tests;
- routing fixtures: **154**, all with explicit deliverable metadata, including
  62 negative/near-miss cases and 12 unknown-domain cases;
- broad trigger collisions: **0** after compound-metadata normalization;
- optional company-context template validation is provider-free and secret-aware;
- dependency-free context benchmarks completed against complete working trees of
  `microsoft/vscode`, `JetBrains/intellij-community`, and `kubernetes/kubernetes`;
  clones used shallow history and blob-filtered object storage, no project
  dependencies were installed, and every temporary clone was deleted;
- bounded nested-manifest discovery was added after the full IntelliJ benchmark
  showed that module-local build files are not always at the repository root;
  the scanner is covered by fixture tests and never executes project commands;
- verification: 802 Python tests, 25 JEV tests, strict prompt audit, strict
  provider-free benchmark, project-context benchmark, consistency, host-native,
  and workflow-security checks;
- fresh-context behavioral smoke replay: three same-model host sessions; baseline
  runs scored 13/32, the first guardrail iteration 4/32, and the refined
  iteration 11/32 raw (17/32 with the final comparison policy, five ambiguous
  domain cases unscored); this is not an independent model benchmark and remains
  a quality gap;
- the provider-free audit reports **29** legacy expected-domain labels: 24 have
  reviewable comparison-only aliases and 5 remain ambiguous; ambiguous domain
  accuracy is not treated as model-quality evidence.

The full setup and dependency matrix is in
`ultimate-dev/INSTALLATION.md`. The measured size is a real staged install, not
the source checkout size.

## Findings and severity

### P0 — fixed in this audit pass

#### 1. Agent Skills name mismatch

Seventeen existing skills used names such as `research-skill` while their
directories were `skills/research/`. The Agent Skills specification expects the
skill name to match its directory. All current skills now comply, and the
consistency gate checks this.

#### 2. Duplicate routing authority

The manifest had 119 concrete agents while the runtime registry had 76 mixed
concrete/abstract roles. The generated catalog and separate workflow-role
registry now make the distinction machine-checkable.

#### 3. Prompt/runtime contradiction

The core prompt described runtime/JEV as mandatory while the product is meant
to work as a prompt-only skill. The core and AGENTS entry point now make the
runtime optional and qualify durable-state instructions.

#### 4. Missing cross-functional evaluation cases

The original golden suite was engineering-heavy. It now includes requirements,
communications, finance, accounting, legal, people, procurement, artifacts,
strategy, data/BI, and audit cases.

### P1 — important remaining improvements

#### 1. Broad trigger collisions — fixed in the metadata pass

Generic trigger tokens were removed from 52 concrete agent definitions. Agents
retain domain/technology-specific signals, while the router policy continues to
require intent, deliverable, context, and risk. The prompt audit now reports
**0** broad trigger collisions. Behavioral false-activation measurement remains
separate and is still pending.

#### 2. Behavioral prompt benchmark — fresh-host smoke only

Static checks prove structure, not answer quality. Three fresh same-model host
sessions were replayed over a 32-case stratified sample. The baseline runs each
passed 13/32; the first guardrail iteration fell to 4/32 after an over-broad
risk rule; the refined iteration reached 11/32 raw and 17/32 with the final
comparison policy. This is useful diagnostic evidence, but it is not an
independent model benchmark. The full behavioral contract still needs:

- expected selected skill
- acceptable alternative skills
- forbidden skills
- output rubric
- false-activation checks
- context/token measurement
- human or calibrated judge results
- a separately identified model/provider and host

The provider-free audit also found 29 legacy expected-domain labels outside the
current capability-index vocabulary. Twenty-four have reviewable comparison-only
aliases and five remain ambiguous. Until the ambiguous labels are reviewed,
domain accuracy is not a fair model-quality metric.

This remains the largest gap to a defensible 9–10 prompt-only rating.

#### 3. Legacy skill inconsistency — high-use slice normalized

The ten highest-use engineering skills now share an `Operating Contract` with
inputs, output, verification, and a when-not-to-use boundary. Other older
skills still vary in format and should be migrated incrementally.

#### 4. Long skills — fixed in the universal-task pass

`self-evolve` and `task-observer` now keep concise cores and move templates,
numbering, confidentiality, review, and promotion details into linked
`references/` files. The audit reports no long-skill warnings. Their evolution
path is candidate-only: durable runtime may issue a memory receipt; prompt-only
hosts return a handoff; neither writes canonical package files automatically.

#### 5. Company-specific references — templates exist, evaluation blocked

Optional company-context templates and authoring rules are present under
`ultimate-dev/reference/`. Template-mode validation passes, but no active
organization-owned pack, policy set, jurisdiction set, approval matrix, or
approved reviewer set is present in this repository. A real organization-
specific evaluation is therefore blocked pending authoritative inputs. The suite
still does not have verified jurisdiction-specific or organization-owned packs
for:

- accounting periods and chart of accounts
- privacy/legal retention schedules
- HR policies and employee data
- vendor risk tiers
- audit evidence formats
- brand and office templates

These should be optional references, not hard-coded into the core prompt.

#### 6. Project-context recipes now have a provider-free generator — partial

The `project-context` skill and recipe template capture build/test/run commands,
architecture, important paths, constraints, provenance, and verification.
`generate-project-context.py` provides a read-only first pass and marks all
candidate commands `not_run`. The remaining improvement is richer path-specific
metadata and human-reviewed command verification.

## Comparison with other systems

| System | What it does better | What Ultimate-Dev should adopt |
|---|---|---|
| Agent Skills specification | Strict `SKILL.md` contract, directory/name matching, progressive disclosure, optional references/assets/scripts | Already adopted; keep the validator |
| Claude Code skills | Clear descriptions, on-demand loading, invocation controls, supporting files, recorded run/verify recipes | Add generated project run/verify recipes and skill-level context controls where supported |
| Claude Code subagents | Short delegation descriptions, tool restrictions, independent context, cost/model selection | Add intent-based agent summaries and context budgets; avoid loading 119 full agent bodies |
| OpenCode | Native on-demand skill discovery and per-agent skill permissions | Preserve host-neutral source and generated adapters; avoid duplicate names |
| Cursor | Project rules and path-specific rules | Add path-specific project-context references |
| GitHub Copilot | Repository-wide and path-specific instructions, validated build/test/run/layout recipes | Add a portable project-context skill and recipe format |
| Cline | Conditional rules that activate by file context | Add optional path/condition metadata to project references, not to every agent |
| Aider | Minimal context, repository map, conventions, automatic lint/test | Add concise context recipes and verification-first skill defaults |
| Anthropic skills repository | Real document, PDF, spreadsheet, slide, MCP, and communication skill examples | Keep Ultimate-Dev host-neutral; add optional templates/validators rather than provider code |
| Superpowers | Strong stage gates, design approval, TDD, review loops, durable plan/ledger | Improve planning/requirements gates and add lightweight plan/ledger templates |
| wshobson/agents | Plugin granularity, harness-native generation, behavioral evaluation framework | Add prompt-skill evaluation and a bounded common/specialized split; do not copy raw scale |
| GitHub awesome-copilot | Searchable catalog of agents, instructions, skills, hooks, and plugins | Add a searchable local capability index and security metadata |
| OpenAI Agents SDK | Explicit handoffs, guardrails, structured outputs, sessions, tracing | Use structured output contracts in common skills; keep runtime concepts optional |
| Microsoft Agent Framework | Clear separation between open-ended agents and well-defined workflows | Preserve Ultimate-Dev's A/B/C/D pattern model and explicit workflow roles |
| MCP security guidance | Consent, least privilege, SSRF, token, session, and local-server boundaries | Keep tool trust language in host adapters; do not add provider integrations to the prompt suite |

## Realistic improvement roadmap

### P0 — complete now

- [x] Make prompt-only operation explicit.
- [x] Make runtime/JEV optional.
- [x] Validate skill names and directory names.
- [x] Separate concrete agents from abstract workflow roles.
- [x] Add capability index and generated agent catalog.
- [x] Add cross-functional golden cases.
- [x] Add deterministic prompt-suite audit.
- [x] Add universal task envelope, four-channel contract, and unknown fallback.
- [x] Add provider-free routing fixture benchmark and 154-case suite.
- [x] Make self-evolution candidate-only and split long skills into references.

### P1 — next implementation

- [x] Add a `project-context` skill and portable recipe template.
- [x] Add path/context metadata to project references (recipe template and generator baseline).
- [x] Add a routing fixture runner that works without providers by checking
      expected/forbidden skill and domain selections.
- [x] Add a trigger-collision report and normalize generic metadata.
- [x] Split `self-evolve` and `task-observer` into concise core + references.
- [x] Normalize operating/output/verification/boundary contracts across the 10 highest-use skills.
- [x] Add optional company reference pack templates under `reference/`.

### P2 — quality improvement

- [ ] Add prompt-only model/host comparisons using the same golden cases.
- [ ] Measure context tokens, latency, false activation, and cost.
- [ ] Add human-reviewed answer rubrics for finance, legal, people, audit, and
      procurement outputs.
- [ ] Expand multilingual/localization and accessibility cases beyond the initial five-language routing fixtures.
- [ ] Add release-time audit reports showing changes in routing and coverage.

### P3 — do not pursue in the prompt skill

- [ ] External provider integrations
- [ ] A mandatory runtime service
- [ ] Kernel/container/browser infrastructure
- [ ] A universal autonomous company agent
- [x] Prohibit automatic canonical agent/skill publication without evaluation and review

## Bottom line

Ultimate-Dev should remain:

> **A prompt-first common-skill suite with optional specialist agents and an optional runtime extension.**

The next meaningful improvement is not a larger agent count. It is real
model/host outcome evidence, trigger-collision cleanup, normalized legacy skill
contracts, and organization-specific references loaded only when needed.
