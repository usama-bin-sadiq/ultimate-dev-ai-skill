#!/usr/bin/env bash
# Run the checks CI runs, before the commit is made rather than after the push
# is rejected.
#
# Why this exists
# ---------------
# Every check here already runs in .github/workflows/validate.yml. What CI does
# not do is tell you which commit introduced the failure, and by the time a job
# is red the push is already on the remote. The same 55 seconds spent here turns
# a rejected push into a rejected commit message.
#
# What it blocks on
# -----------------
# New problems, not all problems. The tree currently carries a known backlog of
# `--strict` warnings -- oversized SKILL.md files that a mechanical move cannot
# reduce without inventing structure. A hook that refuses every commit until
# that backlog is zero is a hook people bypass with --no-verify, and a bypassed
# hook is worse than no hook because it looks like it is working.
#
# So the gate is a regression gate. It compares this tree against HEAD, blocks on
# any new error or any new warning, and shows the backlog as context. The
# backlog is visible on every run and printed in full on request; it is never
# subtracted away or hidden.
#
# The baseline is the tree at HEAD, checked out into a throwaway git worktree.
# Nothing in the working tree is touched, stashed or reset.
#
# Usage
#   tools/pre-commit-check.sh            # fast gate, what the hook runs
#   tools/pre-commit-check.sh --full     # adds bundle build and fence parity
#   tools/pre-commit-check.sh --baseline # print the backlog, block on nothing
#
# Skip once with:  git commit --no-verify
# Always allowed:  git commit            (with the hook installed)

set -uo pipefail

# This file lives at <repo>/ultimate-dev/tools/, so the repository root is two
# levels up, not one. Getting this wrong is not a small mistake: SKILL_DIR then
# points at a directory that does not exist, every check inside it runs in
# nowhere, and the gate reports a clean tree because nothing was ever read.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILL_DIR="$REPO_ROOT/ultimate-dev"
MODE="fast"
BASELINE_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --full)     MODE="full" ;;
    --baseline) BASELINE_ONLY=1 ;;
    -h|--help)  sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)          echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; DIM=$'\033[2m'; OFF=$'\033[0m'
if [ ! -t 1 ]; then RED=""; GRN=""; YLW=""; DIM=""; OFF=""; fi

CACHE_DIR="$REPO_ROOT/.git/pre-commit-baseline"
mkdir -p "$CACHE_DIR"

WORKTREE=""
cleanup() { [ -n "$WORKTREE" ] && git -C "$REPO_ROOT" worktree remove --force "$WORKTREE" >/dev/null 2>&1; }
trap cleanup EXIT

# validate <skill-root> <report-out> -> echoes "errors warnings"
#
# The first parameter is the tree to check. It was accepted and then ignored in
# favour of the hardcoded $SKILL_DIR, so every "baseline" was really a second
# reading of the working tree -- which means the gate was comparing the tree
# against itself, and the difference was always zero.
validate() {
  local root="$1" out="$2"
  ( cd "$root" && python3 tools/validate-skills.py --strict ) >"$out" 2>&1
  local e w
  e=$(grep -cE '^[[:space:]]*error' "$out" || true)
  w=$(grep -c 'warning:' "$out" || true)
  printf '%s %s\n' "$e" "$w"
}

fails=0
note_fail() { echo "${RED}  FAIL${OFF}  $1"; fails=$((fails + 1)); }
note_pass() { echo "${GRN}  PASS${OFF}  $1"; }

echo "${DIM}pre-commit check${OFF} ${DIM}($MODE)${OFF}"
echo

# ---- 1. the CI gate: validator --strict, compared against HEAD --------------
HEAD_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo none)
CUR_OUT="$(mktemp)"; read -r CUR_E CUR_W <<<"$(validate "$SKILL_DIR" "$CUR_OUT")"

