#!/usr/bin/env bash
# PreToolUse hook for Bash.
#
# The companion to validate-write.sh. The reference's path-safety fragment reads
# .tool_input.file_path, which a Bash call does not have -- it carries
# .tool_input.command instead. Applying the file-path test to a command field
# would check the wrong string, so the input-validation fragment is what carries
# over: same tool-name check, same discipline about a malformed payload, and the
# same exit contract.
#
# This hook does not attempt a dangerous-command policy. references/security-
# best-practices.md does not state one, and inventing a blocklist here would put
# a rule in front of the agent that the skill never taught and that nobody
# reviewed. If you want command filtering, write the policy first, then enforce
# it -- and say in the skill that it exists.
#
# Contract: exit 0 allows, exit 2 blocks with the reason on stderr as JSON.
set -euo pipefail

# A parse error must become an empty field, not an abort. `set -e` plus a jq
# failure kills the script with jq's own exit code -- 5, not 2 -- which is a hook
# that errored rather than a hook that decided. The outcome is the same either
# way on a strict host and the opposite on a permissive one, and the difference
# is not visible in this file. `|| true` routes the failure to the validation
# below, where it becomes an explicit deny with a reason.

input=$(cat) || true
tool_name=$(echo "$input" | jq -r '.tool_name // empty' 2>/dev/null || true)
command=$(echo "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

# Input validation, unchanged from the reference.
if [[ ! "$tool_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
  echo '{"decision": "deny", "reason": "Invalid or missing tool name"}' >&2
  exit 2
fi

if [[ "$tool_name" != "Bash" ]]; then
  echo '{"decision": "deny", "reason": "This hook is scoped to Bash"}' >&2
  exit 2
fi

# A Bash call with no command is malformed, not harmless. The reference's rule
# is to validate the input before acting on it, and an absent field is the case
# that rule exists for.
if [[ -z "$command" ]]; then
  echo '{"decision": "deny", "reason": "No command in tool_input"}' >&2
  exit 2
fi

# Path traversal still applies to a command: this is the one check from the
# reference that transfers unchanged, because writing outside the project is
# reachable from a shell as well as from a file write.
if [[ "$command" == *".."* ]]; then
  echo '{"decision": "deny", "reason": "Path traversal detected"}' >&2
  exit 2
fi

exit 0
