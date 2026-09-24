#!/bin/bash
# ultimate-dev — Installer for macOS/Linux
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
    local ver agents skills modules stats
    ver="$(cat "$(dirname "$SCRIPT_DIR")/VERSION" 2>/dev/null || echo "3.0.0")"
    agents="$(find "$SKILL_DIR/agents" -name '*.md' -not -path '*/_shared/*' 2>/dev/null | wc -l | tr -d ' ' || true)"
    skills="$(find "$SKILL_DIR/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ' || true)"
    modules="$(find "$SKILL_DIR/modules" -name '*.md' 2>/dev/null | wc -l | tr -d ' ' || true)"
    stats="${agents:-0} agents • ${skills:-0} skills • ${modules:-0} modules • Any model"
    while [ "${#stats}" -lt 47 ]; do stats="$stats "; done
    local C="${CYAN}" M="${MAGENTA}" B="${BOLD}" D="${DIM}" N="${NC}"
    printf '\n'
    printf '  %s┌─────────────────────────────────────────────────────┐%s\n' "$C" "$N"
    printf '  %s│%s                                                     %s│%s\n' "$C" "$N" "$C" "$N"
    local vpad=$((27 - ${#ver}))
    if [ "$vpad" -lt 0 ]; then vpad=0; fi
    printf '  %s│%s            ' "$C" "$N"
    printf '%s%sultimate-dev%s ' "$B$M" "$N"
    printf '%sv%s%s' "$D" "$ver" "$N"
    printf '%*s' "$vpad" ''
    printf '%s│%s\n' "$C" "$N"
    printf '  %s│%s            %s─────────────────%s                        %s│%s\n' "$C" "$N" "$D" "$N" "$C" "$N"
    printf '  %s│%s  %sMaster Software Engineering Orchestrator%s           %s│%s\n' "$C" "$N" "$M" "$N" "$C" "$N"
    printf '  %s│%s  %s%s%s    %s│%s\n' "$C" "$N" "$D" "$stats" "$N" "$C" "$N"
    printf '  %s│%s                                                     %s│%s\n' "$C" "$N" "$C" "$N"
    printf '  %s└─────────────────────────────────────────────────────┘%s\n' "$C" "$N"
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
CLEAN_MEMORY=false
CLEAN_GITIGNORE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --global)        SCOPE="global"; shift ;;
        --project)       SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --uninstall)     UNINSTALL=true; shift ;;
        --yes|-y)        AUTO_YES=true; shift ;;
        --clean-memory)  CLEAN_MEMORY=true; shift ;;
        --clean-gitignore) CLEAN_GITIGNORE=true; shift ;;
        --all)           CLEAN_MEMORY=true; CLEAN_GITIGNORE=true; shift ;;
        --help|-h)       usage; exit 0 ;;
        *)               err "Unknown option: $1"; usage; exit 1 ;;
    esac
done

print_logo

