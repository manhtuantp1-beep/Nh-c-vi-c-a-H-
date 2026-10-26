[CmdletBinding()]
param()

# CI-only display preparation. ChangeDisplaySettings uses flags=0: apply to
# this ephemeral session without writing the display mode to the registry.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-CaptureNotice {
    param([string]$Message)
    $Escaped = $Message.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
    Write-Host "::notice title=UI capture display::$Escaped"
}

function Write-CaptureError {
    param([string]$Message)
    $Escaped = $Message.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
    Write-Host "::error title=UI capture display::$Escaped"
}

try {
    if ($env:OS -ne 'Windows_NT') { throw 'Display preparation requires the Windows CI runner.' }
    if (-not ('NhacViecCaptureDisplay' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class NhacViecCaptureDisplay
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct Mode
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        public ushort SpecVersion, DriverVersion, Size, DriverExtra;
        public uint Fields;
        public int PositionX, PositionY;
        public uint DisplayOrientation, DisplayFixedOutput;
        public short Color, Duplex, YResolution, TTOption, Collate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FormName;
        public ushort LogPixels;
        public uint BitsPerPel, Width, Height, DisplayFlags, Frequency;
        public uint ICMMethod, ICMIntent, MediaType, DitherType, Reserved1, Reserved2;
        public uint PanningWidth, PanningHeight;
    }

    [DllImport("user32.dll", EntryPoint = "EnumDisplaySettingsW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool EnumDisplaySettings(string device, int modeNumber, ref Mode mode);
    [DllImport("user32.dll", EntryPoint = "ChangeDisplaySettingsW", CharSet = CharSet.Unicode)]
    private static extern int ChangeDisplaySettings(ref Mode mode, uint flags);
    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int index);

    private static Mode EmptyMode()
    {
        Mode result = new Mode();
        result.Size = (ushort)Marshal.SizeOf(typeof(Mode));
        return result;
    }

    public static Mode Current()
    {
        Mode mode = EmptyMode();
        if (!EnumDisplaySettings(null, -1, ref mode))
            throw new Win32Exception(Marshal.GetLastWin32Error(), "EnumDisplaySettings current mode failed");
        return mode;
    }

    public static Mode[] Supported()
    {
        List<Mode> result = new List<Mode>();
        for (int index = 0; index < 4096; index++)
        {
            Mode mode = EmptyMode();
            if (!EnumDisplaySettings(null, index, ref mode)) break;
            result.Add(mode);
        }
        return result.ToArray();
    }

    public static int Apply(Mode mode)
    {
        // DM_PELSWIDTH | DM_PELSHEIGHT. Optional fields come from enumeration.
        mode.Fields = 0x00080000 | 0x00100000;
        if (mode.BitsPerPel != 0) mode.Fields |= 0x00040000;
        if (mode.Frequency > 1) mode.Fields |= 0x00400000;
        return ChangeDisplaySettings(ref mode, 0);
    }
}
'@
    }

    $MinimumWidth = 1536
    $MinimumHeight = 864
    $Original = [NhacViecCaptureDisplay]::Current()
    Write-CaptureNotice "Original mode $($Original.Width)x$($Original.Height) @ $($Original.Frequency)Hz; actual screen $([NhacViecCaptureDisplay]::GetSystemMetrics(0))x$([NhacViecCaptureDisplay]::GetSystemMetrics(1))."

    function Test-CaptureDisplayReady {
        return ([NhacViecCaptureDisplay]::GetSystemMetrics(0) -ge $MinimumWidth -and
                [NhacViecCaptureDisplay]::GetSystemMetrics(1) -ge $MinimumHeight)
    }

    function Write-SelectedCaptureMode {
        param([string]$Method)
        $Selected = [NhacViecCaptureDisplay]::Current()
        Write-CaptureNotice "Selected $($Selected.Width)x$($Selected.Height) @ $($Selected.Frequency)Hz via $Method; actual screen $([NhacViecCaptureDisplay]::GetSystemMetrics(0))x$([NhacViecCaptureDisplay]::GetSystemMetrics(1)). Original mode recorded above; runner session is ephemeral."
    }

    if (Test-CaptureDisplayReady) {
        Write-SelectedCaptureMode 'existing mode'
        exit 0
    }

    $SetDisplayCommand = Get-Command Set-DisplayResolution -ErrorAction SilentlyContinue
    if ($null -ne $SetDisplayCommand) {
        try {
            & $SetDisplayCommand -Width 1920 -Height 1080 -Force -ErrorAction Stop | Out-Null
            if (Test-CaptureDisplayReady) {
                Write-SelectedCaptureMode 'Set-DisplayResolution'
                exit 0
            }
            Write-CaptureNotice 'Set-DisplayResolution returned, but the effective screen is still too small; trying enumerated modes.'
        } catch {
            Write-CaptureNotice "Set-DisplayResolution did not complete: $($_.Exception.Message). Trying enumerated modes."
        }
    } else {
        Write-CaptureNotice 'Set-DisplayResolution is unavailable; trying supported modes through ChangeDisplaySettings.'
    }

    $Supported = @([NhacViecCaptureDisplay]::Supported())
    $Candidates = @($Supported | Where-Object {
        $_.Width -ge $MinimumWidth -and $_.Height -ge $MinimumHeight -and $_.BitsPerPel -ge 24
    } | Sort-Object @{Expression={
        if ($_.Width -eq 1920 -and $_.Height -eq 1080) { 0 }
        elseif ($_.Width -ge 1920 -and $_.Height -ge 1080) { 1 }
        else { 2 }
    }}, @{Expression={ [long]$_.Width * [long]$_.Height }},
       @{Expression={ $_.BitsPerPel }; Descending=$true},
       @{Expression={ $_.Frequency }; Descending=$true} | Select-Object -First 12)
    $Attempts = @()
    foreach ($Candidate in $Candidates) {
        $Result = [NhacViecCaptureDisplay]::Apply($Candidate)
        $Attempts += "$($Candidate.Width)x$($Candidate.Height)@$($Candidate.Frequency)Hz=$Result"
        if ($Result -eq 0) {
            for ($Poll = 0; $Poll -lt 10; $Poll++) {
                if (Test-CaptureDisplayReady) {
                    Write-SelectedCaptureMode 'ChangeDisplaySettings flags=0'
                    exit 0
                }
                Start-Sleep -Milliseconds 100
            }
        }
    }
    $SupportedDescriptions = @($Supported | ForEach-Object {
        "$($_.Width)x$($_.Height)/$($_.BitsPerPel)bpp"
    } | Sort-Object -Unique | Select-Object -First 40)
    throw "No supported mode produced a screen of at least ${MinimumWidth}x${MinimumHeight}. Actual screen $([NhacViecCaptureDisplay]::GetSystemMetrics(0))x$([NhacViecCaptureDisplay]::GetSystemMetrics(1)). Attempts: $($Attempts -join ', '). Supported: $($SupportedDescriptions -join ', ')."
} catch {
    Write-CaptureError $_.Exception.Message
    throw
}
