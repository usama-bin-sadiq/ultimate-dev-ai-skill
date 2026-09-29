#!/usr/bin/env bash
# PreToolUse hook for Write and Edit.
#
# Assembled from the two fragments in references/security-best-practices.md --
# "Input Validation" and "Path Safety" -- put end to end so the hook is runnable
# rather than illustrative. Every check here is one the reference states; nothing
# has been added to it.
#
# Contract: exit 0 allows, exit 2 blocks with the reason on stderr as JSON.
# Anything else is a hook that failed, which is not the same as a hook that
# allowed, so every path below exits deliberately.
set -euo pipefail

# A parse error must become an empty field, not an abort. `set -e` plus a jq
# failure kills the script with jq's own exit code -- 5, not 2 -- which is a hook
# that errored rather than a hook that decided. The outcome is the same either
# way on a strict host and the opposite on a permissive one, and the difference
# is not visible in this file. `|| true` routes the failure to the validation
# below, where it becomes an explicit deny with a reason.

input=$(cat) || true
tool_name=$(echo "$input" | jq -r '.tool_name // empty' 2>/dev/null || true)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)

# Input validation. An unparseable payload yields an empty string, which fails
# this test -- a malformed hook input blocks rather than silently allowing.
if [[ ! "$tool_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
  echo '{"decision": "deny", "reason": "Invalid or missing tool name"}' >&2
  exit 2
fi

# Only Write and Edit carry a file path. A path arriving for any other tool is
# this hook being asked about a tool it does not understand.
if [[ -z "$file_path" ]]; then
  echo '{"decision": "deny", "reason": "No file_path in tool_input"}' >&2
  exit 2
fi

# Path safety: traversal.
if [[ "$file_path" == *".."* ]]; then
  echo '{"decision": "deny", "reason": "Path traversal detected"}' >&2
  exit 2
fi

# Path safety: sensitive files. Matches the reference's own test, which is a
# substring test and therefore blocks .env.example as well as .env. That is
# deliberate here: the cost of the false positive is one blocked write the user
# can see, and the cost of the false negative is a secret committed.
if [[ "$file_path" == *".env"* ]]; then
  echo '{"decision": "deny", "reason": "Sensitive file"}' >&2
  exit 2
fi

# Allowed. No output: a hook that speaks when it has nothing to say trains the
# reader to ignore it.
exit 0