BASE_E=""; BASE_W=""
if [ "$HEAD_SHA" != "none" ]; then
  CACHE_E="$CACHE_DIR/$HEAD_SHA.errors"
  CACHE_W="$CACHE_DIR/$HEAD_SHA.warnings"
  if [ -f "$CACHE_E" ] && [ -f "$CACHE_W" ]; then
    BASE_E=$(cat "$CACHE_E"); BASE_W=$(cat "$CACHE_W")
  else
    # git archive, not git worktree add.
    #
    # A worktree needs the index, and a pre-commit hook runs while the commit
    # that invoked it holds the index lock, so the worktree command failed and
    # the baseline silently stayed at its initial value of zero. The gate then
    # compared the tree against nothing, printed "39 warnings, 0 at HEAD (+39)",
    # and would have blocked every commit for as long as the backlog existed.
    #
    # git archive reads committed objects and never touches the index, so it
    # works under the lock.
    SNAP="$(mktemp -d)"
    if git -C "$REPO_ROOT" archive HEAD 2>/dev/null | tar -x -C "$SNAP" 2>/dev/null; then
      if [ -d "$SNAP/ultimate-dev" ]; then
        BASE_OUT="$(mktemp)"
        read -r BASE_E BASE_W <<<"$(validate "$SNAP/ultimate-dev" "$BASE_OUT")"
        printf '%s' "$BASE_E" > "$CACHE_E"
        printf '%s' "$BASE_W" > "$CACHE_W"
        rm -f "$BASE_OUT"
      fi
    fi
    rm -rf "$SNAP"
  fi
else
  BASE_E=0; BASE_W=0   # first commit; there is nothing to compare against
fi

# A baseline that could not be read means the gate cannot tell a new problem
# from an existing one, and a gate that cannot tell the difference is noise.
# Say so rather than quietly comparing against zero.
if [ -z "$BASE_E" ]; then
  echo "${RED}  FAIL${OFF}  could not read the baseline at HEAD (${HEAD_SHA:0:9})"
  echo "          Without it this gate cannot separate a new error from an"
  echo "          existing warning, so the comparison did not run."
  echo "          Commit with --no-verify once, or remove .git/pre-commit-baseline"
  echo "          and try again."
  rm -f "$CUR_OUT"
  exit 1
fi

if [ "$BASELINE_ONLY" = 1 ]; then
  echo "  baseline at HEAD ($HEAD_SHA): $BASE_E errors, $BASE_W warnings"
  echo "  working tree:                 $CUR_E errors, $CUR_W warnings"
  echo
  if [ "$CUR_W" -gt 0 ] && [ -s "$CUR_OUT" ]; then
    echo "${YLW}known backlog -- ${CUR_W} warning(s)${OFF}"
    grep 'warning:' "$CUR_OUT" | sed -E 's|.*/ultimate-dev/ultimate-dev/||' | sed 's/^/    /'
  fi
  rm -f "$CUR_OUT"
  exit 0
fi

if [ "$CUR_E" -gt "$BASE_E" ]; then
  note_fail "validator: $CUR_E errors, $BASE_E at HEAD (+$((CUR_E - BASE_E)))"
  grep -E '^[[:space:]]*error' "$CUR_OUT" | sed -E 's|.*/ultimate-dev/ultimate-dev/||' \
    | head -15 | sed 's/^/          /'
else
  note_pass "validator: $CUR_E errors (same as HEAD)"
fi

if [ "$CUR_W" -gt "$BASE_W" ]; then
  note_fail "validator: $CUR_W warnings, $BASE_W at HEAD (+$((CUR_W - BASE_W)))"
  grep 'warning:' "$CUR_OUT" | sed -E 's|.*/ultimate-dev/ultimate-dev/||' \
    | head -15 | sed 's/^/          /'
else
  note_pass "validator: $CUR_W warnings ($((CUR_W - BASE_W)) vs HEAD)"
  if [ "$CUR_W" -gt 0 ]; then
    echo "${DIM}          $CUR_W pre-existing warning(s) carried forward; not introduced here${OFF}"
  fi
fi
rm -f "$CUR_OUT"

# ---- 2. the rest of the fast CI steps --------------------------------------
run_step() {
  local label="$1"; shift
  local out; out="$(mktemp)"
  if ( cd "$SKILL_DIR" && "$@" ) >"$out" 2>&1; then
    note_pass "$label"
  else
    note_fail "$label"
    tail -6 "$out" | sed 's/^/          /'
  fi
  rm -f "$out"
  rm -rf "$SKILL_DIR/tools/__pycache__"
}

