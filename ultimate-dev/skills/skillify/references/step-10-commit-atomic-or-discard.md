<!-- Moved verbatim from skillify/SKILL.md, the
     'step-10-commit-atomic-or-discard' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 10 — Commit (atomic) or discard

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
