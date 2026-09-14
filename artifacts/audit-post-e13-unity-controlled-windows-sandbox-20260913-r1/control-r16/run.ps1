$ErrorActionPreference = 'Continue'

$project = 'C:\work\project'
$editorFallback = 'C:\Unity\Editor\Unity.exe'
$editorInstallRoot = 'C:\UnityInstall'
$editorWorkingDirectory = 'C:\Unity\Editor'
$hub = 'C:\UnityHub\Unity Hub.exe'
$runtimeOverlay = 'C:\runtime'
$output = 'C:\output'
$log = Join-Path $output 'unity.log'
$report = Join-Path $output 'package-report.json'
$resultPath = Join-Path $output 'sandbox-result.json'
$markerPath = Join-Path $output 'sandbox-shutdown-requested.txt'
$hubStatePath = Join-Path $output 'hub-started.json'
$waitingPath = Join-Path $output 'waiting-for-user-login.txt'
$waitingStatePath = Join-Path $output 'waiting-for-user-login.json'
$testStartedPath = Join-Path $output 'test-started.txt'
$triggerPath = Join-Path $output 'run-test.trigger'
$abortWaitPath = Join-Path $output 'abort-wait.trigger'
$editorSelectionPath = Join-Path $output 'editor-path.trigger'
$editorInventoryPath = Join-Path $output 'editor-inventory.json'
$editorSelectionReportPath = Join-Path $output 'editor-selection.json'
$heartbeatIntervalSeconds = 15
$pollIntervalSeconds = 2
$unityTimeoutMilliseconds = 240000

New-Item -ItemType Directory -Path 'C:\work' -Force | Out-Null
New-Item -ItemType Directory -Path $project -Force | Out-Null
New-Item -ItemType Directory -Path $output -Force | Out-Null
Copy-Item -Path 'C:\input\*' -Destination $project -Recurse -Force

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
}

function Get-EditorPaths {
    $paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($candidate in @($editorFallback)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $null = $paths.Add($candidate)
        }
    }
    if (Test-Path -LiteralPath $editorInstallRoot -PathType Container) {
        $installed = Get-ChildItem -LiteralPath $editorInstallRoot -Filter 'Unity.exe' -File -Recurse -ErrorAction SilentlyContinue
        foreach ($candidate in @($installed)) {
            $null = $paths.Add($candidate.FullName)
        }
    }
    return @($paths | Select-Object -Unique)
}

function Get-EditorInventory {
    $inventory = @()
    foreach ($path in @(Get-EditorPaths)) {
        $item = Get-Item -LiteralPath $path -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            $inventory += [ordered]@{
                path = $item.FullName
                product_version = $item.VersionInfo.ProductVersion
                file_version = $item.VersionInfo.FileVersion
                length = $item.Length
            }
        }
    }
    return @($inventory)
}

function Write-EditorInventory {
    $inventory = @(Get-EditorInventory)
    Write-JsonFile -Path $editorInventoryPath -Value ([ordered]@{
        observed_utc = [DateTime]::UtcNow.ToString('o')
        persistent_install_mount = $editorInstallRoot
        known_editor_mount = 'C:\Unity\Editor'
        editors = $inventory
        note = 'Inventory only; no Unity process is started until the explicit manual trigger is valid.'
    })
    return $inventory
}

function Write-WaitState {
    param(
        [Parameter(Mandatory = $true)][string]$State,
        [Parameter(Mandatory = $true)][int]$ElapsedSeconds,
        [Parameter(Mandatory = $true)][bool]$TriggerPresent,
        [Parameter(Mandatory = $true)][bool]$TriggerValid,
        [Parameter(Mandatory = $true)][bool]$AbortPresent,
        [Parameter(Mandatory = $true)][bool]$AbortValid
    )
    $inventory = @(Write-EditorInventory)
    Write-JsonFile -Path $waitingStatePath -Value ([ordered]@{
        state = $State
        observed_utc = [DateTime]::UtcNow.ToString('o')
        elapsed_seconds = $ElapsedSeconds
        trigger_present = $TriggerPresent
        trigger_valid = $TriggerValid
        abort_present = $AbortPresent
        abort_valid = $AbortValid
        automatic_timeout_seconds = $null
        automatic_shutdown_before_trigger = $false
        persistent_install_mount = $editorInstallRoot
        editors_available = @($inventory | ForEach-Object { $_.path })
        note = 'The Sandbox remains alive while installation or manual Hub authentication is in progress. Create run-test.trigger only after the owner confirms completion.'
    })
}

