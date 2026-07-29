[CmdletBinding()]
param(
    [ValidateSet("non-qt", "qt", "all")]
    [string]$Group = "non-qt",

    [string[]]$File,

    [string]$Output
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $PSScriptRoot "run_legacy_tests.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python da .venv não encontrado: $Python"
}

$Arguments = @($Runner, "--group", $Group)
foreach ($Item in $File) {
    $Arguments += @("--file", $Item)
}
if ($Output) {
    $Arguments += @("--output", $Output)
}

& $Python @Arguments
exit $LASTEXITCODE
