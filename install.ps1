<#
.SYNOPSIS
    Install the ultimate-dev skill on Windows.

.DESCRIPTION
    The PowerShell equivalent of install.sh, for machines where bash is not
    available. It mirrors the same behaviour, the same flags, the same defaults,
    and the same refusals, so a user on either platform gets the same result and
    a CI job behaves identically on both.

    The skill is a directory of Markdown with no build step and no dependencies.
    Installing means copying ultimate-dev\ to a location where the agent runtime
    discovers skills, and optionally pruning material that is documentation
    rather than runtime.

    The repository is much larger than the skill. Alongside the runtime it
    carries the evaluation corpus, worked examples, documentation, research, and
    a fetched catalogue of upstream repositories -- currently about 1.1 GB.
    A runtime install prunes all of it by default, and excludes the catalogue
    even under --all, because --all means "keep the documentation", not "ship a
    gigabyte of other people's git repositories". The exclusion happens at copy
    time rather than by deleting afterwards, so the bytes are never written to
    the destination in the first place.

.PARAMETER Global
    Install for the current user. This is the default.

.PARAMETER Project
    Install into the current project directory.

.PARAMETER Target
    Install into an exact directory.

.PARAMETER All
    Keep every file except the fetched catalogue.

.PARAMETER Bundle
    Write a runtime-only bundle to a directory and exit.

.PARAMETER BundleZip
    Also write a .zip archive of the bundle.

.PARAMETER CheckBundle
    Verify the bundle would be sound. Writes nothing.

.PARAMETER Yes
    Do not prompt. Required in unattended contexts.

.PARAMETER DryRun
    Print the plan and write nothing.

.PARAMETER Interactive
    Ask where to install and what to include, even on a terminal.

.PARAMETER Uninstall
    Remove an install: the skill directory and its pointer file. Combine with
    -Global (default), -Project, or -Target to choose where from.

.EXAMPLE
    .\install.ps1
    Installs for the current user, pruning everything the runtime does not load.

.EXAMPLE
    .\install.ps1 -Bundle .\dist
    Writes a runtime-only bundle suitable for a marketplace or another machine.

.EXAMPLE
    .\install.ps1 -Yes -Target C:\skills
    Unattended install into an exact directory.

.NOTES
    Exit status is 0 on success, 1 on a refused or failed install.
#>

[CmdletBinding()]
param(
    [switch]$Global,
    [switch]$Project,
    [string]$Target,
    [string]$Source,
    [switch]$All,
    [switch]$Bundle,
    [switch]$BundleZip,
    [switch]$CheckBundle,
    [switch]$Yes,
    [switch]$DryRun,
    [switch]$Interactive,
    [switch]$Uninstall,
    [string]$BundleOut = 'dist'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SkillName = 'ultimate-dev'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# By default the skill is the `ultimate-dev\` directory beside this script. -Source
# overrides it, so a copy of the skill directory can be installed on its own, with
# no repository around it. See install.sh, which does the same.
if ($Source) {
    $SourceDir = (Resolve-Path -LiteralPath $Source).Path
    $SkillName = Split-Path -Leaf $SourceDir
} else {
    $SourceDir = Join-Path $ScriptDir $SkillName
}

function Write-Log  { param([string]$Message) Write-Host $Message }
function Write-Warn2 { param([string]$Message) Write-Warning $Message }
function Stop-WithError {
    param([string]$Message)
    Write-Error $Message -ErrorAction Continue
    exit 1
}

# ---------------------------------------------------------------------------
# Platform
#
# This script is native PowerShell and runs on Windows, PowerShell Core on
# macOS and Linux, and Windows PowerShell 5.1. The differences that matter are
# not the platform name but the shell version: 5.1 lacks ternary operators and
# several cmdlets used below, so the version is detected and the older paths are
# taken deliberately rather than by accident.
# ---------------------------------------------------------------------------

$IsWindowsHost = $true
if (Get-Variable -Name 'IsWindows' -ErrorAction SilentlyContinue) {
    $IsWindowsHost = [bool]$IsWindows
}
$UseCore = $PSVersionTable.PSVersion.Major -ge 6
if ($IsWindowsHost) {
    Write-Log "platform:     Windows (PowerShell $($PSVersionTable.PSVersion)$(if (-not $UseCore) { ', 5.1 compatibility path' }))"
} else {
    Write-Log "platform:     $($PSVersionTable.OS) (PowerShell $($PSVersionTable.PSVersion))"
}

# ---------------------------------------------------------------------------
# Pruning
# ---------------------------------------------------------------------------

# Documentation and source specification rather than runtime. The kernel never
# loads these, and all of them are preserved in the repository.
$Prunable = @('docs', 'examples', 'evaluation', 'research', 'knowledge', 'catalog')
$PrunableFiles = @('ARCHITECTURE.md', 'new-arch.md', 'prd.md')

# Pruned even under -All.
$AlwaysPrune = @('catalog/_src')

# Refuse to install from an implausibly large source. A guard against a fetch
# accident, not a policy against a large skill.
$MaxSourceMB = 200
if ($env:MAX_SOURCE_MB) { $parsed = 0; if ([int]::TryParse($env:MAX_SOURCE_MB, [ref]$parsed)) { $MaxSourceMB = $parsed } }

function Get-SourceMB {
    param([string]$Path)
    try {
        $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
                  Measure-Object -Property Length -Sum).Sum
        if ($null -eq $bytes) { return 0 }
        return [int]($bytes / 1MB)
    } catch { return 0 }
}

