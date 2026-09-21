# Git Commit Conventions

## Conventional Commits v1.0.0

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | When to Use |
|------|-------------|-------------|
| **feat** | New feature | User-facing functionality |
| **fix** | Bug fix | Correcting unexpected behavior |
| **docs** | Documentation | README, comments, API docs |
| **style** | Formatting | No code change (whitespace, semicolons) |
| **refactor** | Restructure | No feature or fix (code cleanup) |
| **perf** | Performance | Improving speed/efficiency |
| **test** | Tests | Adding/updating tests |
| **build** | Build system | Webpack, Vite, Docker |
| **ci** | CI/CD | GitHub Actions, pipelines |
| **chore** | Maintenance | Dependencies, configs, tooling |
| **revert** | Revert | Reverting a previous commit |

### Scopes

| Scope | Description |
|-------|-------------|
| **auth** | Authentication/authorization |
| **api** | API endpoints |
| **ui** | User interface |
| **db** | Database |
| **deps** | Dependencies |
| **config** | Configuration |
| **ci** | CI/CD |
| **docs** | Documentation |
| **test** | Testing |

### Examples

#### Simple
```bash
git commit -m "feat(auth): add JWT refresh token rotation"
git commit -m "fix(api): handle null response from payment gateway"
git commit -m "docs(readme): update installation instructions"
```

#### With Body
```bash
git commit -m "feat(auth): implement OAuth2 Google login

- Add Google OAuth2 strategy
- Create user session management
- Handle token refresh automatically

Closes #123"
```

#### Breaking Change
```bash
git commit -m "feat(api)!: change user endpoint response format

BREAKING CHANGE: /api/users now returns { user: {...} } instead of {...}"
```

#### Multi-line Footer
```bash
git commit -m "fix(auth): prevent token leakage in logs

- Sanitize auth headers before logging
- Remove sensitive data from error messages

Reviewed-by: Alice <alice@example.com>
Refs: #456"
```

### Commit Message Rules

1. **Subject line**: ≤72 characters, imperative mood, no period
2. **Body**: Wrap at 72 characters, explain what and why (not how)
3. **Footer**: Reference issues, breaking changes, reviewers
4. **Type**: Must be one of the listed types
5. **Scope**: Optional, lowercase, describes the area of change
6. **Description**: Imperative, lowercase, no period, completes "This commit will..."

### Bad Examples
```bash
# Too vague
git commit -m "fix stuff"
git commit -m "update"
git commit -m "WIP"

# Not imperative
git commit -m "added new feature"
git commit -m "fixed bug"

# Too long
git commit -m "feat(auth): add a new authentication system that supports multiple providers including Google, GitHub, and Twitter with proper error handling and token management"
```

### Good Examples
```bash
# Clear and concise
git commit -m "feat(auth): add Google OAuth2 login"
git commit -m "fix(db): prevent connection pool exhaustion"
git commit -m "perf(api): cache user permissions"

# With context
git commit -m "refactor(api): extract validation middleware

- Move validation logic to shared middleware
- Reduce duplication across endpoints
- Improve test coverage for edge cases"
```

### Branch Naming Conventions

| Pattern | Description | Example |
|---------|-------------|---------|
| `feature/<name>` | New feature | `feature/user-authentication` |
| `fix/<name>` | Bug fix | `fix/login-redirect-loop` |
| `hotfix/<name>` | Urgent production fix | `hotfix/security-patch` |
| `release/<version>` | Release preparation | `release/v1.2.0` |
| `chore/<name>` | Maintenance | `chore/update-dependencies` |
| `docs/<name>` | Documentation | `docs/api-reference` |
| `test/<name>` | Tests | `test/auth-integration` |

### PR Title Conventions

Follow same format as commit messages:
```
feat(auth): add OAuth2 Google login
fix(api): handle null payment response
docs(readme): update installation steps
```

### Changelog Generation

Auto-generate from commits:
```bash
# Using conventional-changelog
npx conventional-changelog -p angular -i CHANGELOG.md -s

# Using git-cliff
git-cliff --output CHANGELOG.md
```