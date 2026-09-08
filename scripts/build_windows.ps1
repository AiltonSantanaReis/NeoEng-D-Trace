[CmdletBinding()]
param(
    [string]$OutputRoot = "release",
    [string]$PythonExecutable = ""
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repositoryRoot
try {
    if ([IO.Path]::IsPathRooted($OutputRoot)) {
        $releaseRoot = [IO.Path]::GetFullPath($OutputRoot)
    } else {
        $releaseRoot = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputRoot))
    }
    $repositoryPrefix = $repositoryRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (
        $releaseRoot.Equals($repositoryRoot, [StringComparison]::OrdinalIgnoreCase) -or
        -not $releaseRoot.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "OutputRoot must be a child directory inside the repository workspace"
    }

    $pythonCommand = $null
    $pythonPrefix = @()
    if ($PythonExecutable) {
        $pythonCommand = (Resolve-Path -LiteralPath $PythonExecutable -ErrorAction Stop).Path
    } elseif (Get-Command poetry -ErrorAction SilentlyContinue) {
        $pythonCommand = (Get-Command poetry).Source
        $pythonPrefix = @("run")
    } else {
        $localPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
        if (Test-Path -LiteralPath $localPython) {
            $pythonCommand = (Resolve-Path -LiteralPath $localPython).Path
        } else {
            throw "No project Python runner found. Pass -PythonExecutable or install Poetry."
        }
    }

    $sourceStatus = git status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0) { throw "Unable to inspect source tree" }
    if ($sourceStatus) {
        throw "Release build requires a clean source tree"
    }

    if (Test-Path -LiteralPath $releaseRoot) {
        Remove-Item -LiteralPath $releaseRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

    $sourceCommit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve source commit" }
    $sourceBranch = (git branch --show-current).Trim()
    if (-not $sourceBranch) { $sourceBranch = "(detached)" }
    $continuityRegistryPath = Join-Path $repositoryRoot "docs\CONTROLE_CONTINUIDADE_ATUAL.json"
    if (-not (Test-Path -LiteralPath $continuityRegistryPath)) {
        throw "Continuity registry is missing: $continuityRegistryPath"
    }
    & $pythonCommand @pythonPrefix "tools/validate_continuity_registry.py"
    if ($LASTEXITCODE -ne 0) { throw "Continuity registry validation failed" }
    $continuityRegistrySha256 = (Get-FileHash -LiteralPath $continuityRegistryPath -Algorithm SHA256).Hash
    $continuityRegistry = Get-Content -LiteralPath $continuityRegistryPath -Raw | ConvertFrom-Json
    $masterPlanCommit = [string]$continuityRegistry.authority.master_plan_commit
    if (-not $masterPlanCommit) { throw "Continuity registry has no master plan commit" }
    $env:SOURCE_DATE_EPOCH = (git show -s --format=%ct HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve source timestamp" }
    $env:PYTHONHASHSEED = "0"

    $distPath = Join-Path $releaseRoot "portable"
    $workPath = Join-Path $releaseRoot "work"
    & $pythonCommand @pythonPrefix "-m" "PyInstaller" --noconfirm --clean --distpath $distPath --workpath $workPath "packaging/NeoEng-D-Trace.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    $bundle = Join-Path $distPath "NeoEng-D-Trace"
    $smokeOutput = Join-Path $releaseRoot "smoke"
    & $pythonCommand @pythonPrefix "tools/validate_portable_release.py" --bundle $bundle --output $smokeOutput --fixture "tests/fixtures/release_smoke.ndtproj"
    if ($LASTEXITCODE -ne 0) { throw "Portable smoke validation failed" }

    $archive = Join-Path $releaseRoot "NeoEng-D-Trace-0.3.0-win64-portable.zip"
    & $pythonCommand @pythonPrefix "tools/package_portable_release.py" --bundle $bundle --output $archive --source-commit $sourceCommit
    if ($LASTEXITCODE -ne 0) { throw "Portable package creation failed" }

    $binaryPath = Join-Path $bundle "NeoEng-D-Trace.exe"
    if (-not (Test-Path -LiteralPath $binaryPath)) {
        throw "Portable GUI binary is missing: $binaryPath"
    }
    $binarySha256 = (Get-FileHash -LiteralPath $binaryPath -Algorithm SHA256).Hash
    $provenance = [ordered]@{
        schema_version = 1
        status = "PASS"
        source_commit = $sourceCommit
        source_branch = $sourceBranch
        master_plan_commit = $masterPlanCommit
        continuity_registry_sha256 = $continuityRegistrySha256
        python_command = $pythonCommand
        python_prefix = $pythonPrefix
        binary = [ordered]@{
            path = "portable/NeoEng-D-Trace/NeoEng-D-Trace.exe"
            sha256 = $binarySha256
            size = (Get-Item -LiteralPath $binaryPath).Length
        }
        release_root = $releaseRoot
        portable_smoke_report = "smoke/portable-smoke-report.json"
        generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    $provenancePath = Join-Path $releaseRoot "continuity-provenance.json"
    $provenance | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $provenancePath -Encoding utf8

    Write-Output "PORTABLE_BUNDLE=$bundle"
    Write-Output "PORTABLE_ARCHIVE=$archive"
    Write-Output "SOURCE_COMMIT=$sourceCommit"
    Write-Output "CONTINUITY_PROVENANCE=$provenancePath"
} finally {
    Pop-Location
}
