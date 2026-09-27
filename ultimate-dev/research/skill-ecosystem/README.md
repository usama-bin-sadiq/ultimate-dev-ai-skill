# The public AI agent skill ecosystem

What the published skill repositories, the open specification, and the skill
marketplaces actually require, and what they do not. Written to be checked
against, not to be admired.

The point of this survey is narrow. The kernel already has an opinion about what
a skill is and what a delegated role is. The question is whether that opinion is
compatible with the format every other publisher uses, and whether the six roles
in `agents/` leave a capability uncovered that the ecosystem treats as standard.

---

## What I could and could not verify

### Read in full, from primary sources

| Source | URL | What was read |
|---|---|---|
| Agent Skills spec | `https://agentskills.io/specification.md` | whole page (8,127 bytes) |
| Agent Skills best practices | `https://agentskills.io/skill-creation/best-practices.md` | whole page (14,816 bytes) |
| Optimizing descriptions | `https://agentskills.io/skill-creation/optimizing-descriptions.md` | whole page (13,249 bytes) |
| Evaluating skills | `https://agentskills.io/skill-creation/evaluating-skills.md` | first ~9,000 bytes of a longer page — **truncated** |
| Agent Skills doc index | `https://agentskills.io/llms.txt` | whole (1,374 bytes) |
| `agentskills/agentskills` | `https://raw.githubusercontent.com/agentskills/agentskills/main/README.md` | whole (3,315 bytes) |
| `anthropics/skills` | repo page + `README.md` + full recursive tree (511 paths) | whole |
| `anthropics/skills` `template/SKILL.md` | raw | whole (140 bytes) |
| `anthropics/skills` `skills/skill-creator/SKILL.md` | raw | first ~14,000 of 32,987 bytes — **truncated** |
| `anthropics/skills` `skills/skill-creator/agents/grader.md` | raw | whole (9,031 bytes) |
| `anthropics/skills` `.claude-plugin/marketplace.json` | raw | whole |
| `anthropics/claude-plugins-official` | repo page, full tree (778 paths) | whole |
| `.../plugins/example-plugin/.claude-plugin/plugin.json` | raw | whole (270 bytes) |
| `.../plugins/code-simplifier/agents/code-simplifier.md` | raw | first 2,200 bytes |
| `.../plugins/code-modernization/agents/security-auditor.md` | raw | first 2,200 bytes |
| `.../plugins/code-modernization/agents/test-engineer.md` | raw | first 1,400 bytes |
| `openai/skills` | repo page, `README.md`, `contributing.md` | whole (`contributing.md` is 527 bytes and says almost nothing) |
| `openai/plugins` | `README.md`, `.agents/plugins/marketplace.json`, `plugins/notion/.codex-plugin/plugin.json` | `README.md` whole; others partial |
| `google/skills` | repo page | whole |
| `gemini-cli` | `docs/cli/skills.md`, `docs/cli/skills-best-practices.md` (raw) | whole |
| `google-gemini/gemini-cli` | GitHub API root listing | top-level entries only |
| `vercel-labs/agent-skills` | `README.md`, `AGENTS.md` | whole |
| `VoltAgent/awesome-agent-skills` | `README.md` (220,527 bytes) | scanned by keyword; two sections read verbatim |
| `msitarzewski/agency-agents` | `README.md` (83,066 bytes) | scanned by keyword; Security + Testing divisions read verbatim |
| `alirezarezvani/claude-skills` | `README.md` (26,017 bytes) | first 12,000 bytes — **truncated** |
| `ComposioHQ/awesome-claude-skills` | `README.md` on `master` (40,536 bytes) | first 12,000 bytes — **truncated** |
| `agentskills.io`, `skillsmp.com` | HTML | rendered text; `skillsmp.com/submit` returned **404** |
| Anthropic engineering blog | `https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills` | whole (text extracted) |

### Failed, blocked, or not attempted

- `https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/main/README.md` — **404**. The repository's default branch is `master`, not `main`. Retrieved from `master` instead.
- `https://raw.githubusercontent.com/anthropics/skills/main/spec/README.md` — **404**. The spec directory contains exactly one file, `spec/agent-skills-spec.md`, which is now an 87-byte pointer to `https://agentskills.io/specification`. **The specification is no longer in the anthropics/skills repository.** Anything that cites `anthropics/skills` as the spec source is citing a redirect.
- `https://agentskills.io/specification` (HTML) — returned 200 but the fetch returned raw Next.js/Mintlify markup, not prose. Re-fetched the Mintlify-provided `.md` variant, which worked. Same for `agentskills.io/home`.
- `https://skillsmp.com/submit` — **404, "Page Not Found"**. No submission form exists at that path.
- `https://raw.githubusercontent.com/Vercel-labs/...` — not used; `vercel-labs/agent-skills` has its content at repo root plus `packages/`, which I did **not** open.
- No access to `skills.sh`, the registry behind `npx skills add`. I did not find or read the source repository for that CLI. **Every claim about `npx skills add` in this document is inference from install commands quoted in READMEs, not from reading the tool.**
- `skills-ref` (the reference validator named by the spec, at `github.com/agentskills/agentskills/tree/main/skills-ref`) — **not read.** I only know the spec tells you to run `skills-ref validate ./my-skill`. I do not know what it checks beyond "frontmatter is valid and follows all naming conventions," nor whether it is packaged on npm/PyPI.
- The Composio "Creating Skills" section of their README — not reached (file truncated at 12,000 bytes).
- `alirezarezvani/claude-skills` — I did not open any individual skill, nor their `.claude-plugin/` manifests. Their claimed "388 skills" and "118 agents" are their own claims, unverified.
- `google-gemini/gemini-cli` — I read its two skills documentation files. I did **not** read its implementation. I therefore cannot say whether Gemini CLI supports an `agents/` surface for subagent roles.

