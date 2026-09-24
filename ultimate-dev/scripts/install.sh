#!/usr/bin/env bash
# Install the Ultimate-Dev skill by copying the inner skill payload.
# The installer is interactive when no scope is supplied.  It never creates
# symlinks or writes files outside the selected skill destination.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$SKILL_DIR/.." && pwd -P)"
VERSION_FILE="$REPO_ROOT/VERSION"
if [[ ! -r "$VERSION_FILE" ]]; then
  VERSION_FILE="$SKILL_DIR/VERSION"
fi

GLOBAL=0
PROJECT=""
YES=0
UNINSTALL=0
CLEAN_MEMORY=0
CLEAN_GITIGNORE=0
STAGE=""
BACKUP=""
LOCK=""
PYCACHE_DIR=""

# ─── Presentation ───────────────────────────────────────────────────────────

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --global              Install to ~/.agents/skills/ultimate-dev
  --project DIR         Install to DIR/.agents/skills/ultimate-dev
  --yes, -y             Skip prompts (use global scope by default)
  --uninstall            Remove the selected skill destination
  --clean-gitignore      Compatibility flag; no project files are managed
  --clean-memory         Refuse: memory is not managed by this installer
  --all                  Refuse: combines the unsafe memory cleanup request
  --help, -h             Show this help

With no scope option, the installer interactively asks Global or Project and
then asks for confirmation.  Only the contents of the inner ultimate-dev/
folder are copied to .agents/skills/ultimate-dev/.

Examples:
  $0
  $0 --global
  $0 --project ~/my-app
  $0 --global --yes
EOF
}

info() { printf '  ℹ %s\n' "$*"; }
status() { printf '  ✔ %s\n' "$*"; }
warn() { printf '  ⚠ %s\n' "$*" >&2; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

print_banner() {
  local version
  version="$(tr -d '[:space:]' < "$VERSION_FILE" 2>/dev/null || printf 'unknown')"
  printf '\n  ┌──────────────────────────────────────────────┐\n'
  printf '  │ %-44s │\n' "Ultimate-Dev installer v${version}"
  printf '  │ Copy the inner skill folder; no symlinks      │\n'
  printf '  └──────────────────────────────────────────────┘\n\n'
}

menu_select() {
  local prompt="$1"
  shift
  local choice
  printf '  %s\n' "$prompt"
  local index=1
  local option
  for option in "$@"; do
    printf '    %d) %s\n' "$index" "$option"
    index=$((index + 1))
  done
  printf '  Enter number (or q to cancel): '
  if ! read -r choice; then
    printf '\n'
    return 1
  fi
  case "$choice" in
    q|Q|'') printf 'Cancelled.\n'; return 2 ;;
    *)
      if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$#" ]; then
        MENU_RESULT="$choice"
        return 0
      fi
      warn "Invalid choice. Please enter 1-$# or q."
      return 1
      ;;
  esac
}

expand_home() {
  case "$1" in
    '~') printf '%s' "$HOME" ;;
    '~/'*) printf '%s/%s' "$HOME" "${1#\~/}" ;;
    *) printf '%s' "$1" ;;
  esac
}

resolve_directory() {
  local input
  input="$(expand_home "$1")"
  [[ -n "$input" ]] || die "project directory cannot be empty"
  [[ -d "$input" ]] || die "project directory not found: $input"
  (cd "$input" && pwd -P)
}

# ─── Cleanup ────────────────────────────────────────────────────────────────

cleanup() {
  local status_code=$?
  trap - EXIT
  if [[ -n "$STAGE" && -d "$STAGE" ]]; then
    case "$STAGE" in
      */.ultimate-dev.stage.*) rm -rf -- "$STAGE" ;;
    esac
  fi
  if [[ -n "$LOCK" && -d "$LOCK" ]]; then
    case "$LOCK" in
      */.ultimate-dev.install.lock) rmdir -- "$LOCK" 2>/dev/null || true ;;
    esac
  fi
  if [[ -n "$PYCACHE_DIR" && -d "$PYCACHE_DIR" ]]; then
    case "$PYCACHE_DIR" in
      */.ultimate-dev.pycache.*) rm -rf -- "$PYCACHE_DIR" ;;
    esac
  fi
  exit "$status_code"
}
trap cleanup EXIT

