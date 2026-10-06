# Contributing

## Layout

```text
ultimate-dev/
  SKILL.md        the router and execution discipline
  skills/         focused sub-skills (each a directory with SKILL.md)
  agents/         specialist roles (one markdown file per role)
  tools/          validator and corpus-maintenance scripts
  resources/      support material used by those tools
```

The repository is the skill: everything a user installs lives under
`ultimate-dev/`. Repository mechanics live at the root.

## Before you write anything

Run the validator. It is the source of truth for what the tree must satisfy:

```bash
python3 ultimate-dev/tools/validate-skills.py
```

## Adding a capability

Two shapes, and you must pick one deliberately:

- **Skill** — a repeatable procedure. `skills/<name>/SKILL.md` with frontmatter
  (`name`, `description`), an explicit when-to-use, the procedure, failure
  modes, and optional `references/` and scripts.
- **Agent** — a bounded, isolated slice of work that returns a single merged
  answer. `agents/<name>.md` naming its procedure, output contract, and
  prohibitions.

A one-off task is not a skill. Two skills that fire on the same request split
the trigger signal; if you are adding a second, check the first.

## Writing rules

- Descriptions route: name the user goal, include trigger words, stay under
  ~1000 characters. The description is the only entry point.
- SKILL.md stays focused — under ~500 lines where possible; detail goes into
  `references/` files that name when to load them.
- Scripts are executable and self-documenting; reference them with exact
  commands.
- No emoji. No frontmatter where none is specified.
- Never claim a result you did not observe; a capability that does not say how
  it verifies is not finished.

## Testing changes

```bash
python3 ultimate-dev/tools/validate-skills.py --strict
python3 ultimate-dev/tools/check-sibling-imports.py ultimate-dev
python3 ultimate-dev/tools/test-workflow-auth.py
python3 ultimate-dev/tools/check-workflow-auth.py
```

CI runs the same set plus the validator's self-tests, on bare Python 3.
