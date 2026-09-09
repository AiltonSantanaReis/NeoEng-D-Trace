param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [switch]$CaptureSaveDialog,
    [switch]$CapturePrimitiveFlow,
    [switch]$CaptureAuthoringOps,
    [switch]$CaptureSaveReopen,
    [switch]$CapturePointEditing,
    [switch]$CaptureComposition,
    [string]$ProjectPath,
    [int]$InvalidTargetX = 958,
    [int]$InvalidTargetY = 372
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
    private delegate bool EnumChildWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr extra);
    [DllImport("user32.dll")] private static extern bool EnumChildWindows(IntPtr parent, EnumChildWindowsProc callback, IntPtr extra);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int length);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr hWnd, StringBuilder text, int length);
    [DllImport("user32.dll", CharSet = CharSet.Unicode, EntryPoint = "SendMessageW")] private static extern IntPtr SendMessageText(IntPtr hWnd, uint message, IntPtr wParam, string lParam);
    [DllImport("user32.dll", EntryPoint = "SendMessageW")] private static extern IntPtr SendMessageNoText(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] private static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int command);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("kernel32.dll")] private static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] private static extern bool AttachThreadInput(uint sourceThreadId, uint targetThreadId, bool attach);
    [DllImport("user32.dll")] private static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern IntPtr SetFocus(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
    [DllImport("user32.dll")] private static extern void keybd_event(byte key, byte scan, uint flags, UIntPtr extra);

    private const uint WM_SETTEXT = 0x000C;
    private const uint BM_CLICK = 0x00F5;

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

    public static bool SetNativeDialogPath(IntPtr dialog, string path)
    {
        IntPtr edit = IntPtr.Zero;
        IntPtr openButton = IntPtr.Zero;
        EnumChildWindows(dialog, (hWnd, _) =>
        {
            var className = new StringBuilder(128);
            GetClassName(hWnd, className, className.Capacity);
            var title = new StringBuilder(256);
            GetWindowText(hWnd, title, title.Capacity);
            if (className.ToString().Equals("Edit", StringComparison.OrdinalIgnoreCase) && edit == IntPtr.Zero)
                edit = hWnd;
            if (className.ToString().Equals("Button", StringComparison.OrdinalIgnoreCase) &&
                (title.ToString().Replace("&", "").Equals("Abrir", StringComparison.OrdinalIgnoreCase) ||
                 title.ToString().Replace("&", "").Equals("Open", StringComparison.OrdinalIgnoreCase)))
                openButton = hWnd;
            return true;
        }, IntPtr.Zero);
        if (edit == IntPtr.Zero || openButton == IntPtr.Zero) return false;
        SendMessageText(edit, WM_SETTEXT, IntPtr.Zero, path);
        SendMessageNoText(openButton, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
        return true;
    }

    public static string DescribeNativeDialog(IntPtr dialog)
    {
        var items = new System.Collections.Generic.List<string>();
        EnumChildWindows(dialog, (hWnd, _) =>
        {
            var className = new StringBuilder(128);
            GetClassName(hWnd, className, className.Capacity);
            var title = new StringBuilder(256);
            GetWindowText(hWnd, title, title.Capacity);
            items.Add(className + "|" + title);
            return true;
        }, IntPtr.Zero);
        return string.Join("; ", items);
    }

    public static bool Activate(IntPtr hWnd)
    {
        return ShowWindow(hWnd, 3) && SetForegroundWindow(hWnd);
    }

    public static bool FocusWindow(IntPtr hWnd)
    {
        IntPtr foreground = GetForegroundWindow();
        uint foregroundProcess;
        uint foregroundThread = GetWindowThreadProcessId(foreground, out foregroundProcess);
        uint targetProcess;
        uint targetThread = GetWindowThreadProcessId(hWnd, out targetProcess);
        uint currentThread = GetCurrentThreadId();
        bool attachedForeground = foregroundThread != 0 && foregroundThread != currentThread &&
            AttachThreadInput(currentThread, foregroundThread, true);
        bool attachedTarget = targetThread != 0 && targetThread != currentThread &&
            AttachThreadInput(currentThread, targetThread, true);
        try
        {
            BringWindowToTop(hWnd);
            SetForegroundWindow(hWnd);
            SetFocus(hWnd);
            return true;
        }
        finally
        {
            if (attachedTarget) AttachThreadInput(currentThread, targetThread, false);
            if (attachedForeground) AttachThreadInput(currentThread, foregroundThread, false);
        }
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

    public static void SendCtrlShiftS()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x10, 0, 0, UIntPtr.Zero);
        keybd_event(0x53, 0, 0, UIntPtr.Zero);
        keybd_event(0x53, 0, up, UIntPtr.Zero);
        keybd_event(0x10, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlShift(byte key)
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x10, 0, 0, UIntPtr.Zero);
        keybd_event(key, 0, 0, UIntPtr.Zero);
        keybd_event(key, 0, up, UIntPtr.Zero);
        keybd_event(0x10, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlD()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x44, 0, 0, UIntPtr.Zero);
        keybd_event(0x44, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlO()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x4F, 0, 0, UIntPtr.Zero);
        keybd_event(0x4F, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendDelete()
    {
        const uint up = 0x0002;
        keybd_event(0x2E, 0, 0, UIntPtr.Zero);
        keybd_event(0x2E, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlShiftDelete()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x10, 0, 0, UIntPtr.Zero);
        keybd_event(0x2E, 0, 0, UIntPtr.Zero);
        keybd_event(0x2E, 0, up, UIntPtr.Zero);
        keybd_event(0x10, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlAlt(byte key)
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x12, 0, 0, UIntPtr.Zero);
        keybd_event(key, 0, 0, UIntPtr.Zero);
        keybd_event(key, 0, up, UIntPtr.Zero);
        keybd_event(0x12, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlAltShiftE()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x12, 0, 0, UIntPtr.Zero);
        keybd_event(0x10, 0, 0, UIntPtr.Zero);
        keybd_event(0x45, 0, 0, UIntPtr.Zero);
        keybd_event(0x45, 0, up, UIntPtr.Zero);
        keybd_event(0x10, 0, up, UIntPtr.Zero);
        keybd_event(0x12, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void SendEscape()
    {
        const uint up = 0x0002;
        keybd_event(0x1B, 0, 0, UIntPtr.Zero);
        keybd_event(0x1B, 0, up, UIntPtr.Zero);
    }

    public static void SendCtrlZ()
    {
        const uint up = 0x0002;
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        keybd_event(0x5A, 0, 0, UIntPtr.Zero);
        keybd_event(0x5A, 0, up, UIntPtr.Zero);
        keybd_event(0x11, 0, up, UIntPtr.Zero);
    }

    public static void ClickScreen(int x, int y)
    {
        SetCursorPos(x, y);
        mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
        mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
    }

    public static void ClickWindow(IntPtr hWnd, int offsetX, int offsetY)
    {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        ClickScreen(rect.Left + offsetX, rect.Top + offsetY);
    }

    public static void BeginDragWindow(IntPtr hWnd, int startX, int startY)
    {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        SetCursorPos(rect.Left + startX, rect.Top + startY);
        mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
    }

    public static void MoveCursorWindow(IntPtr hWnd, int offsetX, int offsetY)
    {
        RECT rect;
        if (!GetWindowRect(hWnd, out rect)) throw new InvalidOperationException("GetWindowRect failed");
        SetCursorPos(rect.Left + offsetX, rect.Top + offsetY);
        mouse_event(0x0001, 0, 0, 0, UIntPtr.Zero);
    }

    public static void EndDrag()
    {
        mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
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

function Set-DialogPath {
    param(
        [IntPtr]$Handle,
        [string]$Path
    )
    [NeoEngIndependentSceneCapture]::FocusWindow($Handle) | Out-Null
    Start-Sleep -Milliseconds 150
    if ([NeoEngIndependentSceneCapture]::SetNativeDialogPath($Handle, $Path)) {
        Start-Sleep -Milliseconds 400
        return
    }
    Write-Host ("native dialog controls: " + [NeoEngIndependentSceneCapture]::DescribeNativeDialog($Handle))
    [System.Windows.Forms.Clipboard]::SetText($Path)
    [System.Windows.Forms.SendKeys]::SendWait("%n")
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait("^l")
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds 250
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
}

$exePath = (Resolve-Path -LiteralPath $Executable).Path
# Windows PowerShell 5 does not expose System.IO.Path.GetRelativePath. Keep
# the resolved executable path as the provenance value instead of failing
# before the real binary is launched.
$relativeExecutable = $exePath.Replace('\', '/')
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
    [NeoEngIndependentSceneCapture]::FocusWindow($mainHandle) | Out-Null
    Start-Sleep -Milliseconds 300
    [NeoEngIndependentSceneCapture]::SendCtrlAltN()
    Start-Sleep -Milliseconds 1500

    $windows = [NeoEngIndependentSceneCapture]::GetWindows($process.Id)
    $child = $windows | Where-Object { $_.Title -match "Independent Scene|Cen.rio Independente|Novo Cen.rio" } | Select-Object -First 1
    $childRecord = $null
    $primitiveFlowRecord = $null
    $requestedFlow = $CapturePrimitiveFlow -or $CaptureAuthoringOps -or $CaptureSaveReopen -or $CapturePointEditing -or $CaptureComposition
    if ($requestedFlow -and -not $child) {
        $observed = ($windows | ForEach-Object { $_.Title }) -join "; "
        throw "independent scene window was not exposed after Ctrl+Alt+N; observed windows: $observed"
    }
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

    if ($CapturePrimitiveFlow -and $child) {
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlShift(0x52)
        Start-Sleep -Milliseconds 250
        [NeoEngIndependentSceneCapture]::SendCtrlShift(0x45)
        Start-Sleep -Milliseconds 250
        [NeoEngIndependentSceneCapture]::SendCtrlShift(0x50)
        Start-Sleep -Milliseconds 700
        $primitivePath = Join-Path $OutputDirectory "03-independent-scene-primitives.png"
        $primitiveSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $primitivePath)
        $primitiveFlowRecord = [ordered]@{
            window = $primitiveSize
            path = $primitivePath
            sha256 = (Get-FileHash -LiteralPath $primitivePath -Algorithm SHA256).Hash
            shortcuts = @("Ctrl+Shift+R", "Ctrl+Shift+E", "Ctrl+Shift+P")
        }
    }

    $authoringOpsRecord = $null
    if ($CaptureAuthoringOps -and $child) {
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        # The PT-BR object X editor is visible in the standard 1986x1431 window.
        [NeoEngIndependentSceneCapture]::ClickWindow($child.Handle, 420, 1285)
        Start-Sleep -Milliseconds 150
        [System.Windows.Forms.SendKeys]::SendWait("^a42{ENTER}")
        Start-Sleep -Milliseconds 500
        $transformPath = Join-Path $OutputDirectory "04-independent-scene-after-transform.png"
        $transformSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $transformPath)

        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlD()
        Start-Sleep -Milliseconds 500
        $duplicatePath = Join-Path $OutputDirectory "05-independent-scene-after-duplicate.png"
        $duplicateSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $duplicatePath)

        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlShiftDelete()
        Start-Sleep -Milliseconds 500
        $removePath = Join-Path $OutputDirectory "06-independent-scene-after-remove.png"
        $removeSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $removePath)
        $authoringOpsRecord = [ordered]@{
            transform = [ordered]@{
                window = $transformSize
                path = $transformPath
                sha256 = (Get-FileHash -LiteralPath $transformPath -Algorithm SHA256).Hash
                input = "Object X=42"
            }
            duplicate = [ordered]@{
                window = $duplicateSize
                path = $duplicatePath
                sha256 = (Get-FileHash -LiteralPath $duplicatePath -Algorithm SHA256).Hash
                input = "Ctrl+D"
            }
            remove = [ordered]@{
                window = $removeSize
                path = $removePath
                sha256 = (Get-FileHash -LiteralPath $removePath -Algorithm SHA256).Hash
                input = "Ctrl+Shift+Delete"
            }
        }
    }

    $pointEditingRecord = $null
    if ($CapturePointEditing -and $child) {
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        # The primitive-creation flow leaves the polygon selected deterministically.
        [NeoEngIndependentSceneCapture]::SendCtrlAlt(0x45)
        Start-Sleep -Milliseconds 500
        $editModePath = Join-Path $OutputDirectory "04-independent-scene-point-edit-mode.png"
        $editModeSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $editModePath)

        # Move the upper-right handle onto the lower handle while pressed.
        # This produces a duplicate-point preview without committing the document.
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::BeginDragWindow($child.Handle, 991, 341)
        Start-Sleep -Milliseconds 200
        [NeoEngIndependentSceneCapture]::MoveCursorWindow($child.Handle, $InvalidTargetX, $InvalidTargetY)
        Start-Sleep -Milliseconds 400
        $invalidPath = Join-Path $OutputDirectory "05-independent-scene-point-preview-invalid.png"
        $invalidSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $invalidPath)
        [NeoEngIndependentSceneCapture]::EndDrag()
        Start-Sleep -Milliseconds 250
        [NeoEngIndependentSceneCapture]::SendEscape()
        Start-Sleep -Milliseconds 500
        $cancelPath = Join-Path $OutputDirectory "06-independent-scene-point-edit-cancelled.png"
        $cancelSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $cancelPath)

        [NeoEngIndependentSceneCapture]::SendCtrlAlt(0x45)
        Start-Sleep -Milliseconds 400
        [NeoEngIndependentSceneCapture]::BeginDragWindow($child.Handle, 991, 341)
        Start-Sleep -Milliseconds 200
        [NeoEngIndependentSceneCapture]::MoveCursorWindow($child.Handle, 1015, 358)
        [NeoEngIndependentSceneCapture]::EndDrag()
        Start-Sleep -Milliseconds 500
        $finalPath = Join-Path $OutputDirectory "07-independent-scene-point-edit-finalized.png"
        $finalSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $finalPath)
        $pointEditingRecord = [ordered]@{
            edit_mode = [ordered]@{
                window = $editModeSize
                path = $editModePath
                sha256 = (Get-FileHash -LiteralPath $editModePath -Algorithm SHA256).Hash
            }
            invalid_preview = [ordered]@{
                window = $invalidSize
                path = $invalidPath
                sha256 = (Get-FileHash -LiteralPath $invalidPath -Algorithm SHA256).Hash
            }
            cancelled = [ordered]@{
                window = $cancelSize
                path = $cancelPath
                sha256 = (Get-FileHash -LiteralPath $cancelPath -Algorithm SHA256).Hash
            }
            finalized = [ordered]@{
                window = $finalSize
                path = $finalPath
                sha256 = (Get-FileHash -LiteralPath $finalPath -Algorithm SHA256).Hash
            }
            inputs = @("select polygon row", "Ctrl+Alt+E", "native drag", "Escape", "native drag")
        }
    }

    $saveReopenRecord = $null
    if ($CaptureSaveReopen -and $child) {
        $scenePath = (Join-Path (Resolve-Path -LiteralPath $OutputDirectory).Path "e02-b-flow.ndtscene")
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlShiftS()
        Start-Sleep -Milliseconds 1000
        $saveDialogWindows = [NeoEngIndependentSceneCapture]::GetWindows($process.Id)
        $saveDialog = $saveDialogWindows |
            Where-Object { $_.Title -and $_.Title -ne $child.Title -and $_.Title -ne "NeoEng-D-Trace" } |
            Select-Object -First 1
        $saveDialogRecord = $null
        if ($saveDialog) {
            $saveDialogPath = Join-Path $OutputDirectory "07-save-dialog.png"
            $saveDialogSize = [NeoEngIndependentSceneCapture]::Capture($saveDialog.Handle, $saveDialogPath)
            $saveDialogRecord = [ordered]@{
                title = $saveDialog.Title
                window = $saveDialogSize
                path = $saveDialogPath
                sha256 = (Get-FileHash -LiteralPath $saveDialogPath -Algorithm SHA256).Hash
            }
            Set-DialogPath -Handle $saveDialog.Handle -Path $scenePath
            Start-Sleep -Milliseconds 1200
        }
        if (-not (Test-Path -LiteralPath $scenePath)) {
            throw "Native save did not create the expected scene file: $scenePath"
        }
        $savedPath = Join-Path $OutputDirectory "08-independent-scene-after-save.png"
        $savedSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $savedPath)

        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlO()
        Start-Sleep -Milliseconds 1000
        $openDialogWindows = [NeoEngIndependentSceneCapture]::GetWindows($process.Id)
        $openDialog = $openDialogWindows |
            Where-Object { $_.Title -and $_.Title -ne $child.Title -and $_.Title -ne "NeoEng-D-Trace" } |
            Select-Object -First 1
        $openDialogRecord = $null
        if ($openDialog) {
            $openDialogPath = Join-Path $OutputDirectory "09-open-dialog.png"
            $openDialogSize = [NeoEngIndependentSceneCapture]::Capture($openDialog.Handle, $openDialogPath)
            $openDialogRecord = [ordered]@{
                title = $openDialog.Title
                window = $openDialogSize
                path = $openDialogPath
                sha256 = (Get-FileHash -LiteralPath $openDialogPath -Algorithm SHA256).Hash
            }
            Set-DialogPath -Handle $openDialog.Handle -Path $scenePath
            Start-Sleep -Milliseconds 1500
        }
        $reopenPath = Join-Path $OutputDirectory "10-independent-scene-after-reopen.png"
        $reopenSize = [NeoEngIndependentSceneCapture]::Capture($child.Handle, $reopenPath)
        $saveReopenRecord = [ordered]@{
            scene_path = $scenePath
            scene_sha256 = (Get-FileHash -LiteralPath $scenePath -Algorithm SHA256).Hash
            save_dialog = $saveDialogRecord
            after_save = [ordered]@{
                window = $savedSize
                path = $savedPath
                sha256 = (Get-FileHash -LiteralPath $savedPath -Algorithm SHA256).Hash
            }
            open_dialog = $openDialogRecord
            after_reopen = [ordered]@{
                window = $reopenSize
                path = $reopenPath
                sha256 = (Get-FileHash -LiteralPath $reopenPath -Algorithm SHA256).Hash
            }
        }
    }

    $saveDialogRecord = $null
    if ($CaptureSaveDialog -and $child) {
        [NeoEngIndependentSceneCapture]::FocusWindow($child.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::ClickWindow($child.Handle, 260, 80)
        Start-Sleep -Milliseconds 300
        [NeoEngIndependentSceneCapture]::SendCtrlShiftS()
        Start-Sleep -Milliseconds 1200
        $dialogWindows = [NeoEngIndependentSceneCapture]::GetWindows($process.Id)
        $dialog = $dialogWindows |
            Where-Object { $_.Title -and $_.Title -notmatch "Independent Scene|Cen.rio Independente|^NeoEng-D-Trace$" } |
            Select-Object -First 1
        if ($dialog) {
            $dialogPath = Join-Path $OutputDirectory "03-save-dialog.png"
            $dialogSize = [NeoEngIndependentSceneCapture]::Capture($dialog.Handle, $dialogPath)
            $saveDialogRecord = [ordered]@{
                title = $dialog.Title
                window = $dialogSize
                path = $dialogPath
                sha256 = (Get-FileHash -LiteralPath $dialogPath -Algorithm SHA256).Hash
            }
        }
    }

    $compositionRecord = $null
    if ($CaptureComposition) {
        if (-not $ProjectPath) { throw "-ProjectPath is required with -CaptureComposition" }
        $projectPathResolved = (Resolve-Path -LiteralPath $ProjectPath).Path
        [NeoEngIndependentSceneCapture]::FocusWindow($mainHandle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlO()
        Start-Sleep -Milliseconds 1000
        $projectDialog = [NeoEngIndependentSceneCapture]::GetWindows($process.Id) |
            Where-Object {
                $_.Title -and
                $_.Title -notmatch "NeoEng-D-Trace|Independent Scene|Cen.rio Independente|Scenario Editor|Editor de Cen.rio"
            } |
            Select-Object -First 1
        if (-not $projectDialog) { throw "project open dialog was not exposed" }
        [NeoEngIndependentSceneCapture]::Capture(
            $projectDialog.Handle,
            (Join-Path $OutputDirectory "composition-00-project-dialog-before.png")
        ) | Out-Null
        Set-DialogPath -Handle $projectDialog.Handle -Path $projectPathResolved
        Start-Sleep -Milliseconds 800
        $projectDialogAfter = [NeoEngIndependentSceneCapture]::GetWindows($process.Id) |
            Where-Object { $_.Title -eq $projectDialog.Title } |
            Select-Object -First 1
        if ($projectDialogAfter) {
            [NeoEngIndependentSceneCapture]::Capture(
                $projectDialogAfter.Handle,
                (Join-Path $OutputDirectory "composition-00-project-dialog-after.png")
            ) | Out-Null
        }
        Start-Sleep -Milliseconds 700

        [NeoEngIndependentSceneCapture]::FocusWindow($mainHandle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlAlt(0x53)
        Start-Sleep -Milliseconds 1800
        $scenarioWindow = [NeoEngIndependentSceneCapture]::GetWindows($process.Id) |
            Where-Object { $_.Title -match "Scenario Editor|Editor de Cen.rio" } |
            Select-Object -First 1
        if (-not $scenarioWindow) {
            $observed = ([NeoEngIndependentSceneCapture]::GetWindows($process.Id) | ForEach-Object { $_.Title }) -join "; "
            throw "scenario editor window was not exposed; observed windows: $observed"
        }
        $beforePath = Join-Path $OutputDirectory "composition-01-scenario-editor.png"
        $beforeSize = [NeoEngIndependentSceneCapture]::Capture($scenarioWindow.Handle, $beforePath)
        [NeoEngIndependentSceneCapture]::FocusWindow($scenarioWindow.Handle) | Out-Null
        [NeoEngIndependentSceneCapture]::SendCtrlAltShiftE()
        Start-Sleep -Milliseconds 1800
        $afterPath = Join-Path $OutputDirectory "composition-02-exported.png"
        $afterSize = [NeoEngIndependentSceneCapture]::Capture($scenarioWindow.Handle, $afterPath)
        $projectRoot = Split-Path -Parent $projectPathResolved
        $packagePath = Get-ChildItem -LiteralPath (Join-Path $projectRoot "exports") -Directory |
            Where-Object { $_.Name -match '^composition-e11(?:-r\d+)?$' } |
            Sort-Object LastWriteTimeUtc -Descending |
            Select-Object -First 1 -ExpandProperty FullName
        if (-not $packagePath) { throw "native composition export did not create a package directory" }
        $manifestPath = Join-Path $packagePath "composition.json"
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
            throw "native composition export did not create manifest: $manifestPath"
        }
        $compositionRecord = [ordered]@{
            project = $projectPathResolved
            title = $scenarioWindow.Title
            package = $packagePath
            manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
            before = [ordered]@{
                window = $beforeSize
                path = $beforePath
                sha256 = (Get-FileHash -LiteralPath $beforePath -Algorithm SHA256).Hash
            }
            after_export = [ordered]@{
                window = $afterSize
                path = $afterPath
                sha256 = (Get-FileHash -LiteralPath $afterPath -Algorithm SHA256).Hash
            }
            inputs = @("Ctrl+O", "open project fixture", "Ctrl+Alt+S", "Ctrl+Alt+Shift+E")
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
        primitive_flow = $primitiveFlowRecord
        authoring_ops = $authoringOpsRecord
        point_editing = $pointEditingRecord
        save_reopen = $saveReopenRecord
        save_dialog = $saveDialogRecord
        composition = $compositionRecord
        observed_windows = @($windows | ForEach-Object { [ordered]@{ title = $_.Title } })
    } | ConvertTo-Json -Depth 6
}
finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force }
}
