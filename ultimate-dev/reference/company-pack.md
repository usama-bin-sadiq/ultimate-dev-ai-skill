# Optional Company Context Pack

A company pack supplies host- or organization-specific facts that the universal
skill cannot infer. It is optional and must never be treated as authorization.

## Authoring rules

1. Copy `company-context-template.yaml` into a separately managed project or
   organization location; do not put secrets or private policy in the package.
2. Link to authoritative policies instead of copying long documents.
3. Record jurisdiction, effective date, owner, and last verification date.
4. Separate stable terminology from transient project context.
5. Mark missing or stale facts as unknown; do not fill them with generic policy.
6. Load the pack only when the task matches its declared scope.
7. Require human review for legal, financial, privacy, security, employment,
   procurement, and audit decisions.

## Minimal handoff

```yaml
company_context:
  source: <path-or-link>
  scope: []
  verified_fields: []
  missing_fields: []
  human_review: required|recommended|not_required
  last_verified: YYYY-MM-DD
```

The pack improves grounding; it does not replace project context, source
verification, or the selected skill's safety boundaries.
