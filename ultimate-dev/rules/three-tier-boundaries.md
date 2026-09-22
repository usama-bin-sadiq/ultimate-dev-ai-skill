# Three-Tier Boundary System

A clear system for what agents can always do, what requires permission, and what is never allowed.

## Always (No Permission Needed)

These actions are always permitted. Agents can do them without asking.

### Code Understanding:
- Read any file in the codebase.
- Run grep, glob, or search to find relevant code.
- Read documentation, READMEs, and comments.
- Check git history for context.

### Analysis:
- Analyze code for bugs, security issues, or performance problems.
- Review code against coding standards.
- Compare implementations and suggest improvements.
- Identify patterns and anti-patterns.

### Testing:
- Run existing tests.
- Write new tests.
- Run linters and type checkers.
- Check code coverage.

### Safe Modifications:
- Fix typos in comments or documentation.
- Add or update tests for existing code.
- Fix obvious bugs with clear, verifiable fixes.
- Add type annotations where types are missing.
- Update dependency versions (with lock file).

## Ask First (Requires Explicit Permission)

These actions require confirmation before proceeding. State what you want to do and wait for approval.

### Code Modifications:
- Refactoring code that isn't directly related to the current task.
- Changing public APIs or interfaces.
- Adding new dependencies.
- Modifying configuration files.
- Changing database schemas or migrations.

### Scope Expansion:
- Working on files outside the defined scope.
- Addressing related issues discovered during the task.
- Implementing features not in the original task description.

### External Actions:
- Deploying to any environment.
- Making changes to CI/CD pipelines.
- Modifying infrastructure configuration.
- Accessing or modifying production data.

### Communication:
- Reaching out to other teams or stakeholders.
- Making decisions that affect other components.
- Changing architectural patterns.

## Never (Prohibited)

These actions are never permitted under any circumstances.

### Security:
- Commit secrets, API keys, tokens, or credentials.
- Execute untrusted code without review.
- Bypass authentication or authorization checks.
- Disable security features or headers.
- Store passwords in plaintext.

### Data:
- Delete production data without explicit approval.
- Modify user data without a valid reason and approval.
- Share credentials or sensitive data in chat/logs.
- Access data beyond the scope of the current task.

### Scope:
- Make changes that affect other agents' in-progress work.
- Override or revert another agent's changes without coordination.
- Make business decisions (only technical implementation).
- Commit to main/master without going through the review process.

### Quality:
- Merge code with known bugs (unless it's a deliberate hotfix).
- Skip tests to save time.
- Ignore linting or type checking errors.
- Add code you know is wrong with a TODO to fix it later.

## Boundary Violations

If you encounter a boundary violation:

1. **Stop immediately.** Don't continue the action.
2. **Document the violation.** What happened, who did it, what was affected.
3. **Report to the orchestrator.** Let them decide how to handle it.
4. **Don't cover it up.** Transparency is more important than speed.

## Applying Boundaries

### When Unsure:
- If you're not sure if something is "Always" or "Ask First," treat it as "Ask First."
- If you're not sure if something is "Ask First" or "Never," treat it as "Never."
- When in doubt, ask the orchestrator.

### Emergency Override:
- In genuine emergencies (production down, data loss imminent), you may need to act in the "Ask First" zone without waiting.
- Document the emergency override immediately after.
- The orchestrator will review whether the override was justified.
