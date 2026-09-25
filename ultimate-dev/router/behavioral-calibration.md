# Behavioral Calibration Contract

This is the single source of truth for host-replay classification guardrails.
It is local, provider-free guidance. It does not replace the task envelope,
capability index, or human review.

## Decision order

Classify in this order. Do not choose a specialist first.

1. **Requested deliverable** — what artifact or answer the user explicitly asks
   for.
2. **Size** — the amount of coordination, context, uncertainty, and verification.
3. **Domain** — the smallest canonical ID from `config/capability-index.yaml`.
4. **Risk** — the actual action, data, security, production, or regulatory impact.
5. **Capability gap** — whether an applicable route is actually available.
6. **Route** — common skill first, exact specialist only when needed.

## Deliverable calibration

| Requested output | Deliverable |
|---|---|
| Explain a fact or concept | `answer` |
| Investigate and synthesize sources | `research` |
| Compare options | `comparison` |
| Recommend a choice | `recommendation` |
| Define scope, acceptance criteria, or PRD | `requirements` |
| Define an interface, design, or technical contract | `specification` |
| Implement a feature or refactor | `code` |
| Repair a stated defect, failure, crash, or regression | `bug-fix` |
| Write an authored artifact, policy, report, or guide | `document` |
| Write an email, status update, announcement, or meeting note | `communication` |
| Automate or orchestrate a repeatable process | `workflow` |
| Audit a control or produce an assurance finding | `audit` |

Do not call a performance optimization `bug-fix` unless the request explicitly
states a defect. Do not call a footer/content edit `code` merely because it is in
a repository. Do not replace `audit` with financial analysis when the requested
deliverable is a control finding.

## Size calibration

- `atomic`: one local, low-coupling action or one concise answer.
- `moderate`: several dependent steps, one artifact, or a bounded feature.
- `complex`: multiple systems/domains, staged coordination, migration, regulated
  judgment, or substantial unfamiliarity that requires safe bounded discovery.

Unknown-domain does not automatically mean complex. Use the requested artifact
and coordination burden; disclose a capability gap separately.

## Domain calibration

- Use canonical IDs from `config/capability-index.yaml`.
- Use one primary domain unless the task has multiple material deliverables.
- Use `unknown-unclassified` only when no canonical domain is justified.
- Domain labels are not risk labels, skills, technologies, or deliverables.
- Compatibility aliases in `evals/domain-aliases.json` are for fixture comparison,
  not live routing output.

## Risk calibration

| Actual impact | Risk |
|---|---|
| Explanation, ordinary code, documentation, or communication with no sensitive data or boundary | `none` |
| Material personal/sensitive data, data migration, or meaningful operational data impact | `data` |
| Authentication, secrets, production security, or security-control testing | `security` |
| Legal, finance, HR, privacy, audit, or policy judgment requiring approved organizational context | `compliance` |

Risk follows impact, not topic sensitivity. A technical answer about JWT is not
automatically `security`; an authentication implementation is. A financial
analysis is `compliance` when it depends on organizational financial records,
assumptions, or approval boundaries. An ordinary document or code change stays
`none` unless one of the higher-impact conditions applies.

## Capability-gap calibration

- `none`: an applicable skill/specialist and required host capabilities exist.
- `partial`: a safe bounded portion can be completed, but a named capability is
  missing.
- `blocking`: safe completion is impossible without clarification, permission,
  data, or a required human decision.

Do not report a gap merely because a specialist would be convenient. Do not hide
a gap when the task is genuinely unfamiliar or crosses an unavailable boundary.

## Calibration examples

- “Optimize this PostgreSQL query” → `code`, not `bug-fix`, unless a defect is
  explicitly stated.
- “Update the copyright year in the footer” → `document`, not `code`.
- “Reconcile the ledger and document control exceptions” → `audit` when the
  requested deliverable is a control finding; use `financial-analysis` only for
  a pure variance/analysis request.
- “Write an executive status update with decisions and next actions” →
  `communication`, usually `moderate` because it has several required sections.
- “Design a workflow for an unfamiliar municipal utility” → `complex` when it
  requires multi-party coordination; route `universal-task` and report a partial
  capability gap.
- “Compare unfamiliar products and cite sources” → `comparison`/`research`; if
  product knowledge is not available, report a bounded partial gap rather than
  inventing facts.

## Output discipline

Return only the fields required by the task envelope or replay harness. Preserve
`not_run`, `unknown`, assumptions, and capability gaps. Do not claim that this
contract itself proves model accuracy.
