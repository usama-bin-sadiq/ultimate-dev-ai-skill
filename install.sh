#!/usr/bin/env bash
# Install the ultimate-dev skill where agent runtimes discover skills.
#
# Discovery paths honoured by the major runtimes (OpenCode, Claude Code,
# Codex, Cursor, Gemini CLI, Copilot, Windsurf, Cline, Trae, Kiro, ...):
#   ~/.agents/skills      the cross-tool standard (Open Agent Skills)
#   ~/.claude/skills      Claude-compatible, also honoured by most others
#   <project>/.agents/skills and <project>/.claude/skills for project scopes
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/ultimate-dev"
SKILL_NAME="ultimate-dev"

MODE="auto"          # auto | all | target
TARGET=""
YES=0
DRY_RUN=0
USE_LINK=0

while [ $# -gt 0 ]; do
  case "$1" in
    --target) MODE="target"; TARGET="$2"; shift 2 ;;
    --all) MODE="all"; shift ;;
    --yes|-y) YES=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --link) USE_LINK=1; shift ;;
    --help|-h) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -f "${SOURCE_DIR}/SKILL.md" ] || { echo "source skill not found at ${SOURCE_DIR}" >&2; exit 1; }

# The destinations every recognised runtime scans, global scope.
GLOBAL_DIRS=( "$HOME/.agents/skills" "$HOME/.claude/skills" )
# Plus the tool-native global dirs that the universal two do not cover.
EXTRA_GLOBAL_DIRS=(
  "$HOME/.config/opencode/skills" "$HOME/.gemini/skills"
  "$HOME/.cursor/skills" "$HOME/.codex/skills"
  "$HOME/.kiro/skills" "$HOME/.trae/skills"
  "$HOME/.config/gemini/skills" "$HOME/.rovodev/skills"
)
# Project-local discovery, relative to cwd.
PROJECT_DIRS=( ".agents/skills" ".claude/skills" )

DESTINATIONS=()
case "$MODE" in
  target) DESTINATIONS=( "$TARGET" ) ;;
  all)
    for d in "${GLOBAL_DIRS[@]}" "${EXTRA_GLOBAL_DIRS[@]}"; do DESTINATIONS+=( "$d" ); done
    for d in "${PROJECT_DIRS[@]}"; do DESTINATIONS+=( "$d" ); done
    ;;
  auto)
    # First existing skills dir wins; fall back to the two universal globals.
    found=""
    for d in "$HOME/.claude/skills" "$HOME/.agents/skills" .claude/skills .agents/skills \
             "$HOME/.config/opencode/skills" "$HOME/.gemini/skills" "$HOME/.cursor/skills"; do
      if [ -d "$d" ]; then found="$d"; break; fi
    done
    if [ -n "$found" ]; then
      DESTINATIONS=( "$found" )
    else
      echo "no existing skills directory found; installing to ${GLOBAL_DIRS[0]} and ${GLOBAL_DIRS[1]}"
      DESTINATIONS=( "${GLOBAL_DIRS[@]}" )
    fi
    ;;
esac

for d in "${DESTINATIONS[@]}"; do
  dest="${d%/}/${SKILL_NAME}"
  echo "-> ${dest}"
  [ "$DRY_RUN" -eq 1 ] && continue

  if [ -e "$dest" ] && [ "$YES" -eq 0 ]; then
    printf 'destination exists: %s. overwrite? [y/N] ' "$dest"
    read -r answer
    case "$answer" in y|Y|yes) ;; *) echo "skipped"; continue ;; esac
  fi

  mkdir -p "$d"
  rm -rf "$dest"
  if [ "$USE_LINK" -eq 1 ]; then
    ln -s "$SOURCE_DIR" "$dest"
  else
    cp -R "$SOURCE_DIR" "$dest"
    find "$dest" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
    find "$dest" -name "*.pyc" -delete 2>/dev/null || true
    # .DS_Store is already gitignored, so it never ships in a clone -- but it is
    # sitting in the working tree of whoever runs the installer on macOS, and
    # Copy-It-along means the installed copy inherits it. validate-skills.py
    # then reports it as an unignored build artefact, which is true of the copy
    # (there is no .gitignore beside it) and useless to whoever is reading it.
    find "$dest" -name ".DS_Store" -delete 2>/dev/null || true
  fi
done

if [ "$DRY_RUN" -eq 0 ] && command -v python3 >/dev/null 2>&1; then
  # Validate the first real destination, not all of them.
  for d in "${DESTINATIONS[@]}"; do
    if [ -d "${d%/}/${SKILL_NAME}/tools" ]; then
      (cd "${d%/}/${SKILL_NAME}" && python3 tools/validate-skills.py) && break
    fi
  done
fi
echo "done"