### Claims that are inference, not reading

1. That `npx skills add` performs no manifest validation. **Inference** from the fact that Anthropic's, Google's, and Vercel's READMEs all present it as a bare `npx skills add owner/repo` with no manifest step, while every *plugin* path does require a manifest.
2. That no ecosystem publisher uses a nested `skills/<sub-skill>/` **inside** a skill directory. I verified this rigorously for `anthropics/skills` (full 511-path recursive tree: zero paths with more than one `skills/` segment). For the other eight repositories I checked the READMEs only. **This is a strong signal, not a proof.**
3. That a candidate role "would not compete for the trigger signal." This is a judgement about *this* kernel's descriptions, made by reading the six role files' intent. It is not something any source states.
4. Byte-versus-character counts in Q3. The kernel's `description` is a single line, so bytes and characters coincide; I measured with `wc -c`.

---

## Q1: Formats and conventions

### The canonical layout is not in dispute

The spec at `https://agentskills.io/specification.md` fixes it:

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

Three directories have meaning. Everything else is explicitly permitted and
undefined. This matters: `agents/`, `tools/`, `knowledge/`, `evaluation/`,
`examples/`, `docs/`, and `research/` are all legal and all opaque to a client.
A client that does not know what a directory is for will not read it, which is
the correct behaviour and also means those directories are invisible to
discovery, indexing, and validation.

**The same three directories appear in every source checked**, with the same
meanings and no additions:

- `https://agentskills.io/specification.md` — normative
- `https://raw.githubusercontent.com/agentskills/agentskills/main/README.md` — same tree
- `https://raw.githubusercontent.com/vercel-labs/agent-skills/main/AGENTS.md` — adds a fourth, `lib/` for shared script code, described as "Optional: shared code for scripts"
- `https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills-best-practices.md` — same four entries, `SKILL.md` / `scripts/` / `references/` / `assets/`
- `https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md` — "Anatomy of a Skill" section: `SKILL.md` plus `scripts/`, `references/`, `assets/`

### Frontmatter: two required fields, four optional, and a hard division between them

From the spec table at `https://agentskills.io/specification.md`:

| Field | Required | Constraint |
|---|---|---|
| `name` | **Yes** | 1–64 chars; unicode lowercase alphanumerics and hyphens only; no leading, trailing, or consecutive hyphens; **must match the parent directory name** |
| `description` | **Yes** | 1–1024 chars; must describe what it does *and* when to use it |
| `license` | No | "License name or reference to a bundled license file" |
| `compatibility` | No | ≤500 chars; environment requirements |
| `metadata` | No | arbitrary string→string map |
| `allowed-tools` | No | space-separated pre-approved tools. **Marked Experimental.** "Support for this field may vary between agent implementations" |

**Universal vs vendor-specific, precisely:**

- `name` and `description` are universal. `https://raw.githubusercontent.com/anthropics/skills/main/README.md` reduces them to exactly these two ("The frontmatter requires only two fields"), and every other source agrees. The Composio list states it independently: "a `SKILL.md` file with YAML frontmatter (name, description) and Markdown instructions."
- `license`, `compatibility`, `metadata`, `allowed-tools` are spec-level but **not universal in practice**. No repository I read uses `compatibility` in a shipped `SKILL.md`. The Anthropic `skill-creator` lists `compatibility` as a field to fill in ("Required tools, dependencies (optional, rarely needed)") but the shipped `skill-creator/SKILL.md` frontmatter contains only `name` and `description`.
- `allowed-tools` is the weakest field in the spec. Nothing I read uses it, and the spec itself calls it experimental.
- **Vendor-specific frontmatter appears only in plugin manifests, never in `SKILL.md`.** Claude Code's `plugin.json` uses `name`/`description`/`author{name,email}` plus a `displayName` convention; Codex's `plugin.json` adds `version`, `homepage`, `developerName`, `longDescription`, `interface.brandColor`/`brandColorDark`/`capabilities`/`compose`, `capabilities[]`, `defaultPrompt`, `privacyPolicyURL`, `screenshots[]`, `logo`, `composeVersion`, `websiteURL`. Neither is a `SKILL.md` concern.

### Size limits and description conventions

Two numbers, consistently repeated, and they are recommendations rather than
validation rules:

- **Metadata: ~100 tokens.** Spec: "The `name` and `description` fields are loaded at startup for all skills." Gemini CLI: "~100 words". Vercel `AGENTS.md`: "only the skill name and description are loaded at startup." `VoltAgent/awesome-agent-skills` "Skill Quality Standards": "Keep top-level metadata under ~100 tokens."
- **Body: under 500 lines and under 5,000 tokens.** Spec: "Keep your main `SKILL.md` under 500 lines." `skill-creator/SKILL.md`: "`<500 lines ideal`" and "These word counts are approximate and you can feel free to go longer if needed." Vercel `AGENTS.md`: "Keep SKILL.md under 500 lines." awesome-agent-skills: "Skill body should stay below 500 lines."

The one rule the spec states about body content is about *reference depth*:
"Keep file references one level deep from `SKILL.md`. Avoid deeply nested
reference chains."

On description style, the sources agree and pull in the same direction:

- Third person, what + when (`awesome-agent-skills` quality criteria).
- "Use imperative phrasing… 'Use this skill when…' rather than 'This skill
  does…'" (`https://agentskills.io/skill-creation/optimizing-descriptions.md`).
- Concrete keywords agents can match on, not categories
  (`awesome-agent-skills`: `"PostgreSQL migration" not "database stuff"`).
