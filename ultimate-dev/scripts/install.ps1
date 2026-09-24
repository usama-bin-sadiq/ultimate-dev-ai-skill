# Install the Ultimate-Dev skill by copying the inner skill payload.
# The installer is interactive when no scope is supplied. It never creates
# symlinks or writes files outside the selected skill destination.

[CmdletBinding()]
param(
    [switch]$Global,
    [string]$Project = "",
    [switch]$Uninstall,
    [switch]$Yes,
    [switch]$CleanMemory,
    [switch]$CleanGitignore,
    [switch]$All,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$SkillDir = (Resolve-Path -LiteralPath (Split-Path -Parent $ScriptDir)).Path
$RepoRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $SkillDir)).Path
$VersionFile = Join-Path $RepoRoot 'VERSION'
if (-not (Test-Path -LiteralPath $VersionFile -PathType Leaf)) {
    $VersionFile = Join-Path $SkillDir 'VERSION'
}

function Write-Info([string]$Message) { Write-Host "  ℹ $Message" -ForegroundColor Cyan }
function Write-Status([string]$Message) { Write-Host "  ✔ $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "  ⚠ $Message" -ForegroundColor Yellow }
function Write-Err([string]$Message) { Write-Host "  ✘ $Message" -ForegroundColor Red }

function Get-CanonicalVersion {
    if (-not (Test-Path -LiteralPath $VersionFile -PathType Leaf)) {
        throw "Canonical VERSION is missing: $VersionFile"
    }
    $value = (Get-Content -LiteralPath $VersionFile -Raw).Trim()
    if ($value -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        throw "Canonical VERSION is not semantic: $value"
    }
    return $value
}

function Expand-HomePath([string]$Path) {
    if ($Path -eq '~') { return $HOME }
    if ($Path.StartsWith('~/')) { return Join-Path $HOME $Path.Substring(2) }
    return $Path
}

function Resolve-ProjectDirectory([string]$Path) {
    $expanded = Expand-HomePath $Path
    if ([string]::IsNullOrWhiteSpace($expanded)) { $expanded = '.' }
    if (-not (Test-Path -LiteralPath $expanded -PathType Container)) {
        throw "Project directory not found: $expanded"
    }
    return (Resolve-Path -LiteralPath $expanded).Path
}

function Assert-NotReparsePoint([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing to use reparse point: $Path"
        }
    }
}

function Remove-StagedPath([string]$Path, [string]$Parent) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return }
    $full = [System.IO.Path]::GetFullPath($Path)
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([char[]]"\/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($parentFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the staging parent: $full"
    }
    Remove-Item -LiteralPath $full -Recurse -Force
}

function Select-Scope {
    if ($Global) { return 'global' }
    if (-not [string]::IsNullOrWhiteSpace($Project)) { return 'project' }
    if ($Yes) { return 'global' }

    Write-Host "`n  Ultimate-Dev installer" -ForegroundColor Cyan
    Write-Host "  Copy the inner skill folder; no symlinks or extra project files.`n"
    while ($true) {
        Write-Host "  1) Global  — ~/.agents/skills/ultimate-dev/"
        Write-Host "  2) Project — <project>/.agents/skills/ultimate-dev/"
        Write-Host "  q) Cancel`n"
        $choice = (Read-Host '  Enter number (or q to cancel)').Trim().ToLowerInvariant()
        if ($choice -eq '1') { return 'global' }
        if ($choice -eq '2') {
            $inputPath = (Read-Host '  Project directory (Enter for current directory)')
            $script:Project = if ([string]::IsNullOrWhiteSpace($inputPath)) { '.' } else { $inputPath }
            return 'project'
        }
        if ($choice -eq 'q' -or $choice -eq '') {
            Write-Info 'Cancelled.'
            exit 0
        }
        Write-Warn "Invalid choice. Enter 1, 2, or q."
    }
}

if ($Help) {
    Write-Host 'Usage: install.ps1 [--Global|--Project DIR] [--Yes] [--Uninstall]'
    Write-Host 'With no scope, the installer interactively asks Global or Project.'
    Write-Host 'Only the inner skill folder is copied; no symlink or extra project file is created.'
    exit 0
}

if ($All) { $CleanMemory = $true; $CleanGitignore = $true }
if ($CleanMemory) {
    throw 'Memory deletion is disabled; this installer only manages the skill folder.'
}

$version = Get-CanonicalVersion
if ($Global -and -not [string]::IsNullOrWhiteSpace($Project)) {
    throw 'Choose either -Global or -Project.'
}
$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
if ($Global -and [string]::IsNullOrWhiteSpace($homeDir)) { throw 'HOME/USERPROFILE is not set.' }

$scope = Select-Scope
if ($scope -eq 'global') {
    $projectDir = (Resolve-Path -LiteralPath $homeDir).Path
    $target = Join-Path $projectDir '.agents/skills/ultimate-dev'
} else {
    $projectDir = Resolve-ProjectDirectory $Project
    $target = Join-Path $projectDir '.agents/skills/ultimate-dev'
}
$targetParent = Split-Path -Parent $target
foreach ($pathComponent in @(
    (Join-Path $projectDir '.agents'),
    (Join-Path $projectDir '.agents/skills')
)) {
    Assert-NotReparsePoint $pathComponent
}
New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
$targetParent = (Resolve-Path -LiteralPath $targetParent).Path
Assert-NotReparsePoint $targetParent
Assert-NotReparsePoint $target
if ((Test-Path -LiteralPath $target) -and -not (Get-Item -LiteralPath $target -Force).PSIsContainer) {
    throw "Skill target exists but is not a directory: $target"
}