function Test-ManualMarker {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Expected
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $content = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
    return $content.Trim() -eq $Expected
}

function Test-AllowedEditorPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fallbackRoot = 'C:\Unity\Editor\'
    $installRoot = 'C:\UnityInstall\'
    return (($fullPath.StartsWith($fallbackRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
            $fullPath.StartsWith($installRoot, [System.StringComparison]::OrdinalIgnoreCase)) -and
            $fullPath.EndsWith('\Unity.exe', [System.StringComparison]::OrdinalIgnoreCase))
}

function Resolve-EditorPath {
    if (Test-Path -LiteralPath $editorSelectionPath -PathType Leaf) {
        $requested = (Get-Content -LiteralPath $editorSelectionPath -Raw -ErrorAction SilentlyContinue).Trim()
        if ([string]::IsNullOrWhiteSpace($requested) -or -not (Test-AllowedEditorPath -Path $requested)) {
            throw 'editor-path.trigger is invalid or outside the approved Sandbox editor mounts'
        }
        if (-not (Test-Path -LiteralPath $requested -PathType Leaf)) {
            throw 'editor-path.trigger points to an unavailable Unity.exe'
        }
        return [System.IO.Path]::GetFullPath($requested)
    }
    if (-not (Test-Path -LiteralPath $editorFallback -PathType Leaf)) {
        throw 'mapped fallback Unity editor executable is unavailable'
    }
    return $editorFallback
}

$started = [DateTime]::UtcNow
$hubStarted = $false
$hubStartError = ''
$hubProcessId = $null
$triggerObserved = $false
$triggerPresent = $false
$triggerValid = $false
$waitAborted = $false
$abortPresent = $false
$abortValid = $false
$activationWaitSeconds = 0
$processStarted = $false
$exitCode = 125
$timedOut = $false
$startError = ''
$unity = $null
$hubProcess = $null
$selectedEditor = $null
$waitTermination = 'not_reached'

try {
    if (-not (Test-Path -LiteralPath $hub -PathType Leaf)) {
        throw 'mapped Unity Hub executable is unavailable'
    }
    $hubProcess = Start-Process -FilePath $hub -WorkingDirectory 'C:\UnityHub' -PassThru
    $hubStarted = $true
    $hubProcessId = $hubProcess.Id
} catch {
    $hubStartError = $_.Exception.Message
}

Write-JsonFile -Path $hubStatePath -Value ([ordered]@{
    hub_path = $hub
    started = $hubStarted
    process_id = $hubProcessId
    start_error = $hubStartError
    note = 'User authentication and installation choices are manual; no password, token, or browser content is collected by this runner.'
})
Set-Content -LiteralPath $waitingPath -Value 'WAITING_FOR_MANUAL_HUB_LOGIN=true' -Encoding ASCII
Write-WaitState -State 'WAITING_FOR_MANUAL_HUB_LOGIN_OR_INSTALLATION' -ElapsedSeconds 0 -TriggerPresent $false -TriggerValid $false -AbortPresent $false -AbortValid $false

