$ErrorActionPreference = 'Continue'

# Controlled setup only: register the disposable Sandbox's web handler and
# open its default-apps page. Authentication, passwords, tokens, and browser
# contents remain manual.
$edgePath = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$associationMarker = 'C:\output\browser-associations-configured.txt'
$associationErrorPath = 'C:\output\browser-associations-error.txt'
$edgeStartedPath = 'C:\output\edge-browser-started.txt'
try {
    if (-not (Test-Path -LiteralPath $edgePath -PathType Leaf)) {
        throw 'mapped Microsoft Edge executable is unavailable'
    }
    $classesRoot = 'HKCU:\Software\Classes'
    foreach ($scheme in @('http', 'https')) {
        $commandKey = Join-Path $classesRoot "$scheme\shell\open\command"
        New-Item -Path $commandKey -Force | Out-Null
        Set-ItemProperty -LiteralPath $commandKey -Name '(default)' -Value ('"' + $edgePath + '" -- "%1"')
        $userChoice = "HKCU:\Software\Microsoft\Windows\Shell\Associations\UrlAssociations\$scheme\UserChoice"
        Remove-Item -LiteralPath $userChoice -Recurse -Force -ErrorAction SilentlyContinue
    }
    foreach ($extension in @('.htm', '.html')) {
        $extensionKey = Join-Path $classesRoot $extension
        New-Item -Path $extensionKey -Force | Out-Null
        Set-ItemProperty -LiteralPath $extensionKey -Name '(default)' -Value 'MSEdgeHTM'
    }
    $edgeClassKey = Join-Path $classesRoot 'MSEdgeHTM\shell\open\command'
    New-Item -Path $edgeClassKey -Force | Out-Null
    Set-ItemProperty -LiteralPath $edgeClassKey -Name '(default)' -Value ('"' + $edgePath + '" -- "%1"')
    Set-Content -LiteralPath $associationMarker -Value 'HTTP_HTTPS_EDGE_HANDLER_REGISTERED_INSIDE_SANDBOX=true' -Encoding ASCII
    $edgeProcess = Start-Process -FilePath $edgePath -ArgumentList @('--new-window', 'about:blank') -PassThru -WindowStyle Normal
    Set-Content -LiteralPath $edgeStartedPath -Value "EDGE_STARTED_INSIDE_SANDBOX=true`nPROCESS_ID=$($edgeProcess.Id)" -Encoding ASCII
} catch {
    Set-Content -LiteralPath $associationErrorPath -Value $_.Exception.Message -Encoding UTF8
}

$settingsPath = 'C:\output\browser-settings-started.txt'
$settingsErrorPath = 'C:\output\browser-settings-error.txt'
try {
    Start-Process -FilePath 'ms-settings:defaultapps' -ErrorAction Stop | Out-Null
    Set-Content -LiteralPath $settingsPath -Value 'DEFAULT_APPS_SETTINGS_OPEN_REQUESTED=true' -Encoding ASCII
} catch {
    Set-Content -LiteralPath $settingsErrorPath -Value $_.Exception.Message -Encoding UTF8
}
Start-Sleep -Seconds 5
& 'C:\control-r16\run.ps1'
