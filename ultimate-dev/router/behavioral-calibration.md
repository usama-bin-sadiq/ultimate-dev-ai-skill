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
| Produce an ordered list of actions, a plan, or a sequence of work | `plan` |
| Define an interface, design, or technical contract | `specification` |
| Implement a feature or refactor | `code` |
| Repair a stated defect, failure, crash, or regression | `bug-fix` |
| Write an authored artifact, policy, report, or guide | `document` |
| Write an email, status update, announcement, or meeting note | `communication` |
| Recommend a course of action, including a framework or criteria for choosing | `recommendation` |
| Record a choice that has already been made | `decision` |
| Automate or orchestrate a repeatable process | `workflow` |
| Audit a control or produce an assurance finding | `audit` |

Do not call a performance optimization `bug-fix` unless the request explicitly
states a defect. Do not call a footer/content edit `code` merely because it is in
a repository. Do not replace `audit` with financial analysis when the requested
deliverable is a control finding.

`comparison` and `recommendation` split on whether a choice was requested.
Comparing, evaluating, or contrasting options — including asking for sources and
confidence — is `comparison`. It becomes `recommendation` only when the request
asks which one to choose, or asks for advice.

An output that tells the reader **what to do next** is a `plan`, even when it is
short and even when it was derived from a note, a transcript, or a single
source. `document` is for content the reader consumes, not for an action list.

This applies when the action list *is* the requested artifact. It does not
convert a report or a notice into a plan just because it ends with next steps:
an incident timeline addressed to other people is `communication`, and an
incident report written to a file is `document`.

Configuration that defines an automated, repeatable process — a CI pipeline, a
release flow, a scheduled job — is `workflow`, not `code`. Application source
that a process runs is `code`.

Communication and documentation split on audience: an incident timeline,
notification, or next-action notice addressed to other people is
`communication`; an internal technical report such as a postmortem written for
an engineering record is `document`. Incident reporting belongs to
`internal-communications` regardless of the language it is written in.

## Size calibration

- `atomic`: one local, low-coupling action or one concise answer.
- `moderate`: several dependent steps, one artifact, or a bounded feature.
- `complex`: multiple systems/domains, staged coordination, migration, regulated
  judgment, or substantial unfamiliarity that requires safe bounded discovery.

Unknown-domain does not automatically mean complex. Use the requested artifact
and coordination burden; disclose a capability gap separately.

Size rules that are easy to get wrong:

- **Unfamiliar subject, produced artifact**: writing a report, framework,
  recommendation, or plan about an unfamiliar subject is `moderate`, not
  `complex`. Familiarity alone does not create coordination cost.
- **Explaining a known fact vs an unfamiliar subject**: answering from what you
  already know is `atomic`; explaining or characterizing a subject you must first
  understand is `moderate`.
- **Unfamiliar subject, built artifact**: `build`, `integrate`, `deploy`, or
  `operate` something in an unfamiliar subject is `complex`, because unknown
  unknowns are discovered by doing.
- **Single-source transformation**: turning one input into one bounded output
  with no external dependency is `atomic`, however it is phrased.
- **Assurance and regulated work**: reconciliation, control testing, and
  findings that require control evidence are `complex` even when the written
  output is a single document.

## Domain calibration

- Use canonical IDs from `config/capability-index.yaml`.
- Use one primary domain unless the task has multiple material deliverables.
- Use `unknown-unclassified` only when no canonical domain is justified.
- A domain describes the **subject matter**, not the task type. `research` and
  `comparison` are deliverables and routes, never domains for a subject the
  index does not cover. Comparing two unfamiliar products is
  `unknown-unclassified`; the route is still `research`.
- Domain labels are not risk labels, skills, technologies, or deliverables.
- Query, index, and schema tuning in an application codebase is
  `software-engineering`. Use `data-bi` for analytics, modeling, metrics, and
  reporting intent, not for a slow query in a running service.
- When the **subject of the work is a third party** — a vendor, supplier, or
  external organization — include that party's domain alongside the domain of
  the activity. Testing a vendor's security control is
  `audit-risk-assurance` *and* `procurement-vendors`, not just the first.
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

Raise the risk only when you can name the actual impact. State it in one clause:

Diagnosing why something fails is not the same as changing it. Explaining or
debugging a 403, a token, a vulnerability report, or a failed deploy is `none`
until the work actually changes a boundary.

**The exception is the subject, not the action.** A security artifact whose
subject *is* a security boundary is `security` even though it changes nothing: a
threat model, a security review, a vulnerability assessment, or a test of a
security control. Debugging a symptom is diagnosis; assessing a boundary is
security work.

### The technical / organizational boundary

`data` risk turns on **what the work is about**, not on how many words it
produces and not on the task type. Ask: is the subject matter an organization's
records, operations, customers, people, or money?

