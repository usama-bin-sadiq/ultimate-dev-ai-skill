# Coding Standards

Universal coding standards that apply across all projects and languages.

## Naming Conventions

### General Rules:
- Use descriptive, intention-revealing names.
- Avoid abbreviations unless they're universally understood (URL, HTTP, API).
- Names should reveal intent, not implementation.
- Be consistent with the existing codebase.

### By Type:
| Type | Convention | Example |
|------|-----------|---------|
| Variables | camelCase | `userEmail`, `isVisible` |
| Functions | camelCase | `getUserById`, `validateInput` |
| Classes | PascalCase | `UserService`, `AuthMiddleware` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| Files | kebab-case | `user-service.ts`, `auth-middleware.ts` |
| Database columns | snake_case | `user_id`, `created_at` |
| CSS classes | BEM or kebab | `card__title--active` |
| Boolean variables | is/has/can/should prefix | `isActive`, `hasPermission` |

### Bad Names:
```typescript
// Bad: vague
const data = getData();
function process(d: any) { ... }
const flag = true;

// Good: descriptive
const userProfiles = getUserProfiles();
function processPayment(paymentDetails: PaymentDetails) { ... }
const isEligibleForDiscount = true;
```

## Formatting

### General:
- Use consistent indentation (2 spaces for JS/TS/JSON, 4 for Python).
- Max line length: 100 characters (or follow project config).
- Use trailing commas in multi-line structures.
- Single quotes for strings in JS/TS (unless project uses double).
- No unused imports or variables.

### Organization:
- Group imports: external → internal → relative.
- Separate logical blocks with a blank line.
- Keep functions focused and short (prefer under 50 lines).
- One export per file (except closely related types).

## Function Design

### Rules:
- Functions should do one thing and do it well.
- Functions should be small (under 30 lines preferred).
- Functions should have 2-4 parameters; use objects for more.
- Functions should have clear input/output types.
- Avoid side effects — prefer pure functions.
- Use early returns to reduce nesting.

### Example:
```typescript
// Bad: does too much, hard to test
function handleUserAction(action: string, userId: string, data: any) {
  if (action === 'create') {
    // 20 lines of creation logic
  } else if (action === 'update') {
    // 20 lines of update logic
  } else if (action === 'delete') {
    // 20 lines of deletion logic
  }
}

// Good: focused, testable, clear
function createUser(userData: CreateUserData): Promise<User> {
  validateUserData(userData);
  const hashedPassword = await hashPassword(userData.password);
  return db.users.create({ ...userData, password: hashedPassword });
}
```

## Error Handling

### Rules:
- Always handle errors — never let them propagate silently.
- Use typed errors, not string messages.
- Provide actionable error messages.
- Log errors with sufficient context.
- Distinguish between user errors and system errors.

### Example:
```typescript
// Bad: swallows error
try {
  await riskyOperation();
} catch (e) {
  console.log(e);
}

// Good: handles error meaningfully
try {
  await riskyOperation();
} catch (error) {
  if (error instanceof ValidationError) {
    return left(error); // User error — return to caller
  }
  logger.error('Operation failed', { error, context });
  return left(new SystemError('Operation failed', { cause: error }));
}
```

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Instead |
|-------------|--------------|---------|
| God objects | Hard to maintain, test, understand | Single responsibility |
| Magic numbers | Unclear meaning, hard to change | Named constants |
| Deep nesting | Hard to read, error-prone | Early returns, extract functions |
| String concatenation | Error-prone, insecure | Template literals, parameterized queries |
| `any` type | Defeats type safety | Specific types, `unknown` if truly dynamic |
| Copy-paste code | Bugs duplicated, maintenance nightmare | Extract shared functions |
| Boolean parameters | Unclear at call site | Enums, options objects |
| Null callbacks | Confusing error handling | Explicit error types |
| Premature optimization | Complexity without benefit | Profile first, optimize targeted |
| Adding "just in case" | YAGNI — You Ain't Gonna Need It | Add when needed |

## Comments

### Rules:
- Code should be self-documenting — comments explain WHY, not WHAT.
- Don't comment obvious code.
- Use JSDoc/TSDoc for public APIs.
- Keep comments up to date — stale comments are worse than no comments.
- Use TODO/FIXME with a ticket number.

### Good Comments:
```typescript
// WHY: Cache is cleared here because the upstream API has eventual consistency
// and stale data can cause payment mismatches (see INC-4521)
cache.clear();

// TODO(#1234): Replace with official SDK when they add TypeScript support
```

### Bad Comments:
```typescript
// Increment counter by 1
counter++;

// Get the user from the database
const user = await db.users.findById(id);
```

## Testing Standards

- Test behavior, not implementation.
- Use descriptive test names that explain the scenario.
- Follow AAA pattern: Arrange, Act, Assert.
- One assertion per concept (not literally one assert per test).
- Test edge cases: empty, null, boundary, concurrent.
- Mock external dependencies, not internal logic.
- Tests should be deterministic — no flaky tests.
