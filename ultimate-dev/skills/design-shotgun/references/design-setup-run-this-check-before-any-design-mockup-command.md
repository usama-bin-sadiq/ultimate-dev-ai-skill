<!-- Moved verbatim from design-shotgun/SKILL.md, the 'DESIGN SETUP (run this check BEFORE any design mockup command)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# DESIGN SETUP (run this check BEFORE any design mockup command)

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

If `DESIGN_NOT_AVAILABLE`: skip visual mockup generation and fall back to the
existing HTML wireframe approach (`DESIGN_SKETCH`). Design mockups are a
progressive enhancement, not a hard requirement.

Comparison boards are local HTML files: open them with `open file://...` on macOS
(`xdg-open` elsewhere). The user just needs to see the file in their default browser.

If `DESIGN_READY`: the design binary is available for visual mockup generation.
Commands:
- `$D generate --brief "..." --output /path.png` — generate a single mockup
- `$D variants --brief "..." --count 3 --output-dir /path/` — generate N style variants
- `$D compare --images "a.png,b.png,c.png" --output /path/board.html --serve` — comparison board + HTTP server
- `$D serve --html /path/board.html` — serve comparison board and collect feedback via HTTP
- `$D check --image /path.png --brief "..."` — vision quality gate
- `$D iterate --session /path/session.json --feedback "..." --output /path.png` — iterate

**CRITICAL PATH RULE:** Design artifacts belong in `$GSTACK_STATE_ROOT/projects/$SLUG/designs/`.
Use `bin/gstack-paths`: GSTACK_HOME → plugin storage → ~/.gstack. Keep it even if temporary; never substitute
.context/ or another directory.
These are user files, not application source.

> **STOP.** Before writing variant concepts or design briefs (Step 3 onward) — the UX-principles doctrine governs every design direction, Read `~/<agent-config-dir>/gstack/design-shotgun/sections/doctrine.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.
