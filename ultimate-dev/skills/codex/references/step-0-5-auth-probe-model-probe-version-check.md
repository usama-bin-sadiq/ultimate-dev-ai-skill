<!-- Moved verbatim from codex/SKILL.md, the
     'step-0-5-auth-probe-model-probe-version-check' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0.5: Auth probe + model probe + version check

Before building expensive prompts, verify Codex has valid auth, that the account
can actually USE gstack's selected model, AND the installed CLI version isn't in the
known-bad list. Sourcing `gstack-codex-probe` loads the shared helpers that both
`/codex` and `/autoplan` use.

If the user names a model for this request, set `GSTACK_CODEX_MODEL` to that model
before this probe and use it for every invocation in the request. The probe must
check the requested model, including when the frontier default is unavailable.

```bash
_TEL=$(~/.claude/skills/gstack/bin/gstack-config get telemetry 2>/dev/null || echo off)
source ~/.claude/skills/gstack/bin/gstack-codex-probe

# GSTACK_ACTIVE_HOST names the harness, never the model.
if { [ -n "${CODEX_THREAD_ID:-}" ] || [ -n "${CODEX_SANDBOX:-}" ] || [ "${GSTACK_ACTIVE_HOST:-}" = codex ]; }; then
  echo 'Codex outside review unavailable: harness mismatch; no outside process started. Missing coverage.' >&2
  if { [ -n "${CLAUDECODE:-}" ] || [ "${GSTACK_ACTIVE_HOST:-}" = claude ]; } && { [ -n "${CODEX_THREAD_ID:-}" ] || [ -n "${CODEX_SANDBOX:-}" ] || [ "${GSTACK_ACTIVE_HOST:-}" = codex ]; }; then
    echo 'Inherited harness markers conflict. Run setup --host <actual-harness> (claude or codex); do not guess a replacement provider.' >&2
  else
    echo 'Repair installed skills: run setup --host codex from your gstack checkout.' >&2
  fi
  exit 78
fi
if ! _gstack_codex_auth_probe >/dev/null; then
  _gstack_codex_log_event "codex_auth_failed"
  echo "AUTH_FAILED"
else
  _gstack_codex_model_probe   # ~10s round trip on first run, cached 1h (#2477)
fi
_gstack_codex_version_check   # warns if known-bad, non-blocking
```

If the runtime guard reports a harness mismatch, stop. Outside coverage is unavailable. Do not silently substitute another provider or force a same-harness invocation.

If the output contains `AUTH_FAILED`, stop and tell the user:
"No Codex authentication found. Run `codex login` or set `$CODEX_API_KEY` / `$OPENAI_API_KEY`, then re-run this skill."

If the output contains `MODEL_UNUSABLE`, stop — auth exists but the account
cannot use gstack's selected model (`GSTACK_CODEX_MODEL` or the `gpt-6-astra`
default). Relay the probe's HINT lines and
follow the "Model not supported (HTTP 400)" recovery steps in
`## Error Handling` below. Running the modes anyway just burns four
invocations on the same 400 (#2477).

`MODEL_PROBE_INCONCLUSIVE` is non-blocking (timeout/transient network): pass
the warning through and continue.

If the version check printed a `WARN:` line, pass it through to the user verbatim
(non-blocking — Codex may still work, but the user should upgrade).

The probe multi-signal auth logic accepts: `$CODEX_API_KEY` set, `$OPENAI_API_KEY`
set, or `${CODEX_HOME:-~/.codex}/auth.json` exists. Avoids false-negatives for
env-auth users (CI, platform engineers) that file-only checks would reject.

**Update the known-bad list** in `bin/gstack-codex-probe` when a new Codex CLI version
regresses. Current entries (`0.120.0`, `0.120.1`, `0.120.2`) trace to the stdin
deadlock fixed in #972.

---
