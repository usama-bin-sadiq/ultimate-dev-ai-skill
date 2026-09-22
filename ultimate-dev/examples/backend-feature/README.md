# Example: Backend API Feature

A complete example of implementing a new backend feature from specification to deployment.

## Task Description

**Feature Request:** Add a user search API endpoint that supports filtering by name and email, with pagination and sorting.

**Requirements:**
- Endpoint: `GET /api/users/search`
- Query parameters: `q` (search term), `page`, `limit`, `sort_by`, `sort_order`
- Search should match name (partial, case-insensitive) and email (exact or partial)
- Return paginated results with metadata
- Require authentication (JWT)
- Rate limit: 100 requests per minute per user

## Context

```yaml
task_id: "implement-user-search-001"
title: "Implement user search API endpoint"
objective: "Add GET /api/users/search with filtering, pagination, and sorting"
priority: "high"
agent: "backend-specialist"
context:
  background: >
    The admin dashboard needs a user search feature. Currently, admins
    can only view a flat list of all users with no filtering capability.
    This endpoint will power the search functionality.
  related_files:
    - "src/routes/users.ts"
    - "src/services/user.ts"
    - "src/middleware/auth.ts"
    - "src/middleware/rateLimit.ts"
    - "src/types/user.ts"
    - "src/db/schema.ts"
  existing_patterns: >
    Other search endpoints in src/routes/ follow the pattern of:
    1. Validate query params with Zod
    2. Check authentication middleware
    3. Call service method
    4. Return formatted response with pagination metadata
    Database queries use the query builder from src/db/queryBuilder.ts
```

## Workflow Steps

### Step 1: Spec (Clarify Requirements)

Before coding, confirm the specification:

```yaml
spec:
  endpoint: "GET /api/users/search"
  auth: "Required (JWT in Authorization header)"
  query_params:
    q:
      type: string
      required: false
      description: "Search term (matches name or email)"
      min_length: 1
      max_length: 100
    page:
      type: integer
      required: false
      default: 1
      min: 1
    limit:
      type: integer
      required: false
      default: 20
      min: 1
      max: 100
    sort_by:
      type: string
      required: false
      default: "created_at"
      enum: ["name", "email", "created_at"]
    sort_order:
      type: string
      required: false
      default: "desc"
      enum: ["asc", "desc"]
  response:
    status: 200
    body:
      users: "User[]"
      pagination:
        page: integer
        limit: integer
        total: integer
        total_pages: integer
  errors:
    - status: 401
      description: "Missing or invalid JWT"
    - status: 422
      description: "Invalid query parameters"
    - status: 429
      description: "Rate limit exceeded"
```

### Step 2: Plan (Implementation Plan)

```yaml
plan:
  steps:
    - step: 1
      action: "Add search schema validation with Zod"
      file: "src/schemas/userSearch.ts"
      description: "Define query parameter schema"
    - step: 2
      action: "Add search method to UserService"
      file: "src/services/user.ts"
      description: "Implement search with filtering, pagination, sorting"
    - step: 3
      action: "Add search route"
      file: "src/routes/users.ts"
      description: "GET /api/users/search with auth and rate limiting"
    - step: 4
      action: "Add database index for search performance"
      file: "src/db/migrations/xxxx_add_user_search_index.ts"
      description: "Add composite index on name and email"
    - step: 5
      action: "Write tests"
      file: "src/routes/__tests__/users.search.test.ts"
      description: "Unit and integration tests for search"
    - step: 6
      action: "Update API documentation"
      file: "docs/api/users.md"
      description: "Document the new endpoint"
  estimated_effort: "2-3 hours"
  risks:
    - "Search performance without proper indexing"
    - "SQL injection if search term is not sanitized"
```

### Step 3: Implement

**Step 3.1: Schema Validation**
```typescript
// src/schemas/userSearch.ts
import { z } from 'zod';

export const userSearchSchema = z.object({
  q: z.string().min(1).max(100).optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort_by: z.enum(['name', 'email', 'created_at']).default('created_at'),
  sort_order: z.enum(['asc', 'desc']).default('desc'),
});

export type UserSearchParams = z.infer<typeof userSearchSchema>;
```

