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

MODE=""
TARGET=""
YES=0
PRUNE=1
DRY_RUN=0
BUNDLE_OUT="dist"
BUNDLE_ZIP=0
FORCE_INTERACTIVE=0
# Set when the caller names a destination or a bundle operation. It is what makes
# the script non-interactive: a flag is a statement of intent, and a script that
# stops to ask about an intent that was already stated is a script that hangs CI.
EXPLICIT=0

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
  -i, --interactive     ask where to install and what to include, even on a tty
  -h, --help            this message

With no options on a terminal, this runs an interactive installer that asks two
questions -- where to install, and whether to keep the documentation -- and shows
the plan before writing anything. Supply any option and it runs unattended, so
the same script serves a person and a CI job.

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
    --global)   MODE="global"; EXPLICIT=1; shift ;;
    --project)  MODE="project"; EXPLICIT=1; shift
                TARGET="${1:-.}"; [ $# -gt 0 ] && shift || true ;;
    --target)   MODE="target"; EXPLICIT=1; shift
                [ $# -gt 0 ] || die "--target needs a directory"
                TARGET="$1"; shift ;;
    --all)      PRUNE=0; EXPLICIT=1; shift ;;
    --bundle)   MODE="bundle"; EXPLICIT=1; shift
                BUNDLE_OUT="${1:-dist}"; [ $# -gt 0 ] && shift || true ;;
    --bundle-zip) MODE="bundle"; BUNDLE_ZIP=1; EXPLICIT=1
                BUNDLE_OUT="${BUNDLE_OUT:-dist}"; shift ;;
    --check-bundle) MODE="bundle-check"; EXPLICIT=1; shift ;;
    --yes|-y)   YES=1; shift ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -i|--interactive) FORCE_INTERACTIVE=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    *)          die "unknown option: $1 (try --help)" ;;
  esac
done

[ -d "$SOURCE_DIR" ] || die "cannot find ${SOURCE_DIR}; run install.sh from the repository root"

# ---------------------------------------------------------------------------
# Interactive installer
#
# Runs when there is a terminal and the caller named no destination. Two
# questions, both with a default, and the plan is printed before anything is
# written. The point is not politeness: the two choices here are the two a user
# gets wrong most often, and both are irreversible enough to be worth one
# question. Which skill directory a runtime reads is runtime-specific, and
# guessing wrong produces an install that silently never loads.
#
# Everything here is skipped the moment a flag appears, so `install.sh --target X`
# in a pipeline behaves exactly as it always did.
# ---------------------------------------------------------------------------

have_tty() { [ -t 0 ] && [ -t 1 ]; }

# ask <variable-name> <prompt> <default> -- reads into the named variable.
ask() {
  local __var="$1" __prompt="$2" __default="$3" __reply=""
  printf '%s' "$__prompt" >&2
  if [ -n "$__default" ]; then
    printf ' [%s] ' "$__default" >&2
  else
    printf ' ' >&2
  fi
  if ! IFS= read -r __reply; then
    # EOF: a closed stdin is not consent. Take the default and say so.
    printf '\n' >&2
    warn "no input available; using the default for: ${__prompt}"
    printf -v "$__var" '%s' "$__default"
    return 0
  fi
  [ -n "$__reply" ] || __reply="$__default"
  printf -v "$__var" '%s' "$__reply"
}

existing_global() {
  local candidate
  for candidate in "${GLOBAL_CANDIDATES[@]}"; do
    [ -d "$candidate" ] && { printf '%s' "$candidate"; return 0; }
  done
  return 1
}

existing_project() {
  local candidate
  for candidate in "${PROJECT_CANDIDATES[@]}"; do
    [ -d "$candidate" ] && { printf '%s' "$candidate"; return 0; }
  done
  return 1
}

wizard() {
  log ""
  log "ultimate-dev installer"
  log "====================="
  log ""
  log "The repository is about five times the size of the skill. A runtime"
  log "install keeps the kernel and drops the documentation, examples, and"
  log "evaluation corpus. Two questions, then the plan."
  log ""

  local choice default_global default_project
  default_global="$(existing_global || printf '%s' "${GLOBAL_CANDIDATES[0]}")"
  default_project="$(existing_project || printf '%s' "${PROJECT_CANDIDATES[0]}")"

  # A destination flag is a stated intent, so it becomes the wizard's default
  # rather than being overwritten by it. `install.sh --target X -i` used to throw
  # X away and install to the user-global directory, which is the worst possible
  # outcome: the command line said one thing and the machine did another.
  if [ -n "$MODE" ]; then
    log "  destination: given on the command line, kept as-is"
    log ""
  else
    log "  1) This user      ${default_global}"
    log "  2) This project   ${default_project}/   (in $(pwd))"
    log "  3) Somewhere else (type a path)"
    log ""
    ask choice "Where should the skill go?" "1"

    case "$choice" in
      1) MODE="global" ;;
      2) MODE="project"; TARGET="$(pwd)/${default_project}" ;;
      3) ask TARGET "Path to install into:" ""
          [ -n "$TARGET" ] || die "no path given; nothing was changed"
          MODE="target" ;;
      *) MODE="global" ;;
    esac
  fi

  log ""
  log "  1) Runtime only  - kernel, references, roles. Smallest."
  log "  2) Everything    - adds docs, examples, evaluation, research."
  log ""
  local contents
  ask contents "What should be installed?" "1"
  case "$contents" in
    2) PRUNE=0 ;;
    *) PRUNE=1 ;;
  esac

  # Show the plan. A confirmation that does not state what will happen is a
  # confirmation of nothing.
  local planned_root planned_dest size_note
  case "$MODE" in
    global) planned_root="$(existing_global || printf '%s' "${GLOBAL_CANDIDATES[0]}")" ;;
    *)      planned_root="$TARGET" ;;
  esac
  planned_dest="${planned_root%/}/${SKILL_NAME}"
  size_note="runtime only, about 400 KB"
  [ "$PRUNE" -eq 0 ] && size_note="everything, about 2.1 MB"

  log ""
  log "Plan"
  log "  from      ${SOURCE_DIR}"
  log "  to        ${planned_dest}"
  log "  contents  ${size_note}"
  log ""

  local go
  ask go "Proceed?" "y"
  case "$go" in
    y|Y|yes|YES) ;;
    *) die "aborted; nothing was changed" ;;
  esac
  log ""
}

if [ "$MODE" != "bundle" ] && [ "$MODE" != "bundle-check" ]; then
  if [ "$FORCE_INTERACTIVE" -eq 1 ] || { [ "$EXPLICIT" -eq 0 ] && have_tty; }; then
    if ! have_tty; then
      die "no terminal for the interactive installer; pass --global, --project DIR, or --target DIR"
    fi
    wizard
  fi
  # No destination chosen and no terminal: the old default, stated rather than
  # assumed, because a silent default is how an install lands somewhere the user
  # did not expect.
  [ -n "$MODE" ] || { MODE="global"; [ "$EXPLICIT" -eq 0 ] && warn "no terminal and no destination given; defaulting to --global"; }
fi

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
    *) return 1 ;;
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
