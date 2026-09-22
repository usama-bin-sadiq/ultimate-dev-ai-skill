---
name: security-skill
description: >
  Meta-cognitive skill for security. Teaches HOW to think about security
  in ANY system — regardless of language, framework, or platform.
triggers: [security, vulnerability, auth, injection, encryption, hardening, protect, threat]
provides: security_ability
---

# Security Skill — Protect Anything

## Purpose

An **ability**. Security is a mindset, not a tool. This skill teaches you how to
think about security in ANY system — not just specific vulnerability checklists.

## The Ability

```
Given any system to secure, you can:
1. Identify what needs protection (and from whom)
2. Think like an attacker (what would you exploit?)
3. Apply defense in depth (no single point of failure)
4. Verify security (don't just assume it)
5. Balance security with usability
```

## How to Secure ANYTHING

### Step 1: Threat Model First

```
Before securing anything, answer:
1. What am I protecting? (data, availability, integrity)
2. Who is the attacker? (external, internal, automated)
3. What is their goal? (data theft, disruption, fraud)
4. What is their capability? (script kiddie, organized, nation-state)
5. What is the blast radius if compromised?
```

### Step 2: Think Like an Attacker

```
For ANY system, ask:
1. What inputs does it accept? (injection points)
2. What data does it store? (attack surface)
3. What permissions does it have? (privilege escalation)
4. What can go wrong? (failure modes)
5. What would I do if I were the attacker?
```

### Step 3: Defense in Depth

```
Layer 1: INPUT VALIDATION    → Reject bad input at the boundary
Layer 2: AUTHENTICATION      → Verify identity
Layer 3: AUTHORIZATION       → Verify permissions
Layer 4: DATA PROTECTION     → Encrypt, hash, mask
Layer 5: LOGGING & MONITORING → Detect and respond
Layer 6: ERROR HANDLING      → Don't leak information
```

### Step 4: Universal Security Checklist

```
INPUT:
  □ All input validated on server side (never trust client)
  □ Allowlists over blocklists
  □ File uploads validated (type, size, content)
  □ SQL queries parameterized (never string concatenation)

AUTH:
  □ Passwords hashed with bcrypt/argon2 (never MD5/SHA1)
  □ Sessions expire after inactivity
  □ MFA available for sensitive operations
  □ Login rate-limited
  □ Tokens have expiration

DATA:
  □ Sensitive data encrypted at rest
  □ HTTPS enforced (no mixed content)
  □ Secrets not in code, logs, or URLs
  □ PII handled according to regulations

ERRORS:
  □ Error messages don't leak internals
  □ Stack traces hidden from users
  □ Logging doesn't include sensitive data
```

### Step 5: Verify, Don't Assume

```
Security verification:
1. Run automated security scans (SAST, DAST, dependency audit)
2. Manual review of auth/authz code
3. Penetration testing (or at least threat modeling)
4. Verify in staging, not just development
```

## Security Anti-Patterns

- DO NOT trust client-side validation alone
- DO NOT store passwords in plain text
- DO NOT skip security headers
- DO NOT log sensitive data
- DO NOT use deprecated crypto algorithms
