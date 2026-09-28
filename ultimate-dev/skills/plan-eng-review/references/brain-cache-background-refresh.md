<!-- Moved verbatim from plan-eng-review/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Brain Cache Background Refresh

After the skill's work completes (and telemetry has logged), kick a
background refresh of any cache digest that's getting close to its TTL.
This is non-blocking — the user doesn't wait. Next invocation benefits
from the warm cache.

```bash
eval "$(~/<agent-config-dir>/gstack/bin/gstack-slug 2>/dev/null)" 2>/dev/null || true
(~/<agent-config-dir>/gstack/bin/gstack-brain-cache refresh --project "$SLUG" 2>/dev/null &) || true
```


After success telemetry and cache dispatch, call ExitPlanMode for the selected next step only when the host is in plan mode. Outside plan mode, finish the review in the current conversation; do not call ExitPlanMode.
