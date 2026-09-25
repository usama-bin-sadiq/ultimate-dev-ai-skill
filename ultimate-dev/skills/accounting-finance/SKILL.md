---
name: accounting-finance
description: >
  Structure accounting, controllership, management reporting, budgeting,
  forecasting, cash planning, and financial-control work with explicit
  assumptions, periods, currencies, sources, and human review. Use for P&L,
  cash flow, budget, variance, close, reconciliation, or board-report questions.
triggers: [accounting, controllership, ledger, reconciliation, close, accrual, management accounts, budget, forecast, cash flow, board report]
provides: finance_workpaper
---

# Accounting and Finance

Produce a transparent finance workpaper. Never invent numbers or silently
choose an accounting policy.

## Method

1. Define entity, period, currency, accounting basis, and reporting purpose.
2. List source ledgers, statements, policies, assumptions, and owners.
3. Reconcile opening/closing balances and trace material variances.
4. Separate actuals, budget, forecast, and assumptions.
5. Check units, signs, date cutoffs, duplicate transactions, and formula
   dependencies.
6. Explain material changes, risks, liquidity, and decision implications.
7. Mark review status and unresolved items explicitly.

## Output

```yaml
entity: <..>
period: <..>
currency: <..>
basis: <..>
sources: [..]
reconciliations: [..]
actuals: <..>
budget_variance: <..>
forecast: <..>
assumptions: [..]
risks: [..]
review_status: draft|reviewed|approved
```

Financial, tax, accounting, and audit conclusions require qualified human
review. Do not provide individualized investment, tax, or legal advice.
