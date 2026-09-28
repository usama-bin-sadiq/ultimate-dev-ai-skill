<!-- Moved verbatim from terraform-patterns/SKILL.md, the
     'terragrunt-patterns' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Terragrunt Patterns

Terragrunt is a thin wrapper around Terraform that provides DRY configuration for multi-environment setups.

### Root terragrunt.hcl (Shared Config)

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "my-org-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### Child terragrunt.hcl (Environment Override)

```hcl
# prod/vpc/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/vpc"
}

inputs = {
  environment = "prod"
  cidr_block  = "10.0.0.0/16"
}
```

### Dependencies Between Modules

```hcl
# prod/eks/terragrunt.hcl
dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  vpc_id     = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.private_subnet_ids
}
```

### When Terragrunt Adds Value

- **Yes**: 3+ environments with identical module structure, shared backend config, or cross-module dependencies.
- **No**: Single environment, small team, or simple directory-based isolation already works. Terragrunt adds a learning curve and another binary to manage.

---
