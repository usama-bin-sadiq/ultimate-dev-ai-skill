<!-- Moved verbatim from terraform-patterns/SKILL.md, the
     'tooling' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Tooling

### `scripts/tf_module_analyzer.py`

CLI utility for analyzing Terraform directory structure and module quality.

**Features:**
- Resource and data source counting
- Variable and output analysis (missing descriptions, types, validation)
- Naming convention checks
- Module composition detection
- File structure validation
- JSON and text output

**Usage:**
```bash
# Analyze a Terraform directory
python3 scripts/tf_module_analyzer.py ./terraform

# JSON output
python3 scripts/tf_module_analyzer.py ./terraform --output json

# Analyze a specific module
python3 scripts/tf_module_analyzer.py ./modules/vpc
```

### `scripts/tf_security_scanner.py`

CLI utility for scanning `.tf` files for common security issues.

**Features:**
- Hardcoded secret detection (AWS keys, passwords, tokens)
- Overly permissive IAM policy detection
- Open security group detection (0.0.0.0/0 on sensitive ports)
- Missing encryption checks (S3, RDS, EBS)
- Public access detection (S3, RDS, EC2)
- Sensitive variable audit
- JSON and text output

**Usage:**
```bash
# Scan a Terraform directory
python3 scripts/tf_security_scanner.py ./terraform

# JSON output
python3 scripts/tf_security_scanner.py ./terraform --output json

# Strict mode (elevate warnings)
python3 scripts/tf_security_scanner.py ./terraform --strict
```

---