# ─── Arguments ──────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)
      [[ "$GLOBAL" -eq 0 && -z "$PROJECT" ]] || die "choose either --global or --project"
      GLOBAL=1
      shift
      ;;
    --project)
      [[ $# -ge 2 && -n "${2:-}" ]] || die "--project requires a directory"
      [[ "$GLOBAL" -eq 0 ]] || die "choose either --global or --project"
      PROJECT="$2"
      shift 2
      ;;
    --yes|-y) YES=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --clean-memory) CLEAN_MEMORY=1; shift ;;
    --clean-gitignore) CLEAN_GITIGNORE=1; shift ;;
    --all) CLEAN_MEMORY=1; CLEAN_GITIGNORE=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -r "$VERSION_FILE" ]] || die "canonical VERSION is missing: $VERSION_FILE"
VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "canonical VERSION is not semantic: $VERSION"

if [[ "$CLEAN_MEMORY" -eq 1 ]]; then
  die "memory deletion is disabled; this installer only manages the skill folder"
fi
if [[ "$GLOBAL" -eq 1 && -n "$PROJECT" ]]; then
  die "choose either --global or --project"
fi

# ─── Scope and target ───────────────────────────────────────────────────────

if [[ "$GLOBAL" -eq 1 ]]; then
  SCOPE="global"
elif [[ -n "$PROJECT" ]]; then
  SCOPE="project"
elif [[ "$YES" -eq 1 ]]; then
  # Preserve the old CI/default behavior for --yes without a scope.
  SCOPE="global"
else
  print_banner
  while true; do
    if menu_select "Where do you want to install?" \
      "Global  — ~/.agents/skills/ultimate-dev/" \
      "Project — <project>/.agents/skills/ultimate-dev/"; then
      break
    else
      status_code=$?
      [[ "$status_code" -eq 2 ]] && exit 0
    fi
  done
  case "$MENU_RESULT" in
    1) SCOPE="global" ;;
    2)
      SCOPE="project"
      printf '  Project directory (Enter for current directory): '
      if ! read -r PROJECT; then
        printf '\n'
        exit 0
      fi
      PROJECT="${PROJECT:-.}"
      ;;
  esac
fi

if [[ "$SCOPE" == "global" ]]; then
  [[ -n "${HOME:-}" ]] || die "HOME is not set"
  PROJECT_DIR="$(cd "$HOME" && pwd -P)"
  TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
else
  PROJECT_DIR="$(resolve_directory "${PROJECT:-.}")"
  TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
fi
TARGET_PARENT="$(dirname "$TARGET")"

# Never follow or replace a symlink at the selected destination.
for component in "$PROJECT_DIR/.agents" "$PROJECT_DIR/.agents/skills"; do
  [[ ! -L "$component" ]] || die "refusing to use symlinked install path: $component"
done
[[ ! -L "$TARGET" ]] || die "refusing to replace symlinked skill target: $TARGET"
[[ ! -L "$TARGET_PARENT" ]] || die "refusing to use symlinked install parent: $TARGET_PARENT"
mkdir -p "$TARGET_PARENT"
TARGET_PARENT="$(cd "$TARGET_PARENT" && pwd -P)"
[[ ! -L "$TARGET_PARENT" ]] || die "refusing to use symlinked install parent: $TARGET_PARENT"
[[ ! -e "$TARGET" || -d "$TARGET" ]] || die "skill target exists but is not a directory: $TARGET"

# ─── Uninstall ──────────────────────────────────────────────────────────────

if [[ "$UNINSTALL" -eq 1 ]]; then
  print_banner
  printf '  Uninstall target: %s\n' "$TARGET"
  if [[ "$YES" -eq 0 ]]; then
    printf '  Proceed? [y/N]: '
    if ! read -r confirm; then
      printf '\nCancelled.\n'
      exit 0
    fi
    if [[ ! "$confirm" =~ ^[Yy]([Ee][Ss])?$ ]]; then
      printf 'Cancelled.\n'
      exit 0
    fi
  fi
  if [[ -d "$TARGET" ]]; then
    rm -rf -- "$TARGET"
    status "Removed $TARGET"
  else
    info "Skill target not found: $TARGET"
  fi
  if [[ "$CLEAN_GITIGNORE" -eq 1 ]]; then
    info "No project .gitignore is managed by this installer."
  fi
  info "No memory, templates, or host configuration files were changed."
  exit 0
fi

# ─── Confirmation ───────────────────────────────────────────────────────────

print_banner
printf '  Source: %s\n' "$SKILL_DIR"
printf '  Target: %s\n' "$TARGET"
printf '  Scope:  %s\n' "$SCOPE"
printf '  Version: %s\n\n' "$VERSION"
if [[ "$YES" -eq 0 ]]; then
  printf '  Proceed? [y/N]: '
  if ! read -r confirm; then
    printf '\nCancelled.\n'
    exit 0
  fi
  if [[ ! "$confirm" =~ ^[Yy]([Ee][Ss])?$ ]]; then
    printf 'Cancelled.\n'
    exit 0
  fi
