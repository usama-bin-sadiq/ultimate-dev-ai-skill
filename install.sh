#!/usr/bin/env bash
#
# Install the ultimate-dev skill.
#
# The skill is a directory of Markdown with no build step and no dependencies.
# Installing means copying `ultimate-dev/` to a location where the agent runtime
# discovers skills, and optionally pruning the material that is documentation
# rather than runtime.
#
# Runtime-neutral by design: the script detects known skill directories and falls
# back to a printed manual instruction rather than guessing. It never writes
# outside the directory it is told to write to, and never modifies anything
# already present without saying so first.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="ultimate-dev"
SOURCE_DIR="${SCRIPT_DIR}/${SKILL_NAME}"

# Runtimes are listed by where they look, not by product name, so a runtime this
# script has never heard of can still be handled by its project-local path.
GLOBAL_CANDIDATES=(
  "${HOME}/.agents/skills"
  "${HOME}/.claude/skills"
  "${HOME}/.config/opencode/skills"
  "${XDG_DATA_HOME:-$HOME/.local/share}/opencode/skills"
)
PROJECT_CANDIDATES=(
  ".agents/skills"
  ".claude/skills"
)

MODE="global"
TARGET=""
YES=0
PRUNE=1
DRY_RUN=0
BUNDLE_OUT="dist"
BUNDLE_ZIP=0

usage() {
  cat <<'USAGE'
usage: install.sh [options]

  --global              install for the current user (default)
  --project [DIR]       install into DIR, defaulting to the current directory
  --target DIR          install into an exact directory
  --all                 keep every file, including docs, examples, and evaluation
  --bundle [DIR]        write a runtime-only bundle to DIR (default: dist) and exit
  --bundle-zip          also write a .zip archive
  --check-bundle        verify the bundle would be sound, write nothing
  --yes                 do not prompt
  --dry-run             print what would happen, change nothing
  -h, --help            this message

The repository is more than the skill: alongside the runtime it carries the
evaluation corpus, worked examples, documentation, and research, which together
are about five times the size of the skill itself. A runtime install prunes them
by default. `--bundle` produces the pruned form as a standalone directory, for
distribution to a marketplace or another runtime.

Exit status is 0 on success, 1 on a refused or failed install.
USAGE
}

log()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# Paths that are documentation or source specification rather than runtime.
# Pruning them keeps an install small; the kernel never loads them, and they are
# all preserved in the repository.
PRUNABLE=(docs examples evaluation research knowledge)
PRUNABLE_FILES=(ARCHITECTURE.md new-arch.md prd.md)

while [ $# -gt 0 ]; do
  case "$1" in
    --global)   MODE="global"; shift ;;
    --project)  MODE="project"; shift
                TARGET="${1:-.}"; [ $# -gt 0 ] && shift || true ;;
    --target)   MODE="target"; shift
                [ $# -gt 0 ] || die "--target needs a directory"
                TARGET="$1"; shift ;;
    --all)      PRUNE=0; shift ;;
    --bundle)   MODE="bundle"; shift
                BUNDLE_OUT="${1:-dist}"; [ $# -gt 0 ] && shift || true ;;
    --bundle-zip) MODE="bundle"; BUNDLE_ZIP=1
                BUNDLE_OUT="${BUNDLE_OUT:-dist}"; shift ;;
    --check-bundle) MODE="bundle-check"; shift ;;
    --yes|-y)   YES=1; shift ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    *)          die "unknown option: $1 (try --help)" ;;
  esac
done

[ -d "$SOURCE_DIR" ] || die "cannot find ${SOURCE_DIR}; run install.sh from the repository root"

# Bundle mode short-circuits: it is a different operation with a different
# contract, so it does not share the destination logic below.
BUNDLER="${SOURCE_DIR}/tools/bundle-skill.py"
if [ "$MODE" = "bundle" ] || [ "$MODE" = "bundle-check" ]; then
  command -v python3 >/dev/null 2>&1 || die "--bundle needs python3"
  [ -f "$BUNDLER" ] || die "cannot find ${BUNDLER}"
  if [ "$MODE" = "bundle-check" ]; then
    exec python3 "$BUNDLER" --check
  fi
  log "building runtime-only bundle"
  if [ "$BUNDLE_ZIP" -eq 1 ]; then
    python3 "$BUNDLER" --out "$BUNDLE_OUT" --zip
  else
    python3 "$BUNDLER" --out "$BUNDLE_OUT"
  fi
  exit $?
