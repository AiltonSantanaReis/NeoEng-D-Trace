[CmdletBinding()]
param(
    [string]$ReleaseRoot = "release"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repositoryRoot
try {
    if ([IO.Path]::IsPathRooted($ReleaseRoot)) {
        $resolvedReleaseRoot = [IO.Path]::GetFullPath($ReleaseRoot)
    } else {
        $resolvedReleaseRoot = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $ReleaseRoot))
    }
    $repositoryPrefix = $repositoryRoot.TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    ) + [IO.Path]::DirectorySeparatorChar
    if (
        $resolvedReleaseRoot.Equals($repositoryRoot, [StringComparison]::OrdinalIgnoreCase) -or
        -not $resolvedReleaseRoot.StartsWith($repositoryPrefix, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "ReleaseRoot must be a child directory inside the repository workspace"
    }

    $sourceStatus = git status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0) { throw "Unable to inspect source tree" }
    if ($sourceStatus) { throw "Installer build requires a clean source tree" }
    $sourceCommit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve source commit" }
    $sourceEpoch = (git show -s --format=%ct HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve source timestamp" }

    & (Join-Path $PSScriptRoot "build_windows.ps1") -OutputRoot $resolvedReleaseRoot
    if ($LASTEXITCODE -ne 0) { throw "Portable build failed" }

    $bundle = Join-Path $resolvedReleaseRoot "portable\NeoEng-D-Trace"
    $portableManifest = Join-Path $bundle "release-manifest.json"
    if (-not (Test-Path -LiteralPath $portableManifest -PathType Leaf)) {
        throw "A validated portable bundle must be built first"
    }
    $manifest = Get-Content -Raw -LiteralPath $portableManifest | ConvertFrom-Json
    if ($manifest.source_commit -ne $sourceCommit) {
        throw "Portable bundle source commit does not match current HEAD"
    }

    dotnet tool restore --no-cache
    if ($LASTEXITCODE -ne 0) { throw "WiX tool restore failed" }
    $installer = Join-Path $resolvedReleaseRoot "NeoEng-D-Trace-0.2.0-win64.msi"
    poetry run python tools/package_windows_msi.py --bundle $bundle --output $installer --source-commit $sourceCommit --source-epoch $sourceEpoch
    if ($LASTEXITCODE -ne 0) { throw "MSI package creation failed" }

    $validationOutput = Join-Path $resolvedReleaseRoot "installer-validation"
    poetry run python tools/validate_windows_installer.py --installer $installer --output $validationOutput --fixture "tests/fixtures/release_smoke.ndtproj"
    if ($LASTEXITCODE -ne 0) { throw "MSI installation validation failed" }

    Write-Output "WINDOWS_INSTALLER=$installer"
    Write-Output "SOURCE_COMMIT=$sourceCommit"
} finally {
    Pop-Location
}
