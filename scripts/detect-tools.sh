#!/bin/bash
# Detect installed agentic tools on the system
# Usage: ./scripts/detect-tools.sh [--json|--verbose]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Parse arguments
JSON_OUTPUT=false
VERBOSE=false

while [ $# -gt 0 ]; do
  case "$1" in
    --json) JSON_OUTPUT=true; shift ;;
    --verbose) VERBOSE=true; shift ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --json      Output in JSON format"
      echo "  --verbose   Show detailed detection info"
      echo "  -h, --help  Show this help"
      exit 0
      ;;
    *) shift ;;
  esac
done

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           ultimate-dev Tool Detector                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Initialize results
TOOLS_FOUND=()
TOOL_DETAILS=()

# Function to add tool
add_tool() {
  local name="$1"
  local path="$2"
  local status="$3"
  local details="$4"
  
  TOOLS_FOUND+=("$name")
  TOOL_DETAILS+=("{\"name\":\"$name\",\"path\":\"$path\",\"status\":\"$status\",\"details\":\"$details\"}")
  
  if [ "$status" = "detected" ]; then
    echo -e "${GREEN}✅ $name detected${NC}"
    if [ "$VERBOSE" = true ]; then
      echo -e "   ${BLUE}Path: $path${NC}"
      echo -e "   ${BLUE}Details: $details${NC}"
    fi
  elif [ "$status" = "partial" ]; then
    echo -e "${YELLOW}⚠️  $name (partial)${NC}"
    if [ "$VERBOSE" = true ]; then
      echo -e "   ${BLUE}Path: $path${NC}"
      echo -e "   ${BLUE}Details: $details${NC}"
    fi
  else
    echo -e "${RED}❌ $name not found${NC}"
  fi
}

# Detect Claude Code
echo -e "\n${BOLD}Checking for Claude Code...${NC}"
if [ -d "$HOME/.claude" ]; then
  if [ -f "$HOME/.claude/settings.json" ]; then
    add_tool "claude-code" "$HOME/.claude" "detected" "Claude Code with settings"
  else
    add_tool "claude-code" "$HOME/.claude" "partial" "Claude directory exists but no settings.json"
  fi
elif command -v claude >/dev/null 2>&1; then
  add_tool "claude-code" "$(which claude)" "detected" "Claude CLI found in PATH"
else
  add_tool "claude-code" "not found" "not found" ""
fi

# Detect Codex CLI
echo -e "\n${BOLD}Checking for Codex CLI...${NC}"
if [ -d "$HOME/.codex" ]; then
  add_tool "codex" "$HOME/.codex" "detected" "Codex directory exists"
elif command -v codex >/dev/null 2>&1; then
  add_tool "codex" "$(which codex)" "detected" "Codex CLI found in PATH"
else
  add_tool "codex" "not found" "not found" ""
fi

# Detect Cursor
echo -e "\n${BOLD}Checking for Cursor...${NC}"
if command -v cursor >/dev/null 2>&1; then
  add_tool "cursor" "$(which cursor)" "detected" "Cursor CLI found in PATH"
elif [ -d ".cursor" ]; then
  add_tool "cursor" ".cursor" "detected" "Cursor project directory exists"
elif [ -d "$HOME/.cursor" ]; then
  add_tool "cursor" "$HOME/.cursor" "detected" "Cursor user directory exists"
else
  add_tool "cursor" "not found" "not found" ""
fi

# Detect Windsurf
echo -e "\n${BOLD}Checking for Windsurf...${NC}"
if command -v windsurf >/dev/null 2>&1; then
  add_tool "windsurf" "$(which windsurf)" "detected" "Windsurf CLI found in PATH"
elif [ -d "$HOME/.windsurf" ]; then
  add_tool "windsurf" "$HOME/.windsurf" "detected" "Windsurf directory exists"
elif [ -f ".windsurfrules" ]; then
  add_tool "windsurf" ".windsurfrules" "detected" "Windsurf rules file exists"
else
  add_tool "windsurf" "not found" "not found" ""
fi

# Detect Cline
echo -e "\n${BOLD}Checking for Cline...${NC}"
if [ -d "$HOME/.cline" ]; then
  add_tool "cline" "$HOME/.cline" "detected" "Cline directory exists"
elif [ -f ".clinerules" ]; then
  add_tool "cline" ".clinerules" "detected" "Cline rules file exists"
else
  add_tool "cline" "not found" "not found" ""
fi

# Detect GitHub Copilot
echo -e "\n${BOLD}Checking for GitHub Copilot...${NC}"
if [ -d "$HOME/.github/copilot" ]; then
  add_tool "copilot" "$HOME/.github/copilot" "detected" "Copilot directory exists"
elif [ -f ".github/copilot-instructions.md" ]; then
  add_tool "copilot" ".github/copilot-instructions.md" "detected" "Copilot instructions file exists"
