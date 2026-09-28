<!-- Moved verbatim from pair-agent/SKILL.md, the
     'setup-run-this-check-before-any-browse-command' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## SETUP (run this check BEFORE any browse command)

```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
B=""
[ -n "$_ROOT" ] && [ -x "$_ROOT/<agent-config-dir>/gstack/browse/dist/browse" ] && B="$_ROOT/<agent-config-dir>/gstack/browse/dist/browse"
[ -z "$B" ] && B="$HOME/<agent-config-dir>/gstack/browse/dist/browse"
if [ -x "$B" ]; then
  echo "READY: $B"
else
  echo "NEEDS_SETUP"
fi
```

If `NEEDS_SETUP`:
1. Tell the user: "gstack browse needs a one-time build (~10 seconds). OK to proceed?" Then STOP and wait.
3. If `bun` is not installed:
   ```bash
   if ! command -v bun >/dev/null 2>&1; then
     BUN_VERSION="1.3.10"
     BUN_INSTALL_SHA="bab8acfb046aac8c72407bdcce903957665d655d7acaa3e11c7c4616beae68dd"
     tmpfile=$(mktemp)
     curl -fsSL "https://bun.sh/install" -o "$tmpfile"
     # shasum is macOS/perl; coreutils-only Linux ships sha256sum instead —
     # resolve whichever exists so the verify never fails on a missing tool.
     if command -v sha256sum >/dev/null 2>&1; then
       actual_sha=$(sha256sum < "$tmpfile" | awk '{print $(1)}')
     else
       actual_sha=$(shasum -a 256 < "$tmpfile" | awk '{print $(1)}')
     fi
     if [ "$actual_sha" != "$BUN_INSTALL_SHA" ]; then
       echo "ERROR: bun install script checksum mismatch" >&2
       echo "  expected: $BUN_INSTALL_SHA" >&2
       echo "  got:      $actual_sha" >&2
       rm "$tmpfile"; exit 1
     fi
     BUN_VERSION="$BUN_VERSION" bash "$tmpfile"
     rm "$tmpfile"
   fi
   ```
