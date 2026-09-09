[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,
    [string]$PythonExecutable = ""
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stageRoot = Join-Path ([IO.Path]::GetTempPath()) ("neoeng-untracked-stage-" + [guid]::NewGuid().ToString("N"))
$moved = @()

Push-Location $repositoryRoot
try {
    New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null
    $untracked = @(git ls-files --others --exclude-standard)
    if ($LASTEXITCODE -ne 0) { throw "Unable to enumerate untracked artifacts" }
    foreach ($relativePath in $untracked) {
        $source = Join-Path $repositoryRoot $relativePath
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Untracked path is not a regular file: $relativePath"
        }
        $destination = Join-Path $stageRoot $relativePath
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Move-Item -LiteralPath $source -Destination $destination
        $moved += $relativePath
    }
    Write-Output ("STAGED_UNTRACKED=" + $moved.Count)

    $buildArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $repositoryRoot "scripts\build_windows.ps1"), "-OutputRoot", $OutputRoot)
    if ($PythonExecutable) {
        $buildArgs += @("-PythonExecutable", $PythonExecutable)
    }
    & powershell @buildArgs
    if ($LASTEXITCODE -ne 0) { throw "Clean Windows build failed with exit code $LASTEXITCODE" }
}
finally {
    foreach ($relativePath in @($moved | Select-Object -Reverse)) {
        $source = Join-Path $stageRoot $relativePath
        $destination = Join-Path $repositoryRoot $relativePath
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Move-Item -LiteralPath $source -Destination $destination
        }
    }
    if (Test-Path -LiteralPath $stageRoot) {
        Remove-Item -LiteralPath $stageRoot -Recurse -Force
    }
    Pop-Location
}
