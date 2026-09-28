<!-- Moved verbatim from playwright-interactive/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Cleanup

Only run cleanup when the task is actually finished:

- This cleanup is manual. Exiting Codex, closing the terminal, or losing the `js_repl` session does not implicitly run `electronApp.close()`, `context.close()`, or `browser.close()`.
- For Electron specifically, assume the app may keep running if you leave the session without executing the cleanup cell first.

```javascript
if (electronApp) {
  await electronApp.close().catch(() => {});
}

if (mobileContext) {
  await mobileContext.close().catch(() => {});
}

if (context) {
  await context.close().catch(() => {});
}

if (browser) {
  await browser.close().catch(() => {});
}

browser = undefined;
context = undefined;
page = undefined;
mobileContext = undefined;
mobilePage = undefined;
electronApp = undefined;
appWindow = undefined;

console.log("Playwright session closed");
```

If you plan to exit Codex immediately after debugging, run the cleanup cell first and wait for the `"Playwright session closed"` log before quitting.