- **Be pushy.** The spec's optimisation guide: "Err on the side of being pushy…
  even if they don't explicitly mention 'CSV' or 'analysis.'" `skill-creator/SKILL.md`
  is blunter: "currently Claude has a tendency to 'undertrigger' skills… please
  make the skill descriptions a little bit 'pushy'."
- Vercel's `AGENTS.md` asks for trigger phrases verbatim in the description:
  "Include trigger phrases like 'Deploy my app', 'Check logs', etc."

The Composio list adds the token arithmetic that explains the pressure
(`https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/master/README.md`):
"roughly 100 tokens per skill… The full SKILL.md body (typically under 5,000
tokens) loads only when the agent decides the skill is relevant."

### Directory conventions per client

From the table in `https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/README.md`
("Skills Paths for Other AI Coding Assistants"), and independently confirmed for
Gemini CLI in `docs/cli/skills.md`:

| Tool | Project path | Global path |
|---|---|---|
| Antigravity | `.agents/skills/` | `~/.gemini/config/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `.github/skills/` | `~/.copilot/skills/` |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Windsurf | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |

Gemini CLI's docs add a discovery-precedence rule worth noting: four tiers
(built-in → extension → user → workspace), and within a tier the `.agents/skills/`
alias beats `.gemini/skills/`. `.agents/skills/` is described as "an interoperable
path for managing agent-specific expertise that remains compatible across
different AI tools." Codex and Antigravity use the same `.agents/skills/` path.
**`.agents/skills/` is the emerging cross-vendor project path.**

### Do any use `agents/` for subagent roles?

**Yes, in two mutually incompatible senses. This is the most important finding
in Q1.**

**(a) Inside a skill, `agents/` holds delegated role prompts as plain Markdown,
with no frontmatter.** Verified by the complete recursive tree of
`anthropics/skills` — the only `agents/` paths in all 511 entries are:

```
skills/skill-creator/agents/analyzer.md
skills/skill-creator/agents/comparator.md
skills/skill-creator/agents/grader.md
```

I read `grader.md` in full. It begins `# Grader Agent` — a level-one heading,
**no YAML frontmatter at all**. Its structure is: Role, Inputs, Process (numbered
steps), Grading Criteria, Output Format (a JSON schema), Field Descriptions,
Guidelines. It is a role prompt for a subagent, loaded as a document, not a
registered agent.

This is a direct precedent for the kernel's `agents/` convention: a directory of
role prompts inside a skill, addressed by the kernel, not independently
discoverable. Note the overlap with the kernel's own vocabulary — Anthropic ships
`grader.md` and `comparator.md`, and the kernel has `grader.md` and
`comparator.md`.

**(b) At a Claude Code *plugin* root, `agents/` holds real subagent definitions
with a different frontmatter schema.** From
`https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/code-simplifier/agents/code-simplifier.md`:

```yaml
---
name: code-simplifier
description: Simplifies and refines code for clarity, consistency, and
  maintainability while preserving all functionality. Focuses on recently
  modified code unless instructed otherwise.
model: opus
---
```

and from `plugins/code-modernization/agents/security-auditor.md`:

```yaml
---
name: security-auditor
description: Adversarial security reviewer — OWASP Top 10, CWE, dependency CVEs,
  secrets, injection. Use for security debt scanning and pre-modernization hardening.
tools: Read, Glob, Grep, Bash
---
```

So the plugin-level subagent schema is `name` + `description` + optional `model`
+ optional `tools` (comma-separated). The full 778-path tree of
`claude-plugins-official` contains 35 such agent files across `agent-sdk-dev`,
`claude-security`, `code-modernization`, `code-simplifier`, `feature-dev`,
`hookify`, `plugin-dev`, `pr-review-toolkit`, and `skill-creator`.

**The two senses collide, and the collision is a distribution risk.** `agents/`
at plugin root means "Claude Code subagents, will be registered and offered to
the user." `agents/` inside a skill means "role prompts the kernel reads." A
package that is both a plugin and a skill, or that gets its `agents/` lifted to a
plugin root by an installer script, changes the meaning of every file in that
directory without changing a byte. Codex has the same `agents/` surface
(`openai/plugins` README: "plugin-level `agents/`").

### Do any use a nested `skills/` for sub-skills?

**No. Not in any source I could read, and this is a genuine deviation.**

The `skills/` directory appears in exactly two roles across the ecosystem:

1. **A collection root** — `anthropics/skills/skills/` holds 12+ skills at repo
   level. `claude-plugins-official` plugins carry `skills/` at plugin root.
   `google/skills/skills/`, `openai/skills/skills/`. In every case it is a peer
   set, not a child.
2. **Never a child.** The full recursive tree of `anthropics/skills` (511 paths)
   contains **zero** paths with more than one `skills/` segment. I filtered for
   exactly that and got an empty array. No shipped skill anywhere in that repo
   contains a sub-skill.

The spec permits it — `... # Any additional files or directories` — and the
marketplace mechanism actively supports deep skill paths. From
`https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/README.md`:

> "Paths can reach deeper than a single level — for example,
> `["./libA/skill-1", "./libB/skill-2"]` exposes a curated subset across multiple
> library subdirectories."

That sentence is about the *marketplace entry's* paths, not about a skill
declaring a sub-skill. The ecosystem's answer to "I need a sub-capability" is a
peer skill in the same plugin, addressed by the parent skill's instructions —
not a nested directory.

