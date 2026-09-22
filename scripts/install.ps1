# ultimate-dev v2.0.0 — Installer for Windows
# Usage: .\scripts\install.ps1 [-Global] [-Project <DIR>] [-Uninstall] [-Help]
#
# Asks one question: install globally or to a specific project?

param(
    [switch]$Global,
    [string]$Project = "",
    [switch]$Uninstall,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$Version = if (Test-Path "$SkillDir\VERSION") { (Get-Content "$SkillDir\VERSION" -Raw).Trim() } else { "2.0.0" }

# ─── HELP ──────────────────────────────────────────────────
if ($Help) {
    Write-Host ""
    Write-Host "ultimate-dev v$Version Installer" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Global           Install to ~/.agents/skills/ultimate-dev (shared across projects)"
    Write-Host "  -Project <DIR>   Install to DIR\.agents\skills\ultimate-dev (project-specific)"
    Write-Host "  -Uninstall        Remove the skill installation"
    Write-Host "  -Help             Show this help"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.ps1                    # Interactive — asks where to install"
    Write-Host "  .\install.ps1 -Global            # Install globally"
    Write-Host "  .\install.ps1 -Project C:\my-app # Install for C:\my-app only"
    Write-Host ""
    exit 0
}

# ─── HEADER ────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ultimate-dev v$Version Installer               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── FUNCTIONS ─────────────────────────────────────────────
function Install-Skill {
    param([string]$Target)

    Write-Host ""
    Write-Host "Installing to: $Target" -ForegroundColor Cyan
    Write-Host ""

    # Create target directory
    New-Item -ItemType Directory -Force -Path $Target | Out-Null

    # Copy core files
    Copy-Item -Force "$SkillDir\SKILL.md" "$Target\"
    Copy-Item -Force "$SkillDir\README.md" "$Target\"
    Copy-Item -Force "$SkillDir\VERSION" "$Target\"
    Copy-Item -Force "$SkillDir\skill-manifest.yaml" "$Target\"

    # Copy directories (only if they exist and have content)
    $dirs = @("agents", "skills", "modules", "config", "prompts", "workflows",
              "schemas", "rules", "router", "templates", "tools", "scripts",
              "tests", "examples", "evals", "reference", "memory", "changelog")

    foreach ($dir in $dirs) {
        $sourcePath = Join-Path $SkillDir $dir
        if (Test-Path $sourcePath) {
            $items = Get-ChildItem $sourcePath -Force
            if ($items.Count -gt 0) {
                Copy-Item -Recurse -Force $sourcePath "$Target\"
            }
        }
    }

    # Verify installation
    if ((Test-Path "$Target\SKILL.md") -and (Test-Path "$Target\skill-manifest.yaml")) {
        $agentCount = if (Test-Path "$Target\agents") { (Get-ChildItem "$Target\agents" -Recurse -Filter "*.md").Count } else { 0 }
        $skillCount = if (Test-Path "$Target\skills") { (Get-ChildItem "$Target\skills" -Recurse -Filter "SKILL.md").Count } else { 0 }
        $moduleCount = if (Test-Path "$Target\modules") { (Get-ChildItem "$Target\modules" -Recurse -Filter "*.md").Count } else { 0 }

        Write-Host ""
        Write-Host "✅ Installation successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Installed to: $Target" -ForegroundColor White
        Write-Host "  Version:      $Version" -ForegroundColor White
        Write-Host "  Agents:       $agentCount" -ForegroundColor White
        Write-Host "  Skills:       $skillCount" -ForegroundColor White
        Write-Host "  Modules:      $moduleCount" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "❌ Installation failed — core files missing" -ForegroundColor Red
        exit 1
    }
}

function Uninstall-Skill {
    param([string]$Target)
    if (Test-Path $Target) {
        Remove-Item -Recurse -Force $Target
        Write-Host "✅ Uninstalled: $Target" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Nothing to uninstall at: $Target" -ForegroundColor Yellow
    }
}

# ─── UNINSTALL ─────────────────────────────────────────────
if ($Uninstall) {
    Write-Host "Uninstalling ultimate-dev..." -ForegroundColor Yellow
    Uninstall-Skill "$env:USERPROFILE\.agents\skills\ultimate-dev"
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# ─── INTERACTIVE MODE (no arguments) ───────────────────────
if (-not $Global -and -not $Project) {
    Write-Host "Where would you like to install ultimate-dev?" -ForegroundColor White
    Write-Host ""
    Write-Host "  1) Global    — shared across all projects" -ForegroundColor White
    Write-Host "                 → ~/.agents/skills/ultimate-dev/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2) Project   — specific to one project" -ForegroundColor White
    Write-Host "                 → <project>/.agents/skills/ultimate-dev/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Press 1 for global, 2 for project, or Esc to quit" -ForegroundColor Cyan
    Write-Host ""

    $key = [Console]::ReadKey($true)
    Write-Host ""

    switch ($key.KeyChar) {
        '1' { $Global = $true }
        '2' {
            Write-Host "Enter project path (e.g., C:\my-app or . for current directory):" -ForegroundColor Cyan
            $Project = Read-Host
            if ($Project -eq ".") { $Project = (Get-Location).Path }
            if (-not (Test-Path $Project)) {
                Write-Host "❌ Directory does not exist: $Project" -ForegroundColor Red
                exit 1
            }
        }
        default {
            Write-Host "Cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
}

# ─── DETERMINE TARGET ──────────────────────────────────────
if ($Global) {
    $Target = "$env:USERPROFILE\.agents\skills\ultimate-dev"
} else {
    if (-not $Project) { $Project = (Get-Location).Path }
    $Target = "$Project\.agents\skills\ultimate-dev"
}

# ─── CONFIRM ───────────────────────────────────────────────
$scope = if ($Global) { "global" } else { "project" }
Write-Host ""
Write-Host "  Scope:  $scope" -ForegroundColor White
Write-Host "  Target: $Target" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Proceed? (y/N)"
if ($confirm -notmatch '^[Yy]$') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# ─── INSTALL ───────────────────────────────────────────────
Install-Skill $Target

# ─── NEXT STEPS ────────────────────────────────────────────
Write-Host "Next steps:" -ForegroundColor White
if ($Global) {
    Write-Host "  The skill is available to all projects." -ForegroundColor White
    Write-Host "  Your AI coding tool will auto-detect it." -ForegroundColor White
} else {
    Write-Host "  The skill is installed in your project." -ForegroundColor White
    Write-Host "  Your AI coding tool will auto-detect it." -ForegroundColor White
}
Write-Host ""
Write-Host "  To uninstall: .\install.ps1 -Uninstall" -ForegroundColor Cyan
Write-Host ""
