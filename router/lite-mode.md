# LITE MODE — For Small/Tiny Models

Use this router when context is limited (≤32K tokens).

## Quick Classification

Read the task. Answer 3 questions:

1. **Is it one file?** → atomic (do inline)
2. **Is it one feature?** → moderate (load 1 module)
3. **Is it multiple features?** → complex (do best effort)

## Module Lookup (fast)

| Task Contains | Load This Module |
|---------------|------------------|
| API, endpoint, server | modules/engineering/backend.md |
| UI, component, page, CSS | modules/engineering/frontend.md |
| schema, query, index, database | modules/engineering/database.md |
| deploy, CI/CD, Docker | modules/engineering/devops.md |
| auth, security, XSS | modules/engineering/security.md |
| test, coverage, mock | modules/engineering/testing-qa.md |
| mobile, iOS, Android | modules/engineering/mobile.md |
| architecture, system design | modules/engineering/architecture.md |
| docs, README, API docs | modules/engineering/documentation.md |
| Git, commit, branch | modules/engineering/git.md |
| cache, Redis, CDN | modules/caching/caching.md |
| search, autocomplete | modules/search/search.md |
| WebSocket, real-time | modules/real-time/real-time.md |
| queue, async, event | modules/messaging/messaging.md |
| cloud, serverless, IaC | modules/cloud/cloud.md |
| AI, ML, LLM, embedding | modules/ai-ml/ai-ml.md |
| blockchain, smart contract | modules/blockchain/blockchain.md |
| i18n, translation, locale | modules/i18n-l10n/i18n-l10n.md |
| performance, optimize | modules/performance/performance.md |
| accessibility, a11y, WCAG | modules/accessibility/accessibility.md |

## How to Use

1. Match task to table above
2. Read the module: `Read: modules/<path>`
3. Apply patterns from that module
4. Output result

## Output Format
```
[tier: small | module: <name>]
<result>
```

## Fallback

If no module matches → use Best Practices from SKILL.md and do inline.
