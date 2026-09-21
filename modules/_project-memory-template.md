# Project Memory

This file is a per-project cache — NOT part of the canonical skill package. It is never overwritten by skill updates/reinstalls. It lives at `<repo>/.ultimate-dev/project-memory.md`.

## Detected Stack

<!-- Refreshed opportunistically, not on every task -->
- **Language**: [e.g., TypeScript 5.3, Python 3.12]
- **Framework**: [e.g., Next.js 14, FastAPI 0.110]
- **Runtime**: [e.g., Node 20 LTS, Bun 1.1]
- **Package Manager**: [e.g., pnpm 8.15, poetry 1.7]
- **Database**: [e.g., PostgreSQL 16, Redis 7]
- **Deployment**: [e.g., Vercel, AWS ECS, Railway]

## Architecture Patterns

<!-- Established patterns already in use in this repo -->
- **Style**: [e.g., modular monolith, hexagonal, CQRS on write side]
- **API**: [e.g., REST with OpenAPI, GraphQL, tRPC]
- **Auth**: [e.g., NextAuth.js, Clerk, custom JWT]
- **State**: [e.g., Zustand, Redux Toolkit, Jotai]

## ADR Links

<!-- Links to Architecture Decision Records written under documentation module -->
- [ADR-001]: [title] — [date]
- [ADR-002]: [title] — [date]

## Repo-Specific Conventions

<!-- Rules the classification/decomposition steps should treat as constraints -->
- [e.g., "No ORM — raw SQL only via kysely"]
- [e.g., "All API routes must validate with Zod"]
- [e.g., "Commit messages follow Conventional Commits"]
- [e.g., "No console.log in production code — use pino logger"]

## Verified Operational Behavior

<!-- Things confirmed to work, not assumed -->
- [e.g., "Migration from v2 to v3 requires manual step: run `pnpm db:push`"]
- [e.g., "CI pipeline takes ~4 minutes — don't add steps that increase it"]
- [e.g., "Tests must run with `DATABASE_URL=...` env var set"]

## Migration Hazards

<!-- Known dangers when changing certain things -->
- [e.g., "Changing User schema requires updating 3 migration files — check dependencies"]
- [e.g., "Renaming API endpoints breaks mobile app v2.x — coordinate release"]

## Measured Baselines

<!-- Performance/size baselines for regression detection -->
- **Bundle size**: [e.g., 245KB gzipped (check: `pnpm build && du -sh .next/static/chunks`)]
- **API p95**: [e.g., 120ms for /api/users (check: Datadog dashboard)]
- **Test suite**: [e.g., 847 tests, ~45 seconds full run]

---

## Rules

1. **Read at classification time** if present — cheap since it's small
2. **Write only when a complex task produces something durable** — never speculatively
3. **Never treat as authoritative over the actual codebase** — if memory and code disagree, flag the discrepancy
4. **Size ceiling**: Max 50 entries or 2KB, whichever is smaller — summarize oldest/least-relevant when exceeded
5. **Invalidate stale knowledge** when versions, architecture, or assumptions change
