#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -f "$ROOT/SKILL.md"
test "$(<"$ROOT/VERSION")" = "2.5.2"
test -f "$ROOT/runtime/core/engine.py"
test -f "$ROOT/runtime/core/state.py"
test -f "$ROOT/runtime/schemas/task-contract.json"
python3 -m pytest "$ROOT/tests" -q
echo "Ultimate-Dev 2.5 verification: PASS"