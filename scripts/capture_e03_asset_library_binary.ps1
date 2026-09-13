param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [switch]$CaptureTilemapFlow,
    [switch]$CaptureColliderFlow,
    [switch]$CaptureNavMeshFlow,
    [switch]$CaptureEntityPrefabFlow,
    [switch]$CaptureRendererFlow,
    [switch]$CaptureMaterialFlow,
    [switch]$CaptureParallaxFlow,
    [switch]$CaptureVectorContourFlow,
    [switch]$CaptureMaskViewerFlow,
    [switch]$CaptureContextMenuFlow,
    [switch]$CaptureSequenceStudioFlow,
    [switch]$CaptureAssetPackFlow,
    [switch]$CaptureProfessionalContextMenuFlow,
    [switch]$DirectProjectLoad
)

$ErrorActionPreference = "Stop"
$tilesetFlow = $CaptureContextMenuFlow -and $OutputDirectory -match "tileset"
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$drawingAssembly = [System.Drawing.Bitmap].Assembly.Location
$drawingPrimitivesAssembly = [System.Drawing.Size].Assembly.Location
$windowsAssemblies = @(Get-ChildItem -LiteralPath $PSHOME -Filter "System.Private.Windows*.dll" | ForEach-Object { $_.FullName })
$references = @($drawingAssembly, $drawingPrimitivesAssembly) + $windowsAssemblies
Add-Type -TypeDefinition @"
using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;

public static class NeoEngE03Capture
{
    [StructLayout(LayoutKind.Sequential)] private struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public sealed class WindowInfo { public IntPtr Handle; public string Title; }
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr extra);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int length);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] private static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool SetProcessDpiAwarenessContext(IntPtr value);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] private static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] private static extern IntPtr SetFocus(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] private static extern void keybd_event(byte key, byte scan, uint flags, UIntPtr extra);

    public static void EnablePerMonitorDpiAwareness()
    {
        // DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2.  Without this, the
        // PowerShell host virtualizes PrintWindow and clips the Qt surface to
        // the left half of the maximized 200% editor.
        SetProcessDpiAwarenessContext(new IntPtr(-4));
    }

    public static WindowInfo[] GetWindows(int pid)
    {
        var result = new WindowInfo[256]; int count = 0;
        EnumWindows((hWnd, _) => {
            uint ownerPid; GetWindowThreadProcessId(hWnd, out ownerPid);
            if (ownerPid != pid || !IsWindowVisible(hWnd)) return true;
            var text = new StringBuilder(512); GetWindowText(hWnd, text, text.Capacity);
            if (count < result.Length) result[count++] = new WindowInfo { Handle = hWnd, Title = text.ToString() };
            return true;
        }, IntPtr.Zero);
        var final = new WindowInfo[count]; Array.Copy(result, final, count); return final;
    }

    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    public static void Focus(IntPtr hWnd) { ShowWindow(hWnd, 3); BringWindowToTop(hWnd); SetForegroundWindow(hWnd); SetFocus(hWnd); }
    public static void Hide(IntPtr hWnd) { ShowWindow(hWnd, 0); }
    public static void Restore(IntPtr hWnd) { ShowWindow(hWnd, 9); BringWindowToTop(hWnd); SetForegroundWindow(hWnd); }
    public static void ClickWindow(IntPtr hWnd, int offsetX, int offsetY)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        SetCursorPos(rect.Left + offsetX, rect.Top + offsetY);
        const uint down = 0x0002, up = 0x0004;
        mouse_event(down, 0, 0, 0, UIntPtr.Zero); mouse_event(up, 0, 0, 0, UIntPtr.Zero);
    }
    public static void RightClickWindow(IntPtr hWnd, int offsetX, int offsetY)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        SetCursorPos(rect.Left + offsetX, rect.Top + offsetY);
        const uint down = 0x0008, up = 0x0010;
        mouse_event(down, 0, 0, 0, UIntPtr.Zero); mouse_event(up, 0, 0, 0, UIntPtr.Zero);
    }
    public static IntPtr Foreground() { return GetForegroundWindow(); }
    public static void ClickWindowFraction(IntPtr hWnd, double fractionX, double fractionY)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = rect.Right - rect.Left, height = rect.Bottom - rect.Top;
        ClickWindow(hWnd, (int)(width * fractionX), (int)(height * fractionY));
    }
    public static void ScrollWindowFraction(IntPtr hWnd, double fractionX, double fractionY, int delta)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = rect.Right - rect.Left, height = rect.Bottom - rect.Top;
        SetCursorPos(rect.Left + (int)(width * fractionX), rect.Top + (int)(height * fractionY));
        mouse_event(0x0800, 0, 0, (uint)delta, UIntPtr.Zero);
    }
    public static string RectText(IntPtr hWnd)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) return "unknown";
        return String.Format("{0},{1},{2},{3}", rect.Left, rect.Top, rect.Right, rect.Bottom);
    }
    public static void CtrlO() { const uint up = 0x0002; keybd_event(0x11,0,0,UIntPtr.Zero); keybd_event(0x4F,0,0,UIntPtr.Zero); keybd_event(0x4F,0,up,UIntPtr.Zero); keybd_event(0x11,0,up,UIntPtr.Zero); }
    public static string Capture(IntPtr hWnd, string path)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = rect.Right - rect.Left, height = rect.Bottom - rect.Top;
        using (var bitmap = new Bitmap(width, height)) using (var graphics = Graphics.FromImage(bitmap))
        {
            IntPtr hdc = graphics.GetHdc(); try { if (!PrintWindow(hWnd, hdc, 2)) throw new InvalidOperationException("PrintWindow failed"); }
            finally { graphics.ReleaseHdc(hdc); } bitmap.Save(path);
        }
        return width + "x" + height;
    }
}
"@ -ReferencedAssemblies $references

