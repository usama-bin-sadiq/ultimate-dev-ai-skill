#!/bin/bash
# ultimate-dev installer — POSIX (macOS/Linux) with TUI
# Usage: ./scripts/install.sh [--scope user|project] [--tool TOOL] [--division div1,div2,...] [--dry-run] [--tui]
#
# Divisions: engineering, agency, business, research, domain, meta, all
# Tools: claude-code, codex, cursor, windsurf, cline, copilot, aider, opencode, generic

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
MANIFEST_DIR="$HOME/.ultimate-dev"
MANIFEST_FILE="$MANIFEST_DIR/install-manifest.json"

# All available divisions
ALL_DIVISIONS="engineering agency business research domain meta"

# Colors for TUI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Defaults
SCOPE=""
TOOL=""
DIVISION=""
DRY_RUN=false
TUI_MODE=false
VERBOSE=false

# Parse arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2 ;;
    --tool) TOOL="$2"; shift 2 ;;
    --division) DIVISION="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --tui) TUI_MODE=true; shift ;;
    --verbose) VERBOSE=true; shift ;;
    --list)
      echo "Available divisions:"
      echo "  engineering  — backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation"
      echo "  agency       — project-management, product, design-handoff, client-communication"
      echo "  business     — marketing, sales, finance, support, paid-media"
      echo "  research     — research, academic"
      echo "  domain       — healthcare, game-dev, gis, spatial-computing, specialized"
      echo "  meta         — skill-maintainer, gap-tracker (system maintenance)"
      echo "  all          — everything (default)"
      echo ""
      echo "Available tools:"
      echo "  claude-code  — Claude Code (Anthropic)"
      echo "  codex        — Codex CLI (OpenAI)"
      echo "  cursor       — Cursor IDE"
      echo "  windsurf     — Windsurf IDE"
      echo "  cline        — Cline (VS Code)"
      echo "  copilot      — GitHub Copilot"
      echo "  aider        — Aider"
      echo "  opencode     — OpenCode"
      echo "  generic      — Generic CLI fallback"
      exit 0
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --scope user|project     Install scope (default: user)"
      echo "  --tool TOOL              Target tool (see --list for options)"
      echo "  --division DIV1,DIV2    Comma-separated divisions to install"
      echo "  --dry-run                Show what would be installed without doing it"
      echo "  --tui                    Enable interactive TUI mode"
      echo "  --verbose                Show detailed output"
      echo "  --list                   List available divisions and tools"
      echo "  -h, --help               Show this help"
      echo ""
      echo "Examples:"
      echo "  $0 --tui                          # Interactive installation"
      echo "  $0 --tool claude-code --scope user  # Install for Claude Code (user scope)"
      echo "  $0 --tool generic --division engineering,security  # Install specific divisions"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# TUI Functions
print_header() {
  clear
  echo -e "${BOLD}${CYAN}"
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║           ultimate-dev Installer v$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo "1.1.1")                  ║"
  echo "║     Master Software Engineering Orchestrator               ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

print_section() {
  echo -e "\n${BOLD}${YELLOW}── $1 ──${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

# TUI Selection Menu
select_option() {
  local title="$1"
  shift
  local options=("$@")
  local selected=0
  local last=$((${#options[@]} - 1))
  
  print_section "$title"
  
  while true; do
    for i in "${!options[@]}"; do
      if [ $i -eq $selected ]; then
        echo -e "${GREEN}  ► ${options[$i]}${NC}"
      else
        echo -e "    ${options[$i]}"
      fi
    done
    
    echo ""
    echo -e "${CYAN}  Use ↑/↓ arrows to select, Enter to confirm, q to quit${NC}"
    
    read -rsn1 key
    case "$key" in
      $'\x1b')
        read -rsn2 key2
        case "$key2" in
          '[A') selected=$((selected - 1)); [ $selected -lt 0 ] && selected=$last ;;
          '[B') selected=$((selected + 1)); [ $selected -gt $last ] && selected=0 ;;
        esac
        ;;
      '') echo "${options[$selected]}"; return 0 ;;
      q|Q) return 1 ;;
    esac
    clear
    print_header
    print_section "$title"
  done
}

