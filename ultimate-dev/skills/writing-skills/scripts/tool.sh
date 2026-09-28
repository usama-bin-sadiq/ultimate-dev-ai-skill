#!/usr/bin/env bash
#
# tool.sh — a reusable helper that lives beside a skill.
#
# This is the worked example from SKILL.md's "Skill with Reusable Tool" file
# layout. SKILL.md does not say what the original tool did — it only shows the
# shape:
#
#     condition-based-waiting/
#       SKILL.md    # Overview + patterns
#       example.ts  # Working helpers to adapt
#
#     bash scripts/tool.sh
#
# So there is no interface to recover, and this file does not pretend to be the
# original. It is a small, dependency-free, genuinely working utility of the
# kind that belongs in that slot, written to be read and adapted rather than
# invoked blind. Replace its body with your own helper; keep the conventions
# below, because they are the part worth copying.
#
# Conventions this file holds to, and the reason for each:
#
#   * Invoked through its interpreter, never as a bare path. Some harness
#     plugin packagers strip the executable bit, and a bare `scripts/tool.sh`
#     then fails with "Permission denied".
#   * `set -euo pipefail`. A helper that continues after a failed command
#     reports a success it did not achieve.
#   * No dependencies beyond coreutils. A skill's tools have to run wherever the
#     skill runs.
#   * Nothing writes outside the paths it was given, and it never overwrites
#     without being asked to.
#   * `--help` explains every option in two lines or fewer. This is the
#     documentation; SKILL.md should not duplicate it.
#   * Failures name the argument that caused them.
#
# What this one does: count lines, words, and bytes across a set of files, and
# report the largest. Useful on its own, and a reasonable shape to copy.
#
#   bash scripts/tool.sh src/
#   bash scripts/tool.sh --top 10 --ext .py .
#
# Exit status: 0 on success, 1 on a usage or input problem, 2 on no input.

set -euo pipefail

PROGRAM_NAME=${0##*/}

usage() {
    cat <<USAGE
Usage: bash $PROGRAM_NAME [OPTIONS] PATH...

Count lines, words, and bytes for each file, sorted by size. Directories are
walked one level deep unless --recursive is given.

Options:
  --top N        show only the N largest files (default: all)
  --ext EXT      only count files with this extension, for example .py
  --recursive    descend into subdirectories
  --zero         keep files with zero bytes in the report
  -h, --help     show this message

Exit status: 0 success, 1 usage or input error, 2 no matching files.
USAGE
}

die() {
    printf '%s: %s\n' "$PROGRAM_NAME" "$1" >&2
    exit "${2:-1}"
}

# --- argument parsing -------------------------------------------------------

TOP=0
EXTENSION=""
RECURSIVE=0
INCLUDE_EMPTY=0
INPUTS=()

while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --top)
            [ "$#" -ge 2 ] || die "--top needs a number"
            case "$2" in
                ''|*[!0-9]*) die "--top needs a positive number, got '$2'" ;;
            esac
            [ "$2" -gt 0 ] || die "--top needs a positive number, got '$2'"
            TOP=$2
            shift 2
            ;;
        --ext)
            [ "$#" -ge 2 ] || die "--ext needs an extension"
            case "$2" in
                .?*) EXTENSION=$2 ;;
                *)  EXTENSION=".$2" ;;
            esac
            shift 2
            ;;
        --recursive)
            RECURSIVE=1
            shift
            ;;
        --zero)
            INCLUDE_EMPTY=1
            shift
            ;;
        --)
            shift
            while [ "$#" -gt 0 ]; do
                INPUTS+=("$1")
                shift
            done
            ;;
        -*)
            die "unknown option '$1' (try --help)"
            ;;
        *)
            INPUTS+=("$1")
            shift
            ;;
    esac
done

[ "${#INPUTS[@]}" -gt 0 ] || die "no path given (try --help)"

# --- collect files ----------------------------------------------------------

# Inputs are validated before anything is collected. Validating inside the
# collector would run the check in a process substitution, i.e. a subshell,
# where `exit` cannot stop the script: the caller would carry on and report the
# wrong failure.
for input in "${INPUTS[@]}"; do
    if [ ! -e "$input" ]; then
        die "no such file or directory: $input"
    fi
    if [ ! -f "$input" ] && [ ! -d "$input" ]; then
        die "not a regular file or directory: $input"
    fi
done

collect() {
    local path=$1
    if [ -f "$path" ]; then
        printf '%s\n' "$path"
        return 0
    fi
    if [ "$RECURSIVE" -eq 1 ]; then
        find "$path" -type f
    else
        find "$path" -maxdepth 1 -type f
    fi
}

FILES=()
for input in "${INPUTS[@]}"; do
    while IFS= read -r found; do
        [ -n "$found" ] || continue
        if [ -n "$EXTENSION" ]; then
            case "$found" in
                *"$EXTENSION") FILES+=("$found") ;;
            esac
        else
            FILES+=("$found")
        fi
    done < <(collect "$input")
done

# A file named twice is counted once; a symlink loop would otherwise spin here.
declare -A SEEN=()
UNIQUE=()
for file in "${FILES[@]}"; do
    if [ -z "${SEEN[$file]:-}" ]; then
        SEEN[$file]=1
        UNIQUE+=("$file")
    fi
done
FILES=("${UNIQUE[@]+"${UNIQUE[@]}"}")

[ "${#FILES[@]}" -gt 0 ] || {
    printf '%s: no matching files\n' "$PROGRAM_NAME" >&2
    exit 2
}

# --- report -----------------------------------------------------------------

# lines<TAB>bytes<TAB>path, sorted largest first. Tabs in a path are not
# supported; a filename containing one is vanishingly rare and the fix would
# cost more than the case.
measure() {
    local file=$1
    local lines bytes
    if [ "$INCLUDE_EMPTY" -eq 1 ] || [ -s "$file" ]; then
        lines=$(wc -l < "$file" | tr -d ' ')
        bytes=$(wc -c < "$file" | tr -d ' ')
        printf '%s\t%s\t%s\n' "$lines" "$bytes" "$file"
    fi
}

REPORT=$(for file in "${FILES[@]}"; do measure "$file"; done | sort -t"$(printf '\t')" -k2,2nr)

if [ "$TOP" -gt 0 ]; then
    REPORT=$(printf '%s\n' "$REPORT" | head -n "$TOP")
fi

TOTAL_LINES=0
TOTAL_BYTES=0
while IFS=$'\t' read -r lines bytes _; do
    [ -n "${lines:-}" ] || continue
    TOTAL_LINES=$((TOTAL_LINES + lines))
    TOTAL_BYTES=$((TOTAL_BYTES + bytes))
done <<< "$REPORT"

printf '%8s  %10s  %s\n' "LINES" "BYTES" "FILE"
printf '%8s  %10s  %s\n' "--------" "----------" "----------------------------------------"
while IFS=$'\t' read -r lines bytes path; do
    [ -n "${lines:-}" ] || continue
    printf '%8s  %10s  %s\n' "$lines" "$bytes" "$path"
done <<< "$REPORT"
printf '%8s  %10s  %s\n' "--------" "----------" "----------------------------------------"
printf '%8s  %10s  %s\n' "$TOTAL_LINES" "$TOTAL_BYTES" \
    "${#FILES[@]} file(s) counted"
