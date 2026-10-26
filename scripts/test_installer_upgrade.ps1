[CmdletBinding()]
param(
    [string]$SetupPath = "",
    [string]$PythonExe = "",
    [string]$ReportPath = "",
    [switch]$AllowLocalTest
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($env:OS -ne 'Windows_NT') { throw 'Installer upgrade regression requires Windows.' }
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Installer upgrade regression requires PowerShell 7.' }
if ($env:GITHUB_ACTIONS -ne 'true' -and -not $AllowLocalTest) {
    throw 'This test installs temporary applications and changes HKCU shortcuts. Use an isolated Windows test account, then explicitly pass -AllowLocalTest.'
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VersionText = Get-Content (Join-Path $ProjectRoot 'nhacviec\__init__.py') -Raw
if ($VersionText -notmatch '__version__\s*=\s*"([^"]+)"') { throw 'Cannot determine application version.' }
$Version = $Matches[1]
$BaselineVersion = '2.0.3'
$BaselineTag = 'windows-2.0.3-preview.1'
$BaselineSha256 = '8f6ea8538fde80905d68083d15717dfa1fa0111ff3d982970f5faa85e1cb3fc4'
if ($Version -eq $BaselineVersion) { throw 'The upgrade regression must test a newer installer than its legacy baseline.' }
if (-not $SetupPath) { $SetupPath = Join-Path $ProjectRoot "dist\NhacViecAnhHa-Setup-$Version-x64.exe" }
if (-not $PythonExe) { $PythonExe = Join-Path $ProjectRoot '.venv-build\Scripts\python.exe' }
if (-not $ReportPath) { $ReportPath = Join-Path $ProjectRoot 'dist\installer-upgrade-test.json' }
$SetupPath = (Resolve-Path -LiteralPath $SetupPath).Path
$PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
$ReportPath = [IO.Path]::GetFullPath($ReportPath)
$ReportDirectory = Split-Path -Parent $ReportPath
New-Item -ItemType Directory -Path $ReportDirectory -Force | Out-Null
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) ('NhacViec-installer-regression-' + [guid]::NewGuid().ToString('N'))
$InstallDirectory = Join-Path $TestRoot 'Installed App'
$DataDirectory = Join-Path $TestRoot 'User Data'
$DatabasePath = Join-Path $DataDirectory 'data\tasks.db'
$ApplicationPath = Join-Path $InstallDirectory 'NhacViecAnhHa.exe'
$SqliteModule = Join-Path $InstallDirectory '_internal\_sqlite3.pyd'
$UninstallPath = Join-Path $InstallDirectory 'Uninstall.exe'
$Cases = [Collections.Generic.List[object]]::new()
$Report = [ordered]@{
    passed = $false
    version = $Version
    baseline_version = $BaselineVersion
    baseline_sha256 = $BaselineSha256
    setup_sha256 = (Get-FileHash -LiteralPath $SetupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    checks = @()
    cases = @()
}
$Application = $null
$LockedStream = $null
$SavedAttributes = $null
$FixtureRemoved = $false
$PreviousLocation = Get-Location
$Failure = $null

function Add-Case {
    param([string]$Name, [hashtable]$Evidence = @{})
    $Case = [ordered]@{ name = $Name; passed = $true }
    foreach ($Key in $Evidence.Keys) { $Case[$Key] = $Evidence[$Key] }
    $Cases.Add($Case)
    Write-Host "PASS $Name"
}

function Get-TextDigest {
    param([string]$Text)
    $Algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return [Convert]::ToHexString($Algorithm.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text))).ToLowerInvariant()
    } finally { $Algorithm.Dispose() }
}

function Invoke-BoundedProcess {
    param([string]$FilePath, [string[]]$Arguments, [int]$TimeoutMilliseconds = 120000)
    $Timer = [Diagnostics.Stopwatch]::StartNew()
    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru
    if (-not $Process.WaitForExit($TimeoutMilliseconds)) {
        # Only stop a process started by this test; the installer never kills an app.
        $Process.Kill()
        if (-not $Process.WaitForExit(5000)) { throw "Cannot terminate timed-out test process: $FilePath" }
        throw "Process exceeded its timeout; a silent installer may have shown a modal dialog: $FilePath"
    }
    $Process.Refresh()
    $Timer.Stop()
    return @{ exit_code = $Process.ExitCode; elapsed_ms = $Timer.ElapsedMilliseconds }
}

