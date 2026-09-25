# Classification Rules (Compact)

## ⚡ MANDATORY: Run on EVERY user message

**Do not skip. Do not wait for "use skill." This IS the classification workflow.**

Classification determines task size, domains, risk, clarity, and candidate
routing. It does not by itself determine the final implementation.

**Single source of truth for decision values and their calibration is
`router/behavioral-calibration.md`.** This file owns only the mechanics:
how to apply the capability index, select a specialist, and hand off work.
Do not restate the value vocabularies here; a change must land in one place.

---

## Step 1: Size

Apply the size calibration in `router/behavioral-calibration.md`.

- `atomic` — one local, low-coupling action or one concise answer.
- `moderate` — several dependent steps, one artifact, or a bounded feature.
- `complex` — multiple systems/domains, staged coordination, migration, regulated
  judgment, or substantial unfamiliarity needing safe bounded discovery.

Use the smallest accurate classification. Do not classify a task as complex
only because it touches multiple files. Unknown domain alone is not complexity.

---

## Step 2: Deliverable and Domain Match

Classify the requested **deliverable first**, then match **intent + repository
context + technology** to the Capability Index. A department is not a substitute
for understanding what the user wants to receive.

Do not rely on keywords alone. Broad words such as `design`, `analysis`, `data`,
`web`, `new`, or `systems` are hints only. Require a combination of intent,
deliverable, domain, and relevant context before selecting a specialist.

If no existing capability matches, use the safe fallback sequence:

1. classify the deliverable as `unknown` when it cannot be safely inferred;
2. load `skills/universal-task/SKILL.md`;
3. use the universal fallback only for a bounded, safe result;
4. report missing capabilities, assumptions, confidence, and limitations;
5. escalate material decisions to a human or qualified specialist.

For common department routing, prefer the compact
`config/capability-index.yaml`; the table below is a portable fallback for
hosts that do not load YAML configuration.

| Domain             | Keywords / Signals                                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| internal-communications | status update, meeting notes, decision memo, executive summary, stakeholder update, incident communication |
| strategy-operating-model | strategy, operating model, business model, OKR, KPI tree, value chain, capability map |
| data-bi            | dataset, analytics, dashboard, metric definition, data lineage, SQL analysis, visualization |
| finance-fpa        | budget, forecast, variance, cash flow, runway, P&L, unit economics, management accounts |
| accounting-controls | accounting, ledger, reconciliation, close, accrual, tax workflow, control evidence |
| legal-privacy-contracts | contract, clause, DPA, privacy, retention, legal hold, data governance, records |
| audit-risk-assurance | internal audit, control test, evidence request, finding, risk assessment, assurance |
| people-operations  | hiring, recruiting, onboarding, offboarding, workforce, employee relations, HR policy |
| procurement-vendors | procurement, vendor, supplier, RFP, RFQ, purchase order, due diligence, renewal |
| office-knowledge-artifacts | report, PDF, DOCX, XLSX, PPTX, spreadsheet, slide deck, meeting notes, knowledge base |
| automation-integrations | automation, workflow, webhook, schedule, API integration, MCP, idempotency, retry |
| prompt-skill-quality | prompt test, routing regression, golden cases, false activation, context budget, agent benchmark |
| backend            | API, server, endpoint, REST, gRPC, worker, queue, service, lambda, auth, Node.js, Python, Go, Java, GraphQL            |
| frontend           | UI, component, page, form, CSS, render, browser, SPA, SSR, responsive, React, Vue, Angular, Tailwind, accessibility    |
| architecture       | system design, tech stack, migration, scaling, CQRS, hexagonal, architecture, trade-off                                |
| database           | schema, query, index, migration, SQL, NoSQL, data model, slow query, PostgreSQL, MySQL, MongoDB, timeseries, analytics |
| security           | auth, PII, encryption, XSS, CSRF, vulnerability, secrets, RBAC, compliance, audit, penetration, threat, hardening      |
| devops             | deploy, CI/CD, Docker, K8s, Terraform, cloud, pipeline, monitoring, Kubernetes, production, zero-downtime, release     |
| mobile             | iOS, Android, React Native, Flutter, Swift, Kotlin, offline sync                                                       |
| testing-qa         | test, E2E, unit, integration, coverage, mock, flaky, QA, regression, test strategy, test architecture, automation    |
| documentation      | README, API docs, ADR, changelog, docstring, runbook                                                                   |
| project-management | sprint, backlog, ticket, story, epic, estimation, retrospective                                                        |
| product            | requirements, PRD, user story, roadmap, prioritization, feature spec                                                   |
| design-handoff     | wireframe, mockup, design token, typography, component spec, Figma                                                     |
| client-comms       | status update, progress report, blocker, scope change, timeline                                                        |
| marketing          | SEO, content, social media, email, growth, brand, conversion, blog                                                     |
| sales              | pipeline, prospecting, deal, proposal, CRM, forecast, demo, close                                                      |
| finance            | budget, revenue, cost, unit economics, P&L, pricing, margin                                                            |
| support            | ticket, helpdesk, knowledge base, CSAT, escalation, SLA                                                                |
| paid-media         | Google Ads, Meta Ads, PPC, retargeting, ROAS, CPC, campaign                                                            |
| research           | competitive analysis, market research, literature review, benchmark, evaluate, compare, analyze, investigate, best     |
| academic           | thesis, dissertation, citation, methodology, paper, journal                                                            |
| healthcare         | EHR, FHIR, HL7, HIPAA, clinical, patient, interoperability                                                             |
| game-dev           | game design, gameplay, Unity, Unreal, multiplayer, monetization                                                        |
| gis                | spatial, geospatial, map, coordinate, GeoJSON, spatial query                                                           |
| spatial-computing  | AR, VR, MR, headset, 3D UI, hand tracking, immersive, XR                                                               |
| specialized        | blockchain, IoT, embedded, robotics, HPC, CUDA, WebAssembly                                                            |