# Deliberately no elapsed-time cutoff is used here. The previous r15 cutoff
# caused the Sandbox to shut down while the owner was still installing Unity.
while ($true) {
    $triggerPresent = Test-Path -LiteralPath $triggerPath -PathType Leaf
    $triggerValid = Test-ManualMarker -Path $triggerPath -Expected 'MANUAL_HUB_LOGIN_CONFIRMED_BY_USER=true'
    $abortPresent = Test-Path -LiteralPath $abortWaitPath -PathType Leaf
    $abortValid = Test-ManualMarker -Path $abortWaitPath -Expected 'MANUAL_WAIT_ABORT_REQUESTED_BY_USER=true'
    if ($triggerValid) {
        $triggerObserved = $true
        $waitTermination = 'manual_trigger'
        break
    }
    if ($abortValid) {
        $waitAborted = $true
        $waitTermination = 'manual_abort'
        break
    }
    if (($activationWaitSeconds % $heartbeatIntervalSeconds) -eq 0) {
        Write-WaitState -State 'WAITING_FOR_MANUAL_HUB_LOGIN_OR_INSTALLATION' -ElapsedSeconds $activationWaitSeconds -TriggerPresent $triggerPresent -TriggerValid $triggerValid -AbortPresent $abortPresent -AbortValid $abortValid
    }
    Start-Sleep -Seconds $pollIntervalSeconds
    $activationWaitSeconds += $pollIntervalSeconds
}

$licenseLocalAppData = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($licenseLocalAppData)) {
    $sandboxSystemDrive = if ([string]::IsNullOrWhiteSpace($env:SystemDrive)) { 'C:' } else { $env:SystemDrive }
    $licenseLocalAppData = Join-Path $sandboxSystemDrive 'Users\WDAGUtilityAccount\AppData\Local'
}
$roamingAppData = $env:APPDATA
if ([string]::IsNullOrWhiteSpace($roamingAppData)) {
    $sandboxSystemDrive = if ([string]::IsNullOrWhiteSpace($env:SystemDrive)) { 'C:' } else { $env:SystemDrive }
    $roamingAppData = Join-Path $sandboxSystemDrive 'Users\WDAGUtilityAccount\AppData\Roaming'
}
$licenseDirectory = Join-Path $licenseLocalAppData 'Unity\licenses'
$roamingUnityDirectory = Join-Path $roamingAppData 'Unity'
$licenseFiles = @()
if (Test-Path -LiteralPath $licenseDirectory -PathType Container) {
    $licenseFiles = @(Get-ChildItem -LiteralPath $licenseDirectory -File -Force -ErrorAction SilentlyContinue)
}
$roamingFiles = @()
if (Test-Path -LiteralPath $roamingUnityDirectory -PathType Container) {
    $roamingFiles = @(Get-ChildItem -LiteralPath $roamingUnityDirectory -File -Force -ErrorAction SilentlyContinue)
}
$activationInventory = [ordered]@{
    local_unity_licenses_directory_present = Test-Path -LiteralPath $licenseDirectory -PathType Container
    local_unity_license_file_count = $licenseFiles.Count
    local_unity_license_extensions = @($licenseFiles | ForEach-Object { $_.Extension.ToLowerInvariant() } | Sort-Object -Unique)
    roaming_unity_directory_present = Test-Path -LiteralPath $roamingUnityDirectory -PathType Container
    roaming_unity_file_count = $roamingFiles.Count
    content_collected = $false
    note = 'Only presence, counts, and extensions are recorded; activation contents remain inside the disposable sandbox.'
}

if ($triggerObserved) {
    Set-Content -LiteralPath $testStartedPath -Value 'UNITY_TEST_STARTED_AFTER_MANUAL_HUB_LOGIN=true' -Encoding ASCII
    $env:NEOENG_STAGE5_REPORT = $report
    $env:PATH = $editorWorkingDirectory + ';' + $runtimeOverlay + ';' + $env:PATH
    try {
        $selectedEditor = Resolve-EditorPath
        Write-JsonFile -Path $editorSelectionReportPath -Value ([ordered]@{
            selected_editor = $selectedEditor
            selected_by = if (Test-Path -LiteralPath $editorSelectionPath -PathType Leaf) { 'manual_editor_path_trigger' } else { 'mapped_fallback'
            }
            observed_utc = [DateTime]::UtcNow.ToString('o')
        })
        $arguments = '-batchmode -nographics -projectPath "C:\work\project" -executeMethod NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless -logFile "C:\output\unity.log" -quit'
        $unity = Start-Process -FilePath $selectedEditor -ArgumentList $arguments -WorkingDirectory (Split-Path -Parent $selectedEditor) -PassThru -WindowStyle Hidden
        $processStarted = $true
        if (-not $unity.WaitForExit($unityTimeoutMilliseconds)) {
            $timedOut = $true
            $exitCode = 124
        } else {
            $exitCode = $unity.ExitCode
        }
    } catch {
        $startError = $_.Exception.Message
    }
} elseif ($waitAborted) {
    $exitCode = 125
    $startError = 'manual wait abort marker was received before installation/login confirmation'
}

