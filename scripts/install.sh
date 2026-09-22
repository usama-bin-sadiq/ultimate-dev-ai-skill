#!/bin/bash
# ultimate-dev v2.1.0 — Installer for macOS/Linux
# Usage: ./scripts/install.sh [--global|--project DIR|--uninstall|--help]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")/ultimate-dev"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

usage() {
    echo "Usage: $0 [--global|--project DIR|--uninstall|--help]"
    echo ""
    echo "  --global        Install to ~/.agents/skills/ultimate-dev"
    echo "  --project DIR   Install to DIR/.agents/skills/ultimate-dev"
    echo "  --uninstall     Remove the installation"
    echo ""
}

# Parse args
SCOPE=""; PROJECT_DIR=""; UNINSTALL=false
while [ $# -gt 0 ]; do
    case "$1" in
        --global)    SCOPE="global"; shift ;;
        --project)   SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *)           echo -e "${RED}Unknown: $1${NC}"; usage; exit 1 ;;
    esac
done

# Uninstall
if [ "$UNINSTALL" = true ]; then
    rm -rf "$HOME/.agents/skills/ultimate-dev"
    echo -e "${GREEN}✅ Uninstalled${NC}"
    exit 0
fi

# Interactive mode
if [ -z "$SCOPE" ]; then
    echo ""
    echo -e "${BOLD}ultimate-dev Installer${NC}"
    echo ""
    echo "  1) Global   — ~/.agents/skills/ultimate-dev/"
    echo "  2) Project  — <project>/.agents/skills/ultimate-dev/"
    echo ""
    read -r -n1 -s choice
    echo ""
    case "$choice" in
        1) SCOPE="global" ;;
        2)
            SCOPE="project"
            echo "Project path:"
            read -r PROJECT_DIR
            PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
            [ ! -d "$PROJECT_DIR" ] && echo -e "${RED}Not found: $PROJECT_DIR${NC}" && exit 1
            ;;
        q|Q) exit 0 ;;
        *)   exit 1 ;;
    esac
fi

# Target
if [ "$SCOPE" = "global" ]; then
    TARGET="$HOME/.agents/skills/ultimate-dev"
else
    PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
    TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
fi

# Confirm
echo ""
echo -e "  Target: ${BOLD}$TARGET${NC}"
read -r -p "Proceed? (y/N) " confirm
[[ ! "$confirm" =~ ^[Yy]$ ]] && echo "Cancelled." && exit 0

# Install — just copy the whole directory
mkdir -p "$(dirname "$TARGET")"
rm -rf "$TARGET"
cp -r "$SKILL_DIR" "$TARGET"

echo ""
echo -e "${GREEN}✅ Installed to $TARGET${NC}"
echo -e "   Version: $(cat "$TARGET/VERSION")"
echo -e "   Agents: $(find "$TARGET/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')"
echo -e "   Skills: $(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')"
echo ""
