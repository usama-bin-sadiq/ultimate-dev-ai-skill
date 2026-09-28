<!-- Moved verbatim from design-consultation/SKILL.md, the
     'design-setup-run-this-check-before-any-design-mockup-command' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## DESIGN SETUP (run this check BEFORE any design mockup command)

```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
D=""
[ -n "$_ROOT" ] && [ -x "$_ROOT/<agent-config-dir>/gstack/design/dist/design" ] && D="$_ROOT/<agent-config-dir>/gstack/design/dist/design"
[ -z "$D" ] && D="$HOME/<agent-config-dir>/gstack/design/dist/design"
if [ -x "$D" ]; then
  echo "DESIGN_READY: $D"
else
  echo "DESIGN_NOT_AVAILABLE"
fi
```

If `DESIGN_NOT_AVAILABLE`: use Phase 5 Path B (HTML preview). Mockups are optional.

For interactive feedback, use `compare --serve` and its printed HTTP URL; opening board HTML directly is only a static preview.

If `DESIGN_READY`: the design binary is available for visual mockup generation.
Commands:
- `$D generate --brief "..." --output /path.png` — generate a single mockup
- `$D variants --brief "..." --count 3 --output-dir /path/` — generate N style variants
- `$D compare --images "a.png,b.png,c.png" --output /path/board.html --serve` — comparison board + HTTP server
- `$D serve --html /path/board.html` — serve comparison board and collect feedback via HTTP
- `$D check --image /path.png --brief "..."` — vision quality gate
- `$D iterate --session /path/session.json --feedback "..." --output /path.png` — iterate
- `$D extract --image /absolute/path.png` — print tokens and automatically update DESIGN.md in the current Git repository; no read-only flag

`generate` returns `sessionFile`; `iterate` requires that existing session. `variants` returns `paths` but creates no session: regenerate with an updated brief instead.

**CRITICAL PATH RULE:** Design artifacts belong in `$GSTACK_STATE_ROOT/projects/$SLUG/designs/`.
Use `bin/gstack-paths`: GSTACK_HOME → plugin storage → ~/.gstack. Keep it even if temporary; never substitute
.context/, docs/designs/ or another directory.
These are user files, not application source.

Phase 5: `DESIGN_READY` uses AI mockups on realistic product screens; `DESIGN_NOT_AVAILABLE` uses an HTML preview.

---
