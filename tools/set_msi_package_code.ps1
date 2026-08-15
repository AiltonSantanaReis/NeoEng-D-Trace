[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [Parameter(Mandatory = $true)]
    [string]$PackageCode
)

$ErrorActionPreference = "Stop"
$resolvedPath = (Resolve-Path -LiteralPath $Path).Path
$installer = New-Object -ComObject WindowsInstaller.Installer
$database = $installer.OpenDatabase($resolvedPath, 1)
$summary = $database.SummaryInformation(20)
$summary.Property(9) = $PackageCode
$fixedTime = [DateTime]::SpecifyKind([DateTime]::Parse("2000-01-01T00:00:00"), [DateTimeKind]::Utc)
$summary.Property(12) = $fixedTime
$summary.Property(13) = $fixedTime
$summary.Persist()
$database.Commit()
[Runtime.InteropServices.Marshal]::FinalReleaseComObject($summary) | Out-Null
[Runtime.InteropServices.Marshal]::FinalReleaseComObject($database) | Out-Null
[Runtime.InteropServices.Marshal]::FinalReleaseComObject($installer) | Out-Null
