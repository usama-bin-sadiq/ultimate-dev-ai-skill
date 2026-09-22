#!/bin/bash
# ultimate-dev v2.1.0 — Installer for macOS/Linux
# Usage: ./scripts/install.sh [--global|--project DIR|--uninstall|--yes|--help]
# https://www.gnu.org/software/bash/manual/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")/ultimate-dev"

# ─── Colors (ANSI-C quoting for portability) ────────────────
RED=$'\033[0;31m';  GREEN=$'\033[0;32m';  YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'; CYAN=$'\033[0;36m';  MAGENTA=$'\033[0;35m'
BOLD=$'\033[1m';    DIM=$'\033[2m';      NC=$'\033[0m'

# ─── Cleanup trap ───────────────────────────────────────────
cleanup() { printf '\e[?25h'; }  # show cursor on exit
trap cleanup EXIT

# ─── Helpers ────────────────────────────────────────────────
print_logo() {
    local ver
    ver="$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "2.1.0")"
    printf '\n'
    printf '  %s┌─────────────────────────────────────────────────────┐%s\n' "$CYAN" "$NC"
    printf '  %s│%s                                                     %s│%s\n' "$CYAN" "$NC" "$CYAN" "$NC"
    printf '  %s│%s            %s%s%sultimate-dev%s %sv%s%s                          %s│%s\n' \
        "$CYAN" "$NC" "$BOLD" "$MAGENTA" "" "$NC" "$DIM" "$ver" "$NC" "$CYAN" "$NC"
    printf '  %s│%s            %s─────────────────%s                          %s│%s\n' \
        "$CYAN" "$NC" "$DIM" "$NC" "$CYAN" "$NC"
    printf '  %s│%s  %sMaster Software Engineering Orchestrator%s              %s│%s\n' \
        "$CYAN" "$NC" "$MAGENTA" "$NC" "$CYAN" "$NC"
    printf '  %s│%s  %s120 agents • 17 skills • 45 modules • Any model%s    %s│%s\n' \
        "$CYAN" "$NC" "$DIM" "$NC" "$CYAN" "$NC"
    printf '  %s│%s                                                     %s│%s\n' "$CYAN" "$NC" "$CYAN" "$NC"
    printf '  %s└─────────────────────────────────────────────────────┘%s\n' "$CYAN" "$NC"
    printf '\n'
}

status()  { printf '  %s✔%s %s\n' "$GREEN" "$NC" "$1"; }
warn()    { printf '  %s⚠%s %s\n' "$YELLOW" "$NC" "$1"; }
err()     { printf '  %s✘%s %s\n' "$RED" "$NC" "$1"; }
info()    { printf '  %sℹ%s %s\n' "$CYAN" "$NC" "$1"; }
header()  { printf '\n  %s── %s ──%s\n' "${BOLD}${BLUE}" "$1" "$NC"; }

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --global        Install to ~/.agents/skills/ultimate-dev
  --project DIR   Install to DIR/.agents/skills/ultimate-dev
  --uninstall     Remove the installation
  --yes, -y       Skip confirmation prompt
  --help, -h      Show this help

Examples:
  $0                        # Interactive
  $0 --global               # All projects
  $0 --project ~/my-app     # One project
  $0 --global --yes         # Non-interactive
EOF
}

# ─── Numbered menu (reliable, portable) ─────────────────────
# Returns selection in MENU_RESULT
MENU_RESULT=""
menu_select() {
    local prompt="$1"
    shift
    local options=("$@")
    local count=${#options[@]}

    printf '\n'
    printf '  %s%s%s\n' "$BOLD" "$prompt" "$NC"
    printf '\n'

    for i in "${!options[@]}"; do
        printf '    %s%s)%s %s\n' "$BOLD" "$((i + 1))" "$NC" "${options[$i]}"
    done

    printf '\n'
    printf '  %sEnter number (1-%d):%s ' "$DIM" "$count" "$NC"

    local choice
    read -r choice

    # Validate
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$count" ]; then
        MENU_RESULT=$choice
        return 0
    else
        printf '  %s✘ Invalid choice. Please enter 1-%d.%s\n' "$RED" "$count" "$NC"
        return 1
    fi
}

# ─── Parse arguments ────────────────────────────────────────
SCOPE=""
PROJECT_DIR=""
UNINSTALL=false
AUTO_YES=false

while [ $# -gt 0 ]; do
    case "$1" in
        --global)    SCOPE="global"; shift ;;
        --project)   SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        --yes|-y)    AUTO_YES=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *)           err "Unknown option: $1"; usage; exit 1 ;;
    esac
done

print_logo

