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

# Inform when the source is implausibly large for a runtime install.
#
# This is a warning, not a refusal, and the distinction is deliberate. Exclusion
# now happens at copy time, so the gigabyte is never written to the destination
# whichever mode is used -- the check exists to tell the user their source tree
# is unexpected, not to stop them building a bundle from it. A bundle from a
# large source is the correct operation, not a mistake, so the check is skipped
# for the modes that write nothing or write a pruned form.
check_source_size() {
  case "$MODE" in
    bundle|bundle-check) return 0 ;;
  esac
  if [ "$DRY_RUN" -eq 1 ]; then return 0; fi
  local mb; mb="$(source_mb "$SOURCE_DIR")"
  [ -z "$mb" ] && return 0
  if [ "$mb" -gt "$MAX_SOURCE_MB" ]; then
    warn "source tree is ${mb} MB, over the ${MAX_SOURCE_MB} MB a runtime install usually is."
    warn "That is normally a fetched catalogue: catalog/_src holds clones of upstream"
    warn "repositories. It is excluded from the copy either way, so the install stays"
    warn "small. If the size is unexpected, 'du -sh ultimate-dev/*' will show what is"
    warn "large. Set MAX_SOURCE_MB=<n> to change the threshold, or 0 to silence this."
  fi
}

# Windows: the script runs, but under a POSIX layer, and the paths the runtimes
# use there are the Windows ones. Saying so up front is cheaper than a user
# discovering it from a failed copy.
warn_platform() {
  case "$PLATFORM_ID" in
    windows-bash)
      warn "running under ${PLATFORM} (${PLATFORM_ID})."
      warn "Windows needs a POSIX layer: WSL, Git Bash, or MSYS. Native PowerShell"
      warn "or cmd.exe cannot run this script. Paths below are POSIX and are"
      warn "resolved inside that layer, not by Windows."
      ;;
    unsupported)
      warn "unrecognised platform '${PLATFORM}'. Continuing, because the script is"
      warn "POSIX bash and may still work, but the known-good set is macOS, Linux,"
      warn "and Windows under WSL, Git Bash, or MSYS."
      ;;
  esac
}

log()  { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# Size in megabytes, computed the same way everywhere. `du -sm` is not
# portable to BusyBox, and the fallback is the only path that must work on a
# machine with nothing installed but a shell.
source_mb() {
  local d="$1" kb
  if kb="$(du -sk "$d" 2>/dev/null | cut -f1)" && [ -n "$kb" ]; then
    printf '%s' "$(( kb / 1024 ))"
    return 0
  fi
  # No du. Walk it, counting bytes. Slow, correct, dependency-free.
  find "$d" -type f -exec cat {} + 2>/dev/null | wc -c | awk '{printf "%d", $1/1048576}'
}

# The bulk-copy is the failure mode on a large source. Copying first and
# deleting afterwards means the gigabyte is written to the destination before
# anything decides not to want it, which on a slow disk is minutes of the user
# watching a progress bar for a file that is about to be removed. Excluding at
# copy time is the difference.
copy_tree() {
  local src="$1" dst="$2"
  if command -v rsync >/dev/null 2>&1; then
    local ex=()
    local d
    for d in "${ALWAYS_PRUNE[@]}"; do
      [ "$PRUNE" -eq 1 ] || ex+=(--exclude "/${d}")
      ex+=(--exclude "/${d}")
    done
    if [ "$PRUNE" -eq 1 ]; then
      for d in "${PRUNABLE[@]}"; do ex+=(--exclude "/${d}"); done
      for d in "${PRUNABLE_FILES[@]}"; do ex+=(--exclude "/${d}"); done
    fi
    rsync -a --quiet "${ex[@]}" "$src/" "$dst/"
  else
    # No rsync: tar's exclude is available everywhere the script runs.
    local ex=()
    for d in "${ALWAYS_PRUNE[@]}"; do ex+=("--exclude=./${d}"); done
    if [ "$PRUNE" -eq 1 ]; then
      for d in "${PRUNABLE[@]}"; do ex+=("--exclude=./${d}"); done
      for d in "${PRUNABLE_FILES[@]}"; do ex+=("--exclude=./${d}"); done
    fi
    ( cd "$src" && tar -cf - "${ex[@]}" . ) | ( cd "$dst" && tar -xf - )
  fi
}

# Platform detection. The script is POSIX bash and that is a real constraint on
# Windows: it runs under WSL, Git Bash, or MSYS, and nowhere else. Saying which,
# and saying what to do when it is not one of those, is better than failing later
# with a syntax error three directories from the target.
PLATFORM="$(uname -s 2>/dev/null || echo unknown)"
case "$PLATFORM" in
  Darwin)          PLATFORM_ID="macos" ;;
  Linux)           PLATFORM_ID="linux" ;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM_ID="windows-bash" ;;
  *)               PLATFORM_ID="unsupported" ;;
