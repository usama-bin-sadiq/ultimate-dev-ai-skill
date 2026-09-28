<!-- Moved verbatim from command-development/SKILL.md, the
     'file-references' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## File References

### Using @ Syntax

Include file contents in command:

```markdown
---
description: Review specific file
argument-hint: [file-path]
---

Review @$1 for:

- Code quality
- Best practices
- Potential bugs
```

**Usage:**

```
> /review-file src/api/users.ts
```

**Effect:** Claude reads `src/api/users.ts` before processing command

### Multiple File References

Reference multiple files:

```markdown
Compare @src/old-version.js with @src/new-version.js

Identify:

- Breaking changes
- New features
- Bug fixes
```

### Static File References

Reference known files without arguments:

```markdown
Review @package.json and @tsconfig.json for consistency

Ensure:

- TypeScript version matches
- Dependencies are aligned
- Build configuration is correct
```
