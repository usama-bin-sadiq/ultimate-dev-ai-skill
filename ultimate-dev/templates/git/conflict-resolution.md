# Git Conflict Resolution Guide

## Conflict Types

| Type | Cause | Resolution |
|------|-------|------------|
| **Content** | Same line modified | Manual merge, keep both intentions |
| **Add/Add** | Same file added on both branches | Merge content, resolve duplicates |
| **Delete/Edit** | File deleted on one, edited on other | Decide: keep edit or accept delete |
| **Rename/Modify** | File renamed on one, modified on other | Merge renamed + modified content |
| **Binary** | Same binary file modified | Choose one version, regenerate if needed |

## Resolution Strategies

### 1. Manual Resolution
```bash
# Mark conflict as resolved
git add <file>

# Or use mergetool
git mergetool
```

### 2. Accept Theirs (incoming changes)
```bash
git checkout --theirs <file>
git add <file>
```

### 3. Accept Ours (current changes)
```bash
git checkout --ours <file>
git add <file>
```

### 4. Accept Specific Version
```bash
# Edit file manually, then:
git add <file>
```

### 5. Abort Merge
```bash
git merge --abort
# or
git rebase --abort
```

## Conflict Markers

```<<<<<<< HEAD (yours)
// Your changes
=======
// Their changes
>>>>>>> branch-name (theirs)
```

## Resolution Workflow

### Step 1: Identify Conflicts
```bash
git status
# Shows: "both modified: <file>"
```

### Step 2: Open Conflicted File
Look for `<<<<<<<`, `=======`, `>>>>>>>` markers.

### Step 3: Resolve
- Edit file to keep correct content
- Remove all conflict markers
- Save file

### Step 4: Mark Resolved
```bash
git add <file>
```

### Step 5: Complete Merge
```bash
git commit  # Merge commit
# or for rebase:
git rebase --continue
```

## Common Scenarios

### Package.json Conflict
```json
{
  "dependencies": {
    "react": "<<<<<<< HEAD
    "^18.2.0",
    =======
    "^18.3.0",
    >>>>>>> feature/update-react"
  }
}
```
**Resolution**: Keep newer version (`^18.3.0`), verify compatibility.

### Import Statement Conflict
```javascript
<<<<<<< HEAD
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
=======
import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';
>>>>>>> feature/add-auth
```
**Resolution**: Combine imports, keep all needed:
```javascript
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../hooks/useAuth';
```

### Config File Conflict
```yaml
#<<<<<<< HEAD
database:
  host: localhost
  port: 5432
#=======
database:
  host: production-db.example.com
  port: 5432
#>>>>>>> feature/production-config
```
**Resolution**: Keep environment-appropriate config, use environment variables.

## Prevention Strategies

### 1. Small, Frequent Commits
- Reduces conflict surface area
- Easier to resolve

### 2. Pull Before Push
```bash
git pull --rebase origin main
```

### 3. Feature Branch Workflow
- Keep main always deployable
- Short-lived feature branches

### 4. Code Ownership
- Clear ownership of files/modules
- Communication on shared files

### 5. Automated Testing
- Catch integration issues early
- CI/CD validates merges

## Tools

### VS Code
- Built-in merge editor
- Visual conflict resolution
- Inline change comparison

### IntelliJ/WebStorm
- Three-way merge tool
- Diff and merge viewers

### Command Line
```bash
# View conflicts
git diff --name-only --diff-filter=U

# View conflict markers
git grep "<<<<<<<"

# Skip conflict in rebase
git rebase --skip
```

## Best Practices

1. **Communicate**: Discuss conflicts with team
2. **Understand**: Know what both changes intend
3. **Test**: Verify resolution works
4. **Document**: Note complex resolutions in commit message
5. **Prevent**: Use strategies to avoid conflicts