esac

# Paths that are documentation or source specification rather than runtime.
# Pruning them keeps an install small; the kernel never loads them, and they are
# all preserved in the repository.
#
# `catalog` is here because it holds a fetched copy of upstream repositories --
# currently about 1.1 GB across thirty-six clones. It is source material for the
# research pipeline, not runtime, and an install that copied it would move a
# gigabyte into a directory the agent reads on every session. The index derived
# from it is kept; the clones are not.
PRUNABLE=(docs examples evaluation research knowledge catalog)
PRUNABLE_FILES=(ARCHITECTURE.md new-arch.md prd.md)

# Sub-paths pruned even under --all, because --all means "keep the
# documentation", not "ship a gigabyte of other people's git repositories".
ALWAYS_PRUNE=(catalog/_src)

# Refuse to start if the source is implausibly large for a runtime install. The
# check is a guard, not a policy: it fires on a fetch accident, not on a large
# skill, and --all exists for a user who genuinely wants everything.
MAX_SOURCE_MB="${MAX_SOURCE_MB:-200}"

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

  # The bundler refuses to classify a top-level directory it has not been told
  # about, which is correct behaviour and is why the fetched catalogue stops the
  # bundle. Rather than teach the bundler about a gigabyte of other people's
  # repositories, stage the pruned tree and bundle that. The catalogue is not
  # runtime, so its absence from the staging tree is the intent, not a loss.
  STAGE=""
  cleanup_stage() { [ -n "$STAGE" ] && [ -d "$STAGE" ] && rm -rf "$STAGE"; return 0; }
  trap cleanup_stage EXIT INT TERM

  STAGE="$(mktemp -d "${TMPDIR:-/tmp}/ultimate-dev-bundle.XXXXXX")"
  log "staging:     pruned tree, excluding ${ALWAYS_PRUNE[*]}"
  if ! copy_tree "$SOURCE_DIR" "$STAGE/ultimate-dev"; then
    die "could not stage the pruned tree"
  fi

  if [ "$MODE" = "bundle-check" ]; then
    ( cd "$STAGE/ultimate-dev" && exec python3 "tools/bundle-skill.py" --check )
  fi
  log "building runtime-only bundle"
  if [ "$BUNDLE_ZIP" -eq 1 ]; then
    ( cd "$STAGE/ultimate-dev" && python3 "tools/bundle-skill.py" \
        --out "$BUNDLE_OUT" --zip )
  else
    ( cd "$STAGE/ultimate-dev" && python3 "tools/bundle-skill.py" \
        --out "$BUNDLE_OUT" )
  fi
  rc=$?
  cleanup_stage
  trap - EXIT INT TERM
  exit $rc
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
warn_platform
check_source_size

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
  # A dry run reports; it never asks and never refuses. The clobber check used
  # to run first, which meant --dry-run prompted and exited 1 on any machine
  # with a differing install already in place -- the one situation where a user
  # most wants to see the plan before deciding.
  if [ "$DRY_RUN" -eq 1 ]; then
    log "dry run:     ${DEST} exists and differs; a real run would ask before replacing it"
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
  if [ "$PRUNE" -eq 1 ]; then
    log "dry run:     would omit ${PRUNABLE[*]}"
  else
    log "dry run:     keeping documentation; ${ALWAYS_PRUNE[*]} still excluded"
  fi
  exit 0
fi

mkdir -p "$DEST"
copy_tree "$SOURCE_DIR" "$DEST"

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
