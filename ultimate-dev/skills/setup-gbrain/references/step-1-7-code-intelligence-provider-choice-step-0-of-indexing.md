<!-- Moved verbatim from setup-gbrain/SKILL.md, the
     'step-1-7-code-intelligence-provider-choice-step-0-of-indexing' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 1.7: Code-intelligence provider choice (Step 0 of indexing)

You are INSIDE /setup-gbrain: the user asked for gbrain by name, so the
provider question is already answered. NEVER ask it here, and never let this
step delay or derail the actual setup. Record the choice best-effort, then
continue immediately with Step 2:

```bash
[ -f ~/.claude/skills/gstack/bin/gstack-code-intelligence ] \
  && bun ~/.claude/skills/gstack/bin/gstack-code-intelligence select gbrain 2>/dev/null \
  || true
```

The offer ceremony below applies ONLY when this skill is reached from another
entry point where no provider was named (a routing skill exploring indexing
options). Even then:

- `"offer": false` with reason `bin-absent` → the installed gstack predates
  the code-intelligence CLI. Skip this step entirely and continue with the
  skill — the user asked for gbrain, so set up gbrain. Never block setup on
  a missing optional gate.

- `"offer": false` with reason `small-repo` → grep is already fast here; say
  so in one line and continue with this skill only if the user asked for
  gbrain by name.
- `"offer": false` with reason `provider-selected` or `declined` → the
  machine-wide question was already answered; apply it silently and continue.
- `"offer": true` → present the returned options ONCE via AskUserQuestion:
  **GBrain** (recommended — semantic memory + code, sends repo content to
  YOUR gbrain DB, per-repo consent), **Sourcebot** (self-hosted whole-repo
  search, local when on localhost), **Graphify** (local tree-sitter graph,
  nothing leaves the machine, user installs it), or **No indexing**. Record
  the choice: `gstack-code-intelligence select <provider|none>` — `none`
  persists the decline so NO skill ever asks again, on any repo
  (re-enable: `gstack-code-intelligence select <provider>`). Local-compute
  and remote-send providers are separate consents — never bundle them.
- Per-repo send consent (GBrain/Sourcebot) is recorded with
  `gstack-code-intelligence consent <repo> yes|no` and is ALWAYS vetoed by a
  `deny` tier in gstack-gbrain-repo-policy — the trust store is the single
  authority for whether code leaves a repo.

If the user picked GBrain (or asked for this skill directly), continue below.
If they picked Sourcebot/Graphify, run `gstack-code-intelligence index <repo>`
and stop — the rest of this skill is gbrain-specific.
