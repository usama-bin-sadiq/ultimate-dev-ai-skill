<!-- Moved verbatim from health/SKILL.md, the
     'step-2-run-tools' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2: Run Tools

Run each detected tool. For each tool:

1. Record the start time
2. Run the command, capturing complete stdout and stderr in a private temporary log
3. Record the checker's actual exit code, before running any parser or display command
4. Record the end time
5. Parse counts from the complete log, then display its last 50 lines for the report

```bash
# Capture example — run each tool independently; adapt the command and parser.
(
  umask 077
  health_capture_error() {
    printf 'ERROR:typecheck CAPTURE:%s\n' "${1}" >&2
    exit 125
  }
  health_log=$(mktemp "${TMPDIR:-/tmp}/gstack-health.XXXXXX") || health_capture_error log_creation
  trap 'rm -f -- "$health_log"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  health_start=$(date +%s) || health_capture_error timing
  # Open separately so a redirection failure cannot masquerade as a checker result.
  if ! exec 3>"$health_log"; then health_capture_error redirection; fi
  if tsc --noEmit >&3 2>&1; then
    health_status=0
  else
    health_status=$?
  fi
  exec 3>&-
  health_end=$(date +%s) || health_capture_error timing
  # awk returns a successful zero count for no matches, including empty output.
  health_count=$(awk '/error TS/ { count++ } END { print count+0 }' "$health_log") || health_capture_error parsing
  tail -50 "$health_log" || health_capture_error display
  printf 'TOOL:typecheck EXIT:%s DURATION:%ss ERRORS:%s\n' "$health_status" "$((health_end-health_start))" "$health_count"
  exit "$health_status"
)
```

Run tools sequentially in independent invocations (some may share resources or lock
files). A failed checker must not prevent later tools from running. Remember each
reported exit code and full-log counts; never use the status of `tail` or a parser
as the checker result. Guard parsers whose no-match exit is expected.

Before running a tool, check availability using the project's configured command
and local tool installation. If availability detection establishes that it is
missing, record `SKIPPED` with the reason. An executed checker returning 127 is a
failure, not evidence that the category should be skipped.

Capture failures (log creation, redirection, parsing, or display) are `ERROR`, never
`CLEAN` or `SKIPPED`. Include the cause and do not invent a category score. Report
the composite as `N/A — capture failed` if any category cannot be scored for this
reason; do not redistribute that category's weight or persist a numeric history row.

---
