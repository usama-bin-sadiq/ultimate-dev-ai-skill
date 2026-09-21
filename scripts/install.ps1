# ultimate-dev installer — Windows PowerShell with TUI
# Usage: .\scripts\install.ps1 [-Scope user|project] [-Tool TOOL] [-Division div1,div2,...] [-DryRun] [-TUI]
#
# Divisions: engineering, agency, business, research, domain, meta, all
# Tools: claude-code, codex, cursor, windsurf, cline, copilot, aider, opencode, generic

param(
    [ValidateSet("user","project")]
    [string]$Scope = "",
    [ValidateSet("claude-code","codex","cursor","windsurf","cline","copilot","aider","opencode","generic")]
    [string]$Tool = "",
    [string]$Division = "",
    [switch]$DryRun,
    [switch]$TUI,
    [switch]$List,
    [switch]$Help,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$ManifestDir = "$env:USERPROFILE\.ultimate-dev"
$ManifestFile = "$ManifestDir\install-manifest.json"

# All available divisions
$AllDivisions = @("engineering", "agency", "business", "research", "domain", "meta")

# Colors for TUI
function Write-ColorOutput {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Success { param([string]$Text) Write-ColorOutput "✅ $Text" "Green" }
function Write-Warning { param([string]$Text) Write-ColorOutput "⚠️  $Text" "Yellow" }
function Write-Error { param([string]$Text) Write-ColorOutput "❌ $Text" "Red" }
function Write-Info { param([string]$Text) Write-ColorOutput "ℹ️  $Text" "Cyan" }

function Write-Header {
    Clear-Host
    Write-ColorOutput ""
    Write-ColorOutput "╔══════════════════════════════════════════════════════════════╗" "Cyan"
    Write-ColorOutput "║           ultimate-dev Installer v$(Get-Content "$SkillDir\VERSION" -ErrorAction SilentlyContinue)                  ║" "Cyan"
    Write-ColorOutput "║     Master Software Engineering Orchestrator               ║" "Cyan"
    Write-ColorOutput "╚══════════════════════════════════════════════════════════════╝" "Cyan"
    Write-ColorOutput ""
}

function Write-Section {
    param([string]$Title)
    Write-ColorOutput ""
    Write-ColorOutput "── $Title ──" "Yellow"
    Write-ColorOutput ""
}

# TUI Selection Menu
function Select-Option {
    param(
        [string]$Title,
        [array]$Options
    )
    
    $selected = 0
    $last = $Options.Count - 1
    
    Write-Section $Title
    
    while ($true) {
        # Move cursor to start of options
        $startY = [Console]::CursorTop
        
        for ($i = 0; $i -lt $Options.Count; $i++) {
            if ($i -eq $selected) {
                Write-ColorOutput "  ► $($Options[$i])" "Green"
            } else {
                Write-Host "    $($Options[$i])"
            }
        }
        
        Write-ColorOutput ""
        Write-ColorOutput "  Use ↑/↓ arrows to select, Enter to confirm, Esc to quit" "Cyan"
        
        $key = [Console]::ReadKey($true)
        
        switch ($key.Key) {
            "UpArrow" {
                $selected--
                if ($selected -lt 0) { $selected = $last }
            }
            "DownArrow" {
                $selected++
                if ($selected -gt $last) { $selected = 0 }
            }
            "Enter" {
                return $Options[$selected]
            }
            "Escape" {
                return $null
            }
        }
        
        # Clear and redraw
        [Console]::SetCursorPosition(0, $startY)
        for ($i = 0; $i -lt $Options.Count; $i++) {
            Write-Host ("    " + $Options[$i]).PadRight(50)
        }
    }
}

# Multi-select menu
function Select-MultipleOptions {
    param(
        [string]$Title,
        [array]$Options
    )
    
    $selected = @{}
    for ($i = 0; $i -lt $Options.Count; $i++) {
        $selected[$i] = $false
    }
    
    $cursor = 0
    $last = $Options.Count - 1
    
    Write-Section $Title
    
    while ($true) {
        $startY = [Console]::CursorTop
        
        for ($i = 0; $i -lt $Options.Count; $i++) {
            $marker = if ($selected[$i]) { "✓" } else { " " }
            if ($i -eq $cursor) {
                Write-ColorOutput "  ► [$marker] $($Options[$i])" "Green"
            } else {
                Write-Host "    [$marker] $($Options[$i])"
            }
        }
        
        Write-ColorOutput ""
        Write-ColorOutput "  Use ↑/↓ to move, Space to toggle, Enter to confirm, A for all, N for none, Esc to quit" "Cyan"
        
        $key = [Console]::ReadKey($true)
        
        switch ($key.Key) {
            "UpArrow" {
                $cursor--
                if ($cursor -lt 0) { $cursor = $last }
            }
            "DownArrow" {
                $cursor++
                if ($cursor -gt $last) { $cursor = 0 }
            }
            "Spacebar" {
                $selected[$cursor] = -not $selected[$cursor]
            }
            "Enter" {
                $result = @()
                for ($i = 0; $i -lt $Options.Count; $i++) {
                    if ($selected[$i]) {
                        $result += $Options[$i]
                    }
                }
                return ($result -join ",")
            }
            "Escape" {
                return $null
            }
            default {
                if ($key.KeyChar -eq 'a' -or $key.KeyChar -eq 'A') {
                    for ($i = 0; $i -lt $Options.Count; $i++) {
                        $selected[$i] = $true
                    }
                } elseif ($key.KeyChar -eq 'n' -or $key.KeyChar -eq 'N') {
                    for ($i = 0; $i -lt $Options.Count; $i++) {
                        $selected[$i] = $false
                    }
                }
            }
        }
        
        # Clear and redraw
        [Console]::SetCursorPosition(0, $startY)
        for ($i = 0; $i -lt $Options.Count; $i++) {
            $marker = if ($selected[$i]) { "✓" } else { " " }
            Write-Host ("    [$marker] " + $Options[$i]).PadRight(50)
        }
    }
}

# Detect installed agent tools
function Detect-AgentTools {
    Write-Section "Detecting Installed Agent Tools"
    
    $toolsFound = @()
    
    # Claude Code
    if (Test-Path "$env:USERPROFILE\.claude" -ErrorAction SilentlyContinue) {
        Write-Success "Claude Code detected"
        $toolsFound += "claude-code"
    } else {
        Write-Warning "Claude Code not found"
    }
    
    # Codex CLI
    if (Test-Path "$env:USERPROFILE\.codex" -ErrorAction SilentlyContinue) {
        Write-Success "Codex CLI detected"
        $toolsFound += "codex"
    } else {
        Write-Warning "Codex CLI not found"
    }
    
    # Cursor
    if (Test-Path "$env:USERPROFILE\.cursor" -ErrorAction SilentlyContinue) {
        Write-Success "Cursor detected"
        $toolsFound += "cursor"
    } else {
        Write-Warning "Cursor not found"
    }
    
    # Windsurf
    if (Test-Path "$env:USERPROFILE\.windsurf" -ErrorAction SilentlyContinue) {
        Write-Success "Windsurf detected"
        $toolsFound += "windsurf"
    } else {
        Write-Warning "Windsurf not found"
    }
    
    # Cline
    if (Test-Path "$env:USERPROFILE\.cline" -ErrorAction SilentlyContinue) {
        Write-Success "Cline detected"
        $toolsFound += "cline"
    } else {
        Write-Warning "Cline not found"
    }
    
    # GitHub Copilot
    if (Test-Path "$env:USERPROFILE\.github" -ErrorAction SilentlyContinue) {
        Write-Success "GitHub Copilot detected"
        $toolsFound += "copilot"
    } else {
        Write-Warning "GitHub Copilot not found"
    }
    
    # Aider
    if (Get-Command aider -ErrorAction SilentlyContinue) {
        Write-Success "Aider detected"
        $toolsFound += "aider"
    } else {
        Write-Warning "Aider not found"
    }
    
    # OpenCode
    if (Test-Path "$env:USERPROFILE\.opencode" -ErrorAction SilentlyContinue) {
        Write-Success "OpenCode detected"
        $toolsFound += "opencode"
    } else {
        Write-Warning "OpenCode not found"
    }
    
    Write-ColorOutput ""
    
    if ($toolsFound.Count -eq 0) {
        Write-Warning "No known agent tools detected"
        $toolsFound += "generic"
    }
    
    return $toolsFound
}

# Get tool installation path
function Get-ToolPath {
    param(
        [string]$Tool,
        [string]$Scope
    )
    
    switch ($Tool) {
        "claude-code" {
            if ($Scope -eq "project") {
                return ".claude\skills\ultimate-dev"
            } else {
                return "$env:USERPROFILE\.claude\skills\ultimate-dev"
            }
        }
        "codex" {
            if ($Scope -eq "project") {
                return ".codex\skills\ultimate-dev"
            } else {
                return "$env:USERPROFILE\.codex\skills\ultimate-dev"
            }
        }
        "cursor" {
            return ".cursor\rules"
        }
        "windsurf" {
            if ($Scope -eq "project") {
                return ".windsurf"
            } else {
                return "$env:USERPROFILE\.windsurf"
            }
        }
        "cline" {
            if ($Scope -eq "project") {
                return ".cline"
            } else {
                return "$env:USERPROFILE\.cline"
            }
        }
        "copilot" {
            if ($Scope -eq "project") {
                return ".github"
            } else {
                return "$env:USERPROFILE\.github"
            }
        }
        "aider" {
            if ($Scope -eq "project") {
                return ".aider"
            } else {
                return "$env:USERPROFILE\.aider"
            }
        }
        "opencode" {
            if ($Scope -eq "project") {
                return ".opencode\skills\ultimate-dev"
            } else {
                return "$env:USERPROFILE\.opencode\skills\ultimate-dev"
            }
        }
        default {
            if ($Scope -eq "project") {
                return ".agents\skills\ultimate-dev"
            } else {
                return "$env:USERPROFILE\.agents\skills\ultimate-dev"
            }
        }
    }
}

# Check if a division should be installed
function Should-InstallDivision {
    param([string]$Div)
    
    if ($Division -eq "all" -or $Division -eq "") {
        return $true
    }
    
    return $Division -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -eq $Div }
}

# Get module files for a division
function Get-ModulesForDivision {
    param([string]$Div)
    
    switch ($Div) {
        "engineering" {
            return @(
                "modules\engineering\backend.md",
                "modules\engineering\frontend.md",
                "modules\engineering\architecture.md",
                "modules\engineering\database.md",
                "modules\engineering\security.md",
                "modules\engineering\devops.md",
                "modules\engineering\mobile.md",
                "modules\engineering\testing-qa.md",
                "modules\engineering\documentation.md"
            )
        }
        "agency" {
            return @(
                "modules\agency\project-management.md",
                "modules\agency\product.md",
                "modules\agency\design-handoff.md",
                "modules\agency\client-communication.md"
            )
        }
        "business" {
            return @(
                "modules\marketing\marketing.md",
                "modules\sales\sales.md",
                "modules\finance\finance.md",
                "modules\support\support.md",
                "modules\paid-media\paid-media.md"
            )
        }
        "research" {
            return @(
                "modules\research\research.md",
                "modules\academic\academic.md"
            )
        }
        "domain" {
            return @(
                "modules\healthcare\healthcare.md",
                "modules\game-dev\game-dev.md",
                "modules\gis\gis.md",
                "modules\spatial-computing\spatial-computing.md",
                "modules\specialized\specialized.md"
            )
        }
        "meta" {
            return @(
                "personas\meta\skill-maintainer.md",
                "personas\meta\gap-tracker.md"
            )
        }
        default { return @() }
    }
}

# Write install manifest
function Write-Manifest {
    param(
        [string]$Target,
        [array]$InstalledFiles
    )
    
    if ($DryRun) {
        Write-Info "[dry-run] Would write manifest to $ManifestFile"
        return
    }
    
    New-Item -ItemType Directory -Force -Path $ManifestDir | Out-Null
    
    $version = if (Test-Path "$SkillDir\VERSION") { Get-Content "$SkillDir\VERSION" -Raw } else { "1.1.1" }
    $timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    
    $manifest = @{
        version = $version.Trim()
        installed_at = $timestamp
        scope = $Scope
        target = $Target
        tool = if ($Tool) { $Tool } else { "auto-detect" }
        division = if ($Division) { $Division } else { "all" }
        files = $InstalledFiles
    } | ConvertTo-Json -Depth 3
    
    Set-Content -Path $ManifestFile -Value $manifest
    Write-Success "Manifest written to $ManifestFile"
}

# Install function
function Install-Skill {
    param([string]$Target)
    
    Write-Info "Installing to: $Target"
    if ($DryRun) {
        Write-Info "[dry-run] Would install to $Target"
        return
    }
    
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    
    # Core files
    Copy-Item -Force "$SkillDir\SKILL.md" "$Target\"
    Copy-Item -Force "$SkillDir\README.md" "$Target\"
    Copy-Item -Force "$SkillDir\ARCHITECTURE.md" "$Target\"
    Copy-Item -Force "$SkillDir\CONTRIBUTING.md" "$Target\"
    Copy-Item -Force "$SkillDir\VERSION" "$Target\"
    Copy-Item -Force "$SkillDir\CHANGELOG.md" "$Target\"
    Copy-Item -Force "$SkillDir\skill-manifest.yaml" "$Target\"
    
    # Router
    Copy-Item -Recurse -Force "$SkillDir\router" "$Target\"
    
    # Scripts
    Copy-Item -Recurse -Force "$SkillDir\scripts" "$Target\"
    
    # Adapters
    Copy-Item -Recurse -Force "$SkillDir\adapters" "$Target\"
    
    # Personas
    Copy-Item -Recurse -Force "$SkillDir\personas" "$Target\"
    
    $installedFiles = @(
        "SKILL.md", "README.md", "ARCHITECTURE.md", "CONTRIBUTING.md",
        "VERSION", "CHANGELOG.md", "skill-manifest.yaml"
    )
    
    # Install modules by division
    foreach ($div in $AllDivisions) {
        if (Should-InstallDivision $div) {
            $modules = Get-ModulesForDivision $div
            foreach ($mod in $modules) {
                $sourcePath = Join-Path $SkillDir $mod
                $destPath = Join-Path $Target $mod
                $destDir = Split-Path $destPath -Parent
                
                if (Test-Path $sourcePath) {
                    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
                    Copy-Item -Force $sourcePath $destPath
                    $installedFiles += $mod
                }
            }
            Write-Success "Installed $div modules"
        }
    }
    
    # Always install cross-cutting modules
    Copy-Item -Force "$SkillDir\modules\_emerging-tech-handler.md" "$Target\modules\"
    Copy-Item -Force "$SkillDir\modules\_universal-principles.md" "$Target\modules\"
    $installedFiles += "modules\_emerging-tech-handler.md", "modules\_universal-principles.md"
    
    # Write manifest
    Write-Manifest $Target $installedFiles
    
    Write-Success "Installed to $Target"
}

# Show help
if ($Help) {
    Write-Header
    Write-ColorOutput "Usage: .\install.ps1 [OPTIONS]" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "White"
    Write-ColorOutput "  -Scope user|project     Install scope (default: user)" "White"
    Write-ColorOutput "  -Tool TOOL              Target tool (see -List for options)" "White"
    Write-ColorOutput "  -Division DIV1,DIV2    Comma-separated divisions to install" "White"
    Write-ColorOutput "  -DryRun                 Show what would be installed without doing it" "White"
    Write-ColorOutput "  -TUI                    Enable interactive TUI mode" "White"
    Write-ColorOutput "  -List                   List available divisions and tools" "White"
    Write-ColorOutput "  -Help                   Show this help" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" "White"
    Write-ColorOutput "  .\install.ps1 -TUI                          # Interactive installation" "White"
    Write-ColorOutput "  .\install.ps1 -Tool claude-code -Scope user  # Install for Claude Code" "White"
    Write-ColorOutput "  .\install.ps1 -Tool generic -Division engineering,security" "White"
    exit 0
}

# List divisions and tools
if ($List) {
    Write-Header
    Write-ColorOutput "Available divisions:" "White"
    Write-ColorOutput "  engineering  — backend, frontend, architecture, database, security, devops, mobile, testing-qa, documentation" "White"
    Write-ColorOutput "  agency       — project-management, product, design-handoff, client-communication" "White"
    Write-ColorOutput "  business     — marketing, sales, finance, support, paid-media" "White"
    Write-ColorOutput "  research     — research, academic" "White"
    Write-ColorOutput "  domain       — healthcare, game-dev, gis, spatial-computing, specialized" "White"
    Write-ColorOutput "  meta         — skill-maintainer, gap-tracker (system maintenance)" "White"
    Write-ColorOutput "  all          — everything (default)" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Available tools:" "White"
    Write-ColorOutput "  claude-code  — Claude Code (Anthropic)" "White"
    Write-ColorOutput "  codex        — Codex CLI (OpenAI)" "White"
    Write-ColorOutput "  cursor       — Cursor IDE" "White"
    Write-ColorOutput "  windsurf     — Windsurf IDE" "White"
    Write-ColorOutput "  cline        — Cline (VS Code)" "White"
    Write-ColorOutput "  copilot      — GitHub Copilot" "White"
    Write-ColorOutput "  aider        — Aider" "White"
    Write-ColorOutput "  opencode     — OpenCode" "White"
    Write-ColorOutput "  generic      — Generic CLI fallback" "White"
    exit 0
}

# Main installation flow
Write-Header

# TUI Mode
if ($TUI) {
    # Select scope
    $scopeOptions = @("User (global)", "Project (local)")
    $scopeResult = Select-Option -Title "Select Installation Scope" -Options $scopeOptions
    
    if ($scopeResult -eq $null) { exit 1 }
    
    switch ($scopeResult) {
        "User (global)" { $Scope = "user" }
        "Project (local)" { $Scope = "project" }
    }
    
    # Detect tools
    $toolsFound = Detect-AgentTools
    
    # Select tool
    if ($toolsFound.Count -gt 1) {
        $toolResult = Select-Option -Title "Select Target Tool" -Options $toolsFound
        if ($toolResult -eq $null) { exit 1 }
        $Tool = $toolResult
    } elseif ($toolsFound.Count -eq 1) {
        $Tool = $toolsFound[0]
        Write-Info "Auto-selected: $Tool"
    } else {
        $Tool = "generic"
    }
    
    # Select divisions
    $divisionOptions = @("engineering", "agency", "business", "research", "domain", "meta", "all")
    $divisionResult = Select-MultipleOptions -Title "Select Divisions to Install" -Options $divisionOptions
    
    if ($divisionResult -eq $null -or $divisionResult -eq "") {
        $Division = "all"
    } else {
        $Division = $divisionResult
    }
    
    # Confirm installation
    Write-Section "Installation Summary"
    Write-ColorOutput "Scope: $Scope" "White"
    Write-ColorOutput "Tool: $Tool" "White"
    Write-ColorOutput "Divisions: $Division" "White"
    Write-ColorOutput "Target: $(Get-ToolPath $Tool $Scope)" "White"
    Write-ColorOutput ""
    
    $confirm = Read-Host "Proceed with installation? (y/N)"
    if ($confirm -notmatch '^[Yy]$') {
        Write-Info "Installation cancelled"
        exit 0
    }
}

# Validate inputs
if ($Scope -eq "") {
    $Scope = "user"
}

if ($Tool -eq "") {
    # Auto-detect
    $toolsFound = Detect-AgentTools
    if ($toolsFound.Count -gt 0) {
        $Tool = $toolsFound[0]
    } else {
        $Tool = "generic"
    }
}

if ($Division -eq "") {
    $Division = "all"
}

# Show installation info
Write-Section "Installing ultimate-dev"
Write-ColorOutput "Scope: $Scope" "White"
Write-ColorOutput "Tool: $Tool" "White"
Write-ColorOutput "Divisions: $Division" "White"
Write-ColorOutput "Target: $(Get-ToolPath $Tool $Scope)" "White"
Write-ColorOutput ""

# Install based on tool
switch ($Tool) {
    "claude-code" {
        $target = if ($Scope -eq "project") { ".claude\skills\ultimate-dev" } else { "$env:USERPROFILE\.claude\skills\ultimate-dev" }
        Install-Skill $target
    }
    "codex" {
        $target = if ($Scope -eq "project") {
            Write-Info "Codex project scope: creating AGENTS.md reference"
            if (-not $DryRun) {
                @"
# Agent Instructions

This project uses the **ultimate-dev** skill for engineering tasks.

## Usage
When working on engineering tasks, follow the classification and routing rules defined in the ultimate-dev skill.

## Skill Location
- User scope: ``~\.codex\skills\ultimate-dev\``
- See ``~\.codex\skills\ultimate-dev\README.md`` for full documentation.
"@ | Set-Content "AGENTS.md"
                Write-Success "Created AGENTS.md"
            }
            return
        } else { "$env:USERPROFILE\.codex\skills\ultimate-dev" }
        Install-Skill $target
    }
    "cursor" {
        Write-Info "Cursor: Installing to .cursor\rules\"
        $target = ".cursor\rules"
        Install-Skill $target
    }
    "windsurf" {
        $target = if ($Scope -eq "project") { ".windsurf" } else { "$env:USERPROFILE\.windsurf" }
        Install-Skill $target
    }
    "cline" {
        $target = if ($Scope -eq "project") { ".cline" } else { "$env:USERPROFILE\.cline" }
        Install-Skill $target
    }
    "copilot" {
        $target = if ($Scope -eq "project") { ".github" } else { "$env:USERPROFILE\.github" }
        Install-Skill $target
    }
    "aider" {
        $target = if ($Scope -eq "project") { ".aider" } else { "$env:USERPROFILE\.aider" }
        Install-Skill $target
    }
    "opencode" {
        $target = if ($Scope -eq "project") { ".opencode\skills\ultimate-dev" } else { "$env:USERPROFILE\.opencode\skills\ultimate-dev" }
        Install-Skill $target
    }
    default {
        $target = if ($Scope -eq "project") { ".agents\skills\ultimate-dev" } else { "$env:USERPROFILE\.agents\skills\ultimate-dev" }
        Install-Skill $target
    }
}

Write-Section "Installation Complete"
Write-Success "ultimate-dev has been installed successfully!"
Write-ColorOutput ""
Write-ColorOutput "Installed divisions: $Division" "White"
Write-ColorOutput "Target: $(Get-ToolPath $Tool $Scope)" "White"
Write-ColorOutput ""
Write-Info "Restart your AI coding tool to activate the skill."
Write-ColorOutput ""
Write-Info "For documentation, see: $(Get-ToolPath $Tool $Scope)\README.md"