# Multi-select menu
multi_select() {
  local title="$1"
  shift
  local options=("$@")
  local selected=()
  local cursor=0
  local last=$((${#options[@]} - 1))
  
  # Initialize selected array
  for i in "${!options[@]}"; do
    selected[$i]=0
  done
  
  print_section "$title"
  
  while true; do
    for i in "${!options[@]}"; do
      if [ $i -eq $cursor ]; then
        if [ ${selected[$i]} -eq 1 ]; then
          echo -e "${GREEN}  ► [✓] ${options[$i]}${NC}"
        else
          echo -e "${GREEN}  ► [ ] ${options[$i]}${NC}"
        fi
      else
        if [ ${selected[$i]} -eq 1 ]; then
          echo -e "    [✓] ${options[$i]}"
        else
          echo -e "    [ ] ${options[$i]}"
        fi
      fi
    done
    
    echo ""
    echo -e "${CYAN}  Use ↑/↓ to move, Space to toggle, Enter to confirm, a for all, n for none, q to quit${NC}"
    
    read -rsn1 key
    case "$key" in
      $'\x1b')
        read -rsn2 key2
        case "$key2" in
          '[A') cursor=$((cursor - 1)); [ $cursor -lt 0 ] && cursor=$last ;;
          '[B') cursor=$((cursor + 1)); [ $cursor -gt $last ] && cursor=0 ;;
        esac
        ;;
      ' ')
        if [ ${selected[$cursor]} -eq 1 ]; then
          selected[$cursor]=0
        else
          selected[$cursor]=1
        fi
        ;;
      a|A)
        for i in "${!options[@]}"; do
          selected[$i]=1
        done
        ;;
      n|N)
        for i in "${!options[@]}"; do
          selected[$i]=0
        done
        ;;
      '')
        # Build result string
        result=""
        for i in "${!options[@]}"; do
          if [ ${selected[$i]} -eq 1 ]; then
            if [ -z "$result" ]; then
              result="${options[$i]}"
            else
              result="$result,${options[$i]}"
            fi
          fi
        done
        echo "$result"
        return 0
        ;;
      q|Q) return 1 ;;
    esac
    clear
    print_header
    print_section "$title"
  done
}

# Detect installed agent tools
detect_agent_tools() {
  print_section "Detecting Installed Agent Tools"
  
  local tools_found=()
  
  # Claude Code
  if [ -d "$HOME/.claude" ] || command -v claude >/dev/null 2>&1; then
    print_success "Claude Code detected"
    tools_found+=("claude-code")
  else
    print_warning "Claude Code not found"
  fi
  
  # Codex CLI
  if [ -d "$HOME/.codex" ] || command -v codex >/dev/null 2>&1; then
    print_success "Codex CLI detected"
    tools_found+=("codex")
  else
    print_warning "Codex CLI not found"
  fi
  
  # Cursor
  if command -v cursor >/dev/null 2>&1 || [ -d ".cursor" ]; then
    print_success "Cursor detected"
    tools_found+=("cursor")
  else
    print_warning "Cursor not found"
  fi
  
  # Windsurf
  if [ -d "$HOME/.windsurf" ] || command -v windsurf >/dev/null 2>&1; then
    print_success "Windsurf detected"
    tools_found+=("windsurf")
  else
    print_warning "Windsurf not found"
  fi
  
  # Cline
  if [ -d "$HOME/.cline" ] || [ -f ".clinerules" ]; then
    print_success "Cline detected"
    tools_found+=("cline")
  else
    print_warning "Cline not found"
  fi
  
  # GitHub Copilot
  if [ -d "$HOME/.github/copilot" ] || [ -f ".github/copilot-instructions.md" ]; then
    print_success "GitHub Copilot detected"
    tools_found+=("copilot")
  else
    print_warning "GitHub Copilot not found"
  fi
  
  # Aider
  if command -v aider >/dev/null 2>&1; then
    print_success "Aider detected"
    tools_found+=("aider")
  else
    print_warning "Aider not found"
  fi
  
  # OpenCode
  if [ -d "$HOME/.opencode" ] || command -v opencode >/dev/null 2>&1; then
    print_success "OpenCode detected"
    tools_found+=("opencode")
  else
    print_warning "OpenCode not found"
  fi
  
  echo ""
  
  if [ ${#tools_found[@]} -eq 0 ]; then
    print_warning "No known agent tools detected"
    tools_found+=("generic")
  fi
  
  echo "${tools_found[@]}"
}

# Get tool installation path
get_tool_path() {
  local tool="$1"
  local scope="$2"
  
  case "$tool" in
    claude-code)
      if [ "$scope" = "project" ]; then
        echo ".claude/skills/ultimate-dev"
      else
        echo "$HOME/.claude/skills/ultimate-dev"
      fi
      ;;
    codex)
      if [ "$scope" = "project" ]; then
        echo ".codex/skills/ultimate-dev"
      else
        echo "$HOME/.codex/skills/ultimate-dev"
      fi
      ;;
    cursor)
      echo ".cursor/rules"
      ;;
    windsurf)
      if [ "$scope" = "project" ]; then
        echo ".windsurf"
      else
        echo "$HOME/.windsurf"
      fi
      ;;
    cline)
      if [ "$scope" = "project" ]; then
        echo ".cline"
      else
        echo "$HOME/.cline"
      fi
      ;;
    copilot)
      if [ "$scope" = "project" ]; then
        echo ".github"
      else
        echo "$HOME/.github"
      fi
      ;;
    aider)
      if [ "$scope" = "project" ]; then
        echo ".aider"
      else
        echo "$HOME/.aider"
      fi
      ;;
    opencode)
      if [ "$scope" = "project" ]; then
        echo ".opencode/skills/ultimate-dev"
      else
        echo "$HOME/.opencode/skills/ultimate-dev"
      fi
      ;;
    generic|*)
      if [ "$scope" = "project" ]; then
        echo ".agent/skills/ultimate-dev"
      else
        echo "$HOME/.agent/skills/ultimate-dev"
      fi
      ;;
  esac
}

