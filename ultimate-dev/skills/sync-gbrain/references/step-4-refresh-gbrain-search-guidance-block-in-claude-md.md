<!-- Moved verbatim from sync-gbrain/SKILL.md, the
     'step-4-refresh-gbrain-search-guidance-block-in-claude-md' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4: Refresh `## GBrain Search Guidance` block in CLAUDE.md

Capability check (per /plan-eng-review §6):

```bash
bun run ~/.claude/skills/gstack/bin/gstack-gbrain-read-capability.ts <user-args>
```

The helper reports JSON `status: ready` only after the successful code sync's
source and real worktree match `.gbrain-source`, the source registration points
to that worktree, and a bounded, source-scoped list/get returns the same page.
It never creates or deletes a page. A `get` may update gbrain's internal
retrieval metadata; the guarantee is no page or source mutation, not zero
internal writes. `status: unknown` (including transient CLI errors, stale state,
or an unverified response) is NOT evidence that the brain is unusable. A
`status: skipped` result for `--no-code`, `--dry-run`, `--refresh-cache`, or
`--audit` means no code-read probe was attempted. Do not run a write probe,
switch to another source, or claim a successful read.

Then update CLAUDE.md based on the helper's status:

**If `status=ready`** — write or update the block. Idempotent: find the
HTML-comment-delimited block; replace its body if it exists; append at the
end of CLAUDE.md if it doesn't. NEVER duplicate. Block is machine-AGNOSTIC
(no engine, no page counts, no last-sync time — those are in the existing
`## GBrain Configuration` block).

Verbatim block content (copy exactly):

```markdown
