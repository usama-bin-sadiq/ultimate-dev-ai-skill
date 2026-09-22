---
name: api-patterns
description: >
  API design patterns, versioning, documentation, rate limiting, authentication, error handling, GraphQL, gRPC, WebSocket. Technology-agnostic.
triggers: [API design, REST, GraphQL, gRPC, WebSocket, API versioning, rate limiting, API documentation, OpenAPI, Swagger]
anti_triggers: [database schema, frontend UI, Git operations, CI/CD pipeline]
last_verified: 2026-09-21
---

# API Patterns Module (technology-agnostic)

## Core Principles

1. **Contract-first** — design API before implementation
2. **Consistency** — uniform patterns across all endpoints
3. **Versioning** — backward compatibility by default
4. **Documentation** — machine-readable specs (OpenAPI)
5. **Security** — authentication, authorization, input validation

## Key Patterns

### REST Patterns
- Resource-oriented design
- Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Consistent error responses
- Pagination (cursor-based, offset)
- HATEOAS (optional)

### GraphQL Patterns
- Schema-first design
- Query optimization (N+1 prevention)
- Subscription patterns
- Federation for microservices
- DataLoader for batching

### gRPC Patterns
- Service definition (protobuf)
- Streaming (unary, server, client, bidirectional)
- Interceptors
- Load balancing
- Error handling

### Versioning Patterns
- URL path versioning (/v1/, /v2/)
- Header versioning
- Query parameter versioning
- Content negotiation
- Deprecation strategy

### Security Patterns
- OAuth2 flows
- JWT token management
- API key rotation
- Rate limiting (per user, per endpoint)
- CORS configuration

### Error Patterns
- Standard error response format
- Error codes (not just messages)
- Retry guidance
- Circuit breaker integration

## Anti-Patterns
- Bad: "Breaking changes without version bump" — violates versioning
- Good: "Add new field, deprecate old" — satisfies versioning

- Bad: "Generic error messages" — violates documentation
- Good: "Structured errors with codes and details" — satisfies documentation

## Output Contract
- API specifications (OpenAPI, GraphQL schema, protobuf)
- Versioning strategy document
- Error code catalog
- Security configuration
- Rate limiting rules