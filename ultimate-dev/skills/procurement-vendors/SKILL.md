---
name: procurement-vendors
description: >
  Structure procurement and vendor-management workflows including intake,
  requirements, due diligence, RFPs, quotes, approvals, purchase records,
  renewals, and offboarding. Use for supplier, vendor, purchase order, contract
  handoff, or third-party risk requests.
triggers: [procurement, vendor, supplier, RFP, RFQ, purchase order, due diligence, renewal, third-party risk, offboarding]
provides: procurement_workflow
---

# Procurement and Vendors

Create a traceable procurement workflow from need to renewal or offboarding.

## Method

1. Define the business need, scope, budget, owner, deadline, and required outcome.
2. Identify data, security, privacy, legal, operational, and continuity risks.
3. Define evaluation criteria and weighting before comparing vendors.
4. Collect comparable quotes, assumptions, conflicts, and decision evidence.
5. Route approval, contract, security, privacy, and finance gates explicitly.
6. Record the selected supplier, rationale, conditions, and renewal date.
7. Plan access, data return/deletion, monitoring, and offboarding.

## Output

```yaml
need: <..>
scope: [..]
budget: <..>
criteria: [..]
vendors: [..]
due_diligence: [..]
risks: [..]
approvals: [..]
decision: <..>
contract_handoff: [..>
renewal: <..>
offboarding: [..>
```

Do not invent quotes, certifications, savings, or risk ratings. Do not award a
contract, transmit sensitive data, or create vendor accounts without explicit
authorization.
