[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$output = Join-Path $root $OutputDirectory
New-Item -ItemType Directory -Path $output -Force | Out-Null

# Reuse the approved DPI-aware native capture implementation. Only the helper
# declarations are loaded; the source script's capture workflow is not run.
$captureSource = Get-Content -Raw (Join-Path $PSScriptRoot "capture_e03_asset_library_binary.ps1")
$helperStart = $captureSource.IndexOf("Add-Type -AssemblyName System.Drawing")
$helperEnd = $captureSource.IndexOf("function Set-DialogPath")
& ([scriptblock]::Create($captureSource.Substring($helperStart, $helperEnd - $helperStart)))
[NeoEngE03Capture]::EnablePerMonitorDpiAwareness()

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Threading;
public static class NeoEngHybridGestures {
    [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
    public static void Drag(int x, int y, int toX, int toY, bool middle) {
        const uint leftDown = 0x0002, leftUp = 0x0004;
        const uint middleDown = 0x0020, middleUp = 0x0040;
        uint down = middle ? middleDown : leftDown;
        uint up = middle ? middleUp : leftUp;
        SetCursorPos(x, y);
        mouse_event(down, 0, 0, 0, UIntPtr.Zero);
        try {
            for (int step = 1; step <= 40; step++) {
                SetCursorPos(x + (toX - x) * step / 40, y + (toY - y) * step / 40);
                Thread.Sleep(20);
            }
        } finally {
            mouse_event(up, 0, 0, 0, UIntPtr.Zero);
        }
    }
}
'@

$exePath = (Resolve-Path -LiteralPath $Executable).Path
$sourceProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$fixtureRoot = Join-Path $output "hybrid-fixture"
New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
Copy-Item -LiteralPath $sourceProject -Destination (Join-Path $fixtureRoot (Split-Path $sourceProject -Leaf)) -Force
$sourceScene = [IO.Path]::ChangeExtension($sourceProject, ".ndtscene.json")
if (Test-Path -LiteralPath $sourceScene -PathType Leaf) {
    Copy-Item -LiteralPath $sourceScene -Destination (Join-Path $fixtureRoot (Split-Path $sourceScene -Leaf)) -Force
}
$fixtureProject = (Resolve-Path -LiteralPath (Join-Path $fixtureRoot (Split-Path $sourceProject -Leaf))).Path
$sidecar = [IO.Path]::ChangeExtension($fixtureProject, ".hybrid3d.json")

$records = [ordered]@{
    executable = $exePath
    project = $fixtureProject
    sidecar = $sidecar
    actions = @()
}

function Save-Capture {
    param([IntPtr]$Handle, [string]$Path)
    [NeoEngE03Capture]::Capture($Handle, $Path) | Out-Null
    return [ordered]@{
        path = $Path
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    }
}

function Save-ScreenCapture {
    param([string]$Path)
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen(
            $bounds.Location,
            [System.Drawing.Point]::Empty,
            $bounds.Size
        )
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
    return [ordered]@{
        path = $Path
        sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        capture = "primary screen CopyFromScreen"
        bounds = "$($bounds.Left),$($bounds.Top),$($bounds.Right),$($bounds.Bottom)"
    }
}

function Add-Action {
    param([string]$Name, [string]$Operation, [hashtable]$Capture)
    $records.actions += [ordered]@{
        name = $Name
        operation = $Operation
        capture = $Capture
        time = (Get-Date).ToString("o")
    }
}

function Save-Editor {
    param([IntPtr]$Handle, [string]$Name)
    $path = Join-Path $output "$Name.png"
    return Save-Capture $Handle $path
}

function Save-Desktop {
    param([string]$Name)
    return Save-ScreenCapture (Join-Path $output "$Name.png")
}

function Click-Editor {
    param([IntPtr]$Handle, [int]$X, [int]$Y, [int]$Wait = 700)
    [NeoEngE03Capture]::Focus($Handle)
    [NeoEngE03Capture]::ClickWindow($Handle, $X, $Y)
    Start-Sleep -Milliseconds $Wait
}

function Drag-Editor {
    param(
        [IntPtr]$Handle,
        [int]$X,
        [int]$Y,
        [int]$ToX,
        [int]$ToY,
        [switch]$Middle
    )
    $rect = [NeoEngE03Capture]::RectText($Handle).Split(",")
    [NeoEngHybridGestures]::Drag(
        ([int]$rect[0] + $X),
        ([int]$rect[1] + $Y),
        ([int]$rect[0] + $ToX),
        ([int]$rect[1] + $ToY),
        $Middle.IsPresent
    )
    Start-Sleep -Milliseconds 700
}

function Get-EditorWindow {
    param([int]$ProcessId, [IntPtr]$MainHandle)
    $windows = @([NeoEngE03Capture]::GetWindows($ProcessId))
    $match = $windows |
        Where-Object { $_.Handle -ne $MainHandle -and $_.Title -match "Editor de Cenário|Scenario Editor" } |
        Select-Object -First 1
    if ($match) { return $match }
    return $windows | Where-Object { $_.Handle -ne $MainHandle } | Select-Object -First 1
}

$process = $null
try {
    $process = Start-Process -FilePath $exePath -ArgumentList @(
        "--open-project-gui", $fixtureProject, "--open-scenario-editor-gui"
    ) -PassThru
    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 250
        $process.Refresh()
        $mainHandle = $process.MainWindowHandle
    } while ($mainHandle -eq 0 -and (Get-Date) -lt $deadline)
    if ($mainHandle -eq 0) { throw "GUI main window was not exposed" }

    Start-Sleep -Milliseconds 3500
    $editor = Get-EditorWindow $process.Id $mainHandle
    if (-not $editor) {
        $titles = @([NeoEngE03Capture]::GetWindows($process.Id) | ForEach-Object { $_.Title })
        throw "scenario editor window was not exposed; observed windows: $($titles -join ' | ')"
    }
    [NeoEngE03Capture]::Focus($editor.Handle)
    Add-Action "editor-2d-initial" "direct project load; focus editor" (Save-Editor $editor.Handle "01-editor-2d-initial")

    # View > 3D/Hybrid Viewport. Coordinates are native window offsets on the
    # same DPI-aware host used by the existing post-E13 captures.
    # The capture is commonly displayed downscaled by the review UI.  Native
    # input must use the original 3866px-wide window coordinates: the Ver
    # button is around x=1370, not the downscaled x=730.
    Click-Editor $editor.Handle 1370 80 350
    Add-Action "view-menu" "native click: Ver" (Save-Desktop "02-view-menu")
    # Select the fourth visible menu row with a real mouse click.  Keyboard
    # navigation closes this Qt popup under the native capture host without
    # triggering the QAction, so it is not used as evidence.
    Click-Editor $editor.Handle 1535 295 1200
    Start-Sleep -Milliseconds 1200
    Add-Action "hybrid-entry" "native click: Ver; native click: Viewport 3D/Híbrido" (Save-Editor $editor.Handle "03-hybrid-entry")

    # Add an empty scene's primitives through the visible toolbar.
    Click-Editor $editor.Handle 2000 170 550
    Add-Action "add-plane" "native click: Adicionar plano" (Save-Editor $editor.Handle "04-hybrid-plane")
    Click-Editor $editor.Handle 2235 170 550
    Add-Action "add-light" "native click: Adicionar luz" (Save-Editor $editor.Handle "05-hybrid-light")
    Click-Editor $editor.Handle 2470 170 550
    Add-Action "add-camera" "native click: Adicionar câmera" (Save-Editor $editor.Handle "06-hybrid-camera")

    # Select the camera from the visible hierarchy and edit its target fields.
    Click-Editor $editor.Handle 800 720 450
    Add-Action "camera-selected" "native click: hierarchy camera" (Save-Editor $editor.Handle "07-camera-selected")
    Click-Editor $editor.Handle 2750 1080 150
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    [System.Windows.Forms.SendKeys]::SendWait("2,5")
    [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
    Click-Editor $editor.Handle 2750 1140 150
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    [System.Windows.Forms.SendKeys]::SendWait("1,25")
    [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
    Add-Action "camera-target" "native numeric edits: target X/Y" (Save-Editor $editor.Handle "08-camera-target")

    # Select the cube in the hierarchy and perform a real viewport drag.
    Click-Editor $editor.Handle 800 365 350
    Drag-Editor $editor.Handle 1750 870 1900 870
    Add-Action "mesh-drag" "native left-button drag: mesh position" (Save-Editor $editor.Handle "09-mesh-drag")
    Drag-Editor $editor.Handle 1900 870 2060 760 -Middle
    Add-Action "orbit" "native middle-button drag: viewport orbit" (Save-Editor $editor.Handle "10-viewport-orbit")

    # Exercise the explicit view modes and camera projection.
    Click-Editor $editor.Handle 800 170 250
    [System.Windows.Forms.SendKeys]::SendWait("{HOME}{DOWN 1}{ENTER}")
    Click-Editor $editor.Handle 1140 170 350
    Add-Action "projection-menu" "native click: abrir lista de projeção" (Save-Desktop "11-projection-menu")
    Click-Editor $editor.Handle 1055 285 800
    Add-Action "mode-and-projection" "native combo navigation: 2.5D and orthographic" (Save-Editor $editor.Handle "11-mode-25d-orthographic")

    Click-Editor $editor.Handle 1410 170 700
    Add-Action "save-sidecar" "native click: Salvar 3D" (Save-Editor $editor.Handle "12-hybrid-saved")
    if (-not (Test-Path -LiteralPath $sidecar -PathType Leaf)) {
        throw "hybrid sidecar was not created by native Save 3D"
    }

    # Close the editor window, relaunch the same binary and reopen the same
    # project. The second hybrid entry must load the saved sidecar.
    [NeoEngE03Capture]::Focus($editor.Handle)
    [System.Windows.Forms.SendKeys]::SendWait("%{F4}")
    Start-Sleep -Milliseconds 1200
    if (-not $process.HasExited) { $process.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 600 }
    if (-not $process.HasExited) { $process.Kill() }
    $process = Start-Process -FilePath $exePath -ArgumentList @(
        "--open-project-gui", $fixtureProject, "--open-scenario-editor-gui"
    ) -PassThru
    $deadline = (Get-Date).AddSeconds(25)
    do {
        Start-Sleep -Milliseconds 250
        $process.Refresh()
        $mainHandle = $process.MainWindowHandle
    } while ($mainHandle -eq 0 -and (Get-Date) -lt $deadline)
    Start-Sleep -Milliseconds 3500
    $editor = Get-EditorWindow $process.Id $mainHandle
    if (-not $editor) {
        $titles = @([NeoEngE03Capture]::GetWindows($process.Id) | ForEach-Object { $_.Title })
        throw "scenario editor window was not exposed after reopen; observed windows: $($titles -join ' | ')"
    }
    Click-Editor $editor.Handle 1370 80 350
    Click-Editor $editor.Handle 1535 295 1200
    Start-Sleep -Milliseconds 1200
    Add-Action "hybrid-reopened" "relaunch binary; native hybrid entry; sidecar load" (Save-Editor $editor.Handle "13-hybrid-reopened")
    $records.sidecar_sha256 = (Get-FileHash -LiteralPath $sidecar -Algorithm SHA256).Hash
    $records.editor_title = $editor.Title
    $records.editor_rect = [NeoEngE03Capture]::RectText($editor.Handle)
    $records.process_ids = @($process.Id)
    $records.status = "PASS_NATIVE_FLOW"
}
finally {
    if ($process -and -not $process.HasExited) {
        $process.CloseMainWindow() | Out-Null
        Start-Sleep -Milliseconds 500
        if (-not $process.HasExited) { $process.Kill() }
    }
    $records | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output "actions.json") -Encoding utf8
}

$records | ConvertTo-Json -Depth 8