# Check if a division should be installed
should_install_division() {
  local div="$1"
  if [ "$DIVISION" = "all" ] || [ -z "$DIVISION" ]; then
    return 0
  fi
  case "$DIVISION" in
    *"$div"*) return 0 ;;
    *) return 1 ;;
  esac
}

# Get module files for a division
get_modules_for_division() {
  local div="$1"
  case "$div" in
    engineering)
      echo "modules/engineering/backend.md modules/engineering/frontend.md modules/engineering/architecture.md modules/engineering/database.md modules/engineering/security.md modules/engineering/devops.md modules/engineering/mobile.md modules/engineering/testing-qa.md modules/engineering/documentation.md"
      ;;
    agency)
      echo "modules/agency/project-management.md modules/agency/product.md modules/agency/design-handoff.md modules/agency/client-communication.md"
      ;;
    business)
      echo "modules/marketing/marketing.md modules/sales/sales.md modules/finance/finance.md modules/support/support.md modules/paid-media/paid-media.md"
      ;;
    research)
      echo "modules/research/research.md modules/academic/academic.md"
      ;;
    domain)
      echo "modules/healthcare/healthcare.md modules/game-dev/game-dev.md modules/gis/gis.md modules/spatial-computing/spatial-computing.md modules/specialized/specialized.md"
      ;;
    meta)
      echo "personas/meta/skill-maintainer.md personas/meta/gap-tracker.md"
      ;;
    *)
      echo ""
      ;;
  esac
}

# Write install manifest
write_manifest() {
  local target="$1"
  local installed_files="$2"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would write manifest to $MANIFEST_FILE"
    return
  fi
  
  mkdir -p "$MANIFEST_DIR"
  
  # Write manifest JSON
  cat > "$MANIFEST_FILE" << EOF
{
  "version": "$(cat "$SKILL_DIR/VERSION" 2>/dev/null || echo '1.1.1')",
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "scope": "$SCOPE",
  "target": "$target",
  "tool": "${TOOL:-auto-detect}",
  "division": "${DIVISION:-all}",
  "files": [
$(echo "$installed_files" | tr ' ' '\n' | sed 's/^/    "/' | sed 's/$/"/' | sed '$ ! s/$/,/')
  ]
}
EOF
  print_success "Manifest written to $MANIFEST_FILE"
}

# Install for Claude Code
install_claude_code() {
  local target="$HOME/.claude/skills/ultimate-dev"
  if [ "$SCOPE" = "project" ]; then
    target=".claude/skills/ultimate-dev"
  fi
  
  print_info "Installing to: $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Always install core files
  cp "$SKILL_DIR/SKILL.md" "$target/"
  cp "$SKILL_DIR/README.md" "$target/"
  cp "$SKILL_DIR/ARCHITECTURE.md" "$target/"
  cp "$SKILL_DIR/CONTRIBUTING.md" "$target/"
  cp "$SKILL_DIR/VERSION" "$target/"
  cp "$SKILL_DIR/CHANGELOG.md" "$target/"
  cp "$SKILL_DIR/skill-manifest.yaml" "$target/"
  cp -r "$SKILL_DIR/router" "$target/"
  cp -r "$SKILL_DIR/scripts" "$target/"
  cp -r "$SKILL_DIR/adapters" "$target/"
  cp -r "$SKILL_DIR/personas" "$target/"
  
  local installed_files="SKILL.md README.md ARCHITECTURE.md CONTRIBUTING.md VERSION CHANGELOG.md skill-manifest.yaml"
  
  # Install router files
  for f in "$SKILL_DIR/router/"*.md; do
    installed_files="$installed_files router/$(basename "$f")"
  done
  
  # Install modules by division
  for div in $ALL_DIVISIONS; do
    if should_install_division "$div"; then
      local modules=$(get_modules_for_division "$div")
      for mod in $modules; do
        if [ -f "$SKILL_DIR/$mod" ]; then
          local mod_dir=$(dirname "$mod")
          mkdir -p "$target/$mod_dir"
          cp "$SKILL_DIR/$mod" "$target/$mod"
          installed_files="$installed_files $mod"
        fi
      done
      print_success "Installed $div modules"
    fi
  done
  
  # Always install cross-cutting modules
  cp "$SKILL_DIR/modules/_emerging-tech-handler.md" "$target/modules/"
  cp "$SKILL_DIR/modules/_universal-principles.md" "$target/modules/"
  installed_files="$installed_files modules/_emerging-tech-handler.md modules/_universal-principles.md"
  
  write_manifest "$target" "$installed_files"
  print_success "Installed to $target"
}

