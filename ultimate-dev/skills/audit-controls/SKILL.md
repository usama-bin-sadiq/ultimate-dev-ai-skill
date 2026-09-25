---
name: audit-controls
description: >
  Plan and perform evidence-based control, risk, and assurance reviews for
  software, financial, operational, or compliance processes. Use for internal
  audit preparation, control testing, findings, remediation, and evidence
  requests.
triggers: [audit, internal audit, control test, control testing, evidence request, finding, risk assessment, assurance review]
provides: audit_workpaper
---

# Audit, Risk, and Controls

Assess whether a stated control objective is designed and operating effectively,
while separating evidence, interpretation, and management judgment.

## Method

1. **Set scope and criteria** — process, system, period, jurisdiction, control
   owner, framework, and sampling population.
2. **Understand the objective and risk** — what could fail, impact, likelihood,
   existing controls, and evidence sources.
3. **Request evidence** — define format, period, owner, lineage, and acceptable
   provenance before collecting artifacts.
4. **Test the control** — state the procedure, population, sample rationale,
   expected result, observed result, and exceptions.
5. **Classify the result** — effective, effective with observation, deficiency,
   or not tested; never convert missing evidence into a pass.
6. **Write the finding** — condition, criteria, cause, effect, risk, evidence,
   severity, owner, due date, and remediation.
7. **Track closure** — validate management response, evidence of remediation,
   residual risk, and independent follow-up.

## Workpaper format

```yaml
scope: <..>
criteria: [..]
control_objective: <..>
procedure: <..>
population: <..>
sample: <..>
evidence: [..]
observed: <..>
result: pass|observation|deficiency|not_tested
finding: <..>
owner: <..>
due: <..>
```

## Boundaries

Do not provide legal, accounting, or certification conclusions without a
qualified reviewer. Preserve confidentiality, chain of custody, and source
hashes where available. Escalate suspected fraud or material control failure.