There is a second, concrete reason to be careful. Client discovery scans
conventional locations (`.claude/skills/`, `.agents/skills/`, …). Those scanners
are shallow, but a nested `skills/skill-creator/SKILL.md` is a `SKILL.md` at a
plausible skill root, and aggregators that recurse — including SkillsMP, which
"collects 3M+ `SKILL.md` files from public GitHub repositories"
(`https://skillsmp.com/about`) — will find it. Whether it appears as a top-level
listing or as a nested one, `ultimate-dev/skill-creator` will exist in the index
as a separate skill with a description that begins "Create, extend, compose,
validate, and retire reusable skills when the kernel hits a capability gap." That
description competes with the kernel's own claim on skill-creation intent. See Q4.

---

## Q2: Capability gaps

The six existing roles are `verifier`, `investigator`, `critic`, `grader`,
`comparator`, `author`. The question is which commonly-available role covers a
capability none of them covers, and would not compete for the trigger signal.

Note that `critic` and `comparator` are adjacent to several candidates below, and
that `author` covers writing but not *documentation*. The verdicts are mine.

| Candidate role | Commonly present? | What it does | Conflicts with an existing role? | Verdict |
|---|---|---|---|---|
| **Security reviewer / red-teamer** | **Yes, very.** Trail of Bits ships a whole security section in awesome-agent-skills (`differential-review`, `static-analysis`, `variant-analysis`, `insecure-defaults`, `property-based-testing`, `building-secure-contracts`, `entry-point-analyzer`, `constant-time-analysis`). `google/skills` has ~18 security skills including `secops-triage`, `secops-hunt`, `secops-investigate`, `gke-workload-security`. `agency-agents` has a 12-role Security Division. `claude-plugins-official` has 7 agents in `claude-security` plus `security-auditor` in `code-modernization`. | Assume the code is hostile; trace user-controlled input to sinks; check auth, access control, deserialization, SSRF, secrets, misconfiguration; run SAST but read the code; redact secrets in output. It is an *adversary* role: its job is to find the thing verification assumes absent. | **No.** `verifier` checks whether a stated claim matches observed evidence — a correctness role. `critic` argues against a position. Neither has an attack model, a threat surface, or an exploitability judgement. `security-auditor.md` is explicitly framed as a different thing: "Assume the code is hostile until proven otherwise." | **ADD.** Highest value, zero trigger competition, and it is the one role whose absence the ecosystem treats as conspicuous. |
| **Dependency / license auditor** | **No — this is the interesting negative result.** I keyword-scanned the full 220KB awesome-agent-skills README for `supply`, `supply-chain`, `sbom`, `SBOM`, `renovate`, `dependabot`, `ossf`, `Scorecard`, `License Audit`, `dependency`. Only `dependency` matched, and the hits were n8n configuration skills ("Node configuration with dependency rules"), not auditing. No repository ships a dependency-provenance or license-compliance role. | Would audit transitive dependency risk, licence compatibility, and provenance. | No conflict — but there is no ecosystem definition to draw from, and the role is largely mechanical, which the spec argues should be a `scripts/` entry, not a role prompt. | **SKIP as a role.** If wanted, it belongs as a `scripts/` capability the kernel invokes, not a seventh agent. Rare in the ecosystem because the tooling is mature. |
| **Technical writer / documentation** | **Yes.** `agency-agents` ships `engineering/engineering-technical-writer.md` ("Developer docs, API reference, tutorials"). Vercel ships `writing-guidelines` (80+ rules, "Review docs and prose for compliance with the Vercel writing handbook"). Google ships `google-cloud-filestore-nfs-browser`-style API reference patterns. | Produce or audit reference documentation against a real interface. | **Partially.** `author` writes *the deliverable*; a technical writer writes *about* the deliverable. Different artefact, different trigger. But the word "write" makes description overlap likely, and the trigger discipline is the one the kernel is most protective of. | **SKIP.** Highest collision risk per unit of added capability. If you want this, gate it through `author` with a mode rather than adding a role that can be reached independently. |
| **Test author** | **Yes.** Anthropic ships `webapp-testing` (Playwright). `claude-plugins-official` ships `test-engineer` in `code-modernization` ("characterization, contract, and equivalence tests"). `agency-agents` has a 9-role Testing Division including `Test Automation Engineer` and `API Tester`. Trail of Bits ships `property-based-testing` and `testing-handbook-skills`. | Write tests that pin behaviour, especially equivalence and characterization tests before a rewrite. | **Overlaps `verifier` at the artefact level** (a test is evidence) and `grader` at the judgement level. The distinguishing content — *characterization before transformation* — is a technique, not a role. | **SKIP as a role; consider as a reference file** under the existing verifier. Anthropic's own `test-engineer` is scoped to a migration workflow, which is domain content your kernel is explicitly built not to carry. |
| **Performance / optimization reviewer** | **Yes, but always domain-bound.** Vercel: `vercel-optimize`, `react-best-practices` (40+ rules, prioritised Critical→Low). Google: six Well-Architected Framework pillar skills, one of which is `google-cloud-waf-performance-optimization`. `agency-agents`: `Performance Benchmarker`, `Database Optimizer`, `Autonomous Optimization Architect`. CodeRabbit, Sentry, and Datadog Labs all ship review skills. | Measure first, then investigate only what the measurement points at. `vercel-labs` states the method in one line: "It collects Vercel metrics first, then investigates only the routes and files those metrics point to." | **Yes, seriously.** A performance role's description will match "make this faster," which is a request the kernel already handles at R0. This is the clearest case of two skills both firing on one signal. Also, every instance I found is vendor-specific by construction. | **SKIP.** Conflicts with the kernel's own trigger, and conflicts with your rule 1 (one kernel, no domain paths). |
| **Simplification / code-review** | **Yes, and it is the closest to what you already have.** `claude-plugins-official` ships `code-simplifier` as a **standalone plugin** with its own agent, and a second `code-simplifier` inside `pr-review-toolkit` alongside `code-reviewer`, `pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`, `comment-analyzer`. `agency-agents` has `Code Reviewer` and a distinct `Minimal Change Engineer` ("Minimum-viable diffs — Fixing only what's asked, no scope creep"). | Simplify while preserving exact behaviour; focus on recently modified code; read as a review. | **Yes.** `critic` already argues against a position and `verifier` already checks claims against evidence. A simplifier is a third voice on the same artefact, and `Minimal Change Engineer` is a restatement of your effort gate. | **SKIP.** This is the clearest duplication. Anthropic shipping it as its own plugin is evidence that it is a *product*, not a missing capability. |

