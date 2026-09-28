<!-- Moved verbatim from playwright-interactive/SKILL.md, the
     'common-failure-modes' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Common Failure Modes

- `Cannot find module 'playwright'`: run the one-time setup in the current workspace and verify the import before using `js_repl`.
- Playwright package is installed but the browser executable is missing: run `npx playwright install chromium`.
- `page.goto: net::ERR_CONNECTION_REFUSED`: make sure the dev server is still running in a persistent TTY session, recheck the port, and prefer `http://127.0.0.1:<port>`.
- `electron.launch` hangs, times out, or exits immediately: verify the local `electron` dependency, confirm the `args` target, and make sure any renderer dev server is already running before launch.
- `Identifier has already been declared`: reuse the existing top-level bindings, choose a new name, or wrap the code in `{ ... }`. Use `js_repl_reset` only when the kernel is genuinely stuck.
- `browserContext.newPage: Protocol error (Target.createTarget): Not supported` while working with Electron: do not use `appWindow.context().newPage()` or `electronApp.context().newPage()` as a scratch page; use the Electron-specific screenshot normalization flow in the model-bound screenshots section.
- `js_repl` timed out or reset: rerun the bootstrap cell and recreate the session with shorter, more focused cells.
- Browser launch or network operations fail immediately: confirm the session was started with `--sandbox danger-full-access` and restart that way if needed.

Each file below is loaded on demand, not at triage. 13 file(s):

- `references/bootstrap-run-once.md` — Bootstrap (Run Once). <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/choose-session-mode.md` — Choose Session Mode. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/cleanup.md` — Cleanup. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/common-failure-modes.md` — Common Failure Modes. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/core-workflow.md` — Core Workflow. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/dev-server.md` — Dev Server. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/one-time-setup.md` — One-time setup. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/preconditions.md` — Preconditions. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/reuse-sessions-during-iteration.md` — Reuse Sessions During Iteration. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/screenshot-examples.md` — Screenshot Examples. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/start-or-reuse-electron-session.md` — Start or Reuse Electron Session. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/start-or-reuse-web-session.md` — Start or Reuse Web Session. <!-- Moved verbatim from playwright-interactive/SKILL.md, the
- `references/viewport-fit-checks-required.md` — Viewport Fit Checks (Required). <!-- Moved verbatim from playwright-interactive/SKILL.md, the