### Domain Rules

* A task can have multiple domains.
* Add a domain only when it materially contributes to the work.
* Do not create a separate domain for every technology mentioned.
* A technology mentioned only as context does not automatically require a
  separate specialist.
* `architecture` may be selected in addition to an implementation domain when
  architectural decisions materially affect the task.

---

## Step 3: Risk Flag

Apply the risk calibration in `router/behavioral-calibration.md`. Risk follows the
actual impact of the requested change, not topic sensitivity.

```text
risk: none | data | security | compliance
```

Add `security` for authentication/authorization, PII or sensitive data,
payments, secrets or credentials, security controls, regulated data, or a
production deployment with meaningful security impact.

Multiple risk categories may apply internally. The output should identify the
highest relevant risk and mention additional material risks when needed.

Do not infer compliance obligations without evidence.

---

## Step 4: Agent Selection

Only apply agent selection when the selected execution pattern actually
requires a specialist agent.

Read the agent registry/manifest before routing.

### Tiebreaker

```text
1. DELIVERABLE + EXACT CAPABILITY
   → common skill or agent directly matches the requested output and context

2. TECHNOLOGY MATCH
   → agent explicitly supports the technology in its compound triggers

3. DOMAIN GENERIC
   → generic-<domain>-specialist when execution is justified

4. UNIVERSAL TASK
   → universal-task skill for unknown/unclassified bounded work

5. UNIVERSAL SPECIALIST
   → universal-technology-specialist only when an actual execution role is needed

6. HUMAN REVIEW
   → report the capability gap when no safe route exists
```

### Selection Rules

* **Maximum 1 primary agent per domain.**
* Select by responsibility, not by file count.
* Do not spawn multiple agents for the same domain merely because multiple
  sub-specialties appear.
* An agent's `anti_triggers` always exclude that agent when matched.
* A stronger anti-trigger exclusion overrides a trigger match.

Examples:

