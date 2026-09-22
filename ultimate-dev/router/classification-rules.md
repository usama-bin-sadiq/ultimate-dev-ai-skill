# Classification Rules (Compact)

## ⚡ MANDATORY: Run on EVERY user message

**Do not skip. Do not wait for "use skill." This IS the classification workflow.**

Classification determines task size, domains, risk, clarity, and candidate
routing. It does not by itself determine the final implementation.

---

## Step 1: Size

- **atomic**: single focused function/file/config change, factual question, typo,
  simple lookup, or isolated explanation
- **moderate**: one bounded feature/fix, primarily one domain, limited dependencies
- **complex**: ≥2 materially different domains, architecture change, substantial
  dependencies, multi-stage work, or coordinated execution

Use the smallest accurate classification. Do not classify a task as complex
only because it touches multiple files.

---

## Step 2: Domain Match

Match **intent + repository context + technology** to the Capability Index.

Do not rely on keywords alone.

If no existing capability matches, use:

```text
agents/_emerging-tech-handler.md
````

| Domain             | Keywords / Signals                                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| backend            | API, server, endpoint, REST, gRPC, worker, queue, service, lambda, auth, Node.js, Python, Go, Java, GraphQL            |
| frontend           | UI, component, page, form, CSS, render, browser, SPA, SSR, responsive, React, Vue, Angular, Tailwind, accessibility    |
| architecture       | system design, tech stack, migration, scaling, CQRS, hexagonal, architecture, trade-off                                |
| database           | schema, query, index, migration, SQL, NoSQL, data model, slow query, PostgreSQL, MySQL, MongoDB, timeseries, analytics |
| security           | auth, PII, encryption, XSS, CSRF, vulnerability, secrets, RBAC, compliance, audit, penetration, threat, hardening      |
| devops             | deploy, CI/CD, Docker, K8s, Terraform, cloud, pipeline, monitoring, Kubernetes, production, zero-downtime, release     |
| mobile             | iOS, Android, React Native, Flutter, Swift, Kotlin, offline sync                                                       |
| testing-qa         | test, E2E, unit, integration, coverage, mock, flaky, QA, regression                                                    |
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

Classify risk based on the actual requested change.

Add **security** when the task touches:

* authentication or authorization
* PII or sensitive data
* payments
* secrets or credentials
* security controls
* regulated data
* production deployment with meaningful security impact

Use:

```text
risk: none | data | security | compliance
```

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
1. EXACT MATCH
   → agent directly matches the requested technology/domain

2. TECHNOLOGY MATCH
   → agent explicitly supports the technology in its triggers

3. DOMAIN GENERIC
   → generic-<domain>-specialist

4. UNIVERSAL
   → universal-technology-specialist as last resort
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

Classify clarity as:

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

Those are orchestrator decisions.

---

## Output

For every task, emit a concise classification:

```yaml
size: atomic | moderate | complex
domains:
  - domain-name
risk: none | data | security | compliance
clarity: clear | resolvable | blocked
agents:
  - selected-agent-name
```

For atomic tasks, `agents` may be empty.

For moderate tasks, select agents only when specialist execution is actually
needed.

For complex tasks, list the primary agent for each selected domain.

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

