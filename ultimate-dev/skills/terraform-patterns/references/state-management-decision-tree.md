<!-- Moved verbatim from terraform-patterns/SKILL.md, the
     'state-management-decision-tree' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## State Management Decision Tree

```
Single developer, small project?
├── Yes → Local state (but migrate to remote ASAP)
└── No
    ├── Using Terraform Cloud/Enterprise?
    │   └── Yes → TF Cloud native backend (built-in locking, encryption, RBAC)
    └── No
        ├── AWS?
        │   └── S3 + DynamoDB (encryption, locking, versioning)
        ├── GCP?
        │   └── GCS bucket (native locking, encryption)
        ├── Azure?
        │   └── Azure Blob Storage (native locking, encryption)
        └── Other?
            └── Consul or PostgreSQL backend

Environment isolation strategy:
├── Separate state files per environment (recommended)
│   ├── Option A: Separate directories (dev/, staging/, prod/)
│   └── Option B: Terraform workspaces (simpler but less isolation)
└── Single state file for all environments (never do this)
```

---
