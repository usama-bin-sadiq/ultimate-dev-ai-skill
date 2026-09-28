<!-- Moved verbatim from qt-qml-profiler/SKILL.md, the
     'arguments' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Arguments

Arguments follow qmlprofiler conventions. `--` separates skill arguments from
the application executable and its arguments.

**Profiling mode (run then analyze):**
- `$ARGUMENTS` = `[--profile <mode>] -- <executable> [app-args...]`

**Analysis-only mode (existing trace):**
- `$ARGUMENTS` = `<path-to-trace.qtd>`

If `$ARGUMENTS` ends with `.qtd`, treat it as an existing trace file and skip
directly to the parse and analyze steps.
