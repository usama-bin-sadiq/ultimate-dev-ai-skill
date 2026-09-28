<!-- Moved verbatim from setup-gbrain/SKILL.md, the
     'step-6-per-remote-policy-d3-triad-gated-repo-import' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 6: Per-remote policy (D3 triad, gated repo-import)

If we're in a git repo with an `origin` remote, check the policy:

```bash
current_tier=$(~/.claude/skills/gstack/bin/gstack-gbrain-repo-policy get)
```

Branches:
- `read-write` → import this repo: `gbrain import "$(pwd)" --no-embed` then
  `gbrain embed --stale &` in the background.
- `read-only` → skip import entirely (this tier is enforced by the future
  auto-import hook + by gbrain resolver injection, not here).
- `deny` → do nothing.
- `unset` → AskUserQuestion: "How should `<normalized-remote>` interact with
  gbrain?"
  - `read-write` — agent can search AND write new pages from this repo
  - `read-only` — agent can search but never write
  - `deny` — no interaction at all
  - `skip-for-now` — don't persist, ask next time

  On answer (other than skip-for-now):
  ```bash
  ~/.claude/skills/gstack/bin/gstack-gbrain-repo-policy set "$REMOTE" "$TIER"
  ```
  Then import iff `read-write`.

If outside a git repo OR no origin remote: skip this step with a note.

For `/setup-gbrain --repo` invocations, execute ONLY Step 6 and exit.

---