function Invoke-Setup {
    param([string]$Installer, [int]$TimeoutMilliseconds = 120000)
    # NSIS /D is last and deliberately unquoted; NSIS treats its remainder as the path.
    return Invoke-BoundedProcess $Installer @('/S', "/D=$InstallDirectory") $TimeoutMilliseconds
}

function Get-InstalledState {
    $Rows = foreach ($File in (Get-ChildItem -LiteralPath $InstallDirectory -Recurse -File -Force | Sort-Object FullName)) {
        $Relative = $File.FullName.Substring($InstallDirectory.Length + 1)
        "$Relative`t$($File.Length)`t$($File.Attributes)`t$((Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash)"
    }
    return $Rows -join "`n"
}

function Get-UserDataState {
    # Query a read-only consistent transaction, including the live SQLite WAL.
    # Logs/app.lock may change during normal operation; actual saved rows must not.
    $ReadState = @'
import json, sqlite3, sys
from pathlib import Path
database = Path(sys.argv[1]).resolve()
with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
    connection.execute('BEGIN')
    tables = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    state = {'schema_version': connection.execute('PRAGMA user_version').fetchone()[0], 'tables': []}
    for name, sql in tables:
        quoted = '"' + name.replace('"', '""') + '"'
        rows = connection.execute('SELECT * FROM ' + quoted + ' ORDER BY rowid').fetchall()
        state['tables'].append([name, sql, rows])
    print(json.dumps(state, ensure_ascii=True, separators=(',', ':')))
'@
    $State = & $PythonExe '-c' $ReadState $DatabasePath
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read the regression fixture database.' }
    return $State -join "`n"
}

function Get-InstallationRegistration {
    # Match the NSIS executable's default registry view on 64-bit Windows.
    $Registry = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser, [Microsoft.Win32.RegistryView]::Registry32)
    $App = $null
    $Uninstall = $null
    try {
        $App = $Registry.OpenSubKey('Software\NhacViecAnhHaMoi')
        $Uninstall = $Registry.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Uninstall\NhacViecAnhHaMoi')
        if ($null -eq $App -or $null -eq $Uninstall) { throw 'Installed application registration is missing.' }
        return @($App.GetValue('InstallDir'), $Uninstall.GetValue('InstallLocation'),
                 $Uninstall.GetValue('DisplayVersion'), $Uninstall.GetValue('UninstallString')) -join "`n"
    } finally {
        if ($null -ne $App) { $App.Dispose() }
        if ($null -ne $Uninstall) { $Uninstall.Dispose() }
        $Registry.Dispose()
    }
}

function Stop-OwnedApplication {
    if ($null -ne $script:Application) {
        $script:Application.Refresh()
        if (-not $script:Application.HasExited) {
            # No unsaved form exists in this synthetic fixture. This is test cleanup,
            # not an installation behavior and never targets another user's process.
            $script:Application.Kill()
            if (-not $script:Application.WaitForExit(10000)) { throw 'Cannot stop the app fixture.' }
        }
        $script:Application = $null
    }
}

function Start-OwnedApplication {
    $LogPath = Join-Path $DataDirectory 'logs\lifecycle.log'
    $PreviousStarts = 0
    if (Test-Path -LiteralPath $LogPath) {
        $PreviousStarts = [regex]::Matches((Get-Content -LiteralPath $LogPath -Raw -Encoding utf8), 'data_dir=').Count
    }
    $script:Application = Start-Process -FilePath $ApplicationPath -ArgumentList @('--data-dir', ('"' + $DataDirectory + '"'), '--minimized') -PassThru
    $ReadyDeadline = [datetime]::UtcNow.AddSeconds(35)
    while ([datetime]::UtcNow -lt $ReadyDeadline) {
        $script:Application.Refresh()
        if ($script:Application.HasExited) { throw 'Application fixture exited before the loaded-module check.' }
        try {
            $LoadedSqlite = @($script:Application.Modules | Where-Object { $_.FileName -ieq $SqliteModule }).Count -gt 0
            $Starts = 0
            if (Test-Path -LiteralPath $LogPath) {
                $Starts = [regex]::Matches((Get-Content -LiteralPath $LogPath -Raw -Encoding utf8), 'data_dir=').Count
            }
            if ($LoadedSqlite -and $Starts -gt $PreviousStarts) { return }
        } catch { }
        Start-Sleep -Milliseconds 200
    }
    throw 'Application fixture did not load its actual _sqlite3.pyd and complete startup.'
}