**Step 3.2: Service Method**
```typescript
// src/services/user.ts (add to existing file)
async search(params: UserSearchParams): Promise<{ users: User[]; pagination: PaginationMeta }> {
  const { q, page, limit, sort_by, sort_order } = params;
  const offset = (page - 1) * limit;

  let query = this.db.users.createQueryBuilder();

  if (q) {
    query = query.where(
      '(LOWER(name) LIKE LOWER(:search) OR LOWER(email) LIKE LOWER(:search))',
      { search: `%${q}%` }
    );
  }

  const [users, total] = await query
    .orderBy(sort_by, sort_order)
    .skip(offset)
    .take(limit)
    .getManyAndCount();

  return {
    users,
    pagination: {
      page,
      limit,
      total,
      total_pages: Math.ceil(total / limit),
    },
  };
}
```

**Step 3.3: Route**
```typescript
// src/routes/users.ts (add to existing file)
router.get('/search',
  authMiddleware,
  rateLimitMiddleware({ windowMs: 60000, max: 100 }),
  validate(userSearchSchema, 'query'),
  async (req, res) => {
    const result = await userService.search(req.query);
    res.json(result);
  }
);
```

### Step 4: Test

```typescript
// src/routes/__tests__/users.search.test.ts
describe('GET /api/users/search', () => {
  it('returns paginated results', async () => {
    const response = await request(app)
      .get('/api/users/search?page=1&limit=10')
      .set('Authorization', `Bearer ${validToken}`);

    expect(response.status).toBe(200);
    expect(response.body.users).toHaveLength(10);
    expect(response.body.pagination).toEqual({
      page: 1,
      limit: 10,
      total: expect.any(Number),
      total_pages: expect.any(Number),
    });
  });

  it('filters by search term', async () => {
    const response = await request(app)
      .get('/api/users/search?q=john')
      .set('Authorization', `Bearer ${validToken}`);

    expect(response.status).toBe(200);
    response.body.users.forEach(user => {
      expect(user.name.toLowerCase()).toContain('john');
    });
  });

  it('returns 401 without auth token', async () => {
    const response = await request(app)
      .get('/api/users/search');

    expect(response.status).toBe(401);
  });

  it('returns 422 for invalid parameters', async () => {
    const response = await request(app)
      .get('/api/users/search?limit=999')
      .set('Authorization', `Bearer ${validToken}`);

    expect(response.status).toBe(422);
  });
});
```

### Step 5: Handoff

```yaml
task_id: "implement-user-search-001"
agent: "backend-specialist"
status: "completed"

summary: >
  Implemented GET /api/users/search endpoint with filtering by name/email,
  pagination, sorting, authentication, and rate limiting.

what_changed:
  - file: "src/schemas/userSearch.ts"
    action: "created"
    description: "Zod schema for query parameter validation"
  - file: "src/services/user.ts"
    action: "modified"
    description: "Added search method with filtering, pagination, sorting"
  - file: "src/routes/users.ts"
    action: "modified"
    description: "Added GET /search route with auth and rate limiting"
  - file: "src/db/migrations/xxxx_add_user_search_index.ts"
    action: "created"
    description: "Added composite index on name and email for search performance"
  - file: "src/routes/__tests__/users.search.test.ts"
    action: "created"
    description: "4 test cases covering pagination, filtering, auth, validation"
  - file: "docs/api/users.md"
    action: "modified"
    description: "Documented the new search endpoint"

evidence:
  - type: "test_output"
    content: |
      PASS src/routes/__tests__/users.search.test.ts
        ✓ returns paginated results (45ms)
        ✓ filters by search term (38ms)
        ✓ returns 401 without auth token (12ms)
        ✓ returns 422 for invalid parameters (15ms)
      Tests: 4 passed, 4 total

assumptions:
  - "Case-insensitive search is acceptable for performance"
  - "100 requests/minute rate limit matches other endpoints"

next_steps:
  - "Add full-text search index if performance is insufficient"
  - "Consider adding search by role or status in future"
```

## Key Takeaways

1. **Spec first.** Clarify requirements before writing code.
2. **Plan before implementing.** Break the work into steps with file-level detail.
3. **Follow existing patterns.** Use the same middleware, validation, and error handling as other routes.
4. **Test thoroughly.** Cover happy path, auth, validation, and edge cases.
5. **Document everything.** Update API docs, include evidence in handoff.
