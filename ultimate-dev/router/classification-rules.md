# Classification Rules (compact)

## ⚡ MANDATORY: Run on EVERY user message

**Do not skip. Do not wait for "use skill." This IS your workflow.**

## Step 1: Size
- **atomic**: single function/file/config, factual question
- **moderate**: one feature, one domain, bounded
- **complex**: ≥2 domains, architecture, multi-step

## Step 2: Domain Match
Match keywords/intent → Capability Index. No match → `_emerging-tech-handler.md`.

| Domain | Keywords |
|--------|----------|
| backend | API, server, endpoint, REST, gRPC, worker, queue, service, lambda, auth |
| frontend | UI, component, page, form, CSS, render, browser, SPA, SSR, responsive |
| architecture | system design, tech stack, migration, scaling, CQRS, hexagonal |
| database | schema, query, index, migration, SQL, NoSQL, data model, slow query |
| security | auth, PII, encryption, XSS, CSRF, vulnerability, secrets, RBAC, compliance |
| devops | deploy, CI/CD, Docker, K8s, Terraform, cloud, pipeline, monitoring |
| mobile | iOS, Android, React Native, Flutter, Swift, Kotlin, offline sync |
| testing-qa | test, E2E, unit, integration, coverage, mock, flaky, QA, regression |
| documentation | README, API docs, ADR, changelog, docstring, runbook |
| project-management | sprint, backlog, ticket, story, epic, estimation, retrospective |
| product | requirements, PRD, user story, roadmap, prioritization, feature spec |
| design-handoff | wireframe, mockup, design token, typography, component spec, Figma |
| client-comms | status update, progress report, blocker, scope change, timeline |
| marketing | SEO, content, social media, email, growth, brand, conversion, blog |
| sales | pipeline, prospecting, deal, proposal, CRM, forecast, demo, close |
| finance | budget, revenue, cost, unit economics, P&L, pricing, margin |
| support | ticket, helpdesk, knowledge base, CSAT, escalation, SLA |
| paid-media | Google Ads, Meta Ads, PPC, retargeting, ROAS, CPC, campaign |
| research | competitive analysis, market research, literature review, benchmark |
| academic | thesis, dissertation, citation, methodology, paper, journal |
| healthcare | EHR, FHIR, HL7, HIPAA, clinical, patient, interoperability |
| game-dev | game design, gameplay, Unity, Unreal, multiplayer, monetization |
| gis | spatial, geospatial, map, coordinate, GeoJSON, spatial query |
| spatial-computing | AR, VR, MR, headset, 3D UI, hand tracking, immersive, XR |
| specialized | blockchain, IoT, embedded, robotics, HPC, CUDA, WebAssembly |

## Step 3: Risk Flag
Add **security** if touches: auth, PII, payments, secrets, regulated data, production deploy.

Risk: `none | data | security | compliance`

## Step 4: Agent Selection (when spawning agents)

When multiple agents match a task, apply this tiebreaker:

```
1. EXACT MATCH    → agent name matches task keyword exactly (e.g., "React" → react-specialist)
2. TECHNOLOGY     → agent has specific technology in triggers (e.g., "vue" → vue-specialist)
3. DOMAIN GENERIC → generic-<domain>-specialist (e.g., generic-frontend-specialist)
4. UNIVERSAL      → universal-technology-specialist (last resort)
```

**Rules:**
- NEVER spawn more than 1 agent per domain (frontend = 1 agent, not 4)
- If task mentions "React" → react-specialist ONLY (not css-architect, not vue-specialist)
- If task mentions "CSS" or "Tailwind" → css-architect ONLY
- If task mentions "accessibility" or "WCAG" → accessibility-engineer ONLY
- If task mentions "performance" or "bundle" → perf-specialist ONLY
- If task is generic "frontend" with no technology → generic-frontend-specialist
- Cross-domain tasks: spawn 1 agent per domain, not per sub-specialty

**Anti-Trigger Exclusion:**
Each agent has `anti_triggers` — if the task matches an anti-trigger, that agent is EXCLUDED even if it matches a trigger.

## Step 5: Clarity Check
If size ≠ atomic and missing decision → ask ONE question before proceeding.

## Output (EMIT THIS on every turn)
```
size: atomic | moderate | complex
domains: [list]
risk: none | data | security | compliance
clarity: clear | ambiguous
agents: [selected agent names — max 1 per domain]
```

## Then IMMEDIATELY:
- **atomic** → inline answer, `[tier: tiny | work: inline]`
- **moderate** → load 1 module, `[tier: small | module: <name>]`
- **complex** → decompose, spawn agent, `[tier: small | module: <primary> | agents: 1 | coverage: partial]`