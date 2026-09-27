#!/bin/sh
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown Model"')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
worktree=$(echo "$input" | jq -r '.worktree.name // empty')
total_cost=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')
current_dir=$(echo "$input" | jq -r '.worktree.original_cwd // .workspace.current_dir // .cwd // ""')
rl_5h_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' | awk '{printf "%.0f", $1}')
rl_5h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
rl_7d_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
rl_7d_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

# Token consumption: input + output tokens vs context window size
tok_in=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
tok_out=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
tok_total=$(( tok_in + tok_out ))
tok_max=$(echo "$input" | jq -r '.context_window.context_window_size // 1')

format_tokens() {
  num="$1"
  if [ "$num" -ge 1000 ]; then
    printf "%s" $(( num / 1000 ))k
  else
    printf "%s" "$num"
  fi
}

make_context_bar() {
  pct="$1"
  width=20
  filled=$(( pct * width / 100 ))
  [ "$filled" -gt "$width" ] && filled="$width"
  empty=$(( width - filled ))
  bar=""
  i=0
  while [ $i -lt "$filled" ]; do bar="${bar}█"; i=$(( i + 1 )); done
  while [ $i -lt "$width" ];  do bar="${bar}░"; i=$(( i + 1 )); done
  printf "%s" "$bar"
}

if [ -n "$used" ]; then
  used_display=$(printf "%.0f" "$used")
  usage_str="${used_display}%"
else
  usage_str="0%"
fi

# Only show worktree if one exists

GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

git_str=""
if git rev-parse --git-dir > /dev/null 2>&1; then
  branch=$(git branch --show-current 2>/dev/null)
  [ -z "$branch" ] && branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  staged=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
  modified=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')

  git_str="$branch"
  [ "$staged" -gt 0 ] && git_str="${git_str} $(printf "${GREEN}+${staged}${RESET}")"
  [ "$modified" -gt 0 ] && git_str="${git_str} $(printf "${YELLOW}~${modified}${RESET}")"
else
  git_str="no branch"
fi


case "$total_cost" in
  ''|empty|null)
    block_str="\$0.00"
    ;;
  *)
    cost_display=$(awk "BEGIN { printf \"%.2f\", $total_cost }")
    block_str="\$${cost_display}"
    ;;
esac

make_bar() {
  pct="$1"
  width=10
  filled=$(( pct * width / 100 ))
  empty=$(( width - filled ))
  bar=""
  i=0
  while [ $i -lt $filled ]; do bar="${bar}█"; i=$(( i + 1 )); done
  while [ $i -lt $width ];  do bar="${bar}░"; i=$(( i + 1 )); done
  printf "%s" "$bar"
}

format_rl() {
  pct="$1"
  reset_ts="$2"
  label="$3"
  [ -z "$pct" ] && return
  if [ "$pct" -ge 90 ]; then color="$RED"
  elif [ "$pct" -ge 70 ]; then color="$YELLOW"
  else color="$GREEN"
  fi
  reset_time=$(date -r "$reset_ts" "+%-I:%M%p" 2>/dev/null || date -d "@$reset_ts" "+%-I:%M%p" 2>/dev/null)
  bar=$(make_bar "$pct")
  printf "${color}${label} ${bar} ${pct}%% resets ${reset_time}${RESET}"
}

repo_root=$(cd "$current_dir" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null || pwd)
dir_display=$(basename "$repo_root")
context_bar=$(make_context_bar "${used_display:-0}")
tok_display=$(format_tokens "$tok_total")/$(format_tokens "$tok_max")
# Build output conditionally based on available data
output="${model} | [${context_bar}] ${used_display}% | ${tok_display} | ${block_str} | ${dir_display}"
if [ -n "$worktree" ]; then
  output="${output} | ${worktree}"
fi
output="${output} | ${git_str}"
printf "%s" "$output"
