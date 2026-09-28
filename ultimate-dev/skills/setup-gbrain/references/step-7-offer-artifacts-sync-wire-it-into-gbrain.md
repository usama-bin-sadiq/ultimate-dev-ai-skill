<!-- Moved verbatim from setup-gbrain/SKILL.md, the 'Step 7: Offer artifacts sync + wire it into gbrain' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 7: Offer artifacts sync + wire it into gbrain

Renamed from "session memory sync" in v1.27.0.0 — the on-disk concept is
artifacts (CEO plans, designs, /investigate reports, retros) rather than
"session memory," which was a confusing name for what was always a
human-readable artifact bucket. Behavioral transcript ingest is its own
step (7.5) with its own option set.

Separate AskUserQuestion: "Also sync your gstack artifacts (CEO plans,
designs, reports, retros) to a private git repo that gbrain can index
across machines?"

Options:
- Yes, full sync (everything allowlisted)
- Yes, artifacts-only (plans, designs, retros — skip behavioral data)
- No thanks

If yes, run the artifacts-init helper. It asks the user to pick a git host
(GitHub via `gh`, GitLab via `glab`, or paste a URL manually), creates
`gstack-artifacts-$USER` (private), and writes the canonical HTTPS URL to
`~/.gstack-artifacts-remote.txt`. Pass `--url-form-supported` from Step 4c's
verify output (Path 4) or `false` (Paths 1/2/3 — local mode doesn't probe):

```bash
URL_FORM=${URL_FORM_SUPPORTED:-false}
~/.claude/skills/gstack/bin/gstack-artifacts-init --url-form-supported "$URL_FORM"
~/.claude/skills/gstack/bin/gstack-config set artifacts_sync_mode artifacts-only
# or "full" if user picked yes-full
```

`gstack-artifacts-init` always prints a "Send this to your brain admin" block
at the end with the exact `gbrain sources add` command. Per codex Finding #3:
the skill never auto-executes server-side gbrain commands; even if the user
IS the brain admin, copy-pasting the printed command is the consistent UX.

### Path 4 (Remote MCP) — done after artifacts-init

In remote mode, the local `gstack-gbrain-source-wireup` helper does NOT run
(it shells out to a local `gbrain` CLI which Path 4 doesn't install). The
brain admin runs the printed command on the brain host instead. Skip to Step 7.5.

### Paths 1, 2a, 2b, 3 (Local stdio) — wire up the federated source

Then wire the artifacts repo into gbrain so its content is searchable from
any gbrain client. The helper creates a `git worktree` of `~/.gstack/`,
registers it as a federated source via `gbrain sources add --path
--federated`, and runs an initial `gbrain sync`. Local-Mac only.

Capture the database URL out of `~/.gbrain/config.json` first and pass it
explicitly so the wireup is robust against any other process rewriting
`~/.gbrain/config.json` mid-sync (e.g., concurrent `gbrain init` runs
elsewhere on the machine):

```bash
GBRAIN_URL=$(python3 -c "
import json, os, sys
try:
    c = json.load(open(os.path.expanduser('~/.gbrain/config.json')))
    print(c.get('database_url', ''))
except Exception:
    pass
")
~/.claude/skills/gstack/bin/gstack-gbrain-source-wireup --strict \
  ${GBRAIN_URL:+--database-url "$GBRAIN_URL"}
```

`--strict` exits non-zero on missing prereqs (gbrain not installed, < 0.18.0,
or no `~/.gstack/.git` yet) so the user sees the failure rather than silently
ending up with an unwired brain. On non-zero exit, surface the helper's
output and STOP per skill rules — search-across-machines won't work until
the prereq is fixed.

---
