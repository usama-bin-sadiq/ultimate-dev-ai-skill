<!-- Moved verbatim from terraform-patterns/SKILL.md, the
     'workflow' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Workflow

### `/terraform:review` — Terraform Code Review

1. **Analyze current state**
   - Read all `.tf` files in the target directory
   - Identify module structure (flat vs nested)
   - Count resources, data sources, variables, outputs
   - Check naming conventions

2. **Apply review checklist**

   ```
   MODULE STRUCTURE
   ├── Variables have descriptions and type constraints
   ├── Outputs expose only what consumers need
   ├── Resources use consistent naming: {provider}_{type}_{purpose}
   ├── Locals used for computed values and DRY expressions
   └── No hardcoded values — everything parameterized or in locals

   STATE & BACKEND
   ├── Remote backend configured (S3, GCS, Azure Blob, Terraform Cloud)
   ├── State locking enabled (DynamoDB for S3, native for others)
   ├── State encryption at rest enabled
   ├── No secrets stored in state (or state access is restricted)
   └── Workspaces or directory isolation for environments

   PROVIDERS
   ├── Version constraints use pessimistic operator: ~> 5.0
   ├── Required providers block in terraform {} block
   ├── Provider aliases for multi-region or multi-account
   └── No provider configuration in child modules

   SECURITY
   ├── No hardcoded secrets, keys, or passwords
   ├── IAM follows least-privilege principle
   ├── Encryption enabled for storage, databases, secrets
   ├── Security groups are not overly permissive (no 0.0.0.0/0 ingress on sensitive ports)
   └── Sensitive variables marked with sensitive = true
   ```

3. **Generate report**
   ```bash
   python3 scripts/tf_module_analyzer.py ./terraform
   ```

4. **Run security scan**
   ```bash
   python3 scripts/tf_security_scanner.py ./terraform
   ```

### `/terraform:module` — Module Design

1. **Identify module scope**
   - Single responsibility: one module = one logical grouping
   - Determine inputs (variables), outputs, and resource boundaries
   - Decide: flat module (single directory) vs nested (calling child modules)

2. **Apply module design checklist**

   ```
   STRUCTURE
   ├── main.tf        — Primary resources
   ├── variables.tf   — All input variables with descriptions and types
   ├── outputs.tf     — All outputs with descriptions
   ├── versions.tf    — terraform {} block with required_providers
   ├── locals.tf      — Computed values and naming conventions
   ├── data.tf        — Data sources (if any)
   └── README.md      — Usage examples and variable documentation

   VARIABLES
   ├── Every variable has: description, type, validation (where applicable)
   ├── Sensitive values marked: sensitive = true
   ├── Defaults provided for optional settings
   ├── Use object types for related settings: variable "config" { type = object({...}) }
   └── Validate with: validation { condition = ... }

   OUTPUTS
   ├── Output IDs, ARNs, endpoints — things consumers need
   ├── Include description on every output
   ├── Mark sensitive outputs: sensitive = true
   └── Don't output entire resources — only specific attributes

   COMPOSITION
   ├── Root module calls child modules
   ├── Child modules never call other child modules
   ├── Pass values explicitly — no hidden data source lookups in child modules
   ├── Provider configuration only in root module
   └── Use module "name" { source = "./modules/name" }
   ```

3. **Generate module scaffold**
   - Output file structure with boilerplate
   - Include variable validation blocks
   - Add lifecycle rules where appropriate

### `/terraform:security` — Security Audit

1. **Code-level audit**

   | Check | Severity | Fix |
   |-------|----------|-----|
   | Hardcoded secrets in `.tf` files | Critical | Use variables with sensitive = true or vault |
   | IAM policy with `*` actions | Critical | Scope to specific actions and resources |
   | Security group with 0.0.0.0/0 on port 22/3389 | Critical | Restrict to known CIDR blocks or use SSM/bastion |
   | S3 bucket without encryption | High | Add `server_side_encryption_configuration` block |
   | S3 bucket with public access | High | Add `aws_s3_bucket_public_access_block` |
   | RDS without encryption | High | Set `storage_encrypted = true` |
   | RDS publicly accessible | High | Set `publicly_accessible = false` |
   | CloudTrail not enabled | Medium | Add `aws_cloudtrail` resource |
   | Missing `prevent_destroy` on stateful resources | Medium | Add `lifecycle { prevent_destroy = true }` |
   | Variables without `sensitive = true` for secrets | Medium | Add `sensitive = true` to secret variables |

2. **State security audit**

   | Check | Severity | Fix |
   |-------|----------|-----|
   | Local state file | Critical | Migrate to remote backend with encryption |
   | Remote state without encryption | High | Enable encryption on backend (SSE-S3, KMS) |
   | No state locking | High | Enable DynamoDB for S3, native for TF Cloud |
   | State accessible to all team members | Medium | Restrict via IAM policies or TF Cloud teams |

3. **Generate security report**
   ```bash
   python3 scripts/tf_security_scanner.py ./terraform
   python3 scripts/tf_security_scanner.py ./terraform --output json
   ```

---