$ended = [DateTime]::UtcNow
$logText = ''
if (Test-Path -LiteralPath $log -PathType Leaf) {
    $logText = Get-Content -LiteralPath $log -Raw -ErrorAction SilentlyContinue
}
$remaining = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(Unity|UnityHub|UnityPackageManager|UnityLicensingClient)' })
$result = [ordered]@{
    schema_version = 3
    environment = 'windows-sandbox'
    networking = 'enabled'
    authentication_mode = 'manual-unity-hub-login-inside-sandbox'
    editor_path = $selectedEditor
    editor_fallback_path = $editorFallback
    persistent_install_mount = $editorInstallRoot
    editor_working_directory = $editorWorkingDirectory
    project_path = 'C:\work\project'
    runtime_overlay = $runtimeOverlay
    hub_started = $hubStarted
    hub_start_error = $hubStartError
    trigger_observed = $triggerObserved
    trigger_present = $triggerPresent
    trigger_valid = $triggerValid
    wait_termination = $waitTermination
    activation_wait_seconds = $activationWaitSeconds
    activation_wait_limit_seconds = $null
    automatic_timeout = $false
    automatic_shutdown_before_trigger = $false
    activation_inventory = $activationInventory
    process_started = $processStarted
    process_exit_code = $exitCode
    timed_out = $timedOut
    start_error = $startError
    started_utc = $started.ToString('o')
    ended_utc = $ended.ToString('o')
    report_present = Test-Path -LiteralPath $report -PathType Leaf
    success_marker = $logText -match 'UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS'
    failure_marker = $logText -match 'UNITY_NATIVE_PACKAGE_STAGE5=FAILURE'
    licensing_signals = [ordered]@{
        module_seen = $logText -match '(?i)Licensing::'
        access_token_error = $logText -match '(?i)Access token is unavailable'
        code_10 = $logText -match '(?i)Code 10'
        license_client_seen = $logText -match '(?i)LicenseClient'
        no_valid_editor_license = $logText -match '(?i)No valid Unity Editor license found'
        code_404_entitlement = $logText -match '(?i)Code 404.*entitlement'
    }
    shutdown_signals = [ordered]@{
        batchmode_quit = $logText -match '(?i)Batchmode quit successfully invoked'
        shut_down = $logText -match '(?im)^Shut down\.'
        exited_batchmode = $logText -match '(?i)Exiting batchmode successfully now'
        return_code_zero = $logText -match '(?i)return code 0'
        abort_threads = $logText -match '(?i)abort_threads'
        memory_leaks = $logText -match '(?i)MemoryLeaks'
    }
    remaining_unity_process_count_before_sandbox_shutdown = $remaining.Count
    shutdown_request = 'sandbox-only: shutdown.exe /s /t 0 /f; only after manual trigger or manual abort'
}
Write-JsonFile -Path $resultPath -Value $result

# This shutdown request is intentionally conditional and executes only inside
# the disposable Windows Sandbox. A missing manual trigger never reaches this block.
if ($triggerObserved -or $waitAborted) {
    Set-Content -LiteralPath $markerPath -Value 'SANDBOX_SHUTDOWN_REQUESTED=true' -Encoding ASCII
    shutdown.exe /s /t 0 /f | Out-Null
}
exit $exitCode
