# ultimate-dev v2.1.0 — Installer for Windows
# Usage: .\install.ps1 [-Global] [-Project <DIR>] [-Uninstall] [-Help]

param(
    [switch]$Global,
    [string]$Project = "",
    [switch]$Uninstall,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Join-Path (Split-Path -Parent $ScriptDir) "ultimate-dev"

# ─── Helpers ────────────────────────────────────────────────
function Write-Logo {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                       ║" -ForegroundColor Cyan
    Write-Host "  ║   ██╗   ██╗███╗   ██╗██████╗ ███████╗                ║" -ForegroundColor Cyan
    Write-Host "  ║   ██║   ██║████╗  ██║██╔══██╗██╔════╝                ║" -ForegroundColor Cyan
    Write-Host "  ║   ██║   ██║██╔██╗ ██║██║  ██║███████╗                ║" -ForegroundColor Cyan
    Write-Host "  ║   ██║   ██║██║╚██╗██║██║  ██║╚════██║                ║" -ForegroundColor Cyan
    Write-Host "  ║   ╚██████╔╝██║ ╚████║██████╔╝███████║                ║" -ForegroundColor Cyan
    Write-Host "  ║    ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝                ║" -ForegroundColor Cyan
    Write-Host "  ║                                                       ║" -ForegroundColor Cyan
    Write-Host "  ║   Master Software Engineering Orchestrator            ║" -ForegroundColor Magenta
    Write-Host "  ║   120 agents • 17 skills • 45 modules • Any model    ║" -ForegroundColor DarkGray
    Write-Host "  ║                                                       ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status($msg) { Write-Host "  ✔ $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)    { Write-Host "  ✘ $msg" -ForegroundColor Red }
function Write-Info($msg)   { Write-Host "  ℹ $msg" -ForegroundColor Cyan }
function Write-Header($msg) { Write-Host "`n  ── $msg ──" -ForegroundColor Blue }

# ─── Help ───────────────────────────────────────────────────
if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Global|-Project <DIR>|-Uninstall|-Help]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Global        Install to ~/.agents/skills/ultimate-dev"
    Write-Host "  -Project DIR   Install to DIR\.agents\skills\ultimate-dev"
    Write-Host "  -Uninstall     Remove the installation"
    exit 0
}

Write-Logo

# ─── Uninstall ──────────────────────────────────────────────
if ($Uninstall) {
    Write-Header "Uninstalling"
    $target = "$env:USERPROFILE\.agents\skills\ultimate-dev"
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
    Write-Host "  Where do you want to install?" -ForegroundColor White
    Write-Host ""
    Write-Host "    1)  " -ForegroundColor White -NoNewline
    Write-Host "Global" -ForegroundColor Green -NoNewline
    Write-Host "    →  ~/.agents/skills/ultimate-dev/" -ForegroundColor DarkGray
    Write-Host "        Available to all projects on this machine" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    2)  " -ForegroundColor White -NoNewline
    Write-Host "Project" -ForegroundColor Cyan -NoNewline
    Write-Host "   →  <project>/.agents/skills/ultimate-dev/" -ForegroundColor DarkGray
    Write-Host "        Isolated to a single project" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "    Press 1 for global, 2 for project, or Esc to quit" -ForegroundColor DarkGray
    Write-Host ""

    $key = [Console]::ReadKey($true)
    Write-Host ""

    switch ($key.KeyChar) {
        '1' { $Global = $true }
        '2' {
            $Project = "project"
            Write-Host "  Enter project path (e.g., C:\my-app or . for current dir):" -ForegroundColor Cyan
            $input_path = Read-Host
            if ($input_path -eq ".") { $input_path = (Get-Location).Path }
            $Project = $input_path
            if (-not (Test-Path $Project)) {
                Write-Err "Directory not found: $Project"
                exit 1
            }
        }
        default { Write-Info "Cancelled."; exit 0 }
    }
}

# ─── Determine target ───────────────────────────────────────
if ($Global) {
    $Target = "$env:USERPROFILE\.agents\skills\ultimate-dev"
} else {
    if (-not $Project -or $Project -eq "project") { $Project = (Get-Location).Path }
    $Target = "$Project\.agents\skills\ultimate-dev"
}

# ─── Confirm ────────────────────────────────────────────────
Write-Header "Ready to install"
Write-Host ""
Write-Host "  Source:  $SkillDir" -ForegroundColor White
Write-Host "  Target:  $Target" -ForegroundColor White
Write-Host "  Scope:   $(if ($Global) { 'global' } else { 'project' })" -ForegroundColor White
$version = if (Test-Path "$SkillDir\VERSION") { (Get-Content "$SkillDir\VERSION" -Raw).Trim() } else { "unknown" }
Write-Host "  Version: $version" -ForegroundColor White
Write-Host ""

# Check if already installed
if (Test-Path $Target) {
    Write-Warn "Already installed at $Target"
    $confirm = Read-Host "  Replace? (y/N)"
    if ($confirm -notmatch '^[Yy]$') { Write-Info "Keeping existing install."; exit 0 }
    Remove-Item -Recurse -Force $Target
}

$confirm = Read-Host "  Proceed? (y/N)"
if ($confirm -notmatch '^[Yy]$') { Write-Info "Cancelled."; exit 0 }

# ─── Install ────────────────────────────────────────────────
Write-Header "Installing"

$parentDir = Split-Path -Parent $Target
if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
Copy-Item -Recurse -Force $SkillDir $Target

$agentCount = if (Test-Path "$Target\agents") { (Get-ChildItem "$Target\agents" -Recurse -Filter "*.md").Count } else { 0 }
$skillCount = if (Test-Path "$Target\skills") { (Get-ChildItem "$Target\skills" -Recurse -Filter "SKILL.md").Count } else { 0 }
$moduleCount = if (Test-Path "$Target\modules") { (Get-ChildItem "$Target\modules" -Recurse -Filter "*.md").Count } else { 0 }
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

# ─── Next steps ─────────────────────────────────────────────
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
