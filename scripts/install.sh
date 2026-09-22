#!/bin/bash
# ultimate-dev v2.0.0 — Installer for macOS/Linux
# Usage: ./scripts/install.sh [--global|--project DIR|--help]
#
# Asks one question: install globally or to a specific project?

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "2.0.0")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║   ultimate-dev v${VERSION} Installer               ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_ok()    { echo -e "${GREEN}✅ $1${NC}"; }
print_warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_err()   { echo -e "${RED}❌ $1${NC}"; }
print_info()  { echo -e "${CYAN}ℹ️  $1${NC}"; }

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --global           Install to ~/.agents/skills/ultimate-dev (shared across projects)"
    echo "  --project DIR      Install to DIR/.agents/skills/ultimate-dev (project-specific)"
    echo "  --uninstall        Remove the skill installation"
    echo "  --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                        # Interactive — asks where to install"
    echo "  $0 --global               # Install globally (all projects)"
    echo "  $0 --project ~/my-app     # Install for ~/my-app only"
    echo ""
}

# Copy the entire skill directory
install_skill() {
    local target="$1"
    local scope="$2"

    echo ""
    print_info "Installing to: $target"
    echo ""

    # Create target directory
    mkdir -p "$target"

    # Copy core files
    cp "$SKILL_DIR/SKILL.md" "$target/"
    cp "$SKILL_DIR/README.md" "$target/"
    cp "$SKILL_DIR/VERSION" "$target/"
    cp "$SKILL_DIR/skill-manifest.yaml" "$target/"

    # Copy directories (only if they exist and have content)
    for dir in agents skills modules config prompts workflows schemas rules router templates tools scripts tests examples evals reference memory changelog; do
        if [ -d "$SKILL_DIR/$dir" ] && [ "$(ls -A "$SKILL_DIR/$dir" 2>/dev/null)" ]; then
            cp -r "$SKILL_DIR/$dir" "$target/"
        fi
    done

    # Verify installation
    if [ -f "$target/SKILL.md" ] && [ -f "$target/skill-manifest.yaml" ]; then
        echo ""
        print_ok "Installation successful!"
        echo ""
        echo -e "  ${BOLD}Installed to:${NC} $target"
        echo -e "  ${BOLD}Version:${NC}      $VERSION"
        echo -e "  ${BOLD}Agents:${NC}       $(find "$target/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')"
        echo -e "  ${BOLD}Skills:${NC}       $(find "$target/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')"
        echo -e "  ${BOLD}Modules:${NC}      $(find "$target/modules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')"
        echo ""
    else
        print_err "Installation failed — core files missing"
        exit 1
    fi
}

uninstall_skill() {
    local target="$1"
    if [ -d "$target" ]; then
        rm -rf "$target"
        print_ok "Uninstalled: $target"
    else
        print_warn "Nothing to uninstall at: $target"
    fi
}

# Parse arguments
SCOPE=""
PROJECT_DIR=""
UNINSTALL=false

while [ $# -gt 0 ]; do
    case "$1" in
        --global)    SCOPE="global"; shift ;;
        --project)   SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        --help|-h)   usage; exit 0 ;;
        *)           print_err "Unknown option: $1"; usage; exit 1 ;;
    esac
done

print_header

# ─── UNINSTALL ─────────────────────────────────────────────
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}Uninstalling ultimate-dev...${NC}"
    uninstall_skill "$HOME/.agents/skills/ultimate-dev"
    print_ok "Done."
    exit 0
fi

# ─── INTERACTIVE MODE (no arguments) ───────────────────────
if [ -z "$SCOPE" ]; then
    echo "Where would you like to install ultimate-dev?"
    echo ""
    echo -e "  ${BOLD}1) Global${NC}    — shared across all projects"
    echo -e "                   → ~/.agents/skills/ultimate-dev/"
    echo ""
    echo -e "  ${BOLD}2) Project${NC}  — specific to one project"
    echo -e "                   → <project>/.agents/skills/ultimate-dev/"
    echo ""
    echo -e "  ${CYAN}Press 1 for global, 2 for project, or q to quit${NC}"
    echo ""

    read -r -n1 -s choice
    echo ""

    case "$choice" in
        1) SCOPE="global" ;;
        2)
            SCOPE="project"
            echo -e "${CYAN}Enter project path (e.g., ~/my-app or . for current directory):${NC}"
            read -r PROJECT_DIR
            # Expand ~ and resolve relative paths
            PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
            if [ ! -d "$PROJECT_DIR" ]; then
                print_err "Directory does not exist: $PROJECT_DIR"
                exit 1
            fi
            ;;
        q|Q) print_info "Cancelled."; exit 0 ;;
        *)   print_err "Invalid choice."; exit 1 ;;
    esac
fi

# ─── DETERMINE TARGET ──────────────────────────────────────
if [ "$SCOPE" = "global" ]; then
    TARGET="$HOME/.agents/skills/ultimate-dev"
else
    # Resolve project directory
    if [ -z "$PROJECT_DIR" ]; then
        PROJECT_DIR="$(pwd)"
    fi
    TARGET="$PROJECT_DIR/.agents/skills/ultimate-dev"
fi

# ─── CONFIRM ───────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}Scope:${NC}  $SCOPE"
echo -e "  ${BOLD}Target:${NC} $TARGET"
echo ""
read -r -p "Proceed? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    print_info "Cancelled."
    exit 0
fi

# ─── INSTALL ───────────────────────────────────────────────
install_skill "$TARGET" "$SCOPE"

# ─── NEXT STEPS ────────────────────────────────────────────
echo -e "${BOLD}Next steps:${NC}"
if [ "$SCOPE" = "global" ]; then
    echo "  The skill is available to all projects."
    echo "  Your AI coding tool will auto-detect it."
else
    echo "  The skill is installed in your project."
    echo "  Your AI coding tool will auto-detect it."
fi
echo ""
echo -e "  ${CYAN}To uninstall: $0 --uninstall${NC}"
echo ""