```text
"Build a React login form"
→ frontend: react-specialist

"Fix Tailwind styling"
→ frontend: css-architect

"Improve WCAG accessibility"
→ frontend: accessibility-engineer

"Reduce bundle size"
→ frontend: perf-specialist

"Build a generic frontend feature"
→ frontend: generic-frontend-specialist

"Create test strategy for microservices"
→ testing-qa: test-architect

"Automate E2E tests with Playwright"
→ testing-qa: test-automator

"Run load testing with k6"
→ testing-qa: performance-tester

"Fix flaky integration tests"
→ testing-qa: qa-engineer

"Improve code quality with static analysis"
→ testing-qa: quality-engineer
```

For cross-domain work:

```text
backend + database + security
→ at most one primary agent for each selected domain
```

Do not create four frontend agents because the task contains React, CSS,
accessibility, and performance. Determine the primary responsibility and
select accordingly, unless genuinely independent validation is required.

---

## Step 5: Clarity Check

Classify clarity as defined in `router/behavioral-calibration.md`:

```text
clear | resolvable | blocked
```

Before asking the user, attempt to resolve ambiguity using:

1. User request
2. Repository structure
3. Existing implementation
4. Configuration
5. Project conventions
6. Project memory
7. Relevant skill/module documentation

If the missing decision materially changes the implementation **and cannot be
resolved from available context**, ask **one focused question**.

Do not ask the user to choose:

* an agent
* a pattern
* a workflow
* whether to use subagents
* an internal architecture of `ultimate-dev`

Those are model / intelligence decisions; the orchestrator coordinates their execution.

---

## Output

Emit only the fields required by the task envelope or the replay harness. The
field vocabulary, allowed values, and calibration examples live in
`router/behavioral-calibration.md` and `contracts/task-envelope.yaml`; do not
copy them here. The minimum decision record is:

```yaml
deliverable: <canonical value>
size: atomic | moderate | complex
clarity: clear | resolvable | blocked
risk: none | data | security | compliance
risk_basis: <required when risk is not none; one impact clause>
domains: [<canonical capability-index IDs>]
agents:
  - selected-agent-name
capability_gap:
  level: none | partial | blocking
  missing: []
```

Lint the record with `scripts/validate-routing-decision.py` when the host can run
it. It rejects unknown vocabulary, a raised risk with no named impact, and an
unfamiliar domain reported with no capability gap.

For atomic tasks, `agents` may be empty. For moderate tasks, select agents only
when specialist execution is actually needed. For complex tasks, list the
primary agent for each selected domain.

---

## Execution Handoff

After classification:

### Atomic

Execute inline.

```text
[tier: tiny | work: inline]
```

Do not introduce unnecessary orchestration.

### Moderate

Use the smallest useful specialist/skill structure.

```text
[tier: small | module: <name> | work: inline|specialist]
```

One specialist is normally sufficient when the task has one primary domain.

### Complex

Decompose by meaningful responsibility.

```text
[tier: small | module: <primary> | agents: <count> | coverage: partial|full]
```

Use Subagents, Handoffs, Router, or composition only when justified by the
task's dependencies and execution structure.

---

## Four-Channel Handoff

Before execution, make the handoff explicit:

- **Intent:** task envelope, acceptance criteria, unknowns, and risk.
- **Knowledge:** selected common skill, optional specialist, references, and
  assumptions.
- **Action:** requested capabilities, host-available capabilities, side-effect
  classification, and approval state.
- **Evidence:** checks, sources, artifacts, limitations, confidence, and next
  actions.

The portable contract is `contracts/task-envelope.yaml` and
`contracts/four-channels.md`. A prompt-only host may leave host capability
facts unknown and still complete a plan, explanation, or analysis.

---

## Important Execution Rule

Classification does **not** mean that every complex task must literally spawn
multiple agents.

The orchestrator must distinguish:

```text
agent selection
    ≠
actual subagent execution
```

If the host supports real subagent execution, use it.

If the host does not support real subagent execution, execute the selected
specialist role inline and report:

```text
execution_mode: inline
```

Never claim an agent was spawned when no real subagent was created.

---

## Core Principle

> **Classify every task, but orchestrate only as much as the task requires.**

The goal is not maximum agent count.

The goal is the **smallest safe execution structure that provides sufficient
domain coverage, verification, and correctness**.