# Install for Codex
install_codex() {
  local target="$HOME/.codex/skills/ultimate-dev"
  if [ "$SCOPE" = "project" ]; then
    print_info "Codex project scope: creating AGENTS.md reference"
    if [ "$DRY_RUN" = false ]; then
      cat > "AGENTS.md" << 'EOF'
# Agent Instructions

This project uses the **ultimate-dev** skill for engineering tasks.

## Usage
When working on engineering tasks, follow the classification and routing rules defined in the ultimate-dev skill.

## Skill Location
- User scope: `~/.codex/skills/ultimate-dev/`
- See `~/.codex/skills/ultimate-dev/README.md` for full documentation.
EOF
      print_success "Created AGENTS.md"
    fi
    return
  fi
  
  print_info "Installing to: $target"
  if [ "$DRY_RUN" = false ]; then
    mkdir -p "$target"
    cp "$SKILL_DIR/SKILL.md" "$target/"
    cp -r "$SKILL_DIR/router" "$target/"
    cp -r "$SKILL_DIR/modules" "$target/"
    cp -r "$SKILL_DIR/personas" "$target/"
    cp "$SKILL_DIR/README.md" "$target/"
    cp "$SKILL_DIR/VERSION" "$target/"
    print_success "Installed to $target"
  fi
}

# Install for Cursor
install_cursor() {
  local target=".cursor/rules"
  print_info "Cursor: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy SKILL.md as the main rules file
  cp "$SKILL_DIR/SKILL.md" "$target/ultimate-dev.md"
  
  # Create a reference to the full skill
  cat > "$target/ultimate-dev-reference.md" << 'EOF'
# Ultimate Dev Reference

This file references the full ultimate-dev skill installation.

## Full Skill Location
- User scope: `~/.agents/skills/ultimate-dev/`
- Project scope: `.agent/skills/ultimate-dev/`

## Quick Reference
The main rules are in `ultimate-dev.md` in this directory.
For full documentation, see the skill installation directory.
EOF
  
  print_success "Installed to $target"
}

# Install for Windsurf
install_windsurf() {
  local target="$HOME/.windsurf"
  if [ "$SCOPE" = "project" ]; then
    target=".windsurf"
  fi
  
  print_info "Windsurf: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy SKILL.md as rules
  cp "$SKILL_DIR/SKILL.md" "$target/rules.md"
  
  print_success "Installed to $target"
}

# Install for Cline
install_cline() {
  local target="$HOME/.cline"
  if [ "$SCOPE" = "project" ]; then
    target=".cline"
  fi
  
  print_info "Cline: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy SKILL.md as rules
  cp "$SKILL_DIR/SKILL.md" "$target/rules.md"
  
  print_success "Installed to $target"
}

# Install for Copilot
install_copilot() {
  local target="$HOME/.github"
  if [ "$SCOPE" = "project" ]; then
    target=".github"
  fi
  
  print_info "Copilot: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy SKILL.md as instructions
  cp "$SKILL_DIR/SKILL.md" "$target/copilot-instructions.md"
  
  print_success "Installed to $target"
}

# Install for Aider
install_aider() {
  local target="$HOME/.aider"
  if [ "$SCOPE" = "project" ]; then
    target=".aider"
  fi
  
  print_info "Aider: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy SKILL.md as rules
  cp "$SKILL_DIR/SKILL.md" "$target/rules.md"
  
  print_success "Installed to $target"
}

