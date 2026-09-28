<!-- Moved verbatim from setup-gbrain/SKILL.md, the
     'setup-gbrain-cleanup-orphans-d20' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## `/setup-gbrain --cleanup-orphans` (D20)

Re-collect a PAT (show the Path 2a PAT scope disclosure — it lives in the
brain-init section; read that section if it isn't already loaded), then:

```bash
# List user's Supabase projects (user has to pipe this through their own
# shell to review; we don't rely on a stored PAT).
export SUPABASE_ACCESS_TOKEN="<collected from read_secret_to_env>"
projects=$(curl -s -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  https://api.supabase.com/v1/projects)
```

Parse the response, identify any project named starting with `gbrain` whose
`ref` doesn't match the user's active `~/.gbrain/config.json` pooler URL.
For each orphan, AskUserQuestion per project: "Delete orphan project
`<ref>` (`<name>`, created `<created_at>`)?" — NEVER batch; per-project
confirm is a one-way door.

On confirmed delete:
```bash
curl -s -X DELETE -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  https://api.supabase.com/v1/projects/$REF
```

Never delete the active brain without a second explicit confirmation.

At end: `unset SUPABASE_ACCESS_TOKEN`. Revocation reminder.

---
