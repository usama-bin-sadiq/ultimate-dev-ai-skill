<!-- Moved verbatim from senior-secops/SKILL.md, the
     'owasp-top-10-quick-check' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
