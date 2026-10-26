Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

!ifndef APP_VERSION
  !define APP_VERSION "2.0.4"
!endif
!ifndef SOURCE_DIR
  !error "Pass /DSOURCE_DIR=<absolute path to dist\NhacViecAnhHa>"
!endif
!ifndef OUTPUT_DIR
  !error "Pass /DOUTPUT_DIR=<absolute output directory>"
!endif

!define APP_NAME "Nhắc việc anh Hà (bản dựng mới)"
!define APP_EXE "NhacViecAnhHa.exe"
!define APP_KEY "Software\NhacViecAnhHaMoi"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\NhacViecAnhHaMoi"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "${OUTPUT_DIR}\NhacViecAnhHa-Setup-${APP_VERSION}-x64.exe"
InstallDir "$LOCALAPPDATA\Programs\NhacViecAnhHaMoi"
InstallDirRegKey HKCU "${APP_KEY}" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
ShowInstDetails show
ShowUninstDetails show
; A skipped runtime DLL would leave a mixed, unusable installation.
AllowSkipFiles off
BrandingText "Nhắc việc anh Hà · Mã nguồn dựng mới ${APP_VERSION}"
VIProductVersion "2.0.4.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "Bộ cài Nhắc việc anh Hà - Windows x64"
VIAddVersionKey "LegalCopyright" "Mã nguồn dựng mới cho người sử dụng"

!define MUI_ABORTWARNING
!define MUI_COMPONENTSPAGE_TEXT_TOP "Cài cho tài khoản Windows hiện tại. Hãy Thoát hẳn ứng dụng trước khi cài hoặc cập nhật. Dữ liệu bản dựng mới được lưu riêng với bản 1.7.0."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Mở Nhắc việc anh Hà"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Vietnamese"
!include /CHARSET=UTF8 "installer_preflight.nsh"

Section "Ứng dụng và tài liệu (bắt buộc)" MainSection
  SectionIn RO
  SetShellVarContext current
  Call RequireWritableTarget
  SetOutPath "$INSTDIR"
  File /r "${SOURCE_DIR}\*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\Nhắc việc anh Hà - bản mới"
  CreateShortcut "$SMPROGRAMS\Nhắc việc anh Hà - bản mới\Nhắc việc anh Hà.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortcut "$SMPROGRAMS\Nhắc việc anh Hà - bản mới\Gỡ cài đặt.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "${APP_KEY}" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "${UNINSTALL_KEY}" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
  ; Re-running Setup applies the current component choices.
  Delete "$DESKTOP\Nhắc việc anh Hà - bản mới.lnk"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "NhacViecAnhHaMoi"
SectionEnd

Function .onInit
  SetShellVarContext current
  StrCpy $PreflightOperation "Setup"
  Call InitMaintenanceGuard
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Bộ cài này cần Windows 64-bit."
    Abort
  ${EndIf}
FunctionEnd

Function un.onInit
  SetShellVarContext current
  StrCpy $PreflightOperation "Uninstall"
  Call un.InitMaintenanceGuard
FunctionEnd

Section /o "Tạo lối tắt trên Desktop" DesktopSection
  SetShellVarContext current
  CreateShortcut "$DESKTOP\Nhắc việc anh Hà - bản mới.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section /o "Tự chạy khi đăng nhập Windows" StartupSection
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "NhacViecAnhHaMoi" '$\"$INSTDIR\${APP_EXE}$\" --minimized'
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Call un.RequireWritableTarget
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "NhacViecAnhHaMoi"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
  DeleteRegKey HKCU "${APP_KEY}"
  Delete "$DESKTOP\Nhắc việc anh Hà - bản mới.lnk"
  Delete "$SMPROGRAMS\Nhắc việc anh Hà - bản mới\Nhắc việc anh Hà.lnk"
  Delete "$SMPROGRAMS\Nhắc việc anh Hà - bản mới\Gỡ cài đặt.lnk"
  RMDir "$SMPROGRAMS\Nhắc việc anh Hà - bản mới"
  Delete "$INSTDIR\${APP_EXE}"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  ; User databases live outside INSTDIR. Never remove either data directory.
SectionEnd