elif command -v gh >/dev/null 2>&1; then
  if gh extension list 2>/dev/null | grep -q copilot; then
    add_tool "copilot" "gh extension" "detected" "Copilot extension installed"
  else
    add_tool "copilot" "not found" "not found" ""
  fi
else
  add_tool "copilot" "not found" "not found" ""
fi

# Detect Aider
echo -e "\n${BOLD}Checking for Aider...${NC}"
if command -v aider >/dev/null 2>&1; then
  add_tool "aider" "$(which aider)" "detected" "Aider CLI found in PATH"
elif [ -d "$HOME/.aider" ]; then
  add_tool "aider" "$HOME/.aider" "detected" "Aider directory exists"
else
  add_tool "aider" "not found" "not found" ""
fi

# Detect OpenCode
echo -e "\n${BOLD}Checking for OpenCode...${NC}"
if command -v opencode >/dev/null 2>&1; then
  add_tool "opencode" "$(which opencode)" "detected" "OpenCode CLI found in PATH"
elif [ -d "$HOME/.opencode" ]; then
  add_tool "opencode" "$HOME/.opencode" "detected" "OpenCode directory exists"
else
  add_tool "opencode" "not found" "not found" ""
fi

# Detect Continue
echo -e "\n${BOLD}Checking for Continue...${NC}"
if [ -d "$HOME/.continue" ]; then
  add_tool "continue" "$HOME/.continue" "detected" "Continue directory exists"
elif [ -f ".continuerc" ]; then
  add_tool "continue" ".continuerc" "detected" "Continue config file exists"
else
  add_tool "continue" "not found" "not found" ""
fi

# Detect Tabnine
echo -e "\n${BOLD}Checking for Tabnine...${NC}"
if [ -d "$HOME/.tabnine" ]; then
  add_tool "tabnine" "$HOME/.tabnine" "detected" "Tabnine directory exists"
elif command -v tabnine >/dev/null 2>&1; then
  add_tool "tabnine" "$(which tabnine)" "detected" "Tabnine CLI found in PATH"
else
  add_tool "tabnine" "not found" "not found" ""
fi

# Detect Codeium
echo -e "\n${BOLD}Checking for Codeium...${NC}"
if [ -d "$HOME/.codeium" ]; then
  add_tool "codeium" "$HOME/.codeium" "detected" "Codeium directory exists"
elif command -v codeium >/dev/null 2>&1; then
  add_tool "codeium" "$(which codeium)" "detected" "Codeium CLI found in PATH"
else
  add_tool "codeium" "not found" "not found" ""
fi

# Summary
echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Detection Summary${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"

# Count detected tools
DETECTED_COUNT=0
for tool in "${TOOLS_FOUND[@]}"; do
  DETECTED_COUNT=$((DETECTED_COUNT + 1))
done

echo -e "Tools checked: ${BOLD}$DETECTED_COUNT${NC}"
echo -e ""

# List detected tools
echo -e "${BOLD}Detected tools:${NC}"
for i in "${!TOOLS_FOUND[@]}"; do
  tool="${TOOLS_FOUND[$i]}"
  detail="${TOOL_DETAILS[$i]}"
  
  # Extract status from JSON
  status=$(echo "$detail" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$status" = "detected" ]; then
    echo -e "  ${GREEN}✓${NC} $tool"
  elif [ "$status" = "partial" ]; then
    echo -e "  ${YELLOW}⚠${NC} $tool (partial)"
  fi
done

echo -e ""

# JSON output
if [ "$JSON_OUTPUT" = true ]; then
  echo -e "\n${BOLD}JSON Output:${NC}"
  echo "["
  for i in "${!TOOL_DETAILS[@]}"; do
    if [ $i -lt $((${#TOOL_DETAILS[@]} - 1)) ]; then
      echo "  ${TOOL_DETAILS[$i]},"
    else
      echo "  ${TOOL_DETAILS[$i]}"
    fi
  done
  echo "]"
fi

# Recommendations
echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Recommendations${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"

if [ ${#TOOLS_FOUND[@]} -eq 0 ]; then
  echo -e "${YELLOW}No known agent tools detected.${NC}"
  echo -e "The generic-cli adapter will be used for installation."
  echo -e ""
  echo -e "To install for a specific tool, run:"
  echo -e "  ${BOLD}./scripts/install.sh --tool <tool-name>${NC}"
else
  echo -e "${GREEN}Detected tools can be used with ultimate-dev.${NC}"
  echo -e ""
  echo -e "To install for a specific tool, run:"
  echo -e "  ${BOLD}./scripts/install.sh --tool <tool-name>${NC}"
  echo -e ""
  echo -e "Or use interactive mode:"
  echo -e "  ${BOLD}./scripts/install.sh --tui${NC}"
fi