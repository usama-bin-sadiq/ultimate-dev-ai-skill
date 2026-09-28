#!/usr/bin/env bash
# validate-hook-schema.sh — check a hooks.json against the plugin hook schema.
#
# WHAT THIS IS
#   A dependency-free validator for the hooks.json a Claude Code plugin ships.
#   It checks the shape, the event names, the matcher shapes, and the command
#   strings — and, the part that actually catches mistakes, that every hook
#   command names a real, readable, executable file rather than a string that
#   merely looks right.
#
# WHAT IT EXPECTS
#   Usage:
#     ./validate-hook-schema.sh <path-to-hooks.json>
#     ./validate-hook-schema.sh hooks.json --strict
#     ./validate-hook-schema.sh hooks.json --quiet
#
#   Exit codes:
#     0  valid (warnings allowed unless --strict)
#     1  validation errors, or warnings under --strict
#     2  bad input, unreadable file, or no Python on the machine
#
# WHY A SCRIPT INSTEAD OF DOCUMENTING THE RULES
#   Because the rule that fires in practice is "the command file does not exist".
#   A schema document cannot check that; this can, and that is the whole value
#   here over re-reading the plugin documentation.
#
# WHY PYTHON INSIDE A SHELL SCRIPT
#   JSON cannot be parsed correctly in bash, and jq is not installed everywhere
#   this needs to run. The shell does argument handling and the Python3 one does
#   the validation, so the wrapper stays portable and the rules stay readable.
#
# PROVENANCE
#   Reconstructed to serve the `scripts/validate-hook-schema.sh` example in this
#   skill's SKILL.md (Step 2: developers repeatedly need to validate hooks.json).
#   The event list, the rules, and every message are this file's own.

set -euo pipefail

STRICT=0
QUIET=0
FILE=""

die() { printf 'error: %s\n' "$1" >&2; exit 2; }

for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --quiet)  QUIET=1 ;;
    -h|--help)
      sed -n '2,25p' "$0" | sed 's/^#\{1,\} \{0,1\}//'
      exit 0
      ;;
    -*) die "unknown option: $arg" ;;
    *)  [ -z "$FILE" ] || die "more than one file given: $FILE and $arg"; FILE="$arg" ;;
  esac
done

[ -n "$FILE" ] || die "usage: validate-hook-schema.sh <hooks.json> [--strict] [--quiet]"
[ -e "$FILE" ] || die "not found: $FILE"
[ -f "$FILE" ] || die "not a regular file: $FILE"
[ -r "$FILE" ] || die "not readable: $FILE"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  die "python3 not found. Install Python 3 and re-run; this script has no other dependency."
fi

[ "$QUIET" -eq 1 ] && printf 'validating %s\n' "$FILE"

"$PY" - "$FILE" "$STRICT" <<'PYTHON'
import json
import os
import re
import sys

path = sys.argv[1]
strict = sys.argv[2] == "1"

EVENTS = {
    "PreToolUse", "PostToolUse", "UserPromptSubmit", "Notification",
    "Stop", "SubagentStop", "PreCompact", "SessionStart", "SessionEnd",
}
KNOWN_KEYS = {"command", "type", "timeout", "name", "description"}
# Tool names a matcher may name exactly. A PreToolUse/PostToolUse matcher is a
# tool name, not a pattern, so "Bash" is correct and must not be flagged; the
# matcher check below only objects to a string that names nothing recognisable.
KNOWN_TOOLS = {
    "Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "LS",
    "WebFetch", "WebSearch", "Task", "TodoWrite", "NotebookEdit",
    "NotebookRead", "BashOutput", "KillShell", "SlashCommand",
}
# A token that starts like a path. Anything with a shell metacharacter in front
# of it is a pipeline or a variable, and is left alone.
PATH_LIKE = re.compile(r"^[\w./~$-]+")

errors = []
warnings = []


try:
    with open(path, encoding="utf-8") as handle:
        raw = handle.read()
except OSError as exc:
    print(f"error: could not read {path}: {exc}", file=sys.stderr)
    sys.exit(2)

if not raw.strip():
    print("error: the file is empty", file=sys.stderr)
    sys.exit(1)

try:
    document = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"error: not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(document, dict):
    print(f"error: the top level must be an object, got {type(document).__name__}",
          file=sys.stderr)
    sys.exit(1)

