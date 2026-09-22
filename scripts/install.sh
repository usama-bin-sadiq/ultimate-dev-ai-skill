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
BG_BLUE='\033[44m'; BG_GREEN='\033[42m'; BG_CYAN='\033[46m'

# ─── Helpers ────────────────────────────────────────────────
print_logo() {
    echo ""
    echo -e "${CYAN}  ╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║                                                       ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD}██╗   ██╗███╗   ██╗██████╗ ███████╗${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD}██║   ██║████╗  ██║██╔══██╗██╔════╝${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD}██║   ██║██╔██╗ ██║██║  ██║███████╗${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD}██║   ██║██║╚██╗██║██║  ██║╚════██║${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD}╚██████╔╝██║ ╚████║██████╔╝███████║${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║   ${BOLD} ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝${NC}${CYAN}                ║${NC}"
    echo -e "${CYAN}  ║                                                       ║${NC}"
    echo -e "${CYAN}  ║   ${MAGENTA}Master Software Engineering Orchestrator${NC}${CYAN}              ║${NC}"
    echo -e "${CYAN}  ║   ${DIM}120 agents • 17 skills • 45 modules • Any model${NC}${CYAN}    ║${NC}"
    echo -e "${CYAN}  ║                                                       ║${NC}"
    echo -e "${CYAN}  ╚═══════════════════════════════════════════════════════╝${NC}"
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
# Renders a menu with arrow key navigation
# Usage: arrow_menu "title" "option1" "option2" ...
# Returns: selected index (1-based) in ARROW_MENU_RESULT
ARROW_MENU_RESULT=""
arrow_menu() {
    local title="$1"
    shift
    local options=("$@")
    local count=${#options[@]}
    local selected=1
    local error_msg=""

    # Hide cursor
    echo -ne "\e[?25l"

    while true; do
        # Clear and draw menu
        echo -e "  ${BOLD}$title${NC}"
        echo ""

        for i in "${!options[@]}"; do
            local idx=$((i + 1))
            local label="${options[$i]}"

            if [ "$idx" -eq "$selected" ]; then
                # Selected item — highlighted
                echo -e "    ${BG_BLUE}  ▸ $idx) $label  ${NC}"
            else
                echo -e "    ${DIM}  $idx) $label${NC}"
            fi
        done

        echo ""

        # Show error if any
        if [ -n "$error_msg" ]; then
            echo -e "  ${RED}✘ $error_msg${NC}"
            echo ""
            error_msg=""
        fi

        echo -e "  ${DIM}↑↓ navigate  •  Enter select  •  q quit${NC}"
        echo ""

        # Read input — handle arrow keys and regular keys
        local key=""
        local escape=false

        while true; do
            read -rsn1 char

            if [ "$char" = $'\x1b' ; then
                # Escape sequence — read next 2 chars (arrow keys)
                read -rsn1 char2
                read -rsn1 char3
                case "$char3" in
                    A) key="up"; break ;;    # Up arrow
                    B) key="down"; break ;;  # Down arrow
                esac
                # Other escape sequences — ignore
            elif [ "$char" = $'\x0a' ] || [ "$char" = $'\x0d' ]; then
                key="enter"
                break
            elif [ "$char" = "q" ] || [ "$char" = "Q" ]; then
                key="quit"
                break
            elif [ "$char" = "1" ]; then
                key="num1"
                break
            elif [ "$char" = "2" ]; then
                key="num2"
                break
            elif [ "$char" = "3" ]; then
                key="num3"
                break
            elif [ "$char" = "4" ]; then
                key="num4"
                break
            # Ignore all other keys — do nothing
            fi
        done

        # Process input
        case "$key" in
            up)
                selected=$((selected - 1))
                if [ "$selected" -lt 1 ]; then
                    selected=$count  # Wrap to bottom
                fi
                # Move cursor up and clear
                echo -ne "\e[${count}A"
                for ((i=0; i<count+3; i++)); do echo -ne "\e[2K\e[1B"; done
                echo -ne "\e[${count+3}A"
                ;;
            down)
                selected=$((selected + 1))
                if [ "$selected" -gt "$count" ]; then
                    selected=1  # Wrap to top
                fi
                # Move cursor up and clear
                echo -ne "\e[${count}A"
                for ((i=0; i<count+3; i++)); do echo -ne "\e[2K\e[1B"; done
                echo -ne "\e[${count+3}A"
                ;;
            enter)
                # Show cursor
                echo -ne "\e[?25h"
                ARROW_MENU_RESULT=$selected
                return 0
                ;;
            num1|num2|num3|num4)
                local num=${key#num}
                if [ "$num" -le "$count" ]; then
                    # Show cursor
                    echo -ne "\e[?25h"
                    ARROW_MENU_RESULT=$num
                    return 0
                else
                    error_msg="Invalid option: $num (choose 1-$count)"
                    # Move cursor up and redraw
                    echo -ne "\e[${count}A"
                    for ((i=0; i<count+3; i++)); do echo -ne "\e[2K\e[1B"; done
                    echo -ne "\e[${count+3}A"
                fi
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
SCOPE=""; PROJECT_DIR=""; UNINSTALL=false
while [ $# -gt 0 ]; do
    case "$1" in
        --global)    SCOPE="global"; shift ;;
        --project)   SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
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
    # Main scope menu
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

# ─── Confirm menu ───────────────────────────────────────────
header "Ready to install"
echo ""
echo -e "  ${BOLD}Source:${NC}  $SKILL_DIR"
echo -e "  ${BOLD}Target:${NC}  $TARGET"
echo -e "  ${BOLD}Scope:${NC}   $SCOPE"
echo -e "  ${BOLD}Version:${NC} $(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "unknown")"
echo ""

# Check if already installed
if [ -d "$TARGET" ]; then
    warn "Already installed at $TARGET"
fi

arrow_menu "Proceed?" "Yes — Install" "No — Cancel"

if [ "$ARROW_MENU_RESULT" -ne 1 ]; then
    info "Cancelled."
    exit 0
fi

# ─── Install ────────────────────────────────────────────────
header "Installing"

mkdir -p "$(dirname "$TARGET")"

# Show progress
echo -ne "  ${DIM}Copying files...${NC}"
cp -r "$SKILL_DIR" "$TARGET"
echo -e "\r  ${GREEN}✔${NC} Copied files    "

AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
MODULE_COUNT=$(find "$TARGET/modules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
FILE_COUNT=$(find "$TARGET" -type f 2>/dev/null | wc -l | tr -d ' ')

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
