#!/usr/bin/env bash
# Measure the tree with a validator this session did not write.
#
# Why this exists: the validator in tools/ has been edited several times while its
# own output was being used as evidence that the work was good. That is a conflict
# of interest, and it means "the error count fell" is not a measurement of the
# content -- it is a measurement of the content *and* the instrument.
#
# So: pin the validator to a commit, run it against the current tree, and report
# both numbers. The pinned one is the one to quote. The delta between the two
# validators is the part of the improvement that came from changing the instrument
# rather than the tree, and it should be stated every time.
#
#   ./tools/baseline-check.sh                 # default pin
#   ./tools/baseline-check.sh <commit>        # pin to a specific commit
#   ./tools/baseline-check.sh <commit> --tree # also measure that commit's tree
#
# The default pin is 225266d, the last commit before this session's work began.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN="${1:-225266d}"
WITH_TREE=0
[[ "${2:-}" == "--tree" ]] && WITH_TREE=1

PINNED="$ROOT/tools/.baseline-validator.py"

cleanup() { rm -f "$PINNED"; }
trap cleanup EXIT

if ! git -C "$ROOT" cat-file -e "$PIN:ultimate-dev/tools/validate-skills.py" 2>/dev/null; then
  echo "error: $PIN has no ultimate-dev/tools/validate-skills.py" >&2
  exit 2
fi

git -C "$ROOT" show "$PIN:ultimate-dev/tools/validate-skills.py" > "$PINNED" || exit 2

count() {  # count <validator-path>
  ( cd "$ROOT" && rm -rf tools/__pycache__ \
    && python3 "$1" --strict 2>&1 | grep -cE '^ *error:' )
}

CURRENT=$(count tools/validate-skills.py)
BASELINE=$(count "$PINNED")

printf '  validator pinned to %s (%s lines)\n' "$PIN" "$(wc -l < "$PINNED" | tr -d ' ')"
printf '  %-46s %s\n' "errors, pinned validator, current tree:" "$BASELINE"
printf '  %-46s %s\n' "errors, current validator, current tree:" "$CURRENT"
printf '  %-46s %s\n' "difference attributable to the instrument:" "$(( CURRENT - BASELINE ))"

if [[ "$WITH_TREE" == "1" ]]; then
  WT="$(mktemp -d)/wt"
  git -C "$ROOT" worktree add -q --detach "$WT" "$PIN" 2>/dev/null
  cp "$PINNED" "$WT/ultimate-dev/tools/.baseline-validator.py"
  ( cd "$WT/ultimate-dev" && rm -rf tools/__pycache__ \
    && python3 tools/.baseline-validator.py --strict 2>&1 | grep -cE '^ *error:' ) > /tmp/.bc_old
  OLD=$(cat /tmp/.bc_old); rm -f /tmp/.bc_old
  git -C "$ROOT" worktree remove --force "$WT" 2>/dev/null
  printf '  %-46s %s\n' "errors, pinned validator, tree at $PIN:" "$OLD"
  printf '  %-46s %s\n' "REDUCTION ATTRIBUTABLE TO CONTENT:" "$(( OLD - BASELINE ))"
  printf '\n  Quote the content reduction. The instrument difference (%s) is not a fix.\n' \
    "$(( CURRENT - BASELINE ))"
fi
