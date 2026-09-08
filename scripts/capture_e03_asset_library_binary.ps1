param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
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
    [System.Windows.Forms.SendKeys]::SendWait("%s")
    Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds 2200
    $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
    if (-not $editor) {
        [NeoEngE03Capture]::Focus($mainHandle)
        [System.Windows.Forms.SendKeys]::SendWait("%c")
        Start-Sleep -Milliseconds 250
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        Start-Sleep -Milliseconds 2200
        $editor = [NeoEngE03Capture]::GetWindows($process.Id) | Where-Object { $_.Handle -ne $mainHandle -and $_.Title -match "Scenario|Cen.rio" } | Select-Object -First 1
    }
    if (-not $editor) { throw "professional scenario editor was not exposed" }
    $records.asset_library_ready = Save-Capture $editor.Handle (Join-Path $OutputDirectory "03-asset-library-ready.png")
    [NeoEngE03Capture]::Focus($editor.Handle)
    [System.Windows.Forms.SendKeys]::SendWait("%p")
    Start-Sleep -Milliseconds 500
    $records.asset_library_filtered = Save-Capture $editor.Handle (Join-Path $OutputDirectory "04-asset-library-filtered.png")
    $records.editor_title = $editor.Title
    $records.window = "captured by PrintWindow from binary window handle"
    $records | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "manifest.json") -Encoding utf8
    $records | ConvertTo-Json -Depth 6
} finally {
    if ($process -and -not $process.HasExited) { $process.CloseMainWindow() | Out-Null; Start-Sleep -Milliseconds 500; if (-not $process.HasExited) { $process.Kill() } }
}
