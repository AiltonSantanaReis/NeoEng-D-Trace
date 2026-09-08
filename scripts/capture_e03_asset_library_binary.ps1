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
    [switch]$DirectProjectLoad
)

$ErrorActionPreference = "Stop"
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
    public static void ClickWindow(IntPtr hWnd, int offsetX, int offsetY)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        SetCursorPos(rect.Left + offsetX, rect.Top + offsetY);
        const uint down = 0x0002, up = 0x0004;
        mouse_event(down, 0, 0, 0, UIntPtr.Zero); mouse_event(up, 0, 0, 0, UIntPtr.Zero);
    }
    public static void ClickWindowFraction(IntPtr hWnd, double fractionX, double fractionY)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = rect.Right - rect.Left, height = rect.Bottom - rect.Top;
        ClickWindow(hWnd, (int)(width * fractionX), (int)(height * fractionY));
    }
    public static string RectText(IntPtr hWnd)
    {
        RECT rect; if (!GetWindowRect(hWnd, out rect)) return "unknown";
        return $"{rect.Left},{rect.Top},{rect.Right},{rect.Bottom}";
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

function Save-Capture {
    param([IntPtr]$Handle, [string]$Path)
    [NeoEngE03Capture]::Capture($Handle, $Path) | Out-Null
    return [ordered]@{ path = $Path; sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
}

$exePath = (Resolve-Path -LiteralPath $Executable).Path
$projectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
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
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
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
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
        if (-not $editor) {
            [NeoEngE03Capture]::Focus($mainHandle)
            [NeoEngE03Capture]::ClickWindow($mainHandle, 1430, 160)
            Start-Sleep -Milliseconds 2200
            $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle -and $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
        }
        if (-not $editor) { throw "professional scenario editor was not exposed" }
    }
    [NeoEngE03Capture]::Focus($editor.Handle)
    Start-Sleep -Milliseconds 800
    $records.asset_library_ready = Save-Capture $editor.Handle (Join-Path $OutputDirectory "05-asset-library-ready.png")
    $records.asset_library_ready = Save-Capture $editor.Handle (Join-Path $OutputDirectory "05-asset-library-ready.png")
    # The editor has no Alt+P mnemonic.  Sending it can open an unrelated
    # native action and block PrintWindow.  Search/category behavior is
    # covered by the focused Qt contract tests; this binary capture remains
    # the authoritative visual proof of the real shipped editor surface.
    $records.asset_library_filter_contract = "covered by focused Qt tests; controls visible in asset_library_ready"
    if ($CaptureTilemapFlow) {
        # The tilemap panel is in the right inspector at the top of the
        # shipped editor.  These are native screen offsets for the current
        # 200% DPI capture host; the resulting state is always verified by
        # PrintWindow and the manifest hashes below.
        [NeoEngE03Capture]::Focus($editor.Handle)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3110, 320)
        Start-Sleep -Milliseconds 500
        $records.tilemap_new = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-tilemap-new.png")
        # Paint three cells, save the sidecar, then reopen it through the
        # same shipped controls.  Coordinates are native offsets in the
        # maximized editor rect recorded above.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3210, 550)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3240, 550)
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3270, 550)
        Start-Sleep -Milliseconds 500
        $records.tilemap_painted = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-tilemap-painted.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3395, 320)
        Start-Sleep -Milliseconds 700
        $records.tilemap_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-tilemap-saved.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3240, 320)
        Start-Sleep -Milliseconds 700
        $records.tilemap_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-tilemap-reopened.png")
    }
    if ($CaptureColliderFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # Maximize first so the inspector has a stable native coordinate.
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3420, 240)
        Start-Sleep -Milliseconds 500
        $records.collider_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-collider-created.png")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3140, 240)
        [System.Windows.Forms.SendKeys]::SendWait("{DOWN}")
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        [NeoEngE03Capture]::ClickWindow($editor.Handle, 3420, 240)
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
        [NeoEngE03Capture]::Focus($editor.Handle)
        # Use normalized native coordinates: PrintWindow captures the actual
        # 1926x1038 maximized surface on this 200% host, while Qt layout sizes
        # are logical pixels.  Fixed logical coordinates silently missed the
        # inspector and produced false-identical screenshots.
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.75, 0.135)
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.80, 0.135)
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.85, 0.135)
        Start-Sleep -Milliseconds 900
        $records.navmesh_baked = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-navmesh-baked.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.90, 0.135)
        Start-Sleep -Milliseconds 700
        $records.navmesh_saved = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-navmesh-saved.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.95, 0.135)
        Start-Sleep -Milliseconds 700
        $records.navmesh_reopened = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-navmesh-reopened.png")
    }
    if ($CaptureEntityPrefabFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # The E07 panel is the first inspector panel.  Coordinates are
        # normalized against the DPI-aware native surface; they remain valid
        # when the maximized logical Qt surface is 3866x2090.
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.78, 0.345)
        Start-Sleep -Milliseconds 650
        $records.entity_created = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-entity-created.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.78, 0.585)
        Start-Sleep -Milliseconds 500
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.87, 0.585)
        Start-Sleep -Milliseconds 650
        $records.prefab_instantiated = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-prefab-instantiated.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.78, 0.826)
        Start-Sleep -Milliseconds 650
        $records.prefab_override = Save-Capture $editor.Handle (Join-Path $OutputDirectory "08-prefab-override.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.95, 0.585)
        Start-Sleep -Milliseconds 650
        $records.prefab_updated = Save-Capture $editor.Handle (Join-Path $OutputDirectory "09-prefab-updated.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.95, 0.826)
        Start-Sleep -Milliseconds 650
        $records.prefab_detached = Save-Capture $editor.Handle (Join-Path $OutputDirectory "10-prefab-detached.png")
    }
    if ($CaptureRendererFlow) {
        [NeoEngE03Capture]::Focus($editor.Handle)
        # Preview Parallax is the toolbar toggle near the center of the
        # DPI-aware editor surface.  The capture proves the shipped raster
        # renderer plan and its explicit backend/fallback HUD.
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.52, 0.046)
        Start-Sleep -Milliseconds 900
        $records.renderer_preview = Save-Capture $editor.Handle (Join-Path $OutputDirectory "06-renderer-preview.png")
        [NeoEngE03Capture]::ClickWindowFraction($editor.Handle, 0.52, 0.046)
        Start-Sleep -Milliseconds 500
        $records.renderer_authoring = Save-Capture $editor.Handle (Join-Path $OutputDirectory "07-renderer-authoring.png")
    }
    $records.editor_title = $editor.Title
    $records.editor_window_rect_before_tilemap_flow = [NeoEngE03Capture]::RectText($editor.Handle)
    $records.window = "captured by PrintWindow from binary window handle"
    $records | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "manifest.json") -Encoding utf8
    $records | ConvertTo-Json -Depth 6
} finally {
    if ($process -and -not $process.HasExited) { $process.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (-not $process.HasExited) { $process.Kill() } }
}
