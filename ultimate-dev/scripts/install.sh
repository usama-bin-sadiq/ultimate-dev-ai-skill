#!/usr/bin/env bash
set -euo pipefail
PROJECT=""
GLOBAL=0
YES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="${2:?missing project path}"; shift 2;;
    --global) GLOBAL=1; shift;;
    --yes) YES=1; shift;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$GLOBAL" -eq 1 ]]; then
  DEST="$HOME/.agents/skills/ultimate-dev"
  mkdir -p "$DEST"
  cp -R "$ROOT/." "$DEST/"
  mkdir -p "$HOME/.memory/ultimate-dev"
  # If Claude's native .claude directory exists, symlink skills so Claude sees it too
  if [[ -e "$HOME/.claude" ]]; then
    ln -sfn "$HOME/.agents/skills/ultimate-dev" "$HOME/.claude/skills/ultimate-dev"
    echo "Linked Claude path: $HOME/.claude/skills/ultimate-dev -> $DEST"
  fi
  echo "Installed Ultimate-Dev 2.5 globally at $DEST"
  exit 0
fi
if [[ -z "$PROJECT" ]]; then PROJECT="$(pwd)"; fi
PROJECT="$(cd "$PROJECT" && pwd)"
mkdir -p "$PROJECT/.agents/skills/ultimate-dev" "$PROJECT/.cursor/rules"
cp -R "$ROOT/SKILL.md" "$ROOT/runtime" "$ROOT/router" "$ROOT/config" "$ROOT/skills" "$ROOT/modules" "$ROOT/agents" "$PROJECT/.agents/skills/ultimate-dev/" 2>/dev/null || true
# If Claude's native .claude directory exists in project, symlink skills
if [[ -e "$PROJECT/.claude" ]]; then
  ln -sfn "$PROJECT/.agents/skills/ultimate-dev" "$PROJECT/.claude/skills/ultimate-dev"
  echo "Linked Claude path: $PROJECT/.claude/skills/ultimate-dev -> $PROJECT/.agents/skills/ultimate-dev"
fi
cp "$ROOT/templates/CLAUDE.md" "$PROJECT/CLAUDE.md" 2>/dev/null || true
cp "$ROOT/templates/AGENTS.md" "$PROJECT/AGENTS.md" 2>/dev/null || true
cp "$ROOT/templates/ultimate-dev.mdc" "$PROJECT/.cursor/rules/ultimate-dev.mdc"
mkdir -p "$PROJECT/.memory/ultimate-dev/tasks"
touch "$PROJECT/.memory/ultimate-dev/.gitignore"
printf '%s\n' 'tasks/*' > "$PROJECT/.memory/ultimate-dev/.gitignore"
echo "Installed Ultimate-Dev 2.5 in $PROJECT"
