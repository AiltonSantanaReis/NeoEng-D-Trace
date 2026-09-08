param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
$drawingAssembly = [System.Drawing.Bitmap].Assembly.Location
$drawingPrimitivesAssembly = [System.Drawing.Size].Assembly.Location
$windowsAssemblies = @(Get-ChildItem -LiteralPath $PSHOME -Filter "System.Private.Windows*.dll" | ForEach-Object { $_.FullName })
$references = @($drawingAssembly, $drawingPrimitivesAssembly) + $windowsAssemblies
Add-Type -TypeDefinition @"
using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;

public static class NeoEngIndependentSceneCapture
{
    [StructLayout(LayoutKind.Sequential)]
    private struct RECT { public int Left; public int Top; public int Right; public int Bottom; }

    public sealed class WindowInfo
    {
        public IntPtr Handle;
        public string Title;
    }

    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr extra);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int length);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] private static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern void keybd_event(byte key, byte scan, uint flags, UIntPtr extra);

    public static WindowInfo[] GetWindows(int pid)
    {
        var result = new WindowInfo[256];
        var count = 0;
        EnumWindows((hWnd, _) =>
        {
            uint ownerPid;
            GetWindowThreadProcessId(hWnd, out ownerPid);
            if (ownerPid != pid || !IsWindowVisible(hWnd)) return true;
            var text = new StringBuilder(512);
            GetWindowText(hWnd, text, text.Capacity);
            if (count < result.Length)
                result[count++] = new WindowInfo { Handle = hWnd, Title = text.ToString() };
            return true;
        }, IntPtr.Zero);
        var final = new WindowInfo[count];
        Array.Copy(result, final, count);
        return final;
    }

    public static bool Activate(IntPtr hWnd)
    {
        return ShowWindow(hWnd, 3) && SetForegroundWindow(hWnd);
    }

    public static void SendCtrlAltN()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x12, 0, 0, UIntPtr.Zero);
        keybd_event(0x4E, 0, 0, UIntPtr.Zero);
        keybd_event(0x4E, 0, up, UIntPtr.Zero);
        keybd_event(0x12, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static string Capture(IntPtr hWnd, string path)
    {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        if (width <= 0 || height <= 0) throw new InvalidOperationException("Window has invalid dimensions");
        using (var bitmap = new Bitmap(width, height))
        using (var graphics = Graphics.FromImage(bitmap))
        {
            IntPtr hdc = graphics.GetHdc();
            try
            {
                if (!PrintWindow(hWnd, hdc, 2)) throw new InvalidOperationException("PrintWindow failed");
            }
            finally { graphics.ReleaseHdc(hdc); }
            bitmap.Save(path);
        }
        return width + "x" + height;
    }
}
"@ -ReferencedAssemblies $references

$exePath = (Resolve-Path -LiteralPath $Executable).Path
$relativeExecutable = [IO.Path]::GetRelativePath((Get-Location).Path, $exePath).Replace('\', '/')
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$process = Start-Process -FilePath $exePath -PassThru
try {
    $deadline = (Get-Date).AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $process.Refresh()
        $mainHandle = $process.MainWindowHandle
    } while ($mainHandle -eq 0 -and (Get-Date) -lt $deadline)
    if ($mainHandle -eq 0) { throw "GUI main window was not exposed" }

    $mainPath = Join-Path $OutputDirectory "01-main-before-independent.png"
    $mainSize = [NeoEngIndependentSceneCapture]::Capture($mainHandle, $mainPath)
    [NeoEngIndependentSceneCapture]::Activate($mainHandle) | Out-Null
    Start-Sleep -Milliseconds 300
    [NeoEngIndependentSceneCapture]::SendCtrlAltN()
    Start-Sleep -Milliseconds 1500

    $windows = [NeoEngIndependentSceneCapture]::GetWindows($process.Id)
    $child = $windows | Where-Object { $_.Title -match "Independent Scene|Cen.rio Independente|Novo Cen.rio" } | Select-Object -First 1
    $childRecord = $null
    if ($child) {
        $childPath = Join-Path $OutputDirectory "02-independent-scene-after-shortcut.png"
        $childSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $childPath)
        $childRecord = [ordered]@{
            title = $child.Title
            window = $childSize
            path = $childPath
            sha256 = (Get-FileHash -LiteralPath $childPath -Algorithm SHA256).Hash
        }
    }

    [ordered]@{
        executable = $relativeExecutable
        pid = $process.Id
        main = [ordered]@{
            window = $mainSize
            path = $mainPath
            sha256 = (Get-FileHash -LiteralPath $mainPath -Algorithm SHA256).Hash
        }
        independent_scene = $childRecord
        observed_windows = @($windows | ForEach-Object { [ordered]@{ title = $_.Title } })
    } | ConvertTo-Json -Depth 6
}
finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force }
}
