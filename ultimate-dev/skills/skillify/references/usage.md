<!-- Moved verbatim from skillify/SKILL.md, the
     'usage' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Usage

\`\`\`
$ $B skill run <name>
{ "items": [...], "count": N }
\`\`\`
```

Capture `stagedDir` (the path returned by `stageSkill`). You'll pass it
to `$B skill test` next, then to `commitSkill` or `discardStaged`.
