---
name: legal-privacy
description: >
  Support legal, privacy, contract, policy, records, and data-governance work by
  extracting obligations, identifying risks, preserving evidence, and routing
  decisions to qualified reviewers. Use for contracts, DPAs, retention,
  privacy impact, legal holds, compliance evidence, and policy analysis.
triggers: [legal, privacy, contract, clause, DPA, retention, legal hold, data governance, policy, compliance, records]
provides: legal_privacy_workpaper
---

# Legal, Privacy, and Contracts

Help organize a legal/privacy work product without pretending to replace
qualified counsel or a privacy officer.

## Method

1. Identify jurisdiction, parties, purpose, data subjects, systems, and dates.
2. Extract obligations, permissions, prohibitions, deadlines, and dependencies.
3. Separate contract language, company policy, observed practice, and assumption.
4. Map obligations to owners, evidence, controls, and review dates.
5. Identify conflicts, gaps, retention/legal-hold needs, and decision deadlines.
6. Produce an issue list with options and questions for the qualified owner.
7. Preserve source excerpts, version, and approval status.

## Output

```yaml
context: <..>
source_documents: [..]
obligations: [..]
risks: [..]
gaps: [..]
decisions_needed: [..]
owner: <..>
deadlines: [..]
review_status: draft|reviewed|approved
```

Do not give privileged legal advice, infer consent, or disclose sensitive data.
External submission, contract acceptance, or policy publication requires
explicit approval.
