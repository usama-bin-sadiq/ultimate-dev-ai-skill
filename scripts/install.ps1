# Interactive compatibility entry point. The copy-only installer lives in the versioned skill payload.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$installer = Join-Path $root 'ultimate-dev/scripts/install.ps1'
& $installer @args
exit $LASTEXITCODE