[NeoEngE03Capture]::EnablePerMonitorDpiAwareness()

function Set-DialogPath {
    param([IntPtr]$Handle, [string]$Path)
    [NeoEngE03Capture]::Focus($Handle)
    Start-Sleep -Milliseconds 150
    [System.Windows.Forms.Clipboard]::SetText($Path)
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
}

function New-SilentWave {
    param([string]$Path)
    $sampleRate = 44100
    $channels = 1
    $bitsPerSample = 16
    $sampleCount = $sampleRate
    $blockAlign = $channels * ($bitsPerSample / 8)
    $byteRate = $sampleRate * $blockAlign
    $dataSize = $sampleCount * $blockAlign
    $stream = New-Object System.IO.MemoryStream
    $writer = New-Object System.IO.BinaryWriter($stream)
    try {
        $writer.Write([System.Text.Encoding]::ASCII.GetBytes("RIFF"))
        $writer.Write([int](36 + $dataSize))
        $writer.Write([System.Text.Encoding]::ASCII.GetBytes("WAVE"))
        $writer.Write([System.Text.Encoding]::ASCII.GetBytes("fmt "))
        $writer.Write([int]16)
        $writer.Write([int16]1)
        $writer.Write([int16]$channels)
        $writer.Write([int]$sampleRate)
        $writer.Write([int]$byteRate)
        $writer.Write([int16]$blockAlign)
        $writer.Write([int16]$bitsPerSample)
        $writer.Write([System.Text.Encoding]::ASCII.GetBytes("data"))
        $writer.Write([int]$dataSize)
        for ($sample = 0; $sample -lt $sampleCount; $sample++) {
            $writer.Write([int16]0)
        }
        $writer.Flush()
        [System.IO.File]::WriteAllBytes($Path, $stream.ToArray())
    } finally {
        $writer.Dispose()
        $stream.Dispose()
    }
}

