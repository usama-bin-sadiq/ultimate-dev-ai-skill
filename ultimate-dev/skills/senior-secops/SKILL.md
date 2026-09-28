---
name: "senior-secops"
description: Senior SecOps engineer skill for application security, vulnerability management, compliance verification, and secure development practices. Runs SAST/DAST scans, generates CVE remediation plans, checks dependency vulnerabilities, creates security policies, enforces secure coding patterns, and automates compliance checks against SOC2, PCI-DSS, HIPAA, and GDPR. Use when conducting a security review or audit, responding to a CVE or security incident, hardening infrastructure, implementing authentication or secrets management, running penetration test prep, checking OWASP Top 10 exposure, or enforcing security controls in CI/CD pipelines.
---

# Senior SecOps Engineer

Complete toolkit for Security Operations including vulnerability management, compliance verification, secure coding practices, and security automation.

---

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [Workflows](#workflows)
- [Tool Reference](#tool-reference)
- [Security Standards](#security-standards)
- [Compliance Frameworks](#compliance-frameworks)
- [Best Practices](#best-practices)

---

## Core Capabilities

Detail moved verbatim to `references/core-capabilities.md`. Load it when this section matters and the pointer is not enough.

## Workflows

Detail moved verbatim to `references/workflows.md`. Load it when this section matters and the pointer is not enough.

## Tool Reference

### security_scanner.py

| Option | Description |
|--------|-------------|
| `target` | Directory or file to scan |
| `--severity, -s` | Minimum severity: critical, high, medium, low |
| `--verbose, -v` | Show files as they're scanned |
| `--json` | Output results as JSON |
| `--output, -o` | Write results to file |

**Exit Codes:** `0` = no critical/high findings · `1` = high severity findings · `2` = critical severity findings

### vulnerability_assessor.py

| Option | Description |
|--------|-------------|
| `target` | Directory containing dependency files |
| `--severity, -s` | Minimum severity: critical, high, medium, low |
| `--verbose, -v` | Show files as they're scanned |
| `--json` | Output results as JSON |
| `--output, -o` | Write results to file |

**Exit Codes:** `0` = no critical/high vulnerabilities · `1` = high severity vulnerabilities · `2` = critical severity vulnerabilities

### compliance_checker.py

| Option | Description |
|--------|-------------|
| `target` | Directory to check |
| `--framework, -f` | Framework: soc2, pci-dss, hipaa, gdpr, all |
| `--verbose, -v` | Show checks as they run |
| `--json` | Output results as JSON |
| `--output, -o` | Write results to file |

**Exit Codes:** `0` = compliant (90%+ score) · `1` = non-compliant (50-69% score) · `2` = critical gaps (<50% score)

---

## Security Standards

See `references/security_standards.md` for OWASP Top 10 full guidance, secure coding standards, authentication requirements, and API security controls.

### Secure Coding Checklist

```markdown
## Input Validation
- [ ] Validate all input on server side
- [ ] Use allowlists over denylists
- [ ] Sanitize for specific context (HTML, SQL, shell)

## Output Encoding
- [ ] HTML encode for browser output
- [ ] URL encode for URLs
- [ ] JavaScript encode for script contexts

## Authentication
- [ ] Use bcrypt/argon2 for passwords
- [ ] Implement MFA for sensitive operations
- [ ] Enforce strong password policy

## Session Management
- [ ] Generate secure random session IDs
- [ ] Set HttpOnly, Secure, SameSite flags
- [ ] Implement session timeout (15 min idle)

## Error Handling
- [ ] Log errors with context (no secrets)
- [ ] Return generic messages to users
- [ ] Never expose stack traces in production

## Secrets Management
- [ ] Use environment variables or secrets manager
- [ ] Never commit secrets to version control
- [ ] Rotate credentials regularly
```

---

## Compliance Frameworks

See `references/compliance_requirements.md` for full control mappings. Run `compliance_checker.py` to verify the controls below:

### SOC 2 Type II
- **CC6** Logical Access: authentication, authorization, MFA
- **CC7** System Operations: monitoring, logging, incident response
- **CC8** Change Management: CI/CD, code review, deployment controls

### PCI-DSS v4.0
- **Req 3/4**: Encryption at rest and in transit (TLS 1.2+)
- **Req 6**: Secure development (input validation, secure coding)
- **Req 8**: Strong authentication (MFA, password policy)
- **Req 10/11**: Audit logging, SAST/DAST/penetration testing

### HIPAA Security Rule
- Unique user IDs and audit trails for PHI access (164.312(a)(1), 164.312(b))
- MFA for person/entity authentication (164.312(d))
- Transmission encryption via TLS (164.312(e)(1))

### GDPR
- **Art 25/32**: Privacy by design, encryption, pseudonymization
- **Art 33**: Breach notification within 72 hours
- **Art 17/20**: Right to erasure and data portability

---

## Best Practices

### Secrets Management

```python
# BAD: Hardcoded secret
API_KEY = "sk-1234567890abcdef"

# GOOD: Environment variable
import os
API_KEY = os.environ.get("API_KEY")

# BETTER: Secrets manager
from your_vault_client import get_secret
API_KEY = get_secret("api/key")
```

### SQL Injection Prevention

```python
# BAD: String concatenation
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### XSS Prevention

```javascript
// BAD: Direct innerHTML assignment is vulnerable
// GOOD: Use textContent (auto-escaped)
element.textContent = userInput;

// GOOD: Use sanitization library for HTML
import DOMPurify from 'dompurify';
const safeHTML = DOMPurify.sanitize(userInput);
```

### Authentication

```javascript
// Password hashing
const bcrypt = require('bcrypt');
const SALT_ROUNDS = 12;

// Hash password
const hash = await bcrypt.hash(password, SALT_ROUNDS);

// Verify password
const match = await bcrypt.compare(password, hash);
```

### Security Headers

```javascript
// Express.js security headers
const helmet = require('helmet');
app.use(helmet());

// Or manually set headers:
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  next();
});
```

---

## OWASP Top 10 Quick-Check

Rapid 15-minute assessment — run through each category and note pass/fail. For deep-dive testing, hand off to the **security-pen-testing** skill.

| # | Category | One-Line Check |
|---|----------|----------------|
| A01 | Broken Access Control | Verify role checks on every endpoint; test horizontal privilege escalation |
| A02 | Cryptographic Failures | Confirm TLS 1.2+ everywhere; no secrets in logs or source |
| A03 | Injection | Run parameterized query audit; check ORM raw-query usage |
| A04 | Insecure Design | Review threat model exists for critical flows |
| A05 | Security Misconfiguration | Check default credentials removed; error pages generic |
| A06 | Vulnerable Components | Run `vulnerability_assessor.py`; zero critical/high CVEs |
| A07 | Auth Failures | Verify MFA on admin; brute-force protection active |
| A08 | Software & Data Integrity | Confirm CI/CD pipeline signs artifacts; no unsigned deps |
| A09 | Logging & Monitoring | Validate audit logs capture auth events; alerts configured |
| A10 | SSRF | Test internal URL filters; block metadata endpoints (169.254.169.254) |

> **Deep dive needed?** Hand off to `security-pen-testing` for full OWASP Testing Guide coverage.

---

## Secret Scanning Tools

Choose the right scanner for each stage of your workflow:

| Tool | Best For | Language | Pre-commit | CI/CD | Custom Rules |
|------|----------|----------|:----------:|:-----:|:------------:|
| **gitleaks** | CI pipelines, full-repo scans | Go | Yes | Yes | TOML regexes |
| **detect-secrets** | Pre-commit hooks, incremental | Python | Yes | Partial | Plugin-based |
| **truffleHog** | Deep history scans, entropy | Go | No | Yes | Regex + entropy |

**Recommended setup:** Use `detect-secrets` as a pre-commit hook (catches secrets before they enter history) and `gitleaks` in CI (catches anything that slips through).

```bash
# detect-secrets pre-commit hook (.pre-commit-config.yaml)
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']

# gitleaks in GitHub Actions
- name: gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

---

## Supply Chain Security

Protect against dependency and artifact tampering with SBOM generation, artifact signing, and SLSA compliance.

**SBOM Generation:**
- **syft** — generates SBOMs from container images or source dirs (SPDX, CycloneDX formats)
- **cyclonedx-cli** — CycloneDX-native tooling; merge multiple SBOMs for mono-repos

```bash
# Generate SBOM from container image
syft packages ghcr.io/org/app:latest -o cyclonedx-json > sbom.json
```

**Artifact Signing (Sigstore/cosign):**
```bash
# Sign a container image (keyless via OIDC)
cosign sign ghcr.io/org/app:latest
# Verify signature
cosign verify ghcr.io/org/app:latest --certificate-identity=ci@org.com --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

**SLSA Levels Overview:**
| Level | Requirement | What It Proves |
|-------|-------------|----------------|
| 1 | Build process documented | Provenance exists |
| 2 | Hosted build service, signed provenance | Tamper-resistant provenance |
| 3 | Hardened build platform, non-falsifiable provenance | Tamper-proof build |
| 4 | Two-party review, hermetic builds | Maximum supply-chain assurance |

> **Cross-references:** `security-pen-testing` (vulnerability exploitation testing), `dependency-auditor` (license and CVE audit for dependencies).

---

## Reference Documentation

| Document | Description |
|----------|-------------|
| `references/security_standards.md` | OWASP Top 10, secure coding, authentication, API security |
| `references/vulnerability_management_guide.md` | CVE triage, CVSS scoring, remediation workflows |
| `references/compliance_requirements.md` | SOC 2, PCI-DSS, HIPAA, GDPR full control mappings |

Each file below is loaded on demand, not at triage. 15 file(s):

- `references/authentication.md` — Authentication. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/best-practices.md` — Best Practices. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/compliance-frameworks.md` — Compliance Frameworks. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/error-handling.md` — Error Handling. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/input-validation.md` — Input Validation. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/output-encoding.md` — Output Encoding. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/owasp-top-10-quick-check.md` — OWASP Top 10 Quick-Check. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/reference-documentation.md` — Reference Documentation. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/secret-scanning-tools.md` — Secret Scanning Tools. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/secrets-management.md` — Secrets Management. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/security-standards.md` — Security Standards. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/session-management.md` — Session Management. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/supply-chain-security.md` — Supply Chain Security. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/table-of-contents.md` — Table of Contents. <!-- Moved verbatim from senior-secops/SKILL.md, the
- `references/tool-reference.md` — Tool Reference. <!-- Moved verbatim from senior-secops/SKILL.md, the