### The recommendation

**Add one role: a security reviewer.** Everything else in your list is either
already covered by `critic`/`verifier`/`grader`, is domain-bound by construction,
or would compete for the trigger signal you have explicitly protected.

The security reviewer earns its place on three independent grounds:

1. **It is the most densely populated role in the ecosystem after code review.**
   Trail of Bits alone contributes a dozen security skills; `google/skills`
   contributes ~18; `agency-agents` dedicates an entire 12-role division to it;
   Anthropic's official plugin directory ships seven `claude-security` agents.
2. **It is structurally unlike your existing six.** Every one of the six
   evaluates: a claim against evidence (`verifier`), a problem against available
   context (`investigator`), a position against its support (`critic`), an output
   against an expectation (`grader`), two options against each other
   (`comparator`), a gap against the world (`author`). A security reviewer does
   not evaluate a claim — it *manufactures* an attack. That is why it does not
   duplicate any of them, and it is the same reason the ecosystem keeps splitting
   it into distinct roles: `security-architect` (threat modelling) versus
   `security-auditor` (adversarial review) versus `patch-verifier` (does the fix
   hold).
3. **It is the natural counterpart to your rule 5.** Rule 5 says nothing
   self-promotes — a generated skill stays a candidate until security-reviewed,
   adversarially tested, and explicitly promoted. Your promotion gate names a
   role you do not have. The kernel currently enforces rule 5 by assertion. A
   security-reviewer agent makes it enforceable: the promotion gate becomes a
   role that produces evidence, in the same way `verifier` produces evidence for
   an ordinary claim.

The second, weaker candidate, if you want two: **a `patch-verifier`-style role
for the promotion gate specifically** — does the remediation actually close the
finding, or only silence it. Anthropic ships exactly this as a separate agent
(`claude-security/agents/patch-verifier.md`), which is evidence that the
ecosystem finds it separable. Do not add it as a general reviewer; add it as the
promotion-gate step if and only if you add the security reviewer.

**Do not add a technical writer, a test author, or a performance reviewer.** In
each case the trigger would be reachable independently of the kernel's decision,
which is the failure mode your rule 4 exists to prevent. A performance reviewer
is worse than useless here: "make this faster" is an R0 request, and two skills
answering it is precisely the two-half-processes outcome you designed against.

---

## Q3: Distribution requirements

### The Agent Skills format itself: no submission, no manifest, no registry

A skill is publishable the moment it is a directory with a valid `SKILL.md` in
a public Git repository. There is no central registry with a form. The
specification's only instruction for the author is:

> "Use the [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)
> reference library to validate your skills: `skills-ref validate ./my-skill`.
> This checks that your `SKILL.md` frontmatter is valid and follows all naming
> conventions."

Minimum to be *valid*: `SKILL.md` with `name` matching the directory name, and a
`description` under 1024 characters. Nothing else.

### `npx skills add owner/repo` — the widest-reach distribution path

Used verbatim by `google/skills` (`npx skills add google/skills`), Vercel
(`npx skills add vercel-labs/agent-skills`), the Composio list, and
`VoltAgent/awesome-agent-skills` (which documents `npx skills add
mblode/agent-skills --skill {skill-name}`). `skills.sh` is the index.

**Inference, flagged as such:** no manifest is required or requested. Every
author-documented install is a bare `owner/repo` pair with an optional
`--skill` flag. Vercel additionally publishes an "Agent Skills discovery index"
as a GitHub release on every change to `main` — `node scripts/build-discovery-index.mjs`
— which suggests discovery works off repository structure, not a submitted
record. I could not read the tool.

### Claude Code plugin marketplace: a manifest IS required

From `https://github.com/anthropics/claude-plugins-official`:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── .mcp.json            # MCP server configuration (optional)
├── commands/            # Slash commands (optional)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
└── README.md            # Documentation
```

`plugin.json` in the reference implementation is four fields:

```json
{
  "name": "example-plugin",
  "description": "A comprehensive example plugin ...",
  "author": { "name": "Anthropic", "email": "support@anthropic.com" }
}
```

**Naming, and the one hard rule in this whole document:** the plugin `name` is
an **immutable slug**.

> "The `name` field in a marketplace entry is an **immutable slug**. Once a
> plugin has been published, its `name` must not change — users have it
> installed under that slug, and renaming it breaks their install with a
> `plugin-not-found` error."
>
> "To change how a plugin is labeled in the UI, set or update `displayName`
> instead." … "add an entry to the top-level `renames` map in
> `.claude-plugin/marketplace.json` so existing installs auto-migrate."

**Skill-bundle plugins** — the shape you would use — need no `plugin.json` at
all, only a marketplace entry with `strict: false` and an explicit `skills`
array. Real example from `anthropics/skills/.claude-plugin/marketplace.json`:

```json
{
  "name": "document-skills",
  "description": "Collection of document processing suite ...",
  "source": "./",
  "strict": false,
  "skills": ["./skills/xlsx", "./skills/docx", "./skills/pptx", "./skills/pdf"]
}
```

The same file's top level carries `name`, `owner{name,email}`, and
`metadata{description,version}`. Each skill is registered as
`<plugin-name>:<skill-name>` in Claude Code.

**Submission process:** third-party partners use a form,
`https://clau.de/plugin-directory-submission`, and "External plugins must meet
quality and security standards for approval." I did not read the form or the
standards.