run_step "sibling imports"      python3 tools/check-sibling-imports.py .
run_step "evals up to date"     python3 tools/build-evals.py --check
run_step "fixtures"             python3 tools/build-fixtures.py
run_step "progressive-disclosure self-test" python3 tools/test-progressive-disclosure.py
run_step "workflow-auth self-test"  python3 tools/test-workflow-auth.py
run_step "changelog-generator self-test" python3 tools/test-changelog-generator.py
run_step "routing-assertion self-test" python3 tools/test-routing-assertions.py
run_step "marker-drift self-test"      python3 tools/test-marker-drift.py
run_step "run-state self-test"          python3 tools/test-run-state.py
run_step "mode-cost self-test"          python3 tools/test-mode-cost.py
run_step "provider-neutrality self-test"   python3 tools/test-provider-neutral.py
run_step "oracle-coverage self-test"      python3 tools/test-oracle-coverage.py

# The guard itself, not just its self-test. A self-test proves the checker
# works; running the checker proves the workflows are clean. Both, or the
# first one is a test of a tool nobody invokes.
#
# It is here rather than in --full because the release path is the thing that
# was broken three times, and a check that only runs when someone remembers
# --full is the same class of bug one level down.
if [ -d "$REPO_ROOT/.github/workflows" ]; then
  run_step "workflow credentials" python3 tools/check-workflow-auth.py
fi

# ---- 3. syntax gate over the tools ------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  syn=0
  while IFS= read -r f; do
    python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$f" 2>/dev/null || {
      echo "${RED}  FAIL${OFF}  syntax: ${f#$REPO_ROOT/}"; syn=1; fails=$((fails + 1)); }
  done < <(find "$SKILL_DIR/tools" -name '*.py' -type f | sort)
  [ "$syn" -eq 0 ] && note_pass "every tool parses"
fi

# ---- 4. --full: the slow checks ---------------------------------------------
if [ "$MODE" = "full" ]; then
  run_step "fence reader parity" python3 tools/test-fence-parity.py

  BUNDLE_OUT="$(mktemp)"
  rm -rf "$SKILL_DIR/dist"
  if ( cd "$SKILL_DIR" && python3 tools/bundle-skill.py --out dist ) >"$BUNDLE_OUT" 2>&1; then
    note_pass "bundle builds"
    SANDBOX="$(mktemp -d)"
    cp -R "$SKILL_DIR/dist/ultimate-dev" "$SANDBOX/ultimate-dev"
    if ( cd "$SKILL_DIR" && python3 tools/validate-skills.py "$SANDBOX/ultimate-dev" ) \
         >"$BUNDLE_OUT" 2>&1; then
      note_pass "the bundle itself validates"
    else
      note_fail "the bundle does not validate"
      grep -E '^[[:space:]]*error' "$BUNDLE_OUT" | head -10 | sed 's/^/          /'
    fi
    rm -rf "$SANDBOX"
  else
    note_fail "bundle does not build"
    grep -iE 'error|dangling|does not resolve' "$BUNDLE_OUT" | head -8 | sed 's/^/          /'
  fi
  rm -f "$BUNDLE_OUT"
  rm -rf "$SKILL_DIR/dist" "$SKILL_DIR/tools/__pycache__"
fi

# ---- 5. emoji, which is a grep and belongs here ------------------------------
if git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  found=$(git -C "$REPO_ROOT" grep -nIP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' -- \
    'ultimate-dev/SKILL.md' 'ultimate-dev/references/' 'ultimate-dev/knowledge/' \
    'ultimate-dev/docs/' 'ultimate-dev/evaluation/' \
    ':!ultimate-dev/docs/PERSONA-TEMPLATE.md' ':!ultimate-dev/docs/PERSONAS.md' \
    2>/dev/null || true)
  if [ -z "$(printf '%s' "$found" | tr -d '[:space:]')" ]; then
    note_pass "no emoji in the kernel specification documents"
  else
    note_fail "emoji in a kernel specification document"
    printf '%s\n' "$found" | head -8 | cut -c1-110 | sed 's/^/          /'
  fi
fi

echo
if [ "$fails" -eq 0 ]; then
  echo "${GRN}all checks passed${OFF}"
  exit 0
fi
echo "${RED}${fails} check(s) failed${OFF}"
echo
echo "  This gate blocks NEW errors and NEW warnings, not the ${CUR_W} already in the tree."
echo "  See the backlog with:  tools/pre-commit-check.sh --baseline"
echo "  To commit anyway:     git commit --no-verify   (and say why)"
exit 1