| Subject matter | Risk | Example |
|---|---|---|
| Source code, tests, builds, infrastructure, a technical explanation | `none` | CI pipeline, query tuning, "why is this 403" |
| Operational records, customers, people, delivery, or a business decision | `data` | project status, incident timeline, portal requirements, migration plan |
| Physical or industrial operations | `data` | manufacturing process, sensor protocol, utility, logistics, telemetry |

"Operations" covers physical and industrial operations as well as business ones.
A decision framework about a manufacturing process, or a prototype for a sensor
protocol, works on real operational systems and is `data`.

**The deliverable decides, not the subject.** Explaining, describing, or
studying a subject is `none` even when that subject is an organization or an
industry — information about an organization is still information. `data` applies
when the requested artifact **acts on, decides about, or reports the state of**
real operations: a decision, a build on an operational system, a delivery or
incident report, a migration plan. So "explain the social implications of a
cooperative" is `none`, while "a decision framework for a manufacturing process"
is `data`.

**`data` also requires organizational scope.** Personal material stays `none`:
a private note, a personal checklist, a personal budget, a comparison of two
products you are simply evaluating. `data` needs records an organization owns
or operational systems a team runs. Check the scope before raising the risk.

For the same reason the risk follows the artifact you were asked to produce. A
finding that must meet an approved control standard is `compliance` even when
its subject is a security control; a threat model is `security` even when it
proposes no change. Ask what the deliverable is, then take that risk.

So a status update, an incident timeline, a requirements note, or a dependency
plan is `data` when it reports on organizational operations — even though it
writes no code and touches no secret. Meanwhile a bug fix, a refactor, a CI
pipeline, and a factual answer stay `none` **even when they are large**.

Do not inflate technical work to `data` because it is involved, and do not
deflate an operational report to `none` because it is only text.

Prefer `data` over `compliance` when the work is about operational subject
matter without requiring an approved policy. Use `compliance` when the work
needs an organization's approved legal, financial, HR, privacy, or audit
standard — a ledger reconciliation, a contract clause, a control finding.
Public-service, regulatory, or utility subject matter is usually `data`; it
becomes `compliance` only when an approved policy is the actual requirement.

| Requested work | Risk | Named impact |
|---|---|---|
| Explain what a JWT claim means | `none` | no change, no sensitive data |
| Design login/registration endpoints | `security` | authentication boundary is designed |
| Rename a local variable | `none` | no boundary touched |
| Set up a CI pipeline with lint, test, and build | `none` | build tooling, no organizational records |
| Write a project status update with risks and owners | `data` | reports on project delivery records |
| Write an incident timeline and next actions | `data` | reports on an operational incident record |
| Plan a multi-team migration with checkpoints | `data` | organizational migration and delivery records |
| Reconcile a general ledger for close | `compliance` | financial records and control evidence |
| Add PII fields to a user model | `security` | personal data crosses a boundary |

A non-`none` risk without a named impact is a guess. When in doubt, record
`none` and state the assumption, rather than inflating risk to look careful.

## Edit classification

Distinguish **edits inside source code** from **edits to authored content**:

- An edit inside a source file — docstring, comment, log message, error string,
  typo in a string literal — is `code`, or `bug-fix` when it corrects a defect.
- An edit to authored material — site copy, marketing text, changelog prose,
  a report — is `document`.
- Location in a repository does not decide this. Ask what the edited thing *is*.

## Unfamiliar-domain handling

When no canonical domain is justified, these three must agree:

```text
domains: [unknown-unclassified]
capability_gap: partial | blocking
route: universal-task
```

An unfamiliar domain with `capability_gap: none` is incoherent: if no canonical
domain applies, the domain knowledge is missing, and a bounded gap must be
reported. Conversely, do not claim a gap for work a canonical domain covers.

## Capability-gap calibration

- `none`: an applicable skill/specialist and required host capabilities exist.
- `partial`: a safe bounded portion can be completed, but a named capability is
  missing.
- `blocking`: safe completion is impossible without clarification, permission,
  data, or a required human decision.

A capability gap also covers **missing input**, not only a missing tool. When the
requested artifact depends on material the user referenced but did not supply —
their brand guidelines, their contract terms, their employment policy, their
production schema — the safe bounded portion is a plan or a template, so report
`partial` and name the missing input. Do not report `clear` with `none` and then
invent the missing content.

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

## Self-check (one bounded pass)

Before executing, run **at most one** self-correction pass over the decision
record:

1. Re-derive the deliverable from the artifact the user explicitly requested.
2. Re-check risk against actual impact, not topic sensitivity.
3. Confirm every domain is a canonical ID from `config/capability-index.yaml`.
4. Confirm an unavailable route is reported as a capability gap.
5. When the host can run it, lint the record with
   `scripts/validate-routing-decision.py`.

Then execute. Do not iterate: a second pass is a loop, not a correction. If the
record still contains an unresolved error, execute only the safe bounded portion
and report the error, assumption, and next action.

## Output discipline

Return only the fields required by the task envelope or replay harness. Preserve
`not_run`, `unknown`, assumptions, and capability gaps. Do not claim that this
contract itself proves model accuracy.
