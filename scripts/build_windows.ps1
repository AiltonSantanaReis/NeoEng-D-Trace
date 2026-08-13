[CmdletBinding()]
param(
    [string]$OutputRoot = "release"
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
    $env:SOURCE_DATE_EPOCH = (git show -s --format=%ct HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to resolve source timestamp" }

    $distPath = Join-Path $releaseRoot "portable"
    $workPath = Join-Path $releaseRoot "work"
    poetry run pyinstaller --noconfirm --clean --distpath $distPath --workpath $workPath "packaging/NeoEng-D-Trace.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    $bundle = Join-Path $distPath "NeoEng-D-Trace"
    $smokeOutput = Join-Path $releaseRoot "smoke"
    poetry run python tools/validate_portable_release.py --bundle $bundle --output $smokeOutput --fixture "tests/fixtures/release_smoke.ndtproj"
    if ($LASTEXITCODE -ne 0) { throw "Portable smoke validation failed" }

    $archive = Join-Path $releaseRoot "NeoEng-D-Trace-0.2.0-win64-portable.zip"
    poetry run python tools/package_portable_release.py --bundle $bundle --output $archive --source-commit $sourceCommit
    if ($LASTEXITCODE -ne 0) { throw "Portable package creation failed" }

    Write-Output "PORTABLE_BUNDLE=$bundle"
    Write-Output "PORTABLE_ARCHIVE=$archive"
    Write-Output "SOURCE_COMMIT=$sourceCommit"
} finally {
    Pop-Location
}
