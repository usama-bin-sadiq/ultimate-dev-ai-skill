#!/usr/bin/env bash
set -u
for cmd in claude codex cursor python3 git docker node npm bun; do
  if command -v "$cmd" >/dev/null 2>&1; then echo "✓ $cmd: $(command -v "$cmd")"; else echo "- $cmd: not found"; fi
done