try {
    Set-Location $ProjectRoot
    New-Item -ItemType Directory -Path $TestRoot -Force | Out-Null
    $BaselineInstaller = Join-Path $TestRoot "NhacViecAnhHa-Setup-$BaselineVersion-x64.exe"
    $BaselineChecksum = Join-Path $TestRoot 'baseline-SHA256SUMS.txt'
    $ReleaseRoot = "https://github.com/manhtuantp1-beep/Nh-c-vi-c-a-H-/releases/download/$BaselineTag"
    Invoke-WebRequest -Uri "$ReleaseRoot/NhacViecAnhHa-Setup-$BaselineVersion-x64.exe" -OutFile $BaselineInstaller -TimeoutSec 60
    Invoke-WebRequest -Uri "$ReleaseRoot/SHA256SUMS.txt" -OutFile $BaselineChecksum -TimeoutSec 60
    $Checksum = Get-Content -LiteralPath $BaselineChecksum -Raw
    if ($Checksum -notmatch '\A(?<hash>[0-9a-fA-F]{64})  NhacViecAnhHa-Setup-2\.0\.3-x64\.exe(?:\r?\n)?\z' -or
        $Matches['hash'].ToLowerInvariant() -cne $BaselineSha256 -or
        (Get-FileHash -LiteralPath $BaselineInstaller -Algorithm SHA256).Hash.ToLowerInvariant() -cne $BaselineSha256) {
        throw 'Published legacy installer did not match the pinned 2.0.3 checksum.'
    }
    $Installed = Invoke-Setup $BaselineInstaller
    if ($Installed.exit_code -ne 0 -or -not (Test-Path -LiteralPath $SqliteModule)) { throw 'Legacy fixture installation failed.' }

    $SeedData = @'
from datetime import date, datetime, time
from pathlib import Path
import sys
from nhacviec.models import Schedule
from nhacviec.storage import Storage
with Storage(Path(sys.argv[1])) as store:
    task = store.create_task('Công việc giữ qua nâng cấp', datetime(2035, 1, 8, 17), content='Hồ sơ đã lưu',
                             requirements='Giữ nguyên yêu cầu', notes='Đang đối chiếu dữ liệu.\nChú ý mốc bàn giao.')
    store.set_task_status(task.id, 'in_progress')
    schedule = store.save_schedule(Schedule(title='Lịch giữ qua nâng cấp', start_date=date(2035, 1, 8),
                                            start_time=time(9), end_time=time(10), recurrence='once'))
    store.set_occurrence_status(schedule.id, date(2035, 1, 8), 'completed')
    store.save_settings(notifications_enabled=False, days_before=14)
    store.mark_notification('installer-regression-history', datetime(2026, 1, 1, 9))
'@
    & $PythonExe '-c' $SeedData $DatabasePath
    if ($LASTEXITCODE -ne 0) { throw 'Cannot seed regression fixture data.' }
    $ExpectedData = Get-UserDataState

    Start-OwnedApplication
    if ((Get-UserDataState) -cne $ExpectedData) { throw 'App startup changed saved fixture data unexpectedly.' }
    $InitialFiles = Get-InstalledState
    $InitialRegistration = Get-InstallationRegistration
    $Blocked = Invoke-Setup $SetupPath 20000
    if ($Blocked.exit_code -eq 0) { throw 'Installer overwrote a running legacy application.' }
    $Application.Refresh()
    if ($Application.HasExited) { throw 'Installer stopped the running legacy application.' }
    Add-Case 'running_legacy_app_blocks_upgrade' @{ exit_code = $Blocked.exit_code; elapsed_ms = $Blocked.elapsed_ms; loaded_module = '_sqlite3.pyd' }
    if ((Get-InstalledState) -cne $InitialFiles -or (Get-UserDataState) -cne $ExpectedData -or
        (Get-InstallationRegistration) -cne $InitialRegistration) { throw 'Blocked upgrade changed installed files, registration or saved data.' }
    Add-Case 'blocked_upgrade_preserves_files_and_data' @{
        file_tree_sha256 = Get-TextDigest $InitialFiles
        user_data_sha256 = Get-TextDigest $ExpectedData
        registration_sha256 = Get-TextDigest $InitialRegistration
    }

    Stop-OwnedApplication
    $LockedStream = [IO.File]::Open($SqliteModule, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
    try {
        $BlockedLock = Invoke-Setup $SetupPath 20000
        if ($BlockedLock.exit_code -eq 0) { throw 'Installer accepted an exclusively locked _sqlite3.pyd.' }
    } finally { $LockedStream.Dispose(); $LockedStream = $null }
    if ((Get-InstalledState) -cne $InitialFiles -or (Get-UserDataState) -cne $ExpectedData) {
        throw 'Locked-file rejection changed the installation or user data.'
    }
    Add-Case 'locked_sqlite_blocks_upgrade' @{ exit_code = $BlockedLock.exit_code; elapsed_ms = $BlockedLock.elapsed_ms }

    $SavedAttributes = [IO.File]::GetAttributes($SqliteModule)
    [IO.File]::SetAttributes($SqliteModule, ($SavedAttributes -bor [IO.FileAttributes]::ReadOnly))
    $ReadOnlyFiles = Get-InstalledState
    try {
        $BlockedReadOnly = Invoke-Setup $SetupPath 20000
        if ($BlockedReadOnly.exit_code -eq 0) { throw 'Installer accepted a read-only _sqlite3.pyd.' }
        if ((Get-InstalledState) -cne $ReadOnlyFiles) { throw 'Read-only target rejection changed installed files.' }
    } finally { [IO.File]::SetAttributes($SqliteModule, $SavedAttributes); $SavedAttributes = $null }
    Add-Case 'readonly_sqlite_blocks_upgrade' @{ exit_code = $BlockedReadOnly.exit_code }

    $Upgraded = Invoke-Setup $SetupPath
    if ($Upgraded.exit_code -ne 0) { throw "Installer did not succeed after releasing the app and module lock: $($Upgraded.exit_code)" }
    Add-Case 'upgrade_after_exit_succeeds' @{ exit_code = $Upgraded.exit_code }
    foreach ($Gui in @($false, $true)) {
        $Kind = if ($Gui) { 'gui' } else { 'core' }
        $Mode = if ($Gui) { '--gui-smoke-test' } else { '--self-test' }
        $RuntimeReportPath = Join-Path $TestRoot "installed-$Kind.json"
        $Runtime = Invoke-BoundedProcess $ApplicationPath @($Mode, '--self-test-report', ('"' + $RuntimeReportPath + '"')) 60000
        if ($Runtime.exit_code -ne 0 -or -not (Test-Path -LiteralPath $RuntimeReportPath)) { throw "Installed $Kind runtime failed." }
        $RuntimeReport = Get-Content -LiteralPath $RuntimeReportPath -Raw | ConvertFrom-Json
        if ($RuntimeReport.passed -ne $true -or $RuntimeReport.version -cne $Version -or $RuntimeReport.gui -ne $Gui) { throw "Installed $Kind runtime returned invalid evidence." }
        if ($Gui -and ($RuntimeReport.display.awareness -cne 'per-monitor-v2' -or $RuntimeReport.display.window_awareness -cne 'per-monitor-v2')) {
            throw 'Upgraded GUI lost native PerMonitorV2 rendering.'
        }
    }
    Add-Case 'installed_runtime_passes' @{ version = $Version; per_monitor_v2 = $true }

    Start-OwnedApplication
    $UpgradedFiles = Get-InstalledState
    $UpgradedRegistration = Get-InstallationRegistration
    # Test the NEW uninstaller: the published 2.0.3 uninstaller has no guard.
    # In-place NSIS uninstallation reports its real exit code instead of the
    # initial process that merely copies the uninstaller into TEMP.
    $BlockedUninstall = Invoke-BoundedProcess $UninstallPath @('/S', "_?=$InstallDirectory") 20000
    if ($BlockedUninstall.exit_code -eq 0) { throw 'Uninstaller accepted a running application.' }
    $Application.Refresh()
    if ($Application.HasExited -or (Get-InstalledState) -cne $UpgradedFiles -or
        (Get-UserDataState) -cne $ExpectedData -or (Get-InstallationRegistration) -cne $UpgradedRegistration) {
        throw 'Blocked uninstall changed the running app, installed files, registration or data.'
    }
    Add-Case 'running_app_blocks_uninstall' @{ exit_code = $BlockedUninstall.exit_code; elapsed_ms = $BlockedUninstall.elapsed_ms }
    Stop-OwnedApplication
    $Removed = Invoke-BoundedProcess $UninstallPath @('/S', "_?=$InstallDirectory") 30000
    if ($Removed.exit_code -ne 0 -or (Test-Path -LiteralPath $ApplicationPath) -or
        (Test-Path -LiteralPath (Join-Path $InstallDirectory '_internal'))) {
        throw 'New uninstaller did not succeed after the app fixture exited.'
    }
    $FixtureRemoved = $true
    Add-Case 'uninstall_after_exit_succeeds' @{ exit_code = $Removed.exit_code }
    if ((Get-UserDataState) -cne $ExpectedData) { throw 'Successful upgrade changed saved tasks, notes, schedules, settings or history.' }
    Add-Case 'user_data_preserved' @{
        data = 'synthetic task, notes, schedule, occurrence, settings, notification history'
        user_data_sha256 = Get-TextDigest $ExpectedData
    }
    $Report.passed = $true
} catch {
    $Failure = $_
    $Report['error'] = ($_ | Out-String).Trim()
    foreach ($Name in @('Setup', 'Uninstall')) {
        $Log = Join-Path ([IO.Path]::GetTempPath()) "NhacViecAnhHa-$Name-last.log"
        if (Test-Path -LiteralPath $Log) { $Report["last_${Name}_log"] = Get-Content -LiteralPath $Log -Raw }
    }
} finally {
    if ($null -ne $LockedStream) { $LockedStream.Dispose() }
    if ($null -ne $SavedAttributes -and (Test-Path -LiteralPath $SqliteModule)) { [IO.File]::SetAttributes($SqliteModule, $SavedAttributes) }
    try { Stop-OwnedApplication }
    catch {
        $Report.passed = $false
        if ($null -eq $Failure) { $Failure = $_; $Report['error'] = ($_ | Out-String).Trim() }
        Write-Warning "Fixture process cleanup: $_"
    }
    if (-not $FixtureRemoved -and (Test-Path -LiteralPath $UninstallPath)) {
        try { $null = Invoke-BoundedProcess $UninstallPath @('/S', "_?=$InstallDirectory") 30000 }
        catch { Write-Warning "Fixture cleanup: $_" }
    }
    $Report.checks = @($Cases | ForEach-Object { $_.name })
    $Report.cases = @($Cases.ToArray())
    $Report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ReportPath -Encoding utf8
    Set-Location $PreviousLocation
    if ($Report.passed) { Remove-Item -LiteralPath $TestRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
if ($null -ne $Failure) {
    if ($env:GITHUB_ACTIONS -eq 'true') {
        $Diagnostic = [string]$Report.error
        foreach ($Key in @('last_Setup_log', 'last_Uninstall_log')) {
            if ($Report.Contains($Key)) { $Diagnostic += "`n${Key}:`n$($Report[$Key])" }
        }
        if ($Diagnostic.Length -gt 5000) { $Diagnostic = $Diagnostic.Substring($Diagnostic.Length - 5000) }
        $Message = $Diagnostic.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
        Write-Host "::error title=Installer upgrade regression::$Message"
    }
    throw $Failure
}
Write-Host "Installer upgrade regression passed: $ReportPath"
