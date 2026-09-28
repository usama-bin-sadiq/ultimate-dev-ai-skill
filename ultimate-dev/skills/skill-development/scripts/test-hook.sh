#!/usr/bin/env bash
# test-hook.sh — run one hook command with a real payload and see what it does.
#
# WHAT THIS IS
#   A harness for developing a hook without editing a hooks.json and restarting a
#   session every time. It builds the JSON a hook actually receives, hands it to
#   the command on stdin, and reports stdout, stderr, the exit code, and how long
#   it took.
#
# WHAT IT EXPECTS
#   Usage:
#     ./test-hook.sh <path-to-hook-script> [event] [tool-name]
#     ./test-hook.sh scripts/hooks/guard.sh PreToolUse Bash
#     ./test-hook.sh scripts/hooks/guard.sh PreToolUse Bash --payload payload.json
#     ./test-hook.sh scripts/hooks/guard.sh --list-events
#
#   Optional flags:
#     --payload <file>   use this JSON as the hook input instead of a generated one
#     --timeout <secs>   kill the hook after this long (default 10)
#     --deny             also show what a deny decision looks like on stdout
#     --json             emit a machine-readable result
#     --list-events      list the event names and exit
#
#   Exit codes:
#     0    the hook ran and exited 0
#     1    the hook ran and exited non-zero
#     2    bad input, or the hook file is missing
#     124  the hook timed out
#
# WHAT THIS DOES NOT DO
#   It does not install the hook, does not run it inside a real session, and does
#   not prove the matcher fires. It proves the command does the right thing with
#   the right input, which is the half that is hard to eyeball.
#
# PROVENANCE
#   Reconstructed to serve the `scripts/test-hook.sh` example in this skill's
#   SKILL.md (Step 2: developers repeatedly need to test hook scripts). The
#   payload shapes, the reporting, and every message are this file's own.

set -euo pipefail

HOOK=""
EVENT="PreToolUse"
TOOL="Bash"
PAYLOAD=""
TIMEOUT=10
WANT_JSON=0
WANT_DENY=0
LIST_EVENTS=0
POSITIONAL=0

EVENTS="PreToolUse PostToolUse UserPromptSubmit Notification Stop SubagentStop
       PreCompact SessionStart SessionEnd"

die() { printf 'error: %s\n' "$1" >&2; exit 2; }

usage() {
  sed -n '2,26p' "$0" | sed 's/^#\{1,\} \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --list-events) LIST_EVENTS=1; shift ;;
    --json)        WANT_JSON=1; shift ;;
    --deny)        WANT_DENY=1; shift ;;
    --payload)     [ "$#" -ge 2 ] || die "--payload needs a file"; PAYLOAD="$2"; shift 2 ;;
    --payload=*)   PAYLOAD="${1#--payload=}"; shift ;;
    --timeout)     [ "$#" -ge 2 ] || die "--timeout needs a number"; TIMEOUT="$2"; shift 2 ;;
    --timeout=*)   TIMEOUT="${1#--timeout=}"; shift ;;
    -h|--help)     usage; exit 0 ;;
    -*)            die "unknown option: $1" ;;
    *)
      POSITIONAL=$((POSITIONAL + 1))
      case "$POSITIONAL" in
        1) HOOK="$1" ;;
        2) EVENT="$1" ;;
        3) TOOL="$1" ;;
        *) die "too many positional arguments; the fourth was: $1" ;;
      esac
      shift
      ;;
  esac
done

if [ "$LIST_EVENTS" -eq 1 ]; then
  printf 'hook events:\n'
  for name in $EVENTS; do printf '  %s\n' "$name"; done
  exit 0
fi

[ -n "$HOOK" ] || { usage >&2; exit 2; }
[ -e "$HOOK" ] || die "not found: $HOOK"
[ -f "$HOOK" ] || die "not a regular file: $HOOK"

case "$EVENT" in
  PreToolUse|PostToolUse|UserPromptSubmit|Notification|Stop|SubagentStop|PreCompact|SessionStart|SessionEnd)
    ;;
  *) die "unknown event: $EVENT. Run with --list-events." ;;
esac

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  die "python3 not found. This script needs Python 3 to build the payload; install it and re-run."
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
STDERR_FILE="$WORKDIR/stderr"
STDOUT_FILE="$WORKDIR/stdout"
PAYLOAD_FILE="$WORKDIR/payload.json"

if [ -n "$PAYLOAD" ]; then
  [ -f "$PAYLOAD" ] || die "payload file not found: $PAYLOAD"
  cp "$PAYLOAD" "$PAYLOAD_FILE"
else
  # The payload a hook actually receives, shaped for the chosen event. Generated
  # rather than hand-written so the shape is right by construction.
  "$PY" - "$EVENT" "$TOOL" "$PAYLOAD_FILE" <<'PYTHON'
import json
import sys

event, tool, out = sys.argv[1], sys.argv[2], sys.argv[3]

base = {
    "session_id": "test-session",
    "transcript_path": "/tmp/transcript.jsonl",
    "cwd": "/tmp/project",
    "hook_event_name": event,
    "permission_mode": "default",
}

