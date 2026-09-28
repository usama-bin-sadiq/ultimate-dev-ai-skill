<!-- Moved verbatim from senior-secops/SKILL.md, the
     'compliance-frameworks' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

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
