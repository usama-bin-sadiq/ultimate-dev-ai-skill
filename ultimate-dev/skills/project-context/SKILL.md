---
name: project-context
description: >
  Build or apply a compact, evidence-based project context recipe before
  implementation: purpose, stack, architecture, build/test/run commands,
  important paths, conventions, constraints, and verification. Use when an
  agent would otherwise repeatedly explore a repository or when onboarding a
  new codebase, project, or host.
triggers: [project context, repository context, codebase recipe, build commands, test commands, project instructions, onboarding, discover project]
provides: project_context_recipe
---

# Project Context

Create a short project recipe that reduces repeated exploration without turning
the prompt into a full repository dump.

## Method

For a provider-free first pass, run `scripts/generate-project-context.py` with
an explicit project path. It is read-only unless `--output` is supplied, marks
all candidate commands `not_run`, and must be reviewed before use.

1. **Read the evidence** — inspect README, manifests, lockfiles, CI, test
   configuration, architecture notes, and the smallest relevant source paths.
2. **Record purpose and boundaries** — what the project does, what it must not
   change, and which assumptions are unverified.
3. **Record the toolchain** — language, framework, package manager, build,
   lint, test, run, and deployment commands exactly as verified.
4. **Map responsibility** — name the important entrypoints, modules, tests,
   generated files, and path-specific conventions.
5. **Record constraints** — compatibility, performance, security, privacy,
   release, and environment requirements.
6. **Define verification** — list the smallest checks that prove a change and
   any checks that cannot run in the current environment.
7. **Keep it current** — update the recipe when the build, architecture, or
   conventions change; mark stale facts instead of guessing.

## Output contract

```yaml
project: <name>
purpose: <..>
stack: [..>
entrypoints: [..]
important_paths: [..]
path_rules: [..]
commands:
  install: <..>
  build: <..>
  test: <..>
  lint: <..>
  run: <..>
conventions: [..]
constraints: [..]
verification: [..>
provenance:
  sources_inspected: [..]
  command_status: not_run
unknowns: [..>
last_verified: YYYY-MM-DD
```

Load the recipe before a task, then load only the files relevant to the current
change. Do not treat a recipe as authorization to run destructive commands or
as proof that an unverified command works.
