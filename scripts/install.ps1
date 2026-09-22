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

if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Global|-Project <DIR>|-Uninstall|-Help]"
    exit 0
}

# Uninstall
if ($Uninstall) {
    $target = "$env:USERPROFILE\.agents\skills\ultimate-dev"
    if (Test-Path $target) { Remove-Item -Recurse -Force $target; Write-Host "✅ Uninstalled" -ForegroundColor Green }
    else { Write-Host "Nothing to uninstall" -ForegroundColor Yellow }
    exit 0
}

# Interactive mode
if (-not $Global -and -not $Project) {
    Write-Host "`nultimate-dev Installer" -ForegroundColor Cyan
    Write-Host "`n  1) Global   — ~/.agents/skills/ultimate-dev/"
    Write-Host "  2) Project  — <project>/.agents/skills/ultimate-dev/`n"
    $key = [Console]::ReadKey($true)
    Write-Host ""
    switch ($key.KeyChar) {
        '1' { $Global = $true }
        '2' {
            Write-Host "Project path:" -ForegroundColor Cyan
            $Project = Read-Host
            if ($Project -eq ".") { $Project = (Get-Location).Path }
            if (-not (Test-Path $Project)) { Write-Host "❌ Not found: $Project" -ForegroundColor Red; exit 1 }
        }
        default { exit 0 }
    }
}

# Target
if ($Global) {
    $Target = "$env:USERPROFILE\.agents\skills\ultimate-dev"
} else {
    if (-not $Project) { $Project = (Get-Location).Path }
    $Target = "$Project\.agents\skills\ultimate-dev"
}

# Confirm
Write-Host "`n  Target: $Target" -ForegroundColor White
$confirm = Read-Host "Proceed? (y/N)"
if ($confirm -notmatch '^[Yy]$') { Write-Host "Cancelled." -ForegroundColor Yellow; exit 0 }

# Install — just copy the whole directory
$parentDir = Split-Path -Parent $Target
if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
if (Test-Path $Target) { Remove-Item -Recurse -Force $Target }
Copy-Item -Recurse -Force $SkillDir $Target

$version = if (Test-Path "$Target\VERSION") { (Get-Content "$Target\VERSION" -Raw).Trim() } else { "unknown" }
$agentCount = if (Test-Path "$Target\agents") { (Get-ChildItem "$Target\agents" -Recurse -Filter "*.md").Count } else { 0 }
$skillCount = if (Test-Path "$Target\skills") { (Get-ChildItem "$Target\skills" -Recurse -Filter "SKILL.md").Count } else { 0 }

Write-Host "`n✅ Installed to $Target" -ForegroundColor Green
Write-Host "   Version: $version"
Write-Host "   Agents: $agentCount"
Write-Host "   Skills: $skillCount`n"
