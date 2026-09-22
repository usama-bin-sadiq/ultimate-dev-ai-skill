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
    echo -e "  ${BOLD}Where do you want to install?${NC}"
    echo ""
    echo -e "    ${BOLD}1)${NC}  ${GREEN}Global${NC}    ${DIM}→  ~/.agents/skills/ultimate-dev/${NC}"
    echo -e "        ${DIM}Available to all projects on this machine${NC}"
    echo ""
    echo -e "    ${BOLD}2)${NC}  ${CYAN}Project${NC}   ${DIM}→  <project>/.agents/skills/ultimate-dev/${NC}"
    echo -e "        ${DIM}Isolated to a single project${NC}"
    echo ""
    echo -e "    ${DIM}Press ${BOLD}1${NC}${DIM} for global, ${BOLD}2${NC}${DIM} for project, or ${BOLD}q${NC}${DIM} to quit${NC}"
    echo ""

    read -r -n1 -s choice
    echo ""

    case "$choice" in
        1) SCOPE="global" ;;
        2)
            SCOPE="project"
            echo -e "  ${CYAN}Enter project path (e.g., ~/my-app or . for current dir):${NC}"
            read -r PROJECT_DIR
            PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
            if [ ! -d "$PROJECT_DIR" ]; then
                err "Directory not found: $PROJECT_DIR"
                exit 1
            fi
            ;;
        q|Q) info "Cancelled."; exit 0 ;;
        *)   err "Invalid choice."; exit 1 ;;
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

# Check if already installed
if [ -d "$TARGET" ]; then
    warn "Already installed at $TARGET"
    read -r -p "  Replace? (y/N) " confirm
    [[ ! "$confirm" =~ ^[Yy]$ ]] && info "Keeping existing install." && exit 0
    rm -rf "$TARGET"
fi

read -r -p "  Proceed? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    info "Cancelled."
    exit 0
fi

# ─── Install ────────────────────────────────────────────────
header "Installing"

# Create parent directory
mkdir -p "$(dirname "$TARGET")"

# Copy the entire skill directory
echo -ne "  ${DIM}Copying files...${NC}\r"
cp -r "$SKILL_DIR" "$TARGET"

# Count what was installed
AGENT_COUNT=$(find "$TARGET/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
MODULE_COUNT=$(find "$TARGET/modules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
FILE_COUNT=$(find "$TARGET" -type f 2>/dev/null | wc -l | tr -d ' ')

echo -e "  ${GREEN}✔${NC} Copied $FILE_COUNT files"
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

# ─── Next steps ─────────────────────────────────────────────
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
