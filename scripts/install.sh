#!/bin/bash
# ultimate-dev v2.1.0 — Installer for macOS/Linux
# Usage: ./scripts/install.sh [--global|--project DIR|--uninstall|--help]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")/ultimate-dev"

# ─── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; MAGENTA='\033[0;35m'
BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

# ─── Helpers ────────────────────────────────────────────────
print_logo() {
    local ver=$(cat "$(dirname "$0")/../VERSION" 2>/dev/null || echo "2.1.0")
    echo ""
    echo -e "  ${CYAN}┌─────────────────────────────────────────────────────┐${NC}"
    echo -e "  ${CYAN}│                                                     │${NC}"
    echo -e "  ${CYAN}│${NC}            ${BOLD}${MAGENTA}ultimate-dev${NC} ${DIM}v${ver}${NC}                          ${CYAN}│${NC}"
    echo -e "  ${CYAN}│${NC}            ${DIM}─────────────────${NC}                          ${CYAN}│${NC}"
    echo -e "  ${CYAN}│${NC}  ${MAGENTA}Master Software Engineering Orchestrator${NC}              ${CYAN}│${NC}"
    echo -e "  ${CYAN}│${NC}  ${DIM}120 agents • 17 skills • 45 modules • Any model${NC}    ${CYAN}│${NC}"
    echo -e "  ${CYAN}│${NC}                                                     ${CYAN}│${NC}"
    echo -e "  ${CYAN}└─────────────────────────────────────────────────────┘${NC}"
    echo ""
}

status()  { echo -e "  ${GREEN}✔${NC} $1"; }
warn()    { echo -e "  ${YELLOW}⚠${NC} $1"; }
err()     { echo -e "  ${RED}✘${NC} $1"; }
info()    { echo -e "  ${CYAN}ℹ${NC} $1"; }
header()  { echo -e "\n${BOLD}${BLUE}  ── $1 ──${NC}"; }

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --global        Install to ~/.agents/skills/ultimate-dev"
    echo "  --project DIR   Install to DIR/.agents/skills/ultimate-dev"
    echo "  --uninstall     Remove the installation"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                        # Interactive"
    echo "  $0 --global               # All projects"
    echo "  $0 --project ~/my-app     # One project"
    echo ""
}

# ─── Arrow key menu ─────────────────────────────────────────
ARROW_MENU_RESULT=""
arrow_menu() {
    local title="$1"
    shift
    local options=("$@")
    local count=${#options[@]}
    local selected=1

    # Save cursor position, hide cursor
    echo -ne "\e[?25l"

    while true; do
        # Draw title
        echo -e "  ${BOLD}$title${NC}"
        echo ""

        # Draw options
        for i in "${!options[@]}"; do
            local idx=$((i + 1))
            if [ "$idx" -eq "$selected" ]; then
                echo -e "    ${BLUE}▸${NC} ${BOLD}$idx)${NC} ${options[$i]}"
            else
                echo -e "      ${DIM}$idx) ${options[$i]}${NC}"
            fi
        done

        echo ""
        echo -e "  ${DIM}↑↓ navigate  •  Enter select  •  q quit${NC}"
        echo ""

        # Read a single keypress
        local key=""
        while true; do
            IFS= read -rsn1 char
            local code=$(printf '%d' "'$char" 2>/dev/null || echo "0")

            if [ "$code" -eq 27 ]; then
                # Escape — read 2 more bytes for arrow
                read -rsn1 -t 0.1 _
                read -rsn1 -t 0.1 arrow
                local arrow_code=$(printf '%d' "'$arrow" 2>/dev/null || echo "0")
                if [ "$arrow_code" -eq 65 ]; then
                    key="up"
                elif [ "$arrow_code" -eq 66 ]; then
                    key="down"
                fi
                break
            elif [ "$code" -eq 10 ] || [ "$code" -eq 13 ]; then
                key="enter"
                break
            elif [ "$char" = "q" ] || [ "$char" = "Q" ]; then
                key="quit"
                break
            elif [ "$char" = "1" ] && [ "$count" -ge 1 ]; then
                key="num1"
                break
            elif [ "$char" = "2" ] && [ "$count" -ge 2 ]; then
                key="num2"
                break
            elif [ "$char" = "3" ] && [ "$count" -ge 3 ]; then
                key="num3"
                break
            elif [ "$char" = "4" ] && [ "$count" -ge 4 ]; then
                key="num4"
                break
            fi
            # All other keys — ignore, keep reading
        done

        # Process
        case "$key" in
            up)
                selected=$((selected - 1))
                [ "$selected" -lt 1 ] && selected=$count
                # Move up to start of options, clear, redraw
                local lines=$((count + 4))
                echo -ne "\e[${lines}A"
                for ((j=0; j<lines; j++)); do echo -ne "\e[2K\e[1B"; done
                echo -ne "\e[${lines}A"
                ;;
            down)
                selected=$((selected + 1))
                [ "$selected" -gt "$count" ] && selected=1
                local lines=$((count + 4))
                echo -ne "\e[${lines}A"
                for ((j=0; j<lines; j++)); do echo -ne "\e[2K\e[1B"; done
                echo -ne "\e[${lines}A"
                ;;
            enter)
                echo -ne "\e[?25h"
                ARROW_MENU_RESULT=$selected
                return 0
                ;;
            num1|num2|num3|num4)
                local num=${key#num}
                echo -ne "\e[?25h"
                ARROW_MENU_RESULT=$num
                return 0
                ;;
            quit)
                echo -ne "\e[?25h"
                ARROW_MENU_RESULT=0
                return 1
                ;;
        esac
    done
}