# ─── Uninstall ──────────────────────────────────────────────
if [ "$UNINSTALL" = true ]; then
    header "Uninstalling"
    TARGET="$HOME/.agents/skills/ultimate-dev"
    if [ -d "$TARGET" ]; then
        rm -rf "$TARGET"
        status "Removed $TARGET"
    else
        warn "Nothing to uninstall"
    fi
    exit 0
fi

# ─── Interactive mode ───────────────────────────────────────
if [ -z "$SCOPE" ]; then
    if [ "$AUTO_YES" = true ]; then
        SCOPE="global"
    else
        # Scope selection with retry on invalid input
        until menu_select "Where do you want to install?" \
            "Global    — ~/.agents/skills/ultimate-dev/" \
            "Project   — <project>/.agents/skills/ultimate-dev/"; do
            :
        done

        if [ "$MENU_RESULT" -eq 0 ]; then
            info "Cancelled."
            exit 0
        fi

        case "$MENU_RESULT" in
            1) SCOPE="global" ;;
            2)
                SCOPE="project"
                printf '\n'
                printf '  %sEnter project path:%s\n' "$CYAN" "$NC"
                printf '  %s(e.g., ~/my-app or . for current directory)%s\n' "$DIM" "$NC"
                printf '\n  '
                read -r PROJECT_DIR
                PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
                if [ ! -d "$PROJECT_DIR" ]; then
                    err "Directory not found: $PROJECT_DIR"
                    exit 1
                fi
                ;;
        esac
    fi
fi

# ─── Determine target ───────────────────────────────────────
if [ "$SCOPE" = "global" ]; then
    TARGET="$HOME/.agents/skills/ultimate-dev"
else
    PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
    TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
fi

# ─── Confirm ────────────────────────────────────────────────
header "Ready to install"
printf '\n'
printf '  %sSource:%s  %s\n' "$BOLD" "$NC" "$SKILL_DIR"
printf '  %sTarget:%s  %s\n' "$BOLD" "$NC" "$TARGET"
printf '  %sScope:%s   %s\n' "$BOLD" "$NC" "$SCOPE"
printf '  %sVersion:%s %s\n' "$BOLD" "$NC" "$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "unknown")"
printf '\n'

if [ -d "$TARGET" ]; then
    warn "Already installed at $TARGET"
fi

if [ "$AUTO_YES" = true ]; then
    MENU_RESULT=1
else
    until menu_select "Proceed?" "Yes — Install" "No — Cancel"; do
        :
    done
fi

if [ "$MENU_RESULT" -ne 1 ]; then
    info "Cancelled."
    exit 0
fi

# ─── Install ────────────────────────────────────────────────
header "Installing"

mkdir -p "$(dirname "$TARGET")"
cp -r "$SKILL_DIR" "$TARGET"

# Manage .gitignore for project memory directory
GITIGNORE="$PROJECT_DIR/.gitignore"
MEMORY_ENTRY=".memory/ultimate-dev/"
if [ -f "$GITIGNORE" ]; then
    if ! grep -q "^$MEMORY_ENTRY$" "$GITIGNORE"; then
        printf '\n%s\n' "$MEMORY_ENTRY" >> "$GITIGNORE"
        info "Added $MEMORY_ENTRY to .gitignore"
    fi
else
    printf '%s\n' "$MEMORY_ENTRY" > "$GITIGNORE"
    info "Created .gitignore with $MEMORY_ENTRY"
fi

AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
MODULE_COUNT=$(find "$TARGET/modules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
FILE_COUNT=$(find "$TARGET" -type f 2>/dev/null | wc -l | tr -d ' ')

status "Copied $FILE_COUNT files"
status "Version $(cat "$TARGET/VERSION")"

# ─── Summary ────────────────────────────────────────────────
header "Installed"
printf '\n'
printf '  %sLocation:%s  %s\n' "$BOLD" "$NC" "$TARGET"
printf '  %sAgents:%s    %s\n' "$BOLD" "$NC" "$AGENT_COUNT"
printf '  %sSkills:%s    %s\n' "$BOLD" "$NC" "$SKILL_COUNT"
printf '  %sModules:%s   %s\n' "$BOLD" "$NC" "$MODULE_COUNT"
printf '  %sFiles:%s     %s\n' "$BOLD" "$NC" "$FILE_COUNT"
printf '\n'

printf '  %sNext steps:%s\n' "$BOLD" "$NC"
if [ "$SCOPE" = "global" ]; then
    printf '  %s• Your AI coding tool will auto-detect the skill%s\n' "$DIM" "$NC"
    printf '  %s• Start a new session and it loads automatically%s\n' "$DIM" "$NC"
else
    printf '  %s• Open your project in your AI coding tool%s\n' "$DIM" "$NC"
    printf '  %s• The skill will be detected automatically%s\n' "$DIM" "$NC"
fi
printf '\n'
printf '  %sTo uninstall: %s --uninstall%s\n' "$CYAN" "$0" "$NC"
printf '\n'
