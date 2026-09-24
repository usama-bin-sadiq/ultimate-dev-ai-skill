# Install the Ultimate-Dev skill from a repository checkout (PowerShell).
# The root VERSION file is the sole version source.  A sibling staging
# directory is validated and swapped into place; memory is never hard-deleted.

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
$SkillDir = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $SkillDir
$VersionFile = Join-Path $RepoRoot 'VERSION'

function Write-Info([string]$Message) { Write-Host "  ℹ $Message" -ForegroundColor Cyan }
function Write-Status([string]$Message) { Write-Host "  ✔ $Message" -ForegroundColor Green }
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

function Assert-NotReparsePoint([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $item = Get-Item -LiteralPath $Path -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing to modify reparse point: $Path"
        }
    }
}

function Remove-StagedPath([string]$Path, [string]$Parent) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) {
        return
    }
    $full = [System.IO.Path]::GetFullPath($Path)
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([char[]]"\/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($parentFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the staging parent: $full"
    }
    Remove-Item -LiteralPath $full -Recurse -Force
}

function Remove-GitignoreEntry([string]$ProjectDir) {
    $gitignore = Join-Path $ProjectDir '.gitignore'
    $entry = '.memory/ultimate-dev/'
    if (-not (Test-Path -LiteralPath $gitignore -PathType Leaf)) { return }
    Assert-NotReparsePoint $gitignore
    $lines = @(Get-Content -LiteralPath $gitignore)
    $remaining = @($lines | Where-Object { $_ -cne $entry })
    if ($remaining.Count -eq $lines.Count) { return }
    $tmp = Join-Path $ProjectDir ('.gitignore.tmp.' + [guid]::NewGuid().ToString('N'))
    try {
        if ($remaining.Count -gt 0) {
            Set-Content -LiteralPath $tmp -Value $remaining -Encoding utf8
        } else {
            Set-Content -LiteralPath $tmp -Value '' -Encoding utf8
        }
        Move-Item -LiteralPath $tmp -Destination $gitignore -Force
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}

function Ensure-MemoryScaffolding([string]$ProjectDir, [string]$Target, [bool]$IsGlobal) {
    $memoryRoot = Join-Path $ProjectDir '.memory'
    $memoryDir = Join-Path $memoryRoot 'ultimate-dev'
    Assert-NotReparsePoint $memoryRoot
    Assert-NotReparsePoint $memoryDir
    New-Item -ItemType Directory -Force -Path (Join-Path $memoryDir 'tasks') | Out-Null

    $memoryIgnore = Join-Path $memoryDir '.gitignore'
    if (-not (Test-Path -LiteralPath $memoryIgnore)) {
        $tmp = Join-Path $memoryDir ('.gitignore.tmp.' + [guid]::NewGuid().ToString('N'))
        Set-Content -LiteralPath $tmp -Value 'tasks/*' -Encoding utf8
        Move-Item -LiteralPath $tmp -Destination $memoryIgnore -Force
    }

    $seed = Join-Path $memoryDir 'project-memory.md'
    $template = Join-Path $Target 'memory/project-memory.md'
    if (-not (Test-Path -LiteralPath $seed) -and (Test-Path -LiteralPath $template -PathType Leaf)) {
        $tmp = Join-Path $memoryDir ('project-memory.tmp.' + [guid]::NewGuid().ToString('N'))
        Copy-Item -LiteralPath $template -Destination $tmp -Force
        Move-Item -LiteralPath $tmp -Destination $seed -Force
    }

    # Global installs must not modify a repository's ignore file.  Project
    # installs add exactly one managed entry, preserving all existing content.
    if (-not $IsGlobal) {
        $gitignore = Join-Path $ProjectDir '.gitignore'
        $entry = '.memory/ultimate-dev/'
        Assert-NotReparsePoint $gitignore
        $existing = if (Test-Path -LiteralPath $gitignore -PathType Leaf) {
            @(Get-Content -LiteralPath $gitignore)
        } else { @() }
        if ($existing -notcontains $entry) {
            $tmp = Join-Path $ProjectDir ('.gitignore.tmp.' + [guid]::NewGuid().ToString('N'))
            $newContent = if ($existing.Count -gt 0) {
                ((($existing -join "`n") -replace "[`r`n]+$", '') + "`n" + $entry + "`n")
            } else {
                ($entry + "`n")
            }
            Set-Content -LiteralPath $tmp -Value $newContent -Encoding utf8 -NoNewline
            Move-Item -LiteralPath $tmp -Destination $gitignore -Force
        }
    }
}

if ($Help) {
    Write-Host 'Usage: install.ps1 [--Global|--Project DIR] [--Yes] [--Uninstall] [--CleanGitignore]'
    Write-Host 'Memory deletion is disabled; use the runtime retention workflow.'
    exit 0
}

if ($All) { $CleanMemory = $true; $CleanGitignore = $true }
if ($CleanMemory) {
    throw 'Memory deletion is disabled; use the runtime retention workflow with a dry-run and confirmation.'
}

$version = Get-CanonicalVersion
if ($Global -and -not [string]::IsNullOrWhiteSpace($Project)) {
    throw 'Choose either -Global or -Project.'
}
$homeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
if ($Global -and [string]::IsNullOrWhiteSpace($homeDir)) { throw 'HOME/USERPROFILE is not set.' }

if ($Global) {
    $projectDir = (Resolve-Path -LiteralPath $homeDir).Path
    $target = Join-Path $projectDir '.agents/skills/ultimate-dev'
    $isGlobal = $true
} else {
    $projectInput = if ([string]::IsNullOrWhiteSpace($Project)) { (Get-Location).Path } else { $Project }
    $projectDir = (Resolve-Path -LiteralPath $projectInput).Path
    $target = Join-Path $projectDir '.agents/skills/ultimate-dev'
    $isGlobal = $false
}

foreach ($pathComponent in @(
    (Join-Path $projectDir '.agents'),
    (Join-Path $projectDir '.agents/skills'),
    (Join-Path $projectDir '.claude'),
    (Join-Path $projectDir '.cursor')
)) {
    Assert-NotReparsePoint $pathComponent
}
$targetParent = Split-Path -Parent $target
New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
$targetParent = (Resolve-Path -LiteralPath $targetParent).Path
Assert-NotReparsePoint $target
if ((Test-Path -LiteralPath $target) -and -not (Get-Item -LiteralPath $target -Force).PSIsContainer) {
    throw "Skill target exists but is not a directory: $target"
}
$memoryRoot = Join-Path $projectDir '.memory'
$memoryDir = Join-Path $memoryRoot 'ultimate-dev'
Assert-NotReparsePoint $memoryRoot
Assert-NotReparsePoint $memoryDir
if ((Test-Path -LiteralPath $memoryRoot) -and -not (Get-Item -LiteralPath $memoryRoot -Force).PSIsContainer) {
    throw "Project memory root is not a directory: $memoryRoot"
}
if ((Test-Path -LiteralPath $memoryDir) -and -not (Get-Item -LiteralPath $memoryDir -Force).PSIsContainer) {
    throw "Project memory path is not a directory: $memoryDir"
}
$projectGitignore = Join-Path $projectDir '.gitignore'
if (-not $isGlobal -and (Test-Path -LiteralPath $projectGitignore)) {
    Assert-NotReparsePoint $projectGitignore
    if ((Get-Item -LiteralPath $projectGitignore -Force).PSIsContainer) {
        throw "Project .gitignore is not a regular file: $projectGitignore"
    }
}
$memoryIgnore = Join-Path $memoryDir '.gitignore'
if (Test-Path -LiteralPath $memoryIgnore) {
    Assert-NotReparsePoint $memoryIgnore
    if ((Get-Item -LiteralPath $memoryIgnore -Force).PSIsContainer) {
        throw "Memory .gitignore is not a regular file: $memoryIgnore"
    }
}

if ($Uninstall) {
    if (-not $Yes) { throw 'Uninstall requires explicit -Yes confirmation.' }
    if (Test-Path -LiteralPath $target -PathType Container) {
        Remove-Item -LiteralPath $target -Recurse -Force
        Write-Status "Removed $target"
    } else {
        Write-Info "Skill target not found: $target"
    }
    if ($CleanGitignore) { Remove-GitignoreEntry $projectDir }
    Write-Info 'Project memory was not deleted; use the retention workflow for memory cleanup.'
    exit 0
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
    if ($reparse) { throw "Staged payload contains a reparse point: $($reparse.FullName)" }
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

    Ensure-MemoryScaffolding $projectDir $target $isGlobal
    Write-Status "Installed Ultimate-Dev $version at $target"
    Write-Info "Project memory: $(Join-Path $projectDir '.memory/ultimate-dev') (deletion is retention-managed)"
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