**Directory layout for a skill-bundle plugin** is therefore: a git repo, one
`SKILL.md` per skill in a directory, and a `.claude-plugin/marketplace.json`
that enumerates them. Nothing else is required.

### Codex: `.codex-plugin/plugin.json` is required

From `https://raw.githubusercontent.com/openai/plugins/main/README.md`:

> "Each plugin lives under `plugins/<name>/` with a required
> `.codex-plugin/plugin.json` manifest and optional companion surfaces such as
> `skills/`, `.app.json`, `.mcp.json`, plugin-level `agents/`, `commands/`,
> `hooks.json`, `assets/`, and other supporting files."
>
> "The default marketplace lives at `.agents/plugins/marketplace.json`… API key
> login users have a separate marketplace at `.agents/plugins/api_marketplace.json`."

`plugins/notion/.codex-plugin/plugin.json` (read via the GitHub API, base64
content) shows the observed field set: `apps`, `author{email,name,url}`,
`description`, `homepage`, `interface{brandColor,brandColorDark,capabilities[]}`,
`longDescription`, `logo`, `logoDark`, `defaultPrompt`, `privacyPolicyURL`,
`screenshots[]`, `shortDescription`, `websiteURL`.

Marketplace entries (`.agents/plugins/marketplace.json`) carry `name`,
`source{source:"local",path:"./plugins/linear"}`, `policy{installation:"AVAILABLE",authentication:"ON_INSTALL"}`,
`category`, and a file-level `interface{displayName:"Codex official"}`.

**`openai/skills` is deprecated.** Its README carries an explicit banner: "This
repository is deprecated. For current Codex skill and plugin examples, use the
OpenAI Plugins repository. If you want to add your own skills to Codex, follow
the Build plugins guide." It also has a per-skill licence convention:

> "The license of an individual skill can be found directly inside the skill's
> directory inside the `LICENSE.txt` file."

Confirmed on disk: `anthropics/skills/skills/skill-creator/LICENSE.txt` exists
in that repository's tree. **Per-skill `LICENSE.txt` is the OpenAI convention.**

### Gemini CLI

No manifest. Discovery is by directory. From
`https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills.md`:
tiers are built-in → extension → user (`~/.gemini/skills/` or `~/.agents/skills/`)
→ workspace (`.gemini/skills/` or `.agents/skills/`). Install is
`gemini skills install <git-url> --path <subdir> --consent`, and there is an
explicit **consent prompt** on activation and install: "You will see a
confirmation prompt in the UI detailing the skill's name, purpose, and the
directory path it will gain access to." A published skill gains filesystem
permission to its own directory, and the user is told.

### Google: the one repository that ships all three surfaces

`google/skills` carries `.claude-plugin/`, `.agents/plugins/`, `plugins/cloud/`,
`index.json`, and per-skill directories under `skills/`. Its README documents
installation for three harnesses from one repo: `claude plugin marketplace add
google/skills`, `codex plugin marketplace add google/skills`, and
`agy plugin install https://github.com/google/skills/<plugin-path>`. The
`index.json` at root is a discovery manifest I did not read.

### SkillsMP: a crawler, not a registry

`https://skillsmp.com/about`, read in full:

> "Collect 3M+ `SKILL.md` files from public GitHub repositories… Skills are
> sourced from public GitHub repositories. Always review code before
> installation."

There is **no submission process I could find.** `https://skillsmp.com/submit`
returns 404. The site is an independent community project, explicitly "not
affiliated with Anthropic or OpenAI," and offers an API for third-party search.
**Consequence: publication to SkillsMP is a consequence of being public on
GitHub, not an action you take.** It also means a nested
`skills/skill-creator/SKILL.md` will be indexed as a distinct skill.

### `allowed-tools` and `license`: what actually requires them

**`allowed-tools`:** required by nobody. It is spec-optional, marked
Experimental, and no `SKILL.md` I read uses it. Do not add it speculatively; add
it if a specific client needs it and document which.

**`license`:** spec-optional, and the recommendation is to keep it short — "either
the name of a license or the name of a bundled license file." But the *file*
convention is real and split by publisher:

| Publisher | Convention |
|---|---|
| `anthropics/skills` | Apache-2.0 for most; `docx`/`pdf`/`pptx`/`xlsx` are "source-available, not open source"; per-skill `LICENSE.txt` |
| `agentskills/agentskills` | "Code in this repository is licensed under Apache 2.0. Documentation is licensed under CC-BY-4.0" |
| `openai/skills` | per-skill `LICENSE.txt` inside the skill directory |
| `google/skills` | repo-root Apache 2.0; "You are free to copy, modify, and distribute" |
| `vercel-labs/agent-skills` | repo-root MIT |
| `msitarzewski/agency-agents` | MIT |
| `alirezarezvani/claude-skills` | MIT |
| `claude-plugins-official` | Apache-2.0 repo licence; "Please see each linked plugin for the relevant LICENSE file" |
| `awesome-agent-skills` | MIT, and an explicit non-endorsement clause |

The `awesome-agent-skills` disclaimer is worth copying verbatim in spirit:

> "This is a curated list. Skills listed here are created and maintained by their
> respective authors and teams, not by us… we do not audit, endorse, or
> guarantee the security or correctness of listed projects. They are not
> security-audited and should be reviewed before production use."

---

## Q4: Anti-patterns to check against

Everything in this section is quoted or paraphrased from a source I read. Grouped
by which of your five kernel rules each one bears on.

