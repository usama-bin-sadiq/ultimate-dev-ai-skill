<!-- Moved verbatim from qt-qml-profiler/SKILL.md, the 'Arguments' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Arguments

Arguments follow qmlprofiler conventions. `--` separates skill arguments from
the application executable and its arguments.

**Profiling mode (run then analyze):**
- `$ARGUMENTS` = `[--profile <mode>] -- <executable> [app-args...]`

**Analysis-only mode (existing trace):**
- `$ARGUMENTS` = `<path-to-trace.qtd>`

If `$ARGUMENTS` ends with `.qtd`, treat it as an existing trace file and skip
directly to the parse and analyze steps.
