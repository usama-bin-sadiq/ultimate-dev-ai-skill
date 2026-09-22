# ultimate-dev v2.1.0 — Installer for Windows/macOS/Linux
# Usage: .\install.ps1 [-Global] [-Project <DIR>] [-Uninstall] [-Yes] [-Help]
# https://learn.microsoft.com/en-us/powershell/

param(
    [switch]$Global,
    [string]$Project = "",
    [switch]$Uninstall,
    [switch]$Yes,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Cross-platform home directory
$HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }

$ScriptDir = $PSScriptRoot
$SkillDir = Join-Path (Split-Path -Parent $ScriptDir) "ultimate-dev"

# ─── Helpers ────────────────────────────────────────────────
function Write-Logo {
    $ver = if (Test-Path (Join-Path (Split-Path -Parent $PSScriptRoot) "VERSION")) {
        (Get-Content (Join-Path (Split-Path -Parent $PSScriptRoot) "VERSION") -Raw).Trim()
    } else { "2.1.0" }

    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "  │                                                     │" -ForegroundColor Cyan
    Write-Host "  │            " -ForegroundColor Cyan -NoNewline
    Write-Host "ultimate-dev" -ForegroundColor Magenta -NoNewline
    Write-Host " v$ver                          │" -ForegroundColor Cyan
    Write-Host "  │            ─────────────────                         │" -ForegroundColor Cyan
    Write-Host "  │  " -ForegroundColor Cyan -NoNewline
    Write-Host "Master Software Engineering Orchestrator" -ForegroundColor Magenta -NoNewline
    Write-Host "              │" -ForegroundColor Cyan
    Write-Host "  │  " -ForegroundColor Cyan -NoNewline
    Write-Host "120 agents • 17 skills • 45 modules • Any model" -ForegroundColor DarkGray -NoNewline
    Write-Host "    │" -ForegroundColor Cyan
    Write-Host "  │                                                     │" -ForegroundColor Cyan
    Write-Host "  └─────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status($msg) { Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)    { Write-Host "  ✘ $msg" -ForegroundColor Red }
function Write-Info($msg)   { Write-Host "  ℹ $msg" -ForegroundColor Cyan }
function Write-Header($msg) { Write-Host "`n  ── $msg ──" -ForegroundColor Blue }

# ─── Numbered menu (reliable, portable) ─────────────────────
# Returns selection via $script:MenuResult
$script:MenuResult = 0

function Show-Menu {
    param(
        [string]$Title,
        [string[]]$Options
    )

    $count = $Options.Count

    Write-Host ""
    Write-Host "  $Title" -ForegroundColor White
    Write-Host ""

    for ($i = 0; $i -lt $count; $i++) {
        $num = $i + 1
        Write-Host "    " -NoNewline
        Write-Host "$num)" -ForegroundColor White -NoNewline
        Write-Host " $($Options[$i])" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "  Enter number (1-$count): " -ForegroundColor DarkGray -NoNewline

    $choice = Read-Host

    # Validate
    if ($choice -match '^\d+$') {
        $num = [int]$choice
        if ($num -ge 1 -and $num -le $count) {
            $script:MenuResult = $num
            return $true
        }
    }

    Write-Host "  ✘ Invalid choice. Please enter 1-$count." -ForegroundColor Red
    return $false
}

# ─── Help ───────────────────────────────────────────────────
if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Global|-Project <DIR>|-Uninstall|-Yes|-Help]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Global        Install to ~/.agents/skills/ultimate-dev"
    Write-Host "  -Project DIR   Install to DIR\.agents\skills\ultimate-dev"
    Write-Host "  -Uninstall     Remove the installation"
    Write-Host "  -Yes           Skip confirmation prompt"
    exit 0
}

Write-Logo

# ─── Uninstall ──────────────────────────────────────────────
if ($Uninstall) {
    Write-Header "Uninstalling"
    $target = Join-Path $HomeDir ".agents/skills/ultimate-dev"
    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
        Write-Status "Removed $target"
    } else {
        Write-Warn "Nothing to uninstall"
    }
    exit 0
}

