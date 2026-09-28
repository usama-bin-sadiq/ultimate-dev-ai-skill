<!-- Moved verbatim from codex/SKILL.md, the
     'model-reasoning' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Model & Reasoning

**Model:** gstack defaults Codex invocations to the current frontier agentic coding
model via `-c "model=\"${GSTACK_CODEX_MODEL:-gpt-6-astra}\""` (currently `gpt-6-astra`). A user can override
the default for a shell with `GSTACK_CODEX_MODEL=<model>`, or for one request by naming a
model in the `/codex` prompt.
Native `codex review` also sets `review_model` to the selected model so a separate
review pin in the CLI config cannot override the request.

**Reasoning effort (per-mode defaults):**
- **Review (2A):** `high` — bounded diff input, needs thoroughness but not max tokens
- **Challenge (2B):** `high` — adversarial but bounded by diff size
- **Consult (2C):** `medium` — large context (plans, codebase), interactive, needs speed

`xhigh` uses ~23x more tokens than `high` and causes 50+ minute hangs on large context
tasks (OpenAI issues #8545, #8402, #6931). Users can override with `--xhigh` flag
(e.g., `/codex review --xhigh`) when they want maximum reasoning and are willing to wait.

**Web search:** All codex commands pass `-c 'web_search="cached"'` so `codex exec`
invocations can look up docs and APIs during review. This is OpenAI's cached index —
fast, no extra cost. Unlike the legacy `--enable`-based spelling (deprecated by
codex >=0.144), the `-c` form explicitly overrides any top-level
`web_search` setting in `~/.codex/config.toml`. Note: native `codex review` disables
web search regardless of configuration, so on the default Review path the flag is a
harmless no-op — only exec-based modes actually search.

If the user specifies a model (e.g., `/codex review -m gpt-5.6-sol` or
`/codex challenge --model gpt-daybreak-blue-latest`), translate it to the same config
form and replace the default model flag with `-c "model=\"<model>\""`. Native review
also requires `-c "review_model=\"<model>\""`; replace both model values together.
Review mode runs `codex review`, which REJECTS `-m` (`error: unexpected argument '-m' found`,
verified on 0.147.0), while `-c model=...` is accepted by both `codex review` and
`codex exec`.

---
