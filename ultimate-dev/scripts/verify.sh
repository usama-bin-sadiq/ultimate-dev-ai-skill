#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -f "$ROOT/SKILL.md"
test "$(<"$ROOT/VERSION")" = "2.5.0"
test -f "$ROOT/runtime/core/engine.py"
test -f "$ROOT/runtime/core/state.py"
test -f "$ROOT/runtime/schemas/task-contract.json"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py' -q
python3 -m unittest discover -s "$ROOT/tests/runtime" -p 'test_*.py' -q
echo "Ultimate-Dev 2.5 verification: PASS"