# Install for OpenCode
install_opencode() {
  local target="$HOME/.opencode/skills/ultimate-dev"
  if [ "$SCOPE" = "project" ]; then
    target=".opencode/skills/ultimate-dev"
  fi
  
  print_info "OpenCode: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy all skill files
  cp "$SKILL_DIR/SKILL.md" "$target/"
  cp -r "$SKILL_DIR/router" "$target/"
  cp -r "$SKILL_DIR/modules" "$target/"
  cp -r "$SKILL_DIR/personas" "$target/"
  cp "$SKILL_DIR/README.md" "$target/"
  cp "$SKILL_DIR/VERSION" "$target/"
  
  print_success "Installed to $target"
}

# Install for generic CLI
install_generic() {
  local target="$HOME/.agent/skills/ultimate-dev"
  if [ "$SCOPE" = "project" ]; then
    target=".agent/skills/ultimate-dev"
  fi
  
  print_info "Generic CLI: Installing to $target"
  
  if [ "$DRY_RUN" = true ]; then
    print_info "[dry-run] Would install to $target"
    return
  fi
  
  mkdir -p "$target"
  
  # Copy all skill files
  cp "$SKILL_DIR/SKILL.md" "$target/"
  cp -r "$SKILL_DIR/router" "$target/"
  cp -r "$SKILL_DIR/modules" "$target/"
  cp -r "$SKILL_DIR/personas" "$target/"
  cp "$SKILL_DIR/README.md" "$target/"
  cp "$SKILL_DIR/VERSION" "$target/"
  
  # Create instruction file
  cat > "$(dirname "$target")/instructions.md" << 'EOF'
# Instructions

Follow the ultimate-dev skill at ~/.agents/skills/ultimate-dev/SKILL.md
for all engineering tasks.
EOF
  
  print_success "Installed to $target"
}

# Main installation flow
main() {
  print_header
  
  # TUI Mode
  if [ "$TUI_MODE" = true ]; then
    # Select scope
    SCOPE=$(select_option "Select Installation Scope" "User (global)" "Project (local)")
    case "$SCOPE" in
      "User (global)") SCOPE="user" ;;
      "Project (local)") SCOPE="project" ;;
      *) exit 1 ;;
    esac
    
    # Detect tools
    tools_found=($(detect_agent_tools))
    
    # Select tool
    if [ ${#tools_found[@]} -gt 1 ]; then
      TOOL=$(select_option "Select Target Tool" "${tools_found[@]}")
    elif [ ${#tools_found[@]} -eq 1 ]; then
      TOOL="${tools_found[0]}"
      print_info "Auto-selected: $TOOL"
    else
      TOOL="generic"
    fi
    
    # Select divisions
    division_result=$(multi_select "Select Divisions to Install" "engineering" "agency" "business" "research" "domain" "meta" "all")
    
    if [ -z "$division_result" ]; then
      DIVISION="all"
    else
      DIVISION="$division_result"
    fi
    
    # Confirm installation
    print_section "Installation Summary"
    echo "Scope: $SCOPE"
    echo "Tool: $TOOL"
    echo "Divisions: $DIVISION"
    echo "Target: $(get_tool_path "$TOOL" "$SCOPE")"
    echo ""
    
    read -p "Proceed with installation? (y/N) " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      print_info "Installation cancelled"
      exit 0
    fi
  fi
  
  # Validate inputs
  if [ -z "$SCOPE" ]; then
    SCOPE="user"
  fi
  
  if [ -z "$TOOL" ]; then
    # Auto-detect
    tools_found=($(detect_agent_tools))
    if [ ${#tools_found[@]} -gt 0 ]; then
      TOOL="${tools_found[0]}"
    else
      TOOL="generic"
    fi
  fi
  
  if [ -z "$DIVISION" ]; then
    DIVISION="all"
  fi
  
  # Show installation info
  print_section "Installing ultimate-dev"
  echo "Scope: $SCOPE"
  echo "Tool: $TOOL"
  echo "Divisions: $DIVISION"
  echo "Target: $(get_tool_path "$TOOL" "$SCOPE")"
  echo ""
  
  # Install based on tool
  case "$TOOL" in
    claude-code) install_claude_code ;;
    codex) install_codex ;;
    cursor) install_cursor ;;
    windsurf) install_windsurf ;;
    cline) install_cline ;;
    copilot) install_copilot ;;
    aider) install_aider ;;
    opencode) install_opencode ;;
    generic|*) install_generic ;;
  esac
  
  print_section "Installation Complete"
  print_success "ultimate-dev has been installed successfully!"
  echo ""
  echo "Installed divisions: ${DIVISION}"
  echo "Target: $(get_tool_path "$TOOL" "$SCOPE")"
  echo ""
  print_info "Restart your AI coding tool to activate the skill."
  echo ""
  print_info "For documentation, see: $(get_tool_path "$TOOL" "$SCOPE")/README.md"
}

# Run main function
main