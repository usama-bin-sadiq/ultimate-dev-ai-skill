#!/usr/bin/env bash
# Fetch the upstream catalogue into catalog/_src.
#
# The clones are deliberately NOT committed. They are a few hundred megabytes of
# other people's repositories, they contain their own .git directories, and they
# are fully reproducible from the list below. What IS committed is the derived
# output: catalog/INDEX.json and catalog/OVERLAPS.json, which say what was
# fetched and what it turned out to be.
#
#   ./fetch-catalog.sh              fetch everything
#   ./fetch-catalog.sh --list       show the list and exit
#   ./fetch-catalog.sh --index      fetch, then index and dedupe
#
# A repository that is an index rather than a collection, or that is dominated by
# vendor wrappers, is still fetched. The point of the corpus is to be measured,
# and a repository's reputation is not a measurement.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/catalog/_src"
SKILL_ROOT="$ROOT"

# repo, optional reason it is expected to be thin. The reason is recorded so a
# low yield later is a prediction that was met rather than a surprise.
REPOS=(
  "anthropics/skills|first-party"
  "anthropics/claude-plugins-official|mixed: 44% instruction-bearing"
  "openai/skills|deprecated upstream"
  "google-gemini/gemini-cli|2 builtin skills"
  "google/skills|148 unique, ~85% vendor"
  "vercel-labs/agent-skills|9 stack-bound"
  "huggingface/skills|vendor-bound, 0% cross-cutting"
  "VoltAgent/awesome-agent-skills|index only, 0 local skills"
  "skillmatic-ai/awesome-agent-skills|index only, 0 local skills"
  "subinium/awesome-claude-code|index only"
  "ComposioHQ/awesome-claude-skills|96% vendor wrappers"
  "oaustegard/claude-skills|highest cross-cutting density surveyed"
  "secondsky/claude-skills|mixed, low density"
  "tddworks/claude-skills|small, has a description mismatch"
  "obra/superpowers|15 skills, densest procedure-per-byte"
  "mattpocock/skills|38 skills, tracker-bound"
  "garrytan/gstack|54 real, hook-dependent"
  "addyosmani/agent-skills|25 skills, most portable"
  "kepano/obsidian-skills|domain-bound"
  "coreyhaines31/marketingskills|8% cross-cutting"
  "alirezarezvani/claude-skills|~388, ~12 with real judgement"
  "eristoddle/agent-skills|2 files rewrite user agent config"
  "adamdroberts/agent-skills|2 files, tool-neutral"
  "chriscox/agent-skills|2 skills, both tracker-bound"
  "heyimcarlos/agent-skills|the one bulk-importable repo"
  "TheQtCompanyRnD/agent-skills|100% domain"
  "msitarzewski/agency-agents|323 role prompts"
  "muratcankoylan/Agent-Skills-for-Context-Engineering|densest cross-cutting"
  "DietrichGebert/ponytail|6 skills, anti-over-engineering"
  "anthropics/financial-services|domain, vendor MCP"
  "Leonxlnx/taste-skill|design domain"
  "Lum1104/understand-anything|codebase knowledge graph"
  "nextlevelbuilder/ui-ux-pro-max-skill|design domain"
  "Panniantong/Agent-Reach|1 skill"
  "mvanhorn/last30days-skill|paid third-party APIs"
)

if [[ "${1:-}" == "--list" ]]; then
  printf '%-52s %s\n' "REPOSITORY" "EXPECTATION"
  for r in "${REPOS[@]}"; do
    printf '%-52s %s\n' "${r%%|*}" "${r#*|}"
  done
  exit 0
fi

mkdir -p "$DEST"
ok=0; skipped=0; failed=0
for entry in "${REPOS[@]}"; do
  repo="${entry%%|*}"
  name="$(printf '%s' "$repo" | tr '/' '_')"
  target="$DEST/$name"
  if [[ -d "$target/.git" ]]; then
    skipped=$((skipped + 1)); continue
  fi
  if timeout 300 git clone --depth 1 -q "https://github.com/$repo.git" "$target" 2>/dev/null; then
    skills="$(find "$target" -name SKILL.md 2>/dev/null | wc -l | tr -normal ' ')"
    size="$(du -sh "$target" 2>/dev/null | cut -f1)"
    printf '  OK    %-46s %6s %5s skills\n' "$repo" "$size" "$skills"
    ok=$((ok + 1))
  else
    printf '  FAIL  %-46s (not clonable)\n' "$repo"
    failed=$((failed + 1))
  fi
done

printf '\n  fetched %s, already present %s, failed %s, total on disk %s\n' \
  "$ok" "$skipped" "$failed" "$(du -sh "$DEST" 2>/dev/null | cut -f1)"

if [[ "${1:-}" == "--index" ]]; then
  printf '\n'
  python3 "$SKILL_ROOT/tools/index-catalog.py" --report
  printf '\n'
  python3 "$SKILL_ROOT/tools/dedupe-catalog.py"
fi