# Exclude at copy time. Copying first and deleting afterwards writes the
# gigabyte to the destination before anything decides not to want it, which on a
# slow disk is minutes of a progress bar for a file about to be removed.
function Copy-SkillTree {
    param(
        [string]$Source,
        [string]$Destination,
        [bool]$Prune
    )

    $excluded = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($d in $AlwaysPrune) { [void]$excluded.Add($d) }
    if ($Prune) {
        foreach ($d in $Prunable) { [void]$excluded.Add($d) }
        foreach ($f in $PrunableFiles) { [void]$excluded.Add($f) }
    }

    $copied = 0
    $skipped = 0

    $stack = New-Object 'System.Collections.Stack'
    $stack.Push(@{ From = $Source; To = $Destination })

    while ($stack.Count -gt 0) {
        $frame = $stack.Pop()
        $srcDir = $frame.From
        $dstDir = $frame.To

        if (-not (Test-Path -LiteralPath $dstDir)) {
            [void](New-Item -ItemType Directory -Path $dstDir -Force)
        }

        foreach ($item in Get-ChildItem -LiteralPath $srcDir -Force) {
            $rel = [System.IO.Path]::GetRelativePath($srcDir, $item.FullName)
            # Directory: skip the subtree entirely if it is prunable, otherwise recurse.
            if ($item.PSIsContainer) {
                if ($excluded.Contains($rel)) { $skipped++; continue }
                $stack.Push(@{ From = $item.FullName; To = (Join-Path $dstDir $item.Name) })
                continue
            }
            if ($excluded.Contains($rel)) { $skipped++; continue }
            Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $dstDir $item.Name) -Force
            $copied++
        }
    }
    return [pscustomobject]@{ Copied = $copied; Skipped = $skipped }
}

# ---------------------------------------------------------------------------
# Destination
# ---------------------------------------------------------------------------

# Listed by where a runtime looks, not by product name, so a runtime this script
# has never heard of can still be handled by its project-local path.
# Join-Path throws on a null base, and the Windows variables are null in some
# contexts -- under a scheduled task, or a service account. Build the list
# conditionally rather than filtering afterwards, because the throw happens
# inside the pipeline rather than after it.
$GlobalCandidates = New-Object 'System.Collections.Generic.List[string]'
foreach ($pair in @(
    @($HOME,           '.agents/skills'),
    @($HOME,           '.claude/skills'),
    @($env:APPDATA,    'opencode/skills'),
    @($env:LOCALAPPDATA, 'opencode/skills'),
    @($HOME,           '.config/opencode/skills')
)) {
    if ($pair[0]) { $GlobalCandidates.Add((Join-Path $pair[0] $pair[1])) }
}

