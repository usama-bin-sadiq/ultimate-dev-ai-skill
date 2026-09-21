---
name: backend
description: >
  Backend architecture: API design, server patterns, microservices, event-driven, authentication, caching, queue processing. Works with ANY backend technology.
triggers: [API, server, endpoint, REST, gRPC, worker, queue, service, microservice, serverless function, middleware, auth logic, business logic]
anti_triggers: [UI, component, page, CSS, frontend, browser, schema design, query tuning, CI/CD pipeline]
last_verified: 2026-09-21
---

# Backend Architect (pattern-based)

## Core Principles (technology-agnostic)

1. **API-first design** — contracts before implementation
2. **Defense in depth** — multiple security layers
3. **Graceful degradation** — fail safely, recover quickly
4. **Stateless services** — scale horizontally
5. **Observable systems** — log, metric, trace everything

## Key Patterns

### API Design
- RESTful resource modeling
- GraphQL schema design
- gRPC service definitions
- API versioning strategies
- Error response standards

### Architecture Patterns
- Monolith → Modular monolith → Microservices
- Event-driven architecture
- CQRS (Command Query Separation)
- Saga pattern (distributed transactions)
- Circuit breaker pattern

### Security Patterns
- Authentication (JWT, OAuth2, API keys)
- Authorization (RBAC, ABAC)
- Input validation
- Rate limiting
- CORS configuration

### Performance Patterns
- Connection pooling
- Caching layers
- Async processing
- Batch operations
- Lazy loading

## Anti-Patterns
- Bad: "Build microservices for small teams" — violates architecture fitness
- Good: "Start monolith, extract when justified" — satisfies architecture fitness

- Bad: "Skip API documentation" — violates API-first design
- Good: "OpenAPI spec before implementation" — satisfies API-first design

## Output Contract
- API specifications (OpenAPI, GraphQL schema)
- Architecture diagrams
- Security configurations
- Performance benchmarks
- Deployment strategies