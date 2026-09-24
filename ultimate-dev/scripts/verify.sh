#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Required host-neutral runtime assets.
test -f "$ROOT/SKILL.md"
test -f "$PROJECT_ROOT/VERSION"
test -f "$ROOT/runtime/core/state.py"
test -f "$ROOT/runtime/schemas/task-contract.json"
test -f "$ROOT/runtime/schemas/jev-decision-request.schema.json"
test -f "$ROOT/runtime/schemas/jev-decision-packet.schema.json"
test -f "$ROOT/runtime/jev-policy.json"
test -f "$ROOT/runtime/jev/engine.mjs"

# The mandatory Python path must not import the legacy JEV package.
if grep -Eq 'runtime\.core\.jev|create_jev_core|JevCore' "$ROOT/runtime/core/session_manager.py" "$ROOT/runtime/core/engine.py"; then
  echo "Legacy JEV import remains in the mandatory runtime path" >&2
  exit 1
fi

if find "$ROOT/runtime/jev" -type f -name '*.py' -print -quit | grep -q .; then
  echo "Python implementation found in canonical JEV scope" >&2
  exit 1
fi

# The JEV path has no package-manager dependency.
if command -v node >/dev/null 2>&1; then
  node --test "$ROOT/tests/jev/engine.test.mjs"
else
  echo "JEV tests skipped: Node.js is unavailable" >&2
fi

# The older Python suite is optional legacy maintenance tooling.
if command -v python3 >/dev/null 2>&1 && python3 -c 'import pytest, yaml' >/dev/null 2>&1; then
  (cd "$ROOT" && python3 -m pytest tests -q)
else
  echo "Legacy Python suite skipped: pytest/PyYAML unavailable" >&2
fi

echo "Ultimate-Dev host-native verification: PASS"
