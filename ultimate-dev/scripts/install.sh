#!/usr/bin/env bash
# Install the Ultimate-Dev skill from a repository checkout.
#
# The root VERSION file is the sole version source.  The payload is copied to a
# sibling staging directory, validated, and swapped into place only after all
# checks pass.  Re-running the command replaces the target atomically instead
# of creating a nested skill directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$SKILL_DIR/.." && pwd -P)"
VERSION_FILE="$REPO_ROOT/VERSION"

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

usage() {
  cat <<EOF
Usage: $0 [--global | --project DIR] [--yes] [--uninstall]
       $0 --uninstall [--global | --project DIR] [--clean-gitignore] [--yes]

Options:
  --global              Install to ~/.agents/skills/ultimate-dev
  --project DIR         Install to DIR/.agents/skills/ultimate-dev
  --yes                 Do not prompt (accepted for CI compatibility)
  --uninstall           Remove the installed skill payload
  --clean-gitignore     Remove only the managed memory ignore entry
  --clean-memory        Refuse: project memory deletion is retention-managed
  --all                 Refuse: combines the unsafe memory cleanup request
  --help                Show this help
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  local status=$?
  if [[ -n "$STAGE" && -d "$STAGE" ]]; then
    case "$STAGE" in
      */.ultimate-dev.stage.*) rm -rf -- "$STAGE" ;;
    esac
  fi
  if [[ -n "$PYCACHE_DIR" && -d "$PYCACHE_DIR" ]]; then
    case "$PYCACHE_DIR" in
      */.ultimate-dev.pycache.*) rm -rf -- "$PYCACHE_DIR" ;;
    esac
  fi
  if [[ -n "$LOCK" && -d "$LOCK" ]]; then
    rmdir -- "$LOCK" 2>/dev/null || true
  fi
  exit "$status"
}
trap cleanup EXIT

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
  die "memory deletion is disabled; use the runtime retention workflow with a dry-run and confirmation"
fi

if [[ "$GLOBAL" -eq 1 && -n "$PROJECT" ]]; then
  die "choose either --global or --project"
fi

if [[ "$GLOBAL" -eq 1 ]]; then
  [[ -n "${HOME:-}" ]] || die "HOME is not set"
  PROJECT_DIR="$(cd "$HOME" && pwd -P)"
  TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
elif [[ -n "$PROJECT" ]]; then
  PROJECT_DIR="$(cd "$PROJECT" 2>/dev/null && pwd -P)" || die "project directory not found: $PROJECT"
  TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
else
  PROJECT_DIR="$(pwd -P)"
  TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
fi

# Do not follow attacker-controlled path components while creating an install
# target or project-memory scaffolding.
for path_component in \
  "$PROJECT_DIR/.agents" \
  "$PROJECT_DIR/.agents/skills" \
  "$PROJECT_DIR/.claude" \
  "$PROJECT_DIR/.cursor"; do
  [[ ! -L "$path_component" ]] || die "refusing symlinked install path: $path_component"
done

TARGET_PARENT="$(dirname "$TARGET")"
mkdir -p "$TARGET_PARENT"
TARGET_PARENT="$(cd "$TARGET_PARENT" && pwd -P)"

remove_gitignore_entry() {
  local gitignore="$PROJECT_DIR/.gitignore"
  local entry='.memory/ultimate-dev/'
  local tmp
  [[ -f "$gitignore" ]] || return 0
  [[ ! -L "$gitignore" ]] || die "refusing to modify symlinked .gitignore: $gitignore"
  grep -Fqx -- "$entry" "$gitignore" || return 0
  tmp="$(mktemp "$PROJECT_DIR/.gitignore.tmp.XXXXXX")"
  awk -v entry="$entry" '$0 != entry { print }' "$gitignore" > "$tmp"
  mv -- "$tmp" "$gitignore"
}

if [[ "$UNINSTALL" -eq 1 ]]; then
  [[ "$YES" -eq 1 ]] || die "uninstall requires explicit --yes confirmation"
  [[ ! -L "$TARGET" ]] || die "refusing to remove symlinked skill target: $TARGET"
  if [[ -e "$TARGET" && ! -d "$TARGET" ]]; then
    die "skill target is not a directory: $TARGET"
  fi
  if [[ -d "$TARGET" ]]; then
    rm -rf -- "$TARGET"
    printf 'Removed %s\n' "$TARGET"
  else
    printf 'Skill target not found: %s\n' "$TARGET"
  fi
  if [[ "$CLEAN_GITIGNORE" -eq 1 ]]; then
    remove_gitignore_entry
  fi
  printf 'Project memory was not deleted; use the retention workflow for memory cleanup.\n'
  exit 0
fi

# Refuse a symlink at the destination rather than following it while swapping
# a payload.  This also prevents a malicious project from redirecting writes.
[[ ! -L "$TARGET" ]] || die "refusing to replace symlinked skill target: $TARGET"
if [[ -e "$TARGET" && ! -d "$TARGET" ]]; then
  die "skill target exists but is not a directory: $TARGET"
fi
MEMORY_ROOT="$PROJECT_DIR/.memory"
MEMORY_DIR="$MEMORY_ROOT/ultimate-dev"
if [[ -L "$MEMORY_ROOT" || -L "$MEMORY_DIR" ]]; then
  die "refusing to use symlinked project memory path: $MEMORY_DIR"
fi
[[ ! -e "$MEMORY_ROOT" || -d "$MEMORY_ROOT" ]] || die "project memory root is not a directory: $MEMORY_ROOT"
[[ ! -e "$MEMORY_DIR" || -d "$MEMORY_DIR" ]] || die "project memory path is not a directory: $MEMORY_DIR"
if [[ "$GLOBAL" -eq 0 ]]; then
  project_gitignore="$PROJECT_DIR/.gitignore"
  [[ ! -e "$project_gitignore" || -f "$project_gitignore" ]] || die "project .gitignore is not a regular file"
  [[ ! -L "$project_gitignore" ]] || die "refusing to modify symlinked .gitignore: $project_gitignore"