### Bearing directly on rule 4 (sub-skills must not compete for the trigger)

> "**Avoid overlap**: Ensure your skill descriptions are distinct from one
> another and from the general capabilities of the model."
> — `https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills-best-practices.md`

This is the external validation of your rule 4, stated as a best practice by a
vendor. Gemini CLI also enforces precedence mechanically (higher-precedence
location wins, `.agents/skills/` beats `.gemini/skills/`) — but that resolves
*which copy wins*, not *whether two descriptions both match*. Your framing is
sharper than the published one: you are not worried about precedence, you are
worried about both firing.

The complementary failure is documented in
`https://agentskills.io/skill-creation/optimizing-descriptions.md`: build
should-not-trigger queries that are **near-misses** —

> "The most valuable negative test cases are **near-misses** — queries that share
> keywords or concepts with your skill but actually need something different.
> These test whether the description is precise, not just broad."

Weak negatives ("What's the weather today?") "test nothing." A trigger eval for
a kernel should be built almost entirely of near-misses against the six existing
roles.

### Bearing on the effort gate (your #1 defect)

> "**Aim for moderate detail.** Overly comprehensive skills can hurt more than
> they help — the agent struggles to extract what's relevant and may pursue
> unproductive paths triggered by instructions that don't apply to the current
> task."
> — `https://agentskills.io/skill-creation/best-practices.md`

And the observation about why:

> "Read agent execution traces, not just final outputs. If the agent wastes time
> on unproductive steps, common causes include instructions that are too vague
> (the agent tries several approaches before finding one that works),
> instructions that don't apply to the current task (the agent follows them
> anyway), or too many options presented without a clear default."

That third clause is the published name for your over-orchestration defect, and
the fix it names is a default, not a shorter document.

> "**Provide defaults, not menus.** When multiple tools or approaches could work,
> pick a default and mention alternatives briefly rather than presenting them as
> equal options."
> — same page

### Bearing on rule 1 (one kernel, no domain paths)

> "**Design coherent units.** … Skills scoped too narrowly force multiple skills
> to load for a single task, risking overhead and conflicting instructions.
> Skills scoped too broadly become hard to activate precisely."
> — same page

This is the trade-off stated in one sentence, and it is the strongest published
support for your rule 1: a universal kernel is *deliberately* broad, and the
published cost of breadth is imprecise activation. Your R0–R4 gate is the
mechanism that pays that cost. Nothing in the ecosystem offers an equivalent, and
that is a real argument for your design.

### Bearing on rule 3 (creation is last) and on the author role

