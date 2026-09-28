<!-- Moved verbatim from skillify/SKILL.md, the 'Step 10 — Commit (atomic) or discard' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 10 — Commit (atomic) or discard

If the user approved:

```ts
import { commitSkill } from '<gstack-install>/browse/src/browser-skill-write';
const dest = commitSkill({
  name: '<name>',
  tier: '<global|project>',  // from step 2 answer
  stagedDir: '<stagedDir>',
});
console.log(`Committed: ${dest}`);
```

If `commitSkill` throws "already exists" (tier-shadowing collision the
user dismissed in step 2), report and ask whether to:

- Pick a different name (back to step 2)
- `$B skill rm <name>` then retry
- Discard

If the user rejected in step 9:

```ts
import { discardStaged } from '<gstack-install>/browse/src/browser-skill-write';
discardStaged('<stagedDir>');
```

Report: "Discarded. No skill was written to disk."
