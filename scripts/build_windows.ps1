[CmdletBinding()]
param(
    [string]$PythonExe = "",
    [string]$MakensisPath = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "Bộ cài phải được đóng gói trên Windows 64-bit."
}

function Write-BuildErrorAnnotation {
    param([string]$Message)
    if ($env:GITHUB_ACTIONS -eq "true") {
        if ($Message.Length -gt 3500) { $Message = $Message.Substring($Message.Length - 3500) }
        $Escaped = $Message.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
        Write-Host "::error title=Windows build diagnostics::$Escaped"
    }
}

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    $LogDirectory = Join-Path $ProjectRoot "build"
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    $LogPath = Join-Path $LogDirectory "last-command.log"
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        # Windows PowerShell 5.1 can turn redirected native stderr into a
        # terminating NativeCommandError. Keep native streams intact there.
        & $Executable @Arguments
        $NativeExitCode = $LASTEXITCODE
    } else {
        & $Executable @Arguments 2>&1 | Tee-Object -FilePath $LogPath
        $NativeExitCode = $LASTEXITCODE
    }
    if ($NativeExitCode -ne 0) {
        if ($PSVersionTable.PSVersion.Major -ge 7) {
            $Tail = Get-Content -LiteralPath $LogPath -Tail 65 | Out-String
            Write-BuildErrorAnnotation $Tail
        }
        throw "Lệnh thất bại (mã $NativeExitCode): $Executable $($Arguments -join ' ')"
    }
}

function Resolve-Nsis {
    param([string]$ExplicitPath)
    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath)) { throw "Không tìm thấy NSIS tại: $ExplicitPath" }
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }
    $Command = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }
    $Candidates = @()
    if (${env:ProgramFiles(x86)}) { $Candidates += Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe" }
    if ($env:ProgramFiles) { $Candidates += Join-Path $env:ProgramFiles "NSIS\makensis.exe" }
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate) { return $Candidate }
    }
    throw "Cần NSIS 3.11. Cài từ nsis.sourceforge.io hoặc truyền -MakensisPath đường_dẫn_makensis.exe."
}

function Invoke-AppCheck {
    param([string]$Executable, [string]$Check, [string]$ReportPath)
    if (Test-Path -LiteralPath $ReportPath) { Remove-Item -LiteralPath $ReportPath }
    $Arguments = @($Check, "--self-test-report", ('"' + $ReportPath + '"'))
    $Process = Start-Process -FilePath $Executable -ArgumentList $Arguments -PassThru
    if (-not $Process.WaitForExit(60000)) {
        $Process.Kill()
        throw "Kiểm tra $Check vượt 60 giây."
    }
    if ($Process.ExitCode -ne 0) {
        if (Test-Path -LiteralPath $ReportPath) {
            Write-BuildErrorAnnotation (Get-Content -LiteralPath $ReportPath -Raw)
        }
        throw "Kiểm tra $Check thất bại (mã $($Process.ExitCode))."
    }
    if (-not (Test-Path -LiteralPath $ReportPath)) { throw "Kiểm tra $Check không tạo báo cáo của lần chạy này." }
    $Report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
    if ($null -eq $Report) { throw "Báo cáo kiểm tra $Check rỗng." }
    if ($Report.passed -ne $true -or $Report.version -ne "2.0.4") { throw "Báo cáo $Check không xác nhận bản dựng thành công." }
    if ($Report.gui -ne ($Check -eq "--gui-smoke-test")) { throw "Báo cáo không thuộc đúng loại kiểm tra $Check." }
    $Checks = @($Report.checks | Where-Object { $_ -is [string] -and -not [string]::IsNullOrWhiteSpace($_) })
    if ($Checks.Count -eq 0) { throw "Kiểm tra $Check không chạy bước kiểm chứng nào." }
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PreviousLocation = Get-Location
$VenvPath = Join-Path $ProjectRoot ".venv-build"
$BuildPython = Join-Path $VenvPath "Scripts\python.exe"
$Version = "2.0.4"

try {
    Set-Location $ProjectRoot
    $MakensisPath = Resolve-Nsis $MakensisPath
    $NsisVersion = & $MakensisPath "/VERSION"
    if ($LASTEXITCODE -ne 0 -or "$NsisVersion" -notmatch '^v?3\.11(?:\D|$)') {
        throw "Cần NSIS 3.11 để tái lập build; phiên bản hiện tại: $NsisVersion"
    }
    if (-not (Test-Path -LiteralPath $BuildPython)) {
        if ($PythonExe) {
            Invoke-Checked $PythonExe @("-m", "venv", $VenvPath)
        } elseif (Get-Command py -ErrorAction SilentlyContinue) {
            Invoke-Checked "py" @("-3.13", "-m", "venv", $VenvPath)
        } else {
            throw "Chưa tìm thấy Python Launcher. Cài Python 3.13 64-bit hoặc truyền -PythonExe đường_dẫn_python.exe."
        }
    }
    Invoke-Checked $BuildPython @("-c", "import struct, sys; assert sys.version_info[:2] == (3, 13), 'Can Python 3.13'; assert struct.calcsize('P') == 8, 'Can Python 64-bit'")
    Invoke-Checked $BuildPython @("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-build.txt")
    Invoke-Checked $BuildPython @("-m", "unittest", "discover", "-s", "tests", "-v")
    Invoke-Checked $BuildPython @("-m", "PyInstaller", "--clean", "--noconfirm", "--distpath", "dist", "--workpath", "build\pyinstaller", "packaging\NhacViecAnhHa.spec")

    $DistRoot = Join-Path $ProjectRoot "dist"
    $AppDist = Join-Path $DistRoot "NhacViecAnhHa"
    $AppExe = Join-Path $AppDist "NhacViecAnhHa.exe"
    if (-not (Test-Path -LiteralPath $AppExe)) { throw "Không tìm thấy ứng dụng đã đóng gói: $AppExe" }
    Invoke-AppCheck $AppExe "--self-test" (Join-Path $DistRoot "self-test.json")
    Invoke-AppCheck $AppExe "--gui-smoke-test" (Join-Path $DistRoot "gui-smoke-test.json")

    Invoke-Checked $MakensisPath @("/V3", "/DAPP_VERSION=$Version", "/DSOURCE_DIR=$AppDist", "/DOUTPUT_DIR=$DistRoot", (Join-Path $ProjectRoot "packaging\installer.nsi"))
    $SetupFile = Join-Path $DistRoot "NhacViecAnhHa-Setup-$Version-x64.exe"
    if (-not (Test-Path -LiteralPath $SetupFile)) { throw "NSIS không tạo ra bộ cài dự kiến: $SetupFile" }
    $Hash = (Get-FileHash -LiteralPath $SetupFile -Algorithm SHA256).Hash.ToLowerInvariant()
    "$Hash  $(Split-Path -Leaf $SetupFile)" | Set-Content -LiteralPath (Join-Path $DistRoot "SHA256SUMS.txt") -Encoding Ascii
    Write-Host "Bộ cài đã tạo: $SetupFile"
    Write-Host "Mã kiểm tra: $(Join-Path $DistRoot 'SHA256SUMS.txt')"
    Write-Host "Đã chạy kiểm thử mã nguồn, --self-test và --gui-smoke-test của EXE. Cần kiểm tra khay hệ thống và thông báo trên máy đích."
} catch {
    Write-BuildErrorAnnotation ($_ | Out-String)
    throw
} finally {
    Set-Location $PreviousLocation
}
