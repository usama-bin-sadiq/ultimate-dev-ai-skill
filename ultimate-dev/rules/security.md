# Security Rules

Security rules that all agents must follow. These are non-negotiable.

## Core Principles

1. **Never trust user input.** Validate and sanitize everything.
2. **Least privilege.** Request only the permissions needed for the current task.
3. **Defense in depth.** Don't rely on a single security control.
4. **Fail securely.** When in doubt, deny access.
5. **Separation of concerns.** Security logic should be separate from business logic.

## Input Validation

### Rules:
- Validate all input at system boundaries (API endpoints, form handlers, CLI parsers).
- Use allowlists, not blocklists — specify what IS allowed, not what isn't.
- Validate type, length, range, and format.
- Reject invalid input early with clear error messages.
- Never use input in SQL queries, shell commands, or HTML without sanitization.

### Implementation:
```typescript
// GOOD: Validate with a schema
const schema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  age: z.number().int().min(0).max(150),
});

// BAD: Trust user input
function createUser(input: any) {
  const query = `INSERT INTO users (name, email) VALUES ('${input.name}', '${input.email}')`;
  // SQL injection!
}
```

## Secrets & Credentials

### Rules:
- **Never** commit secrets, API keys, tokens, passwords, or certificates to code.
- **Never** log secrets or include them in error messages.
- **Always** use environment variables or secret managers for credentials.
- **Always** rotate secrets after a suspected breach.
- **Always** use `.env.example` (not `.env`) for documentation.

### What Counts as a Secret:
- API keys and tokens
- Database passwords
- JWT signing keys
- OAuth client secrets
- Encryption keys
- Private certificates
- Any credential that grants access

### Detection:
If you find a secret in code:
1. Remove it immediately.
2. Add it to the secret manager.
3. Rotate the secret (it's compromised).
4. Check git history for when it was added.
5. Add a pre-commit hook to prevent future commits.

## Authentication & Authorization

### Rules:
- Always authenticate before authorizing.
- Use well-tested auth libraries, not custom implementations.
- Store passwords with bcrypt/argon2, never MD5/SHA1.
- Use short-lived JWTs with refresh tokens for session management.
- Validate tokens on every request, not just at login.
- Implement rate limiting on auth endpoints.

### Authorization:
- Check permissions at the API endpoint level, not just in the UI.
- Use role-based access control (RBAC) or attribute-based access control (ABAC).
- Deny by default — require explicit permission for every action.
- Never rely on client-side checks for security.

## OWASP Top 10 Prevention

| Vulnerability | Prevention |
|---------------|------------|
| Injection | Use parameterized queries, ORM, or query builders |
| Broken Auth | Use proven auth libraries, MFA, rate limiting |
| Sensitive Data Exposure | Encrypt at rest and in transit, minimize data collection |
| XML External Entities | Disable XML external entity processing |
| Broken Access Control | Deny by default, check permissions server-side |
| Security Misconfiguration | Use security headers, disable debug mode in production |
| Cross-Site Scripting (XSS) | Encode output, use CSP headers, sanitize input |
| Insecure Deserialization | Validate data integrity, avoid untrusted deserialization |
| Using Components with Known Vulnerabilities | Run `npm audit`, update dependencies regularly |
| Insufficient Logging | Log security events, monitor for anomalies |

## Data Protection

### Rules:
- Encrypt sensitive data at rest (AES-256) and in transit (TLS 1.2+).
- Never store passwords in plaintext — use bcrypt with salt.
- PII (personally identifiable information) must be encrypted or tokenized.
- Implement data retention policies — don't keep data longer than needed.
- Log access to sensitive data for audit purposes.

## Secure Coding Practices

- Use prepared statements for all database queries.
- Encode output to prevent XSS (HTML, URL, JavaScript contexts).
- Validate file uploads (type, size, content).
- Use Content Security Policy (CSP) headers.
- Implement CORS with explicit allowed origins.
- Use HTTP-only, Secure, SameSite cookies for session tokens.
- Set appropriate security headers (HSTS, X-Frame-Options, etc.).

## Dependencies

- Run `npm audit` / `pip audit` / `go vuln check` regularly.
- Pin dependency versions in lock files.
- Review new dependencies before adding them.
- Check for known vulnerabilities before merging.
- Prefer well-maintained, widely-used libraries.