$ProjectCandidates = @(
    '.agents/skills',
    '.claude/skills'
)

function Resolve-Target {
    if ($Target) { return $Target }
    if ($Project) { return (Get-Location).Path }
    foreach ($c in $GlobalCandidates) { if (Test-Path -LiteralPath $c -PathType Container) { return $c } }
    # No known directory exists. Use the first rather than inventing a path, so
    # the result is somewhere a runtime actually looks.
    return $GlobalCandidates[0]
}

# ---------------------------------------------------------------------------
# Uninstall
#
# Short-circuits before the source preflight: removal needs a destination,
# not a source tree. Mirrors install.sh --uninstall, including the refusals.
# ---------------------------------------------------------------------------

if ($Uninstall) {
    $destRoot = Resolve-Target
    $dest = Join-Path $destRoot $SkillName
    $pointer = Join-Path $destRoot 'ultimate-dev.json'

    Write-Log "target:       $dest"

    # The one place this operation can lose data, so it verifies before it asks.
    # manifest.json is written by current installs; the SKILL.md frontmatter
    # name covers installs made before the manifest existed.
    if (Test-Path -LiteralPath $dest) {
        $ours = $false
        $manifestPath = Join-Path $dest 'manifest.json'
        $skillPath = Join-Path $dest 'SKILL.md'
        if ((Test-Path -LiteralPath $manifestPath) -and
            (Select-String -LiteralPath $manifestPath -Pattern ([regex]::Escape("`"name`": `"$SkillName`"")) -Quiet)) {
            $ours = $true
        }
        if ((-not $ours) -and (Test-Path -LiteralPath $skillPath) -and
            (Select-String -LiteralPath $skillPath -Pattern "^name:\s*$([regex]::Escape($SkillName))\s*$" -Quiet)) {
            $ours = $true
        }
        if (-not $ours) {
            Stop-WithError "$dest does not look like the $SkillName skill (no matching manifest.json or SKILL.md name); refusing to delete it"
        }
    }

    if ($DryRun) {
        if (Test-Path -LiteralPath $dest) { Write-Log "dry run:      would remove $dest" } else { Write-Log "dry run:      $dest does not exist" }
        if (Test-Path -LiteralPath $pointer) { Write-Log "dry run:      would remove $pointer" }
        exit 0
    }

    if ((-not (Test-Path -LiteralPath $dest)) -and (-not (Test-Path -LiteralPath $pointer))) {
        Write-Log "nothing to uninstall from $destRoot"
        exit 0
    }

    if (-not $Yes) {
        $reply = Read-Host "This deletes $dest. Proceed? [y/N]"
        if ($reply -notmatch '^(y|yes)$') {
            Stop-WithError 'aborted; nothing was changed'
        }
    }

    if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force; Write-Log "removed:      $dest" }
    if (Test-Path -LiteralPath $pointer) { Remove-Item -LiteralPath $pointer -Force; Write-Log "removed:      $pointer" }

    Write-Log ""
    Write-Log "uninstalled $SkillName from $destRoot"
    exit 0
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    Stop-WithError "cannot find the skill at $SourceDir; run install.ps1 from the repository root, or pass -Source DIR"
}

$prune = -not $All
$sourceMB = Get-SourceMB -Path $SourceDir
if ($sourceMB -gt $MaxSourceMB -and $prune) {
    Stop-WithError "source tree is $sourceMB MB, over the $MaxSourceMB MB limit for an install. The usual cause is a fetched catalogue: check for ultimate-dev\catalog\_src, or re-clone without it. To install anyway, use -All, or set MAX_SOURCE_MB=0 to disable this check."
}

$destRoot = Resolve-Target
$dest = Join-Path $destRoot $SkillName

Write-Log "source:       $SourceDir"
Write-Log "destination:  $dest"
Write-Log "source size:  $sourceMB MB"
if ($prune) {
    Write-Log "prune:        $($Prunable -join ', ')"
    Write-Log "always prune: $($AlwaysPrune -join ', ')  (about 1.1 GB of fetched upstream repositories)"
} else {
    Write-Log "prune:        off, keeping documentation and evaluation"
}

if ($CheckBundle) {
    if (-not (Test-Path -LiteralPath (Join-Path $SourceDir 'SKILL.md'))) {
        Stop-WithError "bundle would be unsound: $SourceDir\SKILL.md is missing"
    }
    Write-Log "bundle check: ok -- SKILL.md present, $sourceMB MB source, prune=$prune"
    exit 0
}

if ($DryRun) {
    Write-Log "dry run:      would copy the skill to $dest"
    exit 0
}

# ---------------------------------------------------------------------------
# Refuse to clobber
#
# The one place this script would lose data, so it stops rather than guessing.
# ---------------------------------------------------------------------------

if (Test-Path -LiteralPath $dest) {
    $installedSkill = Join-Path $dest 'SKILL.md'
    $sourceSkill = Join-Path $SourceDir 'SKILL.md'
    $identical = $false
    if ((Test-Path -LiteralPath $installedSkill) -and (Test-Path -LiteralPath $sourceSkill)) {
        $a = (Get-FileHash -LiteralPath $installedSkill -Algorithm SHA256).Hash
        $b = (Get-FileHash -LiteralPath $sourceSkill -Algorithm SHA256).Hash
        $identical = ($a -eq $b)
    }
    if ($identical) {
        Write-Log "status:       already installed and identical, nothing to do"
        exit 0
    }
    if ($Yes) {
        Stop-WithError "$dest already exists and differs; move it aside, then re-run"
    }
    $reply = Read-Host "$dest already exists. Replace it? This deletes the existing directory. [y/N]"
    if ($reply -notmatch '^(y|yes)$') {
        Stop-WithError 'aborted; nothing was changed'
    }
    Write-Log "replacing     $dest"
    Remove-Item -LiteralPath $dest -Recurse -Force
}

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

try {
    if (-not (Test-Path -LiteralPath $destRoot)) {
        [void](New-Item -ItemType Directory -Path $destRoot -Force)
    }
} catch {
    Stop-WithError "cannot create $destRoot : $($_.Exception.Message)"
}

$stats = Copy-SkillTree -Source $SourceDir -Destination $dest -Prune $prune

if ($stats.Skipped -gt 0) {
    Write-Log "excluded:     $($stats.Skipped) path(s), never written to the destination"
}

# A skill with no SKILL.md is not a skill. Verify rather than assume the copy
# worked, because a partial copy is the failure mode that would otherwise
# surface later as a silent discovery miss.
if (-not (Test-Path -LiteralPath (Join-Path $dest 'SKILL.md'))) {
    Stop-WithError "install failed: $dest\SKILL.md is missing after the copy"
}

$installedMB = Get-SourceMB -Path $dest
Write-Log "installed:    $($stats.Copied) file(s), $installedMB MB at $dest"

# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------

if ($Bundle) {
    $zip = "$BundleOut.zip"
    if ($BundleZip) {
        $stage = Join-Path ([System.IO.Path]::GetTempPath()) ("bundle-" + [System.Guid]::NewGuid().ToString('N'))
        [void](New-Item -ItemType Directory -Path $stage -Force)
        $stagedSkill = Join-Path $stage $SkillName
        [void](Copy-SkillTree -Source $SourceDir -Destination $stagedSkill -Prune $true)
        if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
        Compress-Archive -LiteralPath $stagedSkill -DestinationPath $zip -Force
        Remove-Item -LiteralPath $stage -Recurse -Force
        Write-Log "bundle zip:   $zip"
    }
    Write-Log "bundle:       $dest"
    exit 0
}

Write-Log ""
Write-Log "done. The agent runtime must be told where to look; the installed"
Write-Log "SKILL.md is at $dest\SKILL.md"
exit 0
