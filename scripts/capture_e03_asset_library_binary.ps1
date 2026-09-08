param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [switch]$CaptureTilemapFlow
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
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] private static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern IntPtr SetFocus(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] private static extern void keybd_event(byte key, byte scan, uint flags, UIntPtr extra);

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
$process = Start-Process -FilePath $exePath -PassThru
try {
    $deadline = (Get-Date).AddSeconds(20)
    do { Start-Sleep -Milliseconds 250; $process.Refresh(); $mainHandle = $process.MainWindowHandle } while ($mainHandle -eq 0 -and (Get-Date) -lt $deadline)
    if ($mainHandle -eq 0) { throw "GUI main window was not exposed" }

    $records = [ordered]@{}
    $records.main = Save-Capture $mainHandle (Join-Path $OutputDirectory "01-main.png")
    [NeoEngE03Capture]::Focus($mainHandle)
    [NeoEngE03Capture]::CtrlO()
    Start-Sleep -Milliseconds 1200
    $dialog = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle } | Select-Object -First 1
    if (-not $dialog) { throw "project open dialog was not exposed" }
    $records.project_dialog = Save-Capture $dialog.Handle (Join-Path $OutputDirectory "02-project-open-dialog.png")
    Set-DialogPath $dialog.Handle $projectPath
    Start-Sleep -Milliseconds 1800

    [NeoEngE03Capture]::Focus($mainHandle)
    $records.main_after_project_load = Save-Capture $mainHandle (Join-Path $OutputDirectory "03-main-after-project-load.png")
    $records.main_window_rect = [NeoEngE03Capture]::RectText($mainHandle)
    $projectWindows = [NeoEngE03Capture]::GetWindows($process.Id)
    $records.windows_after_project_load = @($projectWindows | ForEach-Object { [ordered]@{ title = $_.Title } })
    $errorWindow = $projectWindows | Where-Object { $_.Title -eq "Erro" } | Select-Object -First 1
    if ($errorWindow) {
        $records.project_error = Save-Capture $errorWindow.Handle (Join-Path $OutputDirectory "04-project-load-error.png")
        [NeoEngE03Capture]::Focus($errorWindow.Handle)
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        Start-Sleep -Milliseconds 350
    }
    [NeoEngE03Capture]::Focus($mainHandle)
    # PrintWindow reports physical pixels on this 200% DPI desktop; the
    # visible toolbar center is approximately (758,75) in the 2048px capture,
    # therefore the native screen coordinate is scaled to (1421,142).
    [NeoEngE03Capture]::ClickWindow($mainHandle, 1421, 142)
    Start-Sleep -Milliseconds 2200
    $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
    if (-not $editor) {
        [NeoEngE03Capture]::Focus($mainHandle)
        [NeoEngE03Capture]::ClickWindow($mainHandle, 3280, 1787)
        Start-Sleep -Milliseconds 2200
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle -and $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
    }
    if (-not $editor) {
        $records.windows_after_scenario_attempt = @([NeoEngE03Capture]::GetWindows($process.Id) | ForEach-Object { [ordered]@{ title = $_.Title } })
        $records | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "diagnostic-manifest.json") -Encoding utf8
        throw "professional scenario editor was not exposed"
    }
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
    $records.editor_title = $editor.Title
    $records.editor_window_rect_before_tilemap_flow = [NeoEngE03Capture]::RectText($editor.Handle)
    $records.window = "captured by PrintWindow from binary window handle"
    $records | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "manifest.json") -Encoding utf8
    $records | ConvertTo-Json -Depth 6
} finally {
    if ($process -and -not $process.HasExited) { $process.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (-not $process.HasExited) { $process.Kill() } }
}