if event in ("PreToolUse", "PostToolUse"):
    base["tool_name"] = tool
    if tool == "Bash":
        base["tool_input"] = {"command": "ls -la", "description": "list files"}
    elif tool in ("Edit", "Write"):
        base["tool_input"] = {
            "file_path": "/tmp/project/src/app.py",
            "old_string": "",
            "new_string": "print('hello')\n",
        }
    elif tool == "Read":
        base["tool_input"] = {"file_path": "/tmp/project/README.md"}
    else:
        base["tool_input"] = {"note": "generic input; edit this file to match your hook"}
    if event == "PostToolUse":
        base["tool_response"] = {"stdout": "", "stderr": "", "interrupted": False}

if event == "UserPromptSubmit":
    base["prompt"] = "build me a todo app"

if event == "Notification":
    base["message"] = "A tool is waiting for your input"

if event in ("Stop", "SubagentStop"):
    base["stop_hook_active"] = False

with open(out, "w", encoding="utf-8") as handle:
    json.dump(base, handle, indent=2)
    handle.write("\n")
PYTHON
fi

if [ "$WANT_JSON" -eq 0 ]; then
  printf 'hook:   %s\n' "$HOOK"
  printf 'event:  %s\n' "$EVENT"
  printf 'tool:   %s\n' "$TOOL"
  printf 'payload: %s\n' "$PAYLOAD_FILE"
  printf '\n'
  printf -- '--- payload ---\n'
  cat "$PAYLOAD_FILE"
  printf -- '--- hook output ---\n'
fi

START="$(date +%s)"
set +e
if command -v timeout >/dev/null 2>&1; then
  timeout "$TIMEOUT" "$HOOK" <"$PAYLOAD_FILE" >"$STDOUT_FILE" 2>"$STDERR_FILE"
  STATUS=$?
else
  # No coreutils timeout: run it in the background and poll. Slower, and it is
  # the only option on a machine without it.
  "$HOOK" <"$PAYLOAD_FILE" >"$STDOUT_FILE" 2>"$STDERR_FILE" &
  HOOK_PID=$!
  ( sleep "$TIMEOUT"; kill -9 "$HOOK_PID" 2>/dev/null ) &
  WATCHDOG=$!
  wait "$HOOK_PID"; STATUS=$?
  kill "$WATCHDOG" 2>/dev/null || true
fi
set -e
ELAPSED=$(( $(date +%s) - START ))

STDOUT_TEXT="$(cat "$STDOUT_FILE")"
STDERR_TEXT="$(cat "$STDERR_FILE")"

if [ "$WANT_JSON" -eq 0 ]; then
  if [ -n "$STDOUT_TEXT" ]; then
    printf '%s\n' "$STDOUT_TEXT"
  else
    printf '(no stdout)\n'
  fi
  if [ -n "$STDERR_TEXT" ]; then
    printf -- '--- stderr ---\n%s\n' "$STDERR_TEXT"
  fi
  printf -- '--- exit: %d in %ds ---\n' "$STATUS" "$ELAPSED"
  printf '\n'
  case "$STATUS" in
    0)   printf 'pass: the hook exited 0 and its output was captured above.\n' ;;
    124) printf 'TIMEOUT: the hook ran for more than %ss. A hook that hangs blocks the\n' "$TIMEOUT"
         printf 'session, so a timeout here is a real defect, not a slow machine.\n' ;;
    *)   printf 'non-zero exit: for PreToolUse, exit 2 is the conventional deny signal;\n'
         printf 'any other non-zero code is reported as an error and the tool proceeds.\n' ;;
  esac
  if [ -z "$STDOUT_TEXT" ] && [ "$STATUS" -eq 0 ]; then
    printf '\nnote: a PreToolUse hook that prints nothing and exits 0 allows the tool\n'
    printf 'through. If the intent was to block, exit 2 and print the reason.\n'
  fi
  if [ "$WANT_DENY" -eq 1 ]; then
    printf '\n--- what a deny decision looks like on stdout ---\n'
    printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "%s",\n' "$EVENT"
    printf '    "permissionDecision": "deny",\n'
    printf '    "permissionDecisionReason": "Blocked because: <the actual reason>"\n  }\n}\n'
  fi
else
  "$PY" - "$HOOK" "$EVENT" "$TOOL" "$STATUS" "$ELAPSED" \
        "$STDOUT_FILE" "$STDERR_FILE" <<'PYTHON'
import json
import sys

hook, event, tool, status, elapsed = sys.argv[1:6]
with open(sys.argv[6], encoding="utf-8") as handle:
    stdout = handle.read()
with open(sys.argv[7], encoding="utf-8") as handle:
    stderr = handle.read()

print(json.dumps({
    "hook": hook,
    "event": event,
    "tool": tool,
    "exit_code": int(status),
    "elapsed_seconds": int(elapsed),
    "timed_out": int(status) == 124,
    "stdout": stdout,
    "stderr": stderr,
}, indent=2))
PYTHON
fi

exit "$STATUS"
