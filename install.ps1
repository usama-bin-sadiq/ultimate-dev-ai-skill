# Install the ultimate-dev skill where agent runtimes discover skills.
# Mirror of install.sh. Honoured discovery paths:
#   ~/.agents/skills      the cross-tool standard (Open Agent Skills)
#   ~/.claude/skills      Claude-compatible, also honoured by most others
#   <project>\.agents\skills and <project>\.claude\skills  (project scopes)
param(
    [string]$Target = "",
    [switch]$All,
    [switch]$Yes,
    [switch]$DryRun,
    [switch]$Link,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path $ScriptDir "ultimate-dev"
$SkillName = "ultimate-dev"

if ($Help) { Get-Content $PSCommandPath -TotalCount 10; exit 0 }
if (-not (Test-Path (Join-Path $SourceDir "SKILL.md"))) {
    Write-Error "source skill not found at $SourceDir"; exit 1
}

# USERPROFILE first, $HOME second -- but assigned the long way rather than with
# the ?? operator, which is PowerShell 7+. Windows still ships 5.1 as the
# default `powershell.exe`, and there ?? is a parse error, so the installer
# dies before it has copied a single file. Verified: nothing else in this
# script is 7.x-only.
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }
$GlobalDirs = @(
    (Join-Path $HomeDir ".agents\skills"),
    (Join-Path $HomeDir ".claude\skills"),
    (Join-Path $HomeDir ".config\opencode\skills"),
    (Join-Path $HomeDir ".gemini\skills"),
    (Join-Path $HomeDir ".cursor\skills"),
    (Join-Path $HomeDir ".codex\skills"),
    (Join-Path $HomeDir ".kiro\skills"),
    (Join-Path $HomeDir ".trae\skills"),
    (Join-Path $HomeDir ".config\gemini\skills"),
    (Join-Path $HomeDir ".rovodev\skills")
)
$ProjectDirs = @(".agents\skills", ".claude\skills")

$Destinations = @()
if ($Target) {
    $Destinations = @($Target)
} elseif ($All) {
    $Destinations = $GlobalDirs + $ProjectDirs
} else {
    $found = $null
    foreach ($d in @(
        (Join-Path $HomeDir ".claude\skills"), (Join-Path $HomeDir ".agents\skills"),
        ".claude\skills", ".agents\skills",
        (Join-Path $HomeDir ".config\opencode\skills"), (Join-Path $HomeDir ".gemini\skills"),
        (Join-Path $HomeDir ".cursor\skills"))) {
        if (Test-Path $d) { $found = $d; break }
    }
    if ($found) {
        $Destinations = @($found)
    } else {
        Write-Host "no existing skills directory found; installing to the two universal globals"
        $Destinations = @($GlobalDirs[0], $GlobalDirs[1])
    }
}

foreach ($d in $Destinations) {
    $dest = Join-Path $d $SkillName
    Write-Host "-> $dest"
    if ($DryRun) { continue }

    if ((Test-Path $dest) -and -not $Yes) {
        $answer = Read-Host "destination exists: $dest. overwrite? [y/N]"
        if ($answer -notin @("y", "Y", "yes")) { Write-Host "skipped"; continue }
    }

    New-Item -ItemType Directory -Force -Path $d | Out-Null
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    if ($Link) {
        New-Item -ItemType Junction -Path $dest -Target $SourceDir | Out-Null
    } else {
        Copy-Item -Recurse -Force $SourceDir $dest
        Get-ChildItem -Recurse -Force -Directory -Path $dest -Filter "__pycache__" | Remove-Item -Recurse -Force
        Get-ChildItem -Recurse -Force -Path $dest -Filter "*.pyc" | Remove-Item -Force
    }
}

if (-not $DryRun) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
    if ($python) {
        foreach ($d in $Destinations) {
            $tools = Join-Path (Join-Path $d $SkillName) "tools"
            if (Test-Path $tools) {
                Push-Location (Join-Path $d $SkillName)
                try { & $python.Source tools/validate-skills.py } finally { Pop-Location }
                break
            }
        }
    } else {
        Write-Host "python3 not found; skipping validation"
    }
}
Write-Host "done"