if ($Uninstall) {
    Write-Host "`n  Uninstall target: $target"
    if (-not $Yes) {
        $confirm = (Read-Host '  Proceed? [y/N]').Trim()
        if ($confirm -notmatch '^(?i:y|yes)$') {
            Write-Info 'Cancelled.'
            exit 0
        }
    }
    if (Test-Path -LiteralPath $target -PathType Container) {
        Remove-Item -LiteralPath $target -Recurse -Force
        Write-Status "Removed $target"
    } else {
        Write-Info "Skill target not found: $target"
    }
    if ($CleanGitignore) { Write-Info 'No project .gitignore is managed by this installer.' }
    Write-Info 'No memory, templates, or host configuration files were changed.'
    exit 0
}

Write-Host "`n  Source: $SkillDir"
Write-Host "  Target: $target"
Write-Host "  Scope:  $scope"
Write-Host "  Version: $version`n"
if (-not $Yes) {
    $confirm = (Read-Host '  Proceed? [y/N]').Trim()
    if ($confirm -notmatch '^(?i:y|yes)$') {
        Write-Info 'Cancelled.'
        exit 0
    }
}

$lock = Join-Path $targetParent '.ultimate-dev.install.lock'
$stage = $null
$backup = $null
try {
    try {
        New-Item -ItemType Directory -Path $lock -ErrorAction Stop | Out-Null
    } catch {
        throw "Another installer is already running for $target"
    }

    $stage = Join-Path $targetParent ('.ultimate-dev.stage.' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
    Get-ChildItem -LiteralPath $SkillDir -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $stage -Recurse -Force
    }

    $reparse = Get-ChildItem -LiteralPath $stage -Recurse -Force |
        Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 } |
        Select-Object -First 1
    if ($reparse) { throw "Source skill payload contains a reparse point: $($reparse.FullName)" }

    Copy-Item -LiteralPath $VersionFile -Destination (Join-Path $stage 'VERSION') -Force
    foreach ($relative in @(
        'runtime/core/browser/automation.py',
        'runtime/core/sandbox/runner.py',
        'runtime/core/jev/bridge.py'
    )) {
        $protected = Join-Path $stage $relative
        if (Test-Path -LiteralPath $protected -PathType Leaf) {
            Remove-Item -LiteralPath $protected -Force
        }
    }

    foreach ($required in @('SKILL.md', 'VERSION', 'runtime/core/engine.py')) {
        if (-not (Test-Path -LiteralPath (Join-Path $stage $required) -PathType Leaf)) {
            throw "Staged payload is missing $required"
        }
    }
    $stagedVersion = (Get-Content -LiteralPath (Join-Path $stage 'VERSION') -Raw).Trim()
    if ($stagedVersion -ne $version) { throw 'Staged version does not match canonical VERSION.' }
    $manifest = Join-Path $stage 'skill-manifest.yaml'
    if (Test-Path -LiteralPath $manifest -PathType Leaf) {
        $manifestLine = Get-Content -LiteralPath $manifest | Where-Object { $_ -match '^version:' } | Select-Object -First 1
        if ($manifestLine) {
            $manifestVersion = ($manifestLine -replace '^version:\s*', '').Trim().Trim('"').Trim("'")
            if ($manifestVersion -and $manifestVersion -ne $version) {
                throw 'Staged manifest version does not match canonical VERSION.'
            }
        }
    }

    $agentCount = @(Get-ChildItem -LiteralPath (Join-Path $stage 'agents') -Recurse -File -Filter '*.md' |
        Where-Object { $_.FullName -notmatch '[\\/]_shared[\\/]' }).Count
    $skillCount = @(Get-ChildItem -LiteralPath (Join-Path $stage 'skills') -Recurse -File -Filter 'SKILL.md').Count
    if ($agentCount -lt 1 -or $skillCount -lt 1) { throw 'Staged payload has no agent/skill content.' }

    if (Test-Path -LiteralPath $target -PathType Container) {
        $backup = Join-Path $targetParent ('.ultimate-dev.backup.' + [guid]::NewGuid().ToString('N'))
        Move-Item -LiteralPath $target -Destination $backup -Force
    }
    try {
        Move-Item -LiteralPath $stage -Destination $target -Force
        $stage = $null
    } catch {
        if ($backup -and (Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $target)) {
            Move-Item -LiteralPath $backup -Destination $target -Force
            $backup = $null
        }
        throw
    }
    if ($backup) {
        Remove-StagedPath $backup $targetParent
        $backup = $null
    }

    $fileCount = @(Get-ChildItem -LiteralPath $target -Recurse -File).Count
    Write-Status "Copied the inner skill folder to $target"
    Write-Status "Version $version · $agentCount agents · $skillCount skills · $fileCount files"
    Write-Info 'No symlink, memory, template, or host configuration file was created.'
} catch {
    if ($backup -and (Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $target)) {
        Move-Item -LiteralPath $backup -Destination $target -Force
    }
    throw
} finally {
    if ($stage) { Remove-StagedPath $stage $targetParent }
    if (Test-Path -LiteralPath $lock) {
        Assert-NotReparsePoint $lock
        Remove-Item -LiteralPath $lock -Force
    }
}