fi
memory_ignore_path="$MEMORY_DIR/.gitignore"
[[ ! -e "$memory_ignore_path" || -f "$memory_ignore_path" ]] || die "memory .gitignore is not a regular file"
[[ ! -L "$memory_ignore_path" ]] || die "refusing to modify symlinked memory .gitignore: $memory_ignore_path"

LOCK="$TARGET_PARENT/.ultimate-dev.install.lock"
mkdir "$LOCK" 2>/dev/null || die "another installer is already running for $TARGET"
STAGE="$(mktemp -d "$TARGET_PARENT/.ultimate-dev.stage.XXXXXX")"
cp -R "$SKILL_DIR/." "$STAGE/"
if find "$STAGE" -type l -print -quit | grep -q .; then
  die "staged payload contains a symlink"
fi

# The root VERSION is canonical; deliberately replace any stale package copy.
install -m 0644 "$VERSION_FILE" "$STAGE/VERSION"

# Never package the pre-existing untracked optional bridges into a release
# payload.  They remain untouched in the source checkout.
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
  PYCACHE_DIR=""
fi

# Swap directories through a same-filesystem rename.  If the second rename
# fails, restore the previous payload rather than leaving a mixed install.
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

# Project memory is additive and retention-managed.  Never remove or overwrite
# an existing memory file; use an atomic create for new scaffolding.
MEMORY_ROOT="$PROJECT_DIR/.memory"
MEMORY_DIR="$MEMORY_ROOT/ultimate-dev"
if [[ -L "$MEMORY_ROOT" || -L "$MEMORY_DIR" ]]; then
  die "refusing to use symlinked project memory path: $MEMORY_DIR"
fi
mkdir -p "$MEMORY_DIR/tasks"
MEMORY_IGNORE="$MEMORY_DIR/.gitignore"
if [[ ! -e "$MEMORY_IGNORE" ]]; then
  memory_tmp="$(mktemp "$MEMORY_DIR/.gitignore.tmp.XXXXXX")"
  printf '%s\n' 'tasks/*' > "$memory_tmp"
  mv -- "$memory_tmp" "$MEMORY_IGNORE"
fi
if [[ ! -e "$MEMORY_DIR/project-memory.md" && -f "$TARGET/memory/project-memory.md" ]]; then
  memory_tmp="$(mktemp "$MEMORY_DIR/project-memory.md.tmp.XXXXXX")"
  cp "$TARGET/memory/project-memory.md" "$memory_tmp"
  mv -- "$memory_tmp" "$MEMORY_DIR/project-memory.md"
fi

if [[ "$GLOBAL" -eq 0 ]]; then
  GITIGNORE="$PROJECT_DIR/.gitignore"
  MEMORY_ENTRY='.memory/ultimate-dev/'
  if [[ -L "$GITIGNORE" ]]; then
    die "refusing to modify symlinked .gitignore: $GITIGNORE"
  fi
  if [[ ! -f "$GITIGNORE" ]]; then
    gitignore_tmp="$(mktemp "$PROJECT_DIR/.gitignore.tmp.XXXXXX")"
    printf '%s\n' "$MEMORY_ENTRY" > "$gitignore_tmp"
    mv -- "$gitignore_tmp" "$GITIGNORE"
  elif ! grep -Fqx -- "$MEMORY_ENTRY" "$GITIGNORE"; then
    gitignore_tmp="$(mktemp "$PROJECT_DIR/.gitignore.tmp.XXXXXX")"
    cat "$GITIGNORE" > "$gitignore_tmp"
    printf '\n%s\n' "$MEMORY_ENTRY" >> "$gitignore_tmp"
    mv -- "$gitignore_tmp" "$GITIGNORE"
  fi
fi

# Preserve the package's optional host adapters without overwriting user files.
# These compatibility files are copied only into a project scope; a global
# install must not mutate an arbitrary repository checkout.
if [[ "$GLOBAL" -eq 0 ]]; then
  copy_template_if_absent() {
    local source_file="$1"
    local destination_file="$2"
    [[ -f "$source_file" ]] || return 0
    if [[ -e "$destination_file" || -L "$destination_file" ]]; then
      return 0
    fi
    mkdir -p "$(dirname "$destination_file")"
    local template_tmp
    template_tmp="$(mktemp "$(dirname "$destination_file")/.template.tmp.XXXXXX")"
    cp "$source_file" "$template_tmp"
    mv -- "$template_tmp" "$destination_file"
  }
  copy_template_if_absent "$TARGET/templates/CLAUDE.md" "$PROJECT_DIR/CLAUDE.md"
  copy_template_if_absent "$TARGET/templates/AGENTS.md" "$PROJECT_DIR/AGENTS.md"
  copy_template_if_absent "$TARGET/templates/ultimate-dev.mdc" "$PROJECT_DIR/.cursor/rules/ultimate-dev.mdc"
  if [[ -d "$PROJECT_DIR/.claude" ]]; then
    claude_skills="$PROJECT_DIR/.claude/skills"
    mkdir -p "$claude_skills"
    claude_link="$claude_skills/ultimate-dev"
    if [[ -e "$claude_link" && ! -L "$claude_link" ]]; then
      die "refusing to replace existing Claude path: $claude_link"
    fi
    ln -sfn "$TARGET" "$claude_link"
  fi
fi

printf 'Installed Ultimate-Dev %s at %s\n' "$VERSION" "$TARGET"
printf 'Project memory: %s (deletion is retention-managed)\n' "$MEMORY_DIR"