# ─── Parse args ─────────────────────────────────────────────
SCOPE=""; PROJECT_DIR=""; UNINSTALL=false; AUTO_YES=false
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
    arrow_menu "Where do you want to install?" \
        "Global    — ~/.agents/skills/ultimate-dev/" \
        "Project   — <project>/.agents/skills/ultimate-dev/"

    MENU_EXIT=$?
    if [ $MENU_EXIT -ne 0 ] || [ "$ARROW_MENU_RESULT" -eq 0 ]; then
        info "Cancelled."
        exit 0
    fi

    case "$ARROW_MENU_RESULT" in
        1) SCOPE="global" ;;
        2)
            SCOPE="project"
            echo ""
            echo -e "  ${CYAN}Enter project path:${NC}"
            echo -e "  ${DIM}(e.g., ~/my-app or . for current directory)${NC}"
            echo ""
            echo -ne "  "
            read -r PROJECT_DIR
            PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
            if [ ! -d "$PROJECT_DIR" ]; then
                err "Directory not found: $PROJECT_DIR"
                exit 1
            fi
            ;;
    esac
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
echo ""
echo -e "  ${BOLD}Source:${NC}  $SKILL_DIR"
echo -e "  ${BOLD}Target:${NC}  $TARGET"
echo -e "  ${BOLD}Scope:${NC}   $SCOPE"
echo -e "  ${BOLD}Version:${NC} $(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "unknown")"
echo ""

if [ -d "$TARGET" ]; then
    warn "Already installed at $TARGET"
fi

if [ "$AUTO_YES" = true ]; then
    ARROW_MENU_RESULT=1
else
    arrow_menu "Proceed?" "Yes — Install" "No — Cancel"
fi

if [ "$ARROW_MENU_RESULT" -ne 1 ]; then
    info "Cancelled."
    exit 0
fi

# ─── Install ────────────────────────────────────────────────
header "Installing"

mkdir -p "$(dirname "$TARGET")"
cp -r "$SKILL_DIR" "$TARGET"

AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
MODULE_COUNT=$(find "$TARGET/modules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
FILE_COUNT=$(find "$TARGET" -type f 2>/dev/null | wc -l | tr -d ' ')

status "Copied $FILE_COUNT files"
status "Version $(cat "$TARGET/VERSION")"

# ─── Summary ────────────────────────────────────────────────
header "Installed"
echo ""
echo -e "  ${BOLD}Location:${NC}  $TARGET"
echo -e "  ${BOLD}Agents:${NC}    $AGENT_COUNT"
echo -e "  ${BOLD}Skills:${NC}    $SKILL_COUNT"
echo -e "  ${BOLD}Modules:${NC}   $MODULE_COUNT"
echo -e "  ${BOLD}Files:${NC}     $FILE_COUNT"
echo ""

echo -e "  ${BOLD}Next steps:${NC}"
if [ "$SCOPE" = "global" ]; then
    echo -e "  ${DIM}• Your AI coding tool will auto-detect the skill${NC}"
    echo -e "  ${DIM}• Start a new session and it loads automatically${NC}"
else
    echo -e "  ${DIM}• Open your project in your AI coding tool${NC}"
    echo -e "  ${DIM}• The skill will be detected automatically${NC}"
fi
echo ""
echo -e "  ${CYAN}To uninstall: $0 --uninstall${NC}"
echo ""