unknown_top = set(document) - {"hooks", "description", "$schema", "version"}
if unknown_top:
    warnings.append(
        f"unrecognised top-level key(s): {', '.join(sorted(unknown_top))}. A renderer may "
        "ignore them; a human reader will not."
    )

hooks = document.get("hooks")
if not isinstance(hooks, dict):
    errors.append(
        "no 'hooks' object at the top level. The file needs {\"hooks\": {\"PreToolUse\": [...]}}."
    )
    hooks = {}

total = 0

for event, groups in sorted(hooks.items()):
    if event not in EVENTS:
        errors.append(
            f"unknown event {event!r}. Known events: {', '.join(sorted(EVENTS))}"
        )
        continue
    if not isinstance(groups, list):
        errors.append(
            f"hooks.{event} must be a list of matcher groups, got {type(groups).__name__}"
        )
        continue
    if not groups:
        warnings.append(f"hooks.{event} is an empty list; the entry does nothing")

    for group_index, group in enumerate(groups):
        where = f"hooks.{event}[{group_index}]"
        if not isinstance(group, dict):
            errors.append(f"{where} must be an object with 'matcher' and 'hooks'")
            continue

        matcher = group.get("matcher", "*")
        if not isinstance(matcher, str):
            errors.append(
                f"{where}.matcher must be a string, got {type(matcher).__name__}"
            )
        elif event in ("PreToolUse", "PostToolUse"):
            # Tool matchers are exact names. "*" and a glob are both fine; a
            # string that is neither a known tool nor a glob matches nothing, and
            # a hook that matches nothing never fires and never says so.
            if (
                matcher not in ("*", "")
                and matcher not in KNOWN_TOOLS
                and not any(ch in matcher for ch in "*?")
            ):
                warnings.append(
                    f"{where}.matcher is {matcher!r}, which is not a known tool name and "
                    "holds no glob. Known tools: "
                    + ", ".join(sorted(KNOWN_TOOLS)[:8])
                    + ".... Use '*' for all tools, or a real tool name."
                )
        elif matcher not in ("*", "") and not any(ch in matcher for ch in "*?"):
            warnings.append(
                f"{where}.matcher is {matcher!r}. For {event} the matcher usually does not "
                "filter anything; '*' is clearer than a string that looks selective."
            )

        entries = group.get("hooks")
        if not isinstance(entries, list) or not entries:
            errors.append(f"{where}.hooks must be a non-empty list")
            continue

        for entry_index, entry in enumerate(entries):
            entry_where = f"{where}.hooks[{entry_index}]"
            total += 1
            if not isinstance(entry, dict):
                errors.append(f"{entry_where} must be an object")
                continue

            extra = set(entry) - KNOWN_KEYS
            if extra:
                warnings.append(
                    f"{entry_where}: unrecognised key(s): {', '.join(sorted(extra))}"
                )

            kind = entry.get("type")
            if kind is not None and kind != "command":
                errors.append(
                    f"{entry_where}.type is {kind!r}; only 'command' hooks exist"
                )

            timeout = entry.get("timeout")
            if timeout is not None and (not isinstance(timeout, int) or timeout < 0):
                errors.append(f"{entry_where}.timeout must be a non-negative integer")

            command = entry.get("command")
            if command is None:
                errors.append(f"{entry_where} has no 'command'")
                continue
            if not isinstance(command, str) or not command.strip():
                errors.append(f"{entry_where}.command must be a non-empty string")
                continue

            for token in command.split():
                if not PATH_LIKE.match(token) or os.path.sep not in token:
                    continue
                candidate = os.path.normpath(os.path.expanduser(token))
                if os.path.exists(candidate):
                    if os.path.isfile(candidate) and not os.access(candidate, os.X_OK):
                        warnings.append(
                            f"{entry_where}: {token} exists but is not executable"
                        )
                else:
                    errors.append(
                        f"{entry_where}: {token} does not exist. A hook whose command file "
                        "is missing never fires, and it does not report that it did not."
                    )

            if os.path.sep not in command and "$" not in command:
                warnings.append(
                    f"{entry_where}.command names no path; it is a bare command that must "
                    "be on PATH. That works, and it breaks silently where it is not."
                )

print(f"hooks: {total} in {len(hooks)} event(s)", file=sys.stderr)
for message in errors:
    print(f"error: {message}", file=sys.stderr)
for message in warnings:
    print(f"warning: {message}", file=sys.stderr)
print(f"errors: {len(errors)}  warnings: {len(warnings)}")

sys.exit(1 if errors or (strict and warnings) else 0)
PYTHON