fi

# Resolve the destination. An existing skill directory is never silently
# replaced: the user is told, and asked, because a skill directory can hold
# promoted local skills that a blind overwrite would destroy.
detect_target() {
  case "$MODE" in
    target) printf '%s' "$TARGET" ;;
    project) printf '%s' "$TARGET" ;;
    global)
      for candidate in "${GLOBAL_CANDIDATES[@]}"; do
        if [ -d "$candidate" ]; then printf '%s' "$candidate"; return 0; fi
      done
      # No known directory exists. Create the first one rather than inventing a
      # path, so the result is somewhere a runtime actually looks.
      printf '%s' "${GLOBAL_CANDIDATES[0]}"
      ;;
  esac
}

DEST_ROOT="$(detect_target)"
DEST="${DEST_ROOT%/}/${SKILL_NAME}"

log "source:      ${SOURCE_DIR}"
log "destination: ${DEST}"

if [ "$MODE" = "project" ] || [ "$MODE" = "target" ]; then
  mkdir -p "$DEST_ROOT" 2>/dev/null || die "cannot create ${DEST_ROOT}"
  log "mode:        project-local"
else
  log "mode:        user-global"
fi

# Refuse to clobber. This is the one place the script would lose data, so it
# stops rather than guessing.
if [ -e "$DEST" ]; then
  if [ -f "$DEST/SKILL.md" ] && cmp -s "${DEST}/SKILL.md" "${SOURCE_DIR}/SKILL.md" 2>/dev/null; then
    log "status:      already installed and identical, nothing to do"
    exit 0
  fi
  if [ "$YES" -eq 1 ]; then
    die "${DEST} already exists and differs; move it aside, then re-run"
  fi
  printf '%s\n' "${DEST} already exists." >&2
  printf 'Replace it? This deletes the existing directory. [y/N] ' >&2
  read -r reply </dev/tty || reply=""
  case "$reply" in
    y|Y|yes|YES) log "replacing ${DEST}" ;;
    *) die "aborted; nothing was changed" ;;
  esac
  rm -rf "$DEST"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  log "dry run:     would copy the skill to ${DEST}"
  [ "$PRUNE" -eq 1 ] && log "dry run:     would omit ${PRUNABLE[*]}"
  exit 0
fi

mkdir -p "$DEST"
cp -R "${SOURCE_DIR}/." "$DEST/"

if [ "$PRUNE" -eq 1 ]; then
  for dir in "${PRUNABLE[@]}"; do
    rm -rf "${DEST:?}/${dir}"
  done
  for file in "${PRUNABLE_FILES[@]}"; do
    rm -f "${DEST:?}/${file}"
  done
  # Keep the tool: it is small, and it is how a user verifies what they installed.
  log "pruned:      ${PRUNABLE[*]} ${PRUNABLE_FILES[*]} (pass --all to keep them)"
fi

# A skill with no SKILL.md is not a skill. Verify rather than assume the copy
# worked, because a partial copy is the failure mode here that would otherwise
# surface later as a silent discovery miss.
[ -f "${DEST}/SKILL.md" ] || { rm -rf "$DEST"; die "install produced no SKILL.md; rolled back"; }
[ -f "${DEST}/references/triage.md" ] || { rm -rf "$DEST"; die "install produced an incomplete reference tree; rolled back"; }

if command -v python3 >/dev/null 2>&1; then
  if python3 "${DEST}/tools/validate-skills.py" "$DEST" >/dev/null 2>&1; then
    log "verified:    structure valid"
  else
    warn "structure check did not pass; run: python3 ${DEST}/tools/validate-skills.py ${DEST}"
  fi
fi

log ""
log "installed to ${DEST}"
log ""
log "Next:"
log "  1. Restart the agent runtime so it rediscovers skills."
log "  2. Confirm discovery, then try a request that needs the kernel —"
log "     something open-ended or multi-step. A trivial request should NOT"
log "     trigger it; that is correct behaviour, not a failure."
