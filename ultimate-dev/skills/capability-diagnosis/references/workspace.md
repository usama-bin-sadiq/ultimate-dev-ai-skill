# Where the investigation files go

Every case file, analyst prompt, and report this skill produces is written to
one directory. Decide it once, at the start, and tell the caller the path.

## The rule

Write inside the project the user is working in, under a directory named for
the investigation:

```text
<project-root>/.agent-investigations/<session-id>/
```

`<project-root>` is the root of the repository or workspace the user pointed
you at. `<session-id>` is the session identifier you resolved in step 2.

## Why not a path under the user's home directory

A previous version of this skill wrote to a fixed path under the home
directory. Three things were wrong with that:

- **It assumed a location.** The home directory is the user's, not the
  project's, and a reader on another machine has no such path.
- **It collided.** Two investigations of different sessions could write over
  each other's case files.
- **It was not reviewable.** Output outside the project is output nobody
  commits, and an investigation nobody can read is not evidence.

## If the project has no writable root

Some workspaces are read-only. In that case, say so plainly and ask where to
write before continuing — do not silently fall back to a home-directory path,
and do not write into the skill's own directory. A skill's own files are its
definition, not its scratch space.

## What goes in the directory

| File | Written by | Filled from |
|---|---|---|
| `case.md` | you, in step 2 | `templates/case.md` |
| `analyst-<dimension>.md` | each analyst subagent | `prompts/analyst-common.md` plus the dimension file |
| `report.md` | you, in step 4 | `templates/report.md` |

Cite the workspace path in the final report so a reader can find the evidence.
