<!-- Moved verbatim from terraform-patterns/SKILL.md, the
     'proactive-triggers' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Proactive Triggers

Flag these without being asked:

- **No remote backend configured** → Migrate to S3/GCS/Azure Blob with locking and encryption.
- **Provider without version constraint** → Add `version = "~> X.0"` to prevent breaking upgrades.
- **Hardcoded secrets in .tf files** → Use variables with `sensitive = true`, or integrate Vault/SSM.
- **IAM policy with `"Action": "*"`** → Scope to specific actions. No wildcard actions in production.
- **Security group open to 0.0.0.0/0 on SSH/RDP** → Restrict to bastion CIDR or use SSM Session Manager.
- **No state locking** → Enable DynamoDB table for S3 backend, or use TF Cloud.
- **Resources without tags** → Add default_tags in provider block. Tags are mandatory for cost tracking.
- **Missing `prevent_destroy` on databases/storage** → Add lifecycle block to prevent accidental deletion.

---