fi

# ─── Copy-only staged installation ──────────────────────────────────────────

LOCK="$TARGET_PARENT/.ultimate-dev.install.lock"
mkdir "$LOCK" 2>/dev/null || die "another installer is already running for $TARGET"
STAGE="$(mktemp -d "$TARGET_PARENT/.ultimate-dev.stage.XXXXXX")"
cp -R "$SKILL_DIR/." "$STAGE/"

if find "$STAGE" -type l -print -quit | grep -q .; then
  die "source skill payload contains a symlink; copy-only install refuses it"
fi

# The source checkout keeps the canonical version at repository root.  Copy it
# into the installed skill metadata without copying any other repository files.
cp "$VERSION_FILE" "$STAGE/VERSION"

# These are pre-existing optional local bridges, not release payload.
rm -f -- \
  "$STAGE/runtime/core/browser/automation.py" \
  "$STAGE/runtime/core/sandbox/runner.py" \
  "$STAGE/runtime/core/jev/bridge.py"

[[ -s "$STAGE/SKILL.md" ]] || die "staged payload is missing SKILL.md"
[[ -s "$STAGE/VERSION" ]] || die "staged payload is missing VERSION"
[[ -f "$STAGE/runtime/core/engine.py" ]] || die "staged payload is missing runtime/core/engine.py"
STAGED_VERSION="$(tr -d '[:space:]' < "$STAGE/VERSION")"
[[ "$STAGED_VERSION" == "$VERSION" ]] || die "staged version does not match canonical VERSION"

if [[ -f "$STAGE/skill-manifest.yaml" ]]; then
  manifest_version="$(awk '/^version:/ {sub(/^[^:]*:[[:space:]]*/, ""); print; exit}' "$STAGE/skill-manifest.yaml")"
  manifest_version="${manifest_version//\"/}"
  manifest_version="${manifest_version//\'/}"
  manifest_version="${manifest_version//[[:space:]]/}"
  if [[ -n "$manifest_version" && "$manifest_version" != "$VERSION" ]]; then
    die "staged manifest version does not match canonical VERSION"
  fi
fi

AGENT_COUNT="$(find "$STAGE/agents" -name '*.md' -not -path '*/_shared/*' -type f 2>/dev/null | wc -l | tr -d ' ')"
SKILL_COUNT="$(find "$STAGE/skills" -name 'SKILL.md' -type f 2>/dev/null | wc -l | tr -d ' ')"
[[ "$AGENT_COUNT" -gt 0 && "$SKILL_COUNT" -gt 0 ]] || die "staged payload has no agent/skill content"

if command -v python3 >/dev/null 2>&1; then
  PYCACHE_DIR="$(mktemp -d "$TARGET_PARENT/.ultimate-dev.pycache.XXXXXX")"
  PYTHONPYCACHEPREFIX="$PYCACHE_DIR" python3 -m py_compile "$STAGE/runtime/core/engine.py"
  PYTHONPATH="$STAGE" PYTHONPYCACHEPREFIX="$PYCACHE_DIR" python3 -c 'import runtime.core' >/dev/null
  rm -rf -- "$PYCACHE_DIR"
fi

# Replace only the selected skill directory.  No symlink, memory, template,
# .gitignore, .cursor, or .claude path is created.
if [[ -d "$TARGET" ]]; then
  BACKUP="$(mktemp -d "$TARGET_PARENT/.ultimate-dev.backup.XXXXXX")"
  rmdir -- "$BACKUP"
  mv -- "$TARGET" "$BACKUP"
fi
if ! mv -- "$STAGE" "$TARGET"; then
  if [[ -n "$BACKUP" && -d "$BACKUP" && ! -e "$TARGET" ]]; then
    mv -- "$BACKUP" "$TARGET"
    BACKUP=""
  fi
  die "failed to atomically install $TARGET"
fi
STAGE=""
if [[ -n "$BACKUP" && -d "$BACKUP" ]]; then
  rm -rf -- "$BACKUP"
  BACKUP=""
fi

FILE_COUNT="$(find "$TARGET" -type f 2>/dev/null | wc -l | tr -d ' ')"
status "Copied the inner skill folder to $TARGET"
status "Version $VERSION · $AGENT_COUNT agents · $SKILL_COUNT skills · $FILE_COUNT files"
info "No symlink, memory, template, or host configuration file was created."