# ─── Interactive mode ───────────────────────────────────────
if (-not $Global -and -not $Project) {
    if ($Yes) {
        $Global = $true
    } else {
        # Scope selection with retry on invalid input
        do {
            $valid = Show-Menu -Title "Where do you want to install?" -Options @(
                "Global    — ~/.agents/skills/ultimate-dev/"
                "Project   — <project>/.agents/skills/ultimate-dev/"
            )
        } while (-not $valid)

        switch ($script:MenuResult) {
            1 { $Global = $true }
            2 {
                $Project = "project"
                Write-Host ""
                Write-Host "  Enter project path:" -ForegroundColor Cyan
                Write-Host "  (e.g., C:\my-app or . for current directory)" -ForegroundColor DarkGray
                Write-Host ""
                Write-Host "  " -NoNewline
                $input_path = Read-Host
                if ($input_path -eq ".") { $input_path = (Get-Location).Path }
                $Project = $input_path
                if (-not (Test-Path $Project)) {
                    Write-Err "Directory not found: $Project"
                    exit 1
                }
            }
        }
    }
}

# ─── Determine target ───────────────────────────────────────
if ($Global) {
    $Target = Join-Path $HomeDir ".agents/skills/ultimate-dev"
} else {
    if (-not $Project -or $Project -eq "project") { $Project = (Get-Location).Path }
    $Target = Join-Path $Project ".agents/skills/ultimate-dev"
}

# ─── Confirm ────────────────────────────────────────────────
Write-Header "Ready to install"
Write-Host ""
$version = if (Test-Path (Join-Path $SkillDir "VERSION")) { (Get-Content (Join-Path $SkillDir "VERSION") -Raw).Trim() } else { "unknown" }
Write-Host "  Source:  $SkillDir" -ForegroundColor White
Write-Host "  Target:  $Target" -ForegroundColor White
Write-Host "  Scope:   $(if ($Global) { 'global' } else { 'project' })" -ForegroundColor White
Write-Host "  Version: $version" -ForegroundColor White
Write-Host ""

if (Test-Path $Target) {
    Write-Warn "Already installed at $Target"
}

if ($Yes) {
    $confirm = 1
} else {
    do {
        $valid = Show-Menu -Title "Proceed?" -Options @("Yes — Install", "No — Cancel")
    } while (-not $valid)
    $confirm = $script:MenuResult
}

if ($confirm -ne 1) {
    Write-Info "Cancelled."
    exit 0
}

# ─── Install ────────────────────────────────────────────────
Write-Header "Installing"

$parentDir = Split-Path -Parent $Target
if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
Copy-Item -Recurse -Force $SkillDir $Target

# Manage .gitignore for project memory directory
$gitignore = Join-Path $Project ".gitignore"
$memoryEntry = ".memory/ultimate-dev/"
if (Test-Path $gitignore) {
    $content = Get-Content $gitignore -Raw
    if ($content -notmatch "^$memoryEntry$") {
        Add-Content $gitignore "`n$memoryEntry"
        Write-Info "Added $memoryEntry to .gitignore"
    }
} else {
    Set-Content $gitignore $memoryEntry
    Write-Info "Created .gitignore with $memoryEntry"
}

$agentCount = if (Test-Path (Join-Path $Target "agents")) { (Get-ChildItem (Join-Path $Target "agents") -Recurse -Filter "*.md").Count } else { 0 }
$skillCount = if (Test-Path (Join-Path $Target "skills")) { (Get-ChildItem (Join-Path $Target "skills") -Recurse -Filter "SKILL.md").Count } else { 0 }
$moduleCount = if (Test-Path (Join-Path $Target "modules")) { (Get-ChildItem (Join-Path $Target "modules") -Recurse -Filter "*.md").Count } else { 0 }
$fileCount = (Get-ChildItem $Target -Recurse -File).Count

Write-Status "Copied $fileCount files"
Write-Status "Version $version"

# ─── Summary ────────────────────────────────────────────────
Write-Header "Installed"
Write-Host ""
Write-Host "  Location:  $Target" -ForegroundColor White
Write-Host "  Agents:    $agentCount" -ForegroundColor White
Write-Host "  Skills:    $skillCount" -ForegroundColor White
Write-Host "  Modules:   $moduleCount" -ForegroundColor White
Write-Host "  Files:     $fileCount" -ForegroundColor White
Write-Host ""

Write-Host "  Next steps:" -ForegroundColor White
if ($Global) {
    Write-Host "  • Your AI coding tool will auto-detect the skill" -ForegroundColor DarkGray
    Write-Host "  • Start a new session and it loads automatically" -ForegroundColor DarkGray
} else {
    Write-Host "  • Open your project in your AI coding tool" -ForegroundColor DarkGray
    Write-Host "  • The skill will be detected automatically" -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "  To uninstall: .\install.ps1 -Uninstall" -ForegroundColor Cyan
Write-Host ""