> "A common pitfall in skill creation is asking an LLM to generate a skill
> without providing domain-specific context — relying solely on the LLM's general
> training knowledge. The result is vague, generic procedures ('handle errors
> appropriately,' 'follow best practices for authentication') rather than the
> specific API patterns, edge cases, and project conventions that make a skill
> valuable."
> — same page

And the per-token test that should govern `author`:

> "Ask yourself about each piece of content: '**Would the agent get this wrong
> without this instruction?**' If the answer is no, cut it."

> "**Favor procedures over declarations.** A skill should teach the agent *how to
> approach* a class of problems, not *what to produce* for a specific instance."
> — same page

### Bearing on rule 5 (nothing self-promotes)

> "**Principle of Lack of Surprise.** This goes without saying, but skills must
> not contain malware, exploit code, or any content that could compromise system
> security. **A skill's contents should not surprise the user in their intent if
> described.** Don't go along with requests to create misleading skills or skills
> designed to facilitate unauthorized access, data exfiltration, or other
> malicious activities. Things like a 'roleplay as an XYZ' are OK though."
> — `https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md`

Note the escape hatch: persona skills are explicitly fine. That matters for a
`security-auditor` role, which must be able to say "assume hostile" without
tripping this rule — it is a declared intent, not a concealed one.

> "**Security and privacy.** … **Avoid hardcoded secrets** … **Review third-party
> skills**: Inspect the `SKILL.md` and scripts of any skill before installing it
> from an untrusted source. **Limit scope**: Design skills to be as focused as
> possible to minimize the potential impact of errors."
> — Gemini CLI best practices

> "We recommend installing skills only from trusted sources. When installing a
> skill from a less-trusted source, thoroughly audit it before use… pay
> particular attention to code dependencies and bundled resources… pay attention
> to instructions or code within the skill that instruct Claude to connect to
> potentially untrusted external network sources."
> — `https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills`

The network-source clause is the one to check the kernel against specifically: the
kernel's "acquire external" rung in its capability resolution order is exactly the
mechanism this warns about. If the kernel can direct the agent to fetch an
external capability, the acquisition step should require the same scrutiny the
ecosystem applies to installing a skill.

> "Agent skills can include prompt injections, tool poisoning, hidden malware
> payloads, or unsafe data handling patterns. Always review the code and use
> skills at your own discretion."
> — `https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/README.md`

### The published quality criteria, in full

`awesome-agent-skills` "Skill Quality Standards" is the only consolidated
checklist I found. All four rows:

| Area | Guideline |
|---|---|
| Description | Write in third person. State *what* the skill does and *when* to use it. Use specific keywords agents can match on (e.g., "PostgreSQL migration" not "database stuff"). |
| Progressive disclosure | Keep top-level metadata under ~100 tokens. Skill body should stay below 500 lines. Load resources (large docs, schemas) on demand, not inline. |
| No absolute paths | Never hard-code machine-specific paths like `/Users/alice/`. Use relative paths or well-known variables (`$HOME`, `$PROJECT_ROOT`). |
| Scoped tools | Request only the tools the skill actually needs. Avoid blanket `"tools": ["*"]`. Declare tool dependencies explicitly. |

Plus a submission policy worth reading as an anti-signal:

> "**Please don't submit skills you created 3 hours ago.** We're now focusing on
> community-adopted skills, especially those published by development teams and
> proven in real-world usage. Quality over quantity."

The repository header makes the same point: "Unlike many bulk-generated skill
repositories, this collection focuses on real-world Agent Skills created and used
by actual engineering teams, not mass AI-generated stuff." There is an
established, named failure mode here: bulk-generated skill repositories. The
ecosystem treats volume as a defect signal.

### Writing-style anti-patterns

> "Try to explain to the model **why** things are important in lieu of
> heavy-handed musty MUSTs. Use theory of mind and try to make the skill general
> and not super-narrow to specific examples."
> — `skill-creator/SKILL.md`

> "**Prefer using the imperative form** in instructions."
> — same

And the calibration guidance, which is the closest published analogue to your R0–R4
effort gate:

> "**Match specificity to fragility.** Give the agent freedom when multiple
> approaches are valid and the task tolerates variation… **Be prescriptive** when
> operations are fragile, consistency matters, or a specific sequence must be
> followed. Most skills have a mix. Calibrate each part independently."
> — `https://agentskills.io/skill-creation/best-practices.md`

### Evaluation anti-patterns

> "You have two jobs: grade the outputs, and critique the evals themselves.
> **A passing grade on a weak assertion is worse than useless — it creates false
> confidence.**"
> — `https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/agents/grader.md`

> "Weak assertions: 'The output is good' — too vague to grade. 'The output uses
> exactly the phrase "Total Revenue: $X"' — too brittle; correct output with
> different wording would fail."
> — `https://agentskills.io/skill-creation/evaluating-skills.md`

> "Avoid adding specific keywords from failed queries — that's overfitting.
> Instead, find the general category or concept those queries represent… If you
> are stuck after several iterations, try a **structurally different approach** to
> the description rather than incremental tweaks."
> — `optimizing-descriptions.md`

Trigger-rate methodology, if the kernel is ever measured this way: ~20 queries
(8–10 positive, 8–10 negative), 3 runs each, trigger rate threshold 0.5, and a
60/40 train/validation split because "the best description may not be the last one
you produced; an earlier iteration might have a higher validation pass rate than
later ones that overfit."

### The incremental-iteration pattern

> "**Start with evaluation:** Identify specific gaps in your agents' capabilities
> by running them on representative tasks and observing where they struggle…
> **Think from Claude's perspective:** Monitor how Claude uses your skill in real
> scenarios… Pay special attention to the `name` and `description`."
> — Anthropic engineering blog

### One anti-pattern specific to this kernel

Not published anywhere, but follows from the two published rules above. The
kernel's description is 654 characters — under the 1024 limit, but a substantial
share of the ~100-token metadata budget. `optimizing-descriptions.md` warns that
"descriptions tend to grow during optimization" and to check the limit each
iteration. If the kernel's description is ever tuned, its length is a budget, not
a formality.

---

## Open problems

Things I could not determine, listed so they are not mistaken for settled.

1. **Whether the nested `skills/skill-creator/` is safe in practice.** The
   format permits it and the marketplace mechanism supports deep paths, but I
   found zero shipped examples in the one repository I examined exhaustively. I
   did not check whether any client recursively discovers nested skills, whether
   `npx skills add` would install the sub-skill as a peer, or how
   `strict: false` marketplaces handle a sub-skill path. **The only certain
   statement is that it has no precedent, and that SkillsMP will index the nested
   `SKILL.md` as a separate skill.**

2. **What `skills-ref validate` actually enforces.** Named by the spec; source
   unread. If it validates more than frontmatter — for instance if it walks
   `references/` links — that would matter for a 47-file reference tree.

3. **Whether `allowed-tools` has working support anywhere.** The spec calls it
   experimental and no shipped skill uses it. I could not find a client that
   documents honouring it.

4. **The actual quality bar for marketplace inclusion.** The submission form at
   `https://clau.de/plugin-directory-submission` and the "quality and security
   standards for approval" it references were not read.

5. **Whether `npx skills add` performs any validation or manifest reading.**
   Inference only, flagged in the verification section.

6. **Gemini CLI's `agents/` support.** Its docs cover skills and extensions but I
   did not read the implementation, so I cannot say whether a Gemini-targeted
   build of this kernel could use `agents/` for anything other than a file a human
   reads.

7. **The distribution requirement for Antigravity, Cursor, Copilot, and
   OpenCode.** Paths are documented (Q1 table) but I did not read any of their
   marketplace or submission mechanisms.

8. **Whether the six existing roles' descriptions actually pass a near-miss
   trigger eval.** The published methodology is precise and cheap — 20 queries,
   3 runs, 0.5 threshold, 60/40 split. I did not run it. The near-miss cases
   (`critic` vs. a security reviewer; `verifier` vs. a test author; `author` vs. a
   technical writer) are exactly where it would find problems, and those are the
   same boundaries this survey had to judge by reading.

9. **Whether the kernel's own `description` triggers reliably.** 654 characters,
   429-line body, both within published limits. Whether the *word choice*
   triggers, and whether it over-triggers on requests the kernel should decline,
   is unmeasured. No trigger eval exists.

10. **What the ecosystem's `agents/` files contain that the kernel's do not.**
    I read `grader.md` in full, `code-simplifier.md` and `security-auditor.md`
    partially, and `test-engineer.md` partially. I did not read
    `comparator.md` or `analyzer.md` from Anthropic, nor the seven
    `claude-security` agents. The kernel's `grader.md` and `comparator.md` share
    names with Anthropic's; whether the contents are comparable is unknown and
    would be worth checking before adding a seventh role.
