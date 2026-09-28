<!-- Moved verbatim from codex/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Error Handling

- **Binary not found:** Detected in Step 0. Stop with install instructions.
- **Auth error:** Codex prints an auth error to stderr. Surface the error:
  "Codex authentication failed. Run `codex login` in your terminal to authenticate via ChatGPT."
- **Timeout (Bash outer gate):** Every Bash gate sits ABOVE its inner wrapper (360s gate
  over the 330s review wrapper; 660s gate over the 600s challenge/consult wrappers), so
  the wrapper's exit-124 path normally fires first with its explicit message. If the Bash
  call itself times out anyway (wrapper unavailable AND codex hung), tell the user:
  "Codex timed out. The prompt may be too large or the API may be slow. Try again or use a smaller scope."
- **Timeout (inner `timeout` wrapper, exit 124):** If the shell `timeout 600` wrapper fires first, the skill's hang-detection block auto-logs a telemetry event + operational learning and prints: "Codex stalled past 10 minutes. Common causes: model API stall, long prompt, network issue. Try re-running. If persistent, split the prompt or check `~/.codex/logs/`." No extra action needed.
- **`the argument '[PROMPT]' cannot be used with '--base <BRANCH>'`:** a prompt argument
  leaked into a scoped `codex review`. This fails instantly, before any API call, so it
  looks like a hang-free "no output" — do not misread it as a model stall. Drop the
  prompt: the scope flags (`--base`, `--commit`, `--uncommitted`) carry the scope on
  their own. If the prompt was custom review instructions, run them through `codex exec`
  instead (Step 2A, custom-instructions path). Do **not** fix it by removing `--base` and
  keeping the prompt — that parses, but silently reviews the uncommitted working tree
  instead of the branch diff.
- **Review says "no changes" on a branch that clearly has changes:** the scope flag is
  missing or wrong. A prompt-only `codex review` defaults to uncommitted changes, so a
  clean working tree reads as an empty review even when `<base>...HEAD` is large. Confirm
  `--base <base>` is actually on the command line.
- **Model not supported (HTTP 400):** stderr shows
  `The '<model>' model is not supported when using Codex with a ChatGPT account`
  (a `status: 400` / `invalid_request_error` naming a model). This is a
  model-entitlement problem, not an auth or network failure, and the auth probe
  cannot catch it. Recovery, in order:
  1. Check whether `GSTACK_CODEX_MODEL` is set. If so, update it to a model the
     account can use.
  2. If no override is set, gstack defaults to `gpt-6-astra`. If the account cannot
     use it yet, set `GSTACK_CODEX_MODEL=<supported-model>` or replace the default
     flag with `-c "model=\"<supported-model>\""`.
  3. If Codex printed `[notice.model_migrations]`, use that replacement model.
  Never present this as a model stall or a PASS — it is a fail-closed gate result.
- **Empty response:** If `$TMPRESP` is empty or doesn't exist, tell the user:
  "Codex returned no response. Check stderr for errors."
- **Session resume failure:** If resume fails, delete the session file and start fresh.

---