function Save-Capture {
    param([IntPtr]$Handle, [string]$Path)
    [NeoEngE03Capture]::Capture($Handle, $Path) | Out-Null
    return [ordered]@{ path = $Path; sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
}

function Read-NativeTilemapPersistence {
    param([string]$ProjectPath)
    $projectFile = if (Test-Path -LiteralPath $ProjectPath -PathType Leaf) {
        (Resolve-Path -LiteralPath $ProjectPath).Path
    } else {
        Get-ChildItem -LiteralPath $ProjectPath -Filter "*.ndtproj" -File | Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $projectFile) { throw "native Tilemap persistence requires a .ndtproj project file" }
    $tilemapDirectory = Join-Path (Split-Path -Parent $projectFile) "assets\tilemaps"
    $tilemapPath = Join-Path $tilemapDirectory "scenario.tilemap.json"
    if (-not (Test-Path -LiteralPath $tilemapPath -PathType Leaf)) {
        throw "native Tilemap save did not produce the expected sidecar: $tilemapPath"
    }
    $tilemap = Get-Content -LiteralPath $tilemapPath -Raw | ConvertFrom-Json
    $cells = @($tilemap.cells)
    if ($cells.Count -lt 1) {
        throw "native Tilemap sidecar contains no painted cells: $tilemapPath"
    }
    return [ordered]@{
        path = $tilemapPath
        sha256 = (Get-FileHash -LiteralPath $tilemapPath -Algorithm SHA256).Hash
        cell_count = $cells.Count
        layer_count = @($tilemap.layers).Count
        format_id = $tilemap.format_id
        schema_version = $tilemap.schema_version
    }
}

function Read-NativeTilesetPersistence {
    param([string]$ProjectPath)
    $projectFile = if (Test-Path -LiteralPath $ProjectPath -PathType Leaf) {
        (Resolve-Path -LiteralPath $ProjectPath).Path
    } else {
        Get-ChildItem -LiteralPath $ProjectPath -Filter "*.ndtproj" -File | Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $projectFile) { throw "native Tileset persistence requires a .ndtproj project file" }
    $tilesetPath = Join-Path (Split-Path -Parent $projectFile) "assets\tilesets\scenario\tileset.json"
    if (-not (Test-Path -LiteralPath $tilesetPath -PathType Leaf)) {
        throw "native Tileset save did not produce the expected sidecar: $tilesetPath"
    }
    $tileset = Get-Content -LiteralPath $tilesetPath -Raw | ConvertFrom-Json
    $tiles = @($tileset.tiles)
    if ($tiles.Count -lt 1) {
        throw "native Tileset sidecar contains no tiles: $tilesetPath"
    }
    return [ordered]@{
        path = $tilesetPath
        sha256 = (Get-FileHash -LiteralPath $tilesetPath -Algorithm SHA256).Hash
        tile_count = $tiles.Count
        format_id = $tileset.format_id
        schema_version = $tileset.schema_version
        atlas_path = $tileset.atlas_path
        atlas_sha256 = $tileset.atlas_sha256
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

function Enter-AdvancedTool {
    param([IntPtr]$Handle, [int]$TabY)
    [NeoEngE03Capture]::Focus($Handle)
    # The integrated tools are reachable through the same user-visible path:
    # add a timeline clip, open Ferramentas, then choose the west-side tool
    # tab.  All coordinates are native window offsets for this DPI-aware
    # binary capture host.
    [NeoEngE03Capture]::ClickWindow($Handle, 2640, 1670)
    Start-Sleep -Milliseconds 800
    [NeoEngE03Capture]::ClickWindow($Handle, 3290, 150)
    Start-Sleep -Milliseconds 500
    [NeoEngE03Capture]::ClickWindow($Handle, 2970, $TabY)
    Start-Sleep -Milliseconds 700
}

$exePath = (Resolve-Path -LiteralPath $Executable).Path
$projectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
if ($CaptureVectorContourFlow) {
    $fixtureRoot = Join-Path (Resolve-Path -LiteralPath $OutputDirectory).Path "vector-contour-fixture"
    $fixtureAssetDir = Join-Path $fixtureRoot "assets\scene"
    New-Item -ItemType Directory -Path $fixtureAssetDir -Force | Out-Null
    $sourceFixture = (Resolve-Path -LiteralPath "docs\evidence\artifacts\roi-grabcut-collision\source.png").Path
    $fixtureAsset = Join-Path $fixtureAssetDir "vector-source.png"
    Copy-Item -LiteralPath $sourceFixture -Destination $fixtureAsset -Force
    $fixtureHash = (Get-FileHash -LiteralPath $fixtureAsset -Algorithm SHA256).Hash.ToLowerInvariant()
    $baseProjectFile = if (Test-Path -LiteralPath $projectPath -PathType Leaf) {
        $projectPath
    } else {
        Get-ChildItem -LiteralPath $projectPath -Filter "*.ndtproj" -File | Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $baseProjectFile) { throw "vector contour capture requires a base .ndtproj" }
    $vectorProject = Join-Path $fixtureRoot "vector-contour.ndtproj"
    Copy-Item -LiteralPath $baseProjectFile -Destination $vectorProject -Force
    $vectorScene = @"
{
  "format_id": "neoeng-d-trace-scene-authoring",
  "schema_version": 2,
  "metadata": {"name": "E09 Vector Contour Fixture", "generator": "NeoEng-D-Trace E09", "app_version": "0.3.0"},
  "project": {"sha256": "0000000000000000000000000000000000000000000000000000000000000000"},
  "assets": [{"id": "vector-source", "path": "assets/scene/vector-source.png", "path_kind": "relative", "sha256": "$fixtureHash"}],
  "layers": [{"id": "layer_default", "name": "Default", "visible": true, "locked": false}],
  "objects": [], "groups": [], "snap": {"enabled": false, "mode": "pixel", "spacing": {"x": 1.0, "y": 1.0}}
}
"@
    $sceneBytes = [System.Text.UTF8Encoding]::new($false).GetBytes($vectorScene)
    [System.IO.File]::WriteAllBytes((Join-Path $fixtureRoot "vector-contour.ndtscene.json"), $sceneBytes)
    $projectPath = (Resolve-Path -LiteralPath $vectorProject).Path
}
if ($tilesetFlow) {
    $sourceProjectDir = Split-Path -Path $projectPath -Parent
    $fixtureRoot = Join-Path (Resolve-Path -LiteralPath $OutputDirectory).Path "tileset-fixture"
    New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceProjectDir -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $fixtureRoot -Recurse -Force
    }
    $fixtureAssetDir = Join-Path $fixtureRoot "assets\scene"
    New-Item -ItemType Directory -Path $fixtureAssetDir -Force | Out-Null
    $sourceFixture = (Resolve-Path -LiteralPath "docs\evidence\artifacts\roi-grabcut-collision\source.png").Path
    Copy-Item -LiteralPath $sourceFixture -Destination (Join-Path $fixtureAssetDir "tileset-atlas.png") -Force
    $projectPath = (Get-ChildItem -LiteralPath $fixtureRoot -Filter "*.ndtproj" -File | Select-Object -First 1 -ExpandProperty FullName)
}
$audioFixturePath = $null
if ($CaptureSequenceStudioFlow -and -not $tilesetFlow) {
    $audioFixturePath = Join-Path (Split-Path -Path $projectPath -Parent) "assets\audio\sequence-theme.wav"
    New-Item -ItemType Directory -Path (Split-Path -Path $audioFixturePath -Parent) -Force | Out-Null
    New-SilentWave $audioFixturePath
}
$startArguments = @()
if ($DirectProjectLoad) {
    $directProjectFile = if (Test-Path -LiteralPath $projectPath -PathType Leaf) {
        $projectPath
    } else {
        Get-ChildItem -LiteralPath $projectPath -Filter "*.ndtproj" -File | Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $directProjectFile) { throw "direct GUI capture requires an .ndtproj file" }
    $startArguments = @("--open-project-gui", $directProjectFile, "--open-scenario-editor-gui")
}
$process = if ($startArguments.Count) {
    Start-Process -FilePath $exePath -ArgumentList $startArguments -PassThru
} else {
    Start-Process -FilePath $exePath -PassThru
}
try {
    $deadline = (Get-Date).AddSeconds(20)
    do { Start-Sleep -Milliseconds 250; $process.Refresh(); $mainHandle = $process.MainWindowHandle } while ($mainHandle -eq 0 -and (Get-Date) -lt $deadline)
    if ($mainHandle -eq 0) { throw "GUI main window was not exposed" }

    $records = [ordered]@{}
    $records.main = Save-Capture $mainHandle (Join-Path $OutputDirectory "01-main.png")
    if ($DirectProjectLoad) {
        Start-Sleep -Milliseconds 3200
        [NeoEngE03Capture]::Focus($mainHandle)
        $records.main_after_project_load = Save-Capture $mainHandle (Join-Path $OutputDirectory "03-main-after-project-load.png")
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
        if (-not $editor) { throw "professional scenario editor was not exposed by direct GUI load" }
    } else {
        [NeoEngE03Capture]::Focus($mainHandle)
        [System.Windows.Forms.SendKeys]::SendWait("^o")
        Start-Sleep -Milliseconds 1200
        $dialog = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
        if (-not $dialog) {
            [NeoEngE03Capture]::Focus($mainHandle)
            Start-Sleep -Milliseconds 300
            [NeoEngE03Capture]::ClickWindow($mainHandle, 80, 150)
            Start-Sleep -Milliseconds 1200
            $dialog = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
        }
        if (-not $dialog) { throw "project open dialog was not exposed" }
        $records.project_dialog = Save-Capture $dialog.Handle (Join-Path $OutputDirectory "02-project-open-dialog.png")
        Set-DialogPath $dialog.Handle $projectPath
        Start-Sleep -Milliseconds 1800
        [NeoEngE03Capture]::Focus($mainHandle)
        $records.main_after_project_load = Save-Capture $mainHandle (Join-Path $OutputDirectory "03-main-after-project-load.png")
        [NeoEngE03Capture]::ClickWindow($mainHandle, 1430, 160)
        Start-Sleep -Milliseconds 2200
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
        if (-not $editor) {
            [NeoEngE03Capture]::Focus($mainHandle)
            [NeoEngE03Capture]::ClickWindow($mainHandle, 1430, 160)
            Start-Sleep -Milliseconds 2200
            $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
        }
        if (-not $editor) { throw "professional scenario editor was not exposed" }
    }
    if ($CaptureMaskViewerFlow) {
        # Direct project load opens the professional scenario editor as a
        # second top-level window.  The mask command belongs to the main
        # editor; hide the secondary window so the real native click reaches
        # the intended View/Visualizar button.
        [NeoEngE03Capture]::Hide($editor.Handle)
        [NeoEngE03Capture]::Focus($mainHandle)
        # The shipped reference toolbar places View/Visualizar at this
        # native-DPI-relative location. Select the real mask-viewer action
        # from that menu with keyboard navigation so the capture remains
        # language-independent.
        [NeoEngE03Capture]::ClickWindow($mainHandle, 1125, 150)
        Start-Sleep -Milliseconds 250
        # Preserve the actual popup state when a semantic dialog is not
        # exposed.  This is a diagnostic screen capture only; it must never
        # be used as proof that the mask viewer opened.
        $records.view_menu_popup_screen = Save-ScreenCapture (Join-Path $OutputDirectory "03-view-menu-popup-screen.png")
        # The real popup is visible in the preceding screen capture.  Click
        # the semantic Mask Viewer row directly instead of relying on
        # keyboard focus, which can remain with the PowerShell host even
        # though Qt has painted the menu.  The offset is measured from the
        # native-DPI main window on the controlled capture workstation.
        [NeoEngE03Capture]::ClickWindow($mainHandle, 1140, 560)
        Start-Sleep -Milliseconds 1800
        # The professional scenario editor is already another top-level
        # window in this flow.  Do not accept it as a mask capture merely
        # because it is the first window returned by EnumWindows; require the
        # semantic title emitted by MaskViewerDialog instead.
        $mask = [NeoEngE03Capture]::GetWindows($process.Id) |
            Where-Object {
                $_.Handle -ne $mainHandle -and
                $_.Title -match "(?i)mask|máscara|mascara|raio-x|x-ray"
            } |
            Select-Object -First 1
        if (-not $mask) {
            $titles = [NeoEngE03Capture]::GetWindows($process.Id) |
                ForEach-Object { $_.Title } |
                Where-Object { $_ -and $_.Trim() } |
                Select-Object -Unique
            throw "Mask Viewer was not exposed by portable binary; observed windows: $($titles -join ' | ')"
        }
        $records.mask_viewer = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer.png")
        # Exercise the visible processing modes with the image loaded.  These
        # are native clicks in the dialog and each capture is kept separate so
        # a later mode cannot hide an earlier visual result.
        [NeoEngE03Capture]::Focus($mask.Handle)
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 320, 130)
        Start-Sleep -Milliseconds 900
        $records.mask_viewer_perfeito = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-perfeito.png")
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 500, 130)
        Start-Sleep -Milliseconds 900
        $records.mask_viewer_aprim = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-aprim.png")
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 670, 130)
        Start-Sleep -Milliseconds 1200
        $records.mask_viewer_grabcut = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-grabcut.png")
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 320, 285)
        Start-Sleep -Milliseconds 500
        $records.mask_viewer_sobel = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-sobel.png")
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 500, 285)
        Start-Sleep -Milliseconds 500
        $records.mask_viewer_canny = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-canny.png")
        [NeoEngE03Capture]::ClickWindow($mask.Handle, 670, 285)
        Start-Sleep -Milliseconds 500
        $records.mask_viewer_laplaciano = Save-Capture $mask.Handle (Join-Path $OutputDirectory "04-mask-viewer-laplaciano.png")
    }
    [NeoEngE03Capture]::Focus($editor.Handle)
    Start-Sleep -Milliseconds 800
    # Make the library assertion observable: the user-visible catalog is a
    # sibling tab of Molduras/Hierarquia, so select it with a native click
    # before capturing the ready state.  The controlled workstation uses the
    # native-DPI offset below; no catalog data is changed.
    [NeoEngE03Capture]::ClickWindow($editor.Handle, 420, 195)
    Start-Sleep -Milliseconds 600
    $records.asset_library_ready = Save-Capture $editor.Handle (Join-Path $OutputDirectory "05-asset-library-ready.png")
    $records.asset_library_ready = Save-Capture $editor.Handle (Join-Path $OutputDirectory "05-asset-library-ready.png")
    # The editor has no Alt+P mnemonic.  Sending it can open an unrelated
    # native action and block PrintWindow.  Search/category behavior is
    # covered by the focused Qt contract tests; this binary capture remains
    # the authoritative visual proof of the real shipped editor surface.
    $records.asset_library_filter_contract = "covered by focused Qt tests; controls visible in asset_library_ready"
    if ($CaptureProfessionalContextMenuFlow) {
        # The professional viewport is a separate top-level window from the
        # main editor.  Keep it visible and exercise the actual right-click
        # surface over the fixture object; this is distinct from the main
        # editor's list context-menu flow below.
        [NeoEngE03Capture]::Focus($editor.Handle)
        Start-Sleep -Milliseconds 500
        $records.professional_context_before = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-professional-context-before.png")
        # Right-click before selecting so itemAt() resolves the authored
        # graphics item rather than the transform gizmo drawn above it.  The
        # viewport itself then performs the normal selection as part of the
        # context-menu event.
        [NeoEngE03Capture]::RightClickWindow($editor.Handle, 1760, 860)
        Start-Sleep -Milliseconds 700
        $foregroundHandle = [NeoEngE03Capture]::Foreground()
        # QMenu can be painted without a separately enumerable title on this
        # Qt/Windows host.  Capture the real primary screen so the popup and
        # its localized labels remain visible for human review.
        $records.professional_context_menu = Save-ScreenCapture (Join-Path $OutputDirectory "07-professional-context-menu.png")
        if ($foregroundHandle -eq $mainHandle -or $foregroundHandle -eq $editor.Handle) {
            $records.professional_context_window_title = "foreground remained editor; screen capture requires human popup review"
            Write-Warning "professional viewport context menu handle was not exposed; preserved primary-screen diagnostic"
        } else {
            $records.professional_context_window_title = "foreground popup handle $foregroundHandle"
        }
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 600, 600)
        Start-Sleep -Milliseconds 300
    }
    if ($CaptureAssetPackFlow) {
        # Open the bundled, read-only catalog through the same Biblioteca
        # surface a user sees. Require its semantic dialog title before
        # capturing; a generic secondary window is not acceptable evidence.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 420, 355)
        Start-Sleep -Milliseconds 1800
        $pack = [NeoEngE03Capture]::GetWindows($process.Id) |
            Where-Object {
                $_.Handle -ne $mainHandle -and
                $_.Handle -ne $editor.Handle -and
                $_.Title -match "(?i)pacotes|packs"
            } |
            Select-Object -First 1
        if (-not $pack) {
            $titles = [NeoEngE03Capture]::GetWindows($process.Id) |
                ForEach-Object { $_.Title } |
                Where-Object { $_ -and $_.Trim() } |
                Select-Object -Unique
            throw "Asset pack dialog was not exposed by portable binary; observed windows: $($titles -join ' | ')"
        }
        $records.asset_pack_dialog = Save-Capture $pack.Handle (Join-Path $OutputDirectory "06-asset-pack-dialog.png")
        [NeoEngE03Capture]::Focus($pack.Handle)
        [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
        Start-Sleep -Milliseconds 500
    }
    if ($CaptureContextMenuFlow -and -not $tilesetFlow) {
        # The main editor and professional editor are separate top-level
        # windows. Hide the latter for this main-editor interaction so the
        # native list and its popup are actually foreground surfaces.
        [NeoEngE03Capture]::Hide($editor.Handle)
        [NeoEngE03Capture]::Focus($mainHandle)
        Start-Sleep -Milliseconds 500
        $records.main_before_context = Save-Capture $mainHandle (Join-Path $OutputDirectory "05-main-before-context.png")
        # The context menu belongs to the main editor's scene-object list, not
        # to the separate professional scenario window.  Select the first
        # fixture object through the visible list and open its menu with a
        # native right click at the DPI-aware coordinates of that list.
        [NeoEngE03Capture]::RightClickWindow($mainHandle, 3120, 460)
        Start-Sleep -Milliseconds 600
        $foregroundHandle = [NeoEngE03Capture]::Foreground()
        $menuWindow = [NeoEngE03Capture]::GetWindows($process.Id) |
            Where-Object { $_.Handle -ne $mainHandle -and $_.Handle -ne $editor.Handle } |
            Select-Object -First 1
        if ($foregroundHandle -eq $mainHandle -or $foregroundHandle -eq $editor.Handle) {
            # Use the standard keyboard context-menu gesture only as a
            # diagnostic fallback after the real mouse attempt.
            [NeoEngE03Capture]::Focus($mainHandle)
            [NeoEngE03Capture]::ClickWindow($mainHandle, 3120, 460)
            [System.Windows.Forms.SendKeys]::SendWait("+{F10}")
            Start-Sleep -Milliseconds 400
            $foregroundHandle = [NeoEngE03Capture]::Foreground()
            $menuWindow = [NeoEngE03Capture]::GetWindows($process.Id) |
                Where-Object { $_.Handle -ne $mainHandle -and $_.Handle -ne $editor.Handle } |
                Select-Object -First 1
        }
        if ($foregroundHandle -ne [IntPtr]::Zero -and $foregroundHandle -ne $mainHandle -and $foregroundHandle -ne $editor.Handle) {
            $records.context_menu_layer = Save-Capture $foregroundHandle (Join-Path $OutputDirectory "06-context-menu-layer.png")
            $records.context_menu_window_title = "foreground popup"
        } elseif ($menuWindow) {
            $records.context_menu_layer = Save-Capture $menuWindow.Handle (Join-Path $OutputDirectory "06-context-menu-layer.png")
            $records.context_menu_window_title = $menuWindow.Title
        } else {
            # QMenu can remain an unenumerated popup on this Qt/Windows host.
            # A full primary-screen capture still records the real popup if it
            # was painted, and is stronger evidence than recapturing the editor.
            $records.context_menu_layer = Save-ScreenCapture (Join-Path $OutputDirectory "06-context-menu-layer.png")
            $records.context_menu_window_title = "screen capture; popup not exposed as a top-level window"
        }
        [NeoEngE03Capture]::ClickWindow($mainHandle, 600, 600)
        [NeoEngE03Capture]::Restore($editor.Handle)
    }
    if ($CaptureSequenceStudioFlow -and -not $tilesetFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # A real user reaches the integrated studio tools by creating/selecting
        # a timeline clip.  The clip selection emits editor_requested and
        # switches the right dock from the numeric inspector to Ferramentas.
        # This is intentionally a native mouse click on the shipped binary.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2640, 1670)
        Start-Sleep -Milliseconds 900
        $records.sequence_studio_after_clip = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-sequence-studio-after-clip.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2280, 1670)
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{HOME}{DOWN 2}{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2640, 1670)
        Start-Sleep -Milliseconds 900
        $records.sequence_studio_text_clip = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-sequence-studio-text-clip.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2280, 1670)
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{HOME}{DOWN 3}{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2640, 1670)
        Start-Sleep -Milliseconds 900
        $records.sequence_studio_particle_clip = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-sequence-studio-particle-clip.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2280, 1670)
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{HOME}{DOWN 7}{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2640, 1670)
        Start-Sleep -Milliseconds 1000
        $audioDialog = [NeoEngE03Capture]::GetWindows($process.Id) |
            Where-Object { $_.Handle -ne $mainHandle -and $_.Handle -ne $editor.Handle -and $_.Title -match "(?i)áudio|audio|open|abrir" } |
            Select-Object -First 1
        if (-not $audioDialog) {
            $audioDialog = [NeoEngE03Capture]::GetWindows($process.Id) |
                Where-Object { $_.Handle -ne $mainHandle -and $_.Handle -ne $editor.Handle } |
                Select-Object -First 1
        }
        if (-not $audioDialog) { throw "audio file dialog was not exposed by native editor flow" }
        $records.sequence_studio_audio_dialog = Save-Capture $audioDialog.Handle (Join-Path $OutputDirectory "09-sequence-studio-audio-dialog.png")
        Set-DialogPath $audioDialog.Handle $audioFixturePath
        Start-Sleep -Milliseconds 1400
        $records.sequence_studio_audio_clip = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-sequence-studio-audio-clip.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2280, 1670)
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{HOME}{DOWN 8}{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2640, 1670)
        Start-Sleep -Milliseconds 900
        $records.sequence_studio_text_clip_real = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-sequence-studio-text-clip-real.png")
    }
    if ($CaptureVectorContourFlow) {
        Enter-AdvancedTool $editor.Handle 230
        $records.vector_contour_initial = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-vector-contour-initial.png")
        # The real user path is the composition-side Biblioteca tab, not a
        # guessed inspector scroll. Select the fixture asset from that list so
        # the signal reaches Contorno vetorial.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 420, 198)
        Start-Sleep -Milliseconds 700
        $records.vector_library_open = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-vector-library-open.png")
        # The native capture is 3866x2090; the visible raster row is centered
        # at client y~505 after the library is open. Keep the click on the
        # actual asset row so contour authoring starts from a selected asset.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 170, 505)
        Start-Sleep -Milliseconds 700
        $records.vector_library_selected = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-vector-library-selected.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 230)
        Start-Sleep -Milliseconds 700
        $records.vector_contour_asset = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-vector-contour-asset.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.88, 0.24)
        Start-Sleep -Milliseconds 500
        for ($scrollStep = 0; $scrollStep -lt 30; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.985, 0.25, 120)
            Start-Sleep -Milliseconds 100
        }
        Start-Sleep -Milliseconds 600
        $records.vector_contour_selected = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-vector-contour-selected.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3200, 860)
        Start-Sleep -Milliseconds 900
        $records.vector_contour_detected = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-vector-contour-detected.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3480, 1120)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.SendKeys]::SendWait("-5")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3480, 1180)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.SendKeys]::SendWait("-5")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 1250)
        Start-Sleep -Milliseconds 700
        $records.vector_contour_edited = Save-Capture $editor.Handle (Join-Path $OutputDirectory "12-vector-contour-edited.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 1315)
        Start-Sleep -Milliseconds 900
        $records.vector_contour_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "13-vector-contour-created.png")
        # Persist the newly created vector scene object through the same
        # toolbar path a user uses, then reload it to prove the round-trip.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 557, 90)
        Start-Sleep -Milliseconds 800
        $records.vector_contour_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "14-vector-contour-saved.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 708, 90)
        Start-Sleep -Milliseconds 1000
        $records.vector_contour_reloaded = Save-Capture $editor.Handle (Join-Path $OutputDirectory "15-vector-contour-reloaded.png")
    }
    if ($tilesetFlow) {
        Enter-AdvancedTool $editor.Handle 310
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 380)
        Start-Sleep -Milliseconds 600
        $records.tileset_panel_entry = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-tileset-panel-entry.png")
        $atlasPath = Join-Path $fixtureRoot "assets\scene\tileset-atlas.png"
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3350, 313)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.Clipboard]::SetText($atlasPath)
        [System.Windows.Forms.SendKeys]::SendWait("^v")
        [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3310, 625)
        Start-Sleep -Milliseconds 900
        $records.tileset_generated = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-tileset-generated.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3520, 625)
        Start-Sleep -Milliseconds 900
        $records.tileset_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-tileset-saved.png")
        $records.tileset_persistence = Read-NativeTilesetPersistence $projectPath
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3105, 625)
        Start-Sleep -Milliseconds 500
        $records.tileset_new = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-tileset-new.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3715, 625)
        Start-Sleep -Milliseconds 900
        $records.tileset_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-tileset-reopened.png")
    }
    if ($CaptureTilemapFlow) {
        # A user first creates/selects a timeline clip, opens Ferramentas,
        # then selects Tiles.  Without this transition the numeric inspector
        # remains visible and a coordinate-only click is not evidence of a
        # Tilemap operation.
        # Tileset now occupies the second vertical tab; Tilemap is the next
        # tab down at the observed native-DPI coordinate.
        Enter-AdvancedTool $editor.Handle 520
        $records.tilemap_tools_entry = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-tilemap-tools-entry.png")
        # The west tab bar is vertically laid out in the native surface;
        # Tiles is below the new Tileset tab on the current DPI layout.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 520)
        Start-Sleep -Milliseconds 500
        $records.tilemap_panel_entry = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-tilemap-panel-entry.png")
        # The tilemap inspector is a scrollable dock.  In the current
        # responsive layout the action row is below the palette and layer
        # controls; y=320 reaches the grid/tool controls and must not be used
        # as a substitute for the user-visible Novo button.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3180, 750)
        Start-Sleep -Milliseconds 500
        $records.tilemap_new = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-tilemap-new.png")
        # Scroll the same dock to the embedded TileMapCanvas.  The canvas is
        # below the rule editor and is not reachable while the dock is at its
        # initial top position.  Capture the visible canvas before painting so
        # the manifest can distinguish navigation from an actual edit.
        for ($scrollStep = 0; $scrollStep -lt 30; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.99, 0.75, -120)
            Start-Sleep -Milliseconds 70
        }
        Start-Sleep -Milliseconds 500
        $records.tilemap_canvas_visible = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-tilemap-canvas-visible.png")
        # Paint three adjacent cells in the now-visible native TileMapCanvas,
        # save the sidecar, then reopen it through the same shipped controls.
        # These are window offsets for the maximized 3866x2090 capture host.
        # The capture host is DPI-scaled; one logical 32px cell occupies
        # roughly 64 physical pixels in the Win32 coordinate space.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3200, 1435)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3264, 1435)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3328, 1435)
        Start-Sleep -Milliseconds 500
        $records.tilemap_painted = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-tilemap-painted.png")
        # After scrolling, the action row is visible near the top of the dock.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3180, 290)
        Start-Sleep -Milliseconds 700
        $records.tilemap_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-tilemap-saved.png")
        $records.tilemap_persistence = Read-NativeTilemapPersistence $projectPath
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3600, 228)
        Start-Sleep -Milliseconds 700
        $records.tilemap_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-tilemap-reopened.png")
    }
    if ($CaptureColliderFlow) {
        # Tileset is now a first-class tab between Formas and Tilemap.  The
        # collision tab therefore moved down one slot from the pre-Tileset
        # coordinate; keep this aligned with the shipped west-side tab bar.
        Enter-AdvancedTool $editor.Handle 660
        # Maximize first so the inspector has a stable native coordinate.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3420, 270)
        Start-Sleep -Milliseconds 500
        $records.collider_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-collider-created.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3140, 270)
        [System.Windows.Forms.SendKeys]::SendWait("{DOWN}")
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3420, 270)
        Start-Sleep -Milliseconds 500
        $records.collider_circle_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-collider-circle-created.png")
        # Save/Reopen are on the second action row of the collider panel.
        # Use the same physical window offsets as the tilemap flow instead
        # of relying on Qt tab order, which is not stable across DPI hosts.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3315, 320)
        Start-Sleep -Milliseconds 700
        $records.collider_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-collider-saved.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3125, 320)
        Start-Sleep -Milliseconds 700
        $records.collider_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-collider-reopened.png")
    }
    if ($CaptureNavMeshFlow) {
        # Tileset is now a first-class tab between Formas and Colisão.  Keep
        # Navigation explicit at its observed native-DPI position instead of
        # reusing the pre-Tileset coordinate that selected Colisão.
        Enter-AdvancedTool $editor.Handle 800
        $records.navmesh_entry = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-navmesh-entry.png")
        # The native panel places Região, Obstáculo, Bake, Salvar and Reabrir
        # on one action row near the lower half of the inspector.  Use the
        # observed native coordinates so the clicks reach real controls.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3080, 1095)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3260, 1095)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3430, 1095)
        Start-Sleep -Milliseconds 900
        $records.navmesh_baked = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-navmesh-baked.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3590, 1095)
        Start-Sleep -Milliseconds 700
        $records.navmesh_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-navmesh-saved.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3745, 1095)
        Start-Sleep -Milliseconds 700
        $records.navmesh_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-navmesh-reopened.png")
    }
    if ($CaptureEntityPrefabFlow) {
        # Tileset is now a first-class tab between Formas and Tilemap.  The
        # entities tab therefore moved down one slot from the pre-Tileset
        # coordinate; keep this aligned with the shipped west-side tab bar.
        Enter-AdvancedTool $editor.Handle 950
        # These controls are visible in the shipped panel: add one entity,
        # create a prefab from it, then instantiate that prefab.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3200, 752)
        Start-Sleep -Milliseconds 650
        $records.entity_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-entity-created.png")
        # Creating an entity selects it and intentionally returns the right
        # dock to the numeric inspector.  Re-enter Ferramentas > Entidades as
        # a user must do before continuing with prefab authoring.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3200, 1255)
        Start-Sleep -Milliseconds 500
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3600, 1255)
        Start-Sleep -Milliseconds 650
        $records.prefab_instantiated = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-prefab-instantiated.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        $records.prefab_state_visible = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-prefab-state-visible.png")
        for ($scrollStep = 0; $scrollStep -lt 18; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.99, 0.75, -120)
            Start-Sleep -Milliseconds 80
        }
        Start-Sleep -Milliseconds 500
        $records.instance_controls_visible = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-instance-controls-visible.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3200, 1415)
        Start-Sleep -Milliseconds 650
        $records.prefab_override = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-prefab-override.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        for ($scrollStep = 0; $scrollStep -lt 18; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.99, 0.75, -120)
            Start-Sleep -Milliseconds 80
        }
        Start-Sleep -Milliseconds 500
        $records.prefab_override_state = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-prefab-override-state.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 915)
        Start-Sleep -Milliseconds 650
        $records.prefab_updated = Save-Capture $editor.Handle (Join-Path $OutputDirectory "12-prefab-updated.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        for ($scrollStep = 0; $scrollStep -lt 18; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.99, 0.75, -120)
            Start-Sleep -Milliseconds 80
        }
        Start-Sleep -Milliseconds 500
        $records.prefab_updated_state = Save-Capture $editor.Handle (Join-Path $OutputDirectory "13-prefab-updated-state.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 1485)
        Start-Sleep -Milliseconds 650
        $records.prefab_detached = Save-Capture $editor.Handle (Join-Path $OutputDirectory "14-prefab-detached.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3290, 150)
        Start-Sleep -Milliseconds 450
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 2970, 950)
        Start-Sleep -Milliseconds 650
        for ($scrollStep = 0; $scrollStep -lt 18; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.99, 0.75, -120)
            Start-Sleep -Milliseconds 80
        }
        Start-Sleep -Milliseconds 500
        $records.prefab_detached_state = Save-Capture $editor.Handle (Join-Path $OutputDirectory "15-prefab-detached-state.png")
    }
    if ($CaptureRendererFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # The real shipped UI exposes preview through Ver >
        # Pré-visualização de Paralaxe. Open the menu, capture it, then use
        # keyboard navigation to activate the visible action.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 1360, 92)
        Start-Sleep -Milliseconds 400
        $records.renderer_view_menu = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-renderer-view-menu.png")
        [System.Windows.Forms.SendKeys]::SendWait("{DOWN 2}{ENTER}")
        Start-Sleep -Milliseconds 900
        $records.renderer_preview = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-renderer-preview.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 1360, 92)
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{DOWN 3}{ENTER}")
        Start-Sleep -Milliseconds 500
        $records.renderer_authoring = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-renderer-authoring.png")
    }
    if ($CaptureMaterialFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # Select the large receiver through the real canvas, as a user would
        # before editing its persisted material in the inspector.
        # The PrintWindow output is commonly previewed downscaled, while the
        # native surface is DPI-aware (3866x2090 on the capture host).  The
        # left receiver occupies the native rectangle around x=826..1484,
        # y=308..1234; click its blue center so the real user action reaches
        # the graphics item instead of the empty gutter between objects.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 1300, 780)
        Start-Sleep -Milliseconds 700
        $records.material_selection = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-material-selection.png")
        # Material is an explicit inspector category. Select it after the
        # canvas selection so the capture proves the user-visible context.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3440, 257)
        Start-Sleep -Milliseconds 700
        $records.material_authoring_selected = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-material-authoring-selected.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3450, 322)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.Clipboard]::SetText("#ff0000")
        [System.Windows.Forms.SendKeys]::SendWait("^v")
        [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
        Start-Sleep -Milliseconds 350
        $records.material_albedo_edited = Save-Capture $editor.Handle (Join-Path $OutputDirectory "11-material-albedo-edited.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 875)
        Start-Sleep -Milliseconds 700
        $records.material_applied = Save-Capture $editor.Handle (Join-Path $OutputDirectory "12-material-applied.png")
        # Persist the material through the real project controls, then reload
        # it so the final capture proves the user-visible round-trip.
        # The first toolbar action is Save Project/Save As; the direct
        # scenario save action is the third button at native x=557.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 557, 90)
        Start-Sleep -Milliseconds 800
        $records.material_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "13-material-saved.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 708, 90)
        Start-Sleep -Milliseconds 1000
        $records.material_reloaded = Save-Capture $editor.Handle (Join-Path $OutputDirectory "14-material-reloaded.png")
    }
    if ($CaptureParallaxFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # Select the layer in the real composition stack, then open the
        # explicit Camada category. This avoids treating an unselected,
        # scrolled inspector as parallax evidence.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 260, 390)
        Start-Sleep -Milliseconds 500
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3280, 257)
        Start-Sleep -Milliseconds 700
        $records.parallax_panel_entry = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-parallax-panel-entry.png")
        # Edit the visible native fields. Pasting the localized decimal keeps
        # the interaction equivalent to a normal user edit while avoiding
        # guesses about which half of a spin-arrow was hit on a DPI host.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3450, 394)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.Clipboard]::SetText("0,75")
        [System.Windows.Forms.SendKeys]::SendWait("^v")
        [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3450, 455)
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        [System.Windows.Forms.Clipboard]::SetText("0,75")
        [System.Windows.Forms.SendKeys]::SendWait("^v")
        [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3400, 1065)
        Start-Sleep -Milliseconds 700
        $records.parallax_applied = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-parallax-applied.png")
        # Ctrl+End is consumed by the focused child list on some Qt builds.
        # Clicking the visible scrollbar track is deterministic at the native
        # DPI-aware surface and follows the same interaction a user performs.
        for ($scrollStep = 0; $scrollStep -lt 100; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.992, 0.60, -120)
            Start-Sleep -Milliseconds 100
        }
        Start-Sleep -Milliseconds 700
        $records.parallax_controls_bottom = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-parallax-controls-bottom.png")
        for ($scrollStep = 0; $scrollStep -lt 20; $scrollStep++) {
            [NeoEngE03Capture]::ScrollWindowFraction($editor.Handle, 0.992, 0.60, 120)
            Start-Sleep -Milliseconds 100
        }
        Start-Sleep -Milliseconds 500
        $records.parallax_controls_pageup = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-parallax-controls-pageup.png")
    }
    $records.editor_title = $editor.Title
    $records.editor_window_rect_before_tilemap_flow = [NeoEngE03Capture]::RectText($editor.Handle)
    $records.window = "captured by PrintWindow from binary window handle"
    $records | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "manifest.json") -Encoding utf8
    $records | ConvertTo-Json -Depth 6
} finally {
    if ($process -and -not $process.HasExited) { $process.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (-not $process.HasExited) { $process.Kill() } }
}