# ─── Uninstall ──────────────────────────────────────────────
if [ "$UNINSTALL" = true ]; then
    header "Uninstalling ultimate-dev"

    # Determine scope for uninstall (same flow as install)
    if [ -z "$SCOPE" ]; then
        if [ "$AUTO_YES" = true ]; then
            SCOPE="global"
        else
            until menu_select "Where is the installation?" \
                "Global    — ~/.agents/skills/ultimate-dev/" \
                "Project   — <project>/.agents/skills/ultimate-dev/"; do
                :
            done

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

    if [ "$SCOPE" = "global" ]; then
        TARGET="$HOME/.agents/skills/ultimate-dev"
        PROJECT_DIR="$HOME"
    else
        PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
        TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
    fi

    MEMORY_DIR="$PROJECT_DIR/.memory/ultimate-dev"
    GITIGNORE="$PROJECT_DIR/.gitignore"
    MEMORY_ENTRY=".memory/ultimate-dev/"

    # Show what will be removed
    FOUND_ANY=false
    if [ -d "$TARGET" ]; then
        printf '  %s• Skill directory:%s  %s\n' "$BOLD" "$NC" "$TARGET"
        FOUND_ANY=true
    else
        warn "Skill directory not found: $TARGET"
    fi

    if [ "$CLEAN_MEMORY" = true ] && [ -d "$MEMORY_DIR" ]; then
        printf '  %s• Memory directory:%s  %s\n' "$BOLD" "$NC" "$MEMORY_DIR"
        FOUND_ANY=true
    elif [ "$CLEAN_MEMORY" = true ]; then
        info "Memory directory not found: $MEMORY_DIR"
    fi

    if [ "$CLEAN_GITIGNORE" = true ] && [ -f "$GITIGNORE" ] && grep -q "^$MEMORY_ENTRY$" "$GITIGNORE"; then
        printf '  %s• .gitignore entry:%s  %s\n' "$BOLD" "$NC" "$MEMORY_ENTRY"
        FOUND_ANY=true
    elif [ "$CLEAN_GITIGNORE" = true ]; then
        info ".gitignore entry not found: $MEMORY_ENTRY"
    fi

    if [ "$FOUND_ANY" = false ]; then
        warn "Nothing to uninstall"
        exit 0
    fi

    # Confirm
    if [ "$AUTO_YES" = false ]; then
        printf '\n'
        until menu_select "Proceed with uninstall?" "Yes — Uninstall" "No — Cancel"; do
            :
        done
        if [ "$MENU_RESULT" -ne 1 ]; then
            info "Cancelled."
            exit 0
        fi
    fi

    # Execute uninstall
    if [ -d "$TARGET" ]; then
        rm -rf "$TARGET"
        status "Removed $TARGET"
    fi

    if [ "$CLEAN_MEMORY" = true ] && [ -d "$MEMORY_DIR" ]; then
        rm -rf "$MEMORY_DIR"
        status "Removed $MEMORY_DIR"
    fi

    if [ "$CLEAN_GITIGNORE" = true ] && [ -f "$GITIGNORE" ]; then
        if grep -q "^$MEMORY_ENTRY$" "$GITIGNORE"; then
            sed -i.bak "\|^$MEMORY_ENTRY$|d" "$GITIGNORE"
            rm -f "$GITIGNORE.bak"
            if [ ! -s "$GITIGNORE" ]; then
                rm -f "$GITIGNORE"
                info "Removed empty .gitignore"
            else
                status "Removed $MEMORY_ENTRY from .gitignore"
            fi
        fi
    fi

    header "Uninstalled"
    printf '\n'
    printf '  %sScope:%s       %s\n' "$BOLD" "$NC" "$SCOPE"
    if [ -d "$TARGET" ]; then
        warn "Skill directory still exists"
    else
        status "Skill directory removed"
    fi
    if [ "$CLEAN_MEMORY" = true ]; then
        if [ -d "$MEMORY_DIR" ]; then
            warn "Memory directory still exists"
        else
            status "Memory directory removed"
        fi
    fi
    if [ "$CLEAN_GITIGNORE" = true ]; then
        if [ -f "$GITIGNORE" ] && grep -q "^$MEMORY_ENTRY$" "$GITIGNORE"; then
            warn ".gitignore entry still exists"
        else
            status ".gitignore entry removed"
        fi
    fi
    printf '\n'
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
    PROJECT_DIR="$HOME"
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

# Manage .gitignore for project memory directory (only for project scope)
if [ "$SCOPE" = "project" ]; then
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
fi

# Create .memory folder at the project root (project memory lives at the
# project root — never inside the skill directory)
MEMORY_DIR="$PROJECT_DIR/.memory/ultimate-dev"
if [ ! -d "$MEMORY_DIR" ]; then
    mkdir -p "$MEMORY_DIR"
    info "Created project memory: $MEMORY_DIR"
fi
if [ ! -f "$MEMORY_DIR/project-memory.md" ] && [ -f "$TARGET/memory/project-memory.md" ]; then
    cp "$TARGET/memory/project-memory.md" "$MEMORY_DIR/project-memory.md"
    info "Seeded $MEMORY_DIR/project-memory.md from template"
fi

AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" -not -path "*/_shared/*" 2>/dev/null | wc -l | tr -d ' ')
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
