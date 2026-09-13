$ErrorActionPreference = 'Continue'

$project = 'C:\work\project'
$editor = 'C:\Unity\Editor\Unity.exe'
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
$testStartedPath = Join-Path $output 'test-started.txt'
$triggerPath = Join-Path $output 'run-test.trigger'
$activationWaitLimitSeconds = 1800
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
    $json = $Value | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
}

$started = [DateTime]::UtcNow
$hubStarted = $false
$hubStartError = ''
$hubProcessId = $null
$triggerObserved = $false
$activationWaitSeconds = 0
$processStarted = $false
$exitCode = 125
$timedOut = $false
$startError = ''
$unity = $null

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
    hub_path = 'C:\UnityHub\Unity Hub.exe'
    started = $hubStarted
    process_id = $hubProcessId
    start_error = $hubStartError
    note = 'User authentication is manual; no password, token, or browser content is collected by this runner.'
})
Set-Content -LiteralPath $waitingPath -Value 'WAITING_FOR_MANUAL_HUB_LOGIN=true' -Encoding ASCII

while ((-not (Test-Path -LiteralPath $triggerPath -PathType Leaf)) -and ($activationWaitSeconds -lt $activationWaitLimitSeconds)) {
    Start-Sleep -Seconds 2
    $activationWaitSeconds += 2
}
$triggerObserved = Test-Path -LiteralPath $triggerPath -PathType Leaf

$licenseLocalAppData = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($licenseLocalAppData)) {
    $licenseLocalAppData = 'C:\Users\WDAGUtilityAccount\AppData\Local'
}
$roamingAppData = $env:APPDATA
if ([string]::IsNullOrWhiteSpace($roamingAppData)) {
    $roamingAppData = 'C:\Users\WDAGUtilityAccount\AppData\Roaming'
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
        if (-not (Test-Path -LiteralPath $editor -PathType Leaf)) {
            throw 'mapped Unity editor executable is unavailable'
        }
        $arguments = '-batchmode -nographics -projectPath "C:\work\project" -executeMethod NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless -logFile "C:\output\unity.log" -quit'
        $unity = Start-Process -FilePath $editor -ArgumentList $arguments -WorkingDirectory $editorWorkingDirectory -PassThru -WindowStyle Hidden
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
} else {
    $timedOut = $true
    $exitCode = 124
    $startError = 'manual Hub login trigger was not received before the controlled wait limit'
}

$ended = [DateTime]::UtcNow
$logText = ''
if (Test-Path -LiteralPath $log -PathType Leaf) {
    $logText = Get-Content -LiteralPath $log -Raw -ErrorAction SilentlyContinue
}
$remaining = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(Unity|UnityHub|UnityPackageManager|UnityLicensingClient)' })
$result = [ordered]@{
    schema_version = 2
    environment = 'windows-sandbox'
    networking = 'enabled'
    authentication_mode = 'manual-unity-hub-login-inside-sandbox'
    editor_path = 'C:\Unity\Editor\Unity.exe'
    editor_working_directory = $editorWorkingDirectory
    project_path = 'C:\work\project'
    runtime_overlay = $runtimeOverlay
    hub_started = $hubStarted
    hub_start_error = $hubStartError
    trigger_observed = $triggerObserved
    activation_wait_seconds = $activationWaitSeconds
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
    shutdown_request = 'sandbox-only: shutdown.exe /s /t 0 /f'
}
Write-JsonFile -Path $resultPath -Value $result
Set-Content -LiteralPath $markerPath -Value 'SANDBOX_SHUTDOWN_REQUESTED=true' -Encoding ASCII

# This shutdown request is executed only inside the disposable Windows Sandbox.
shutdown.exe /s /t 0 /f | Out-Null
exit $exitCode
