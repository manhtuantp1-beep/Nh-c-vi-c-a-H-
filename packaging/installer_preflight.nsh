; Native Windows checks run before installing or removing any application file.
; They also detect versions 2.0.0-2.0.3, which do not expose a setup mutex.
!ifndef NHACVIEC_INSTALLER_PREFLIGHT
!define NHACVIEC_INSTALLER_PREFLIGHT

Var PreflightOperation
Var PreflightCode
Var PreflightNativeCode
Var PreflightPath
Var PreflightLog
Var MaintenanceMutex

!macro DefineMaintenancePreflight PREFIX

Function ${PREFIX}WritePreflightLog
  Push $0
  ClearErrors
  FileOpen $0 "$PreflightLog" a
  ${IfNot} ${Errors}
    FileWriteUTF16LE $0 "phase=$PreflightOperation code=$PreflightCode native=$PreflightNativeCode path=$PreflightPath$\r$\n"
    FileClose $0
  ${EndIf}
  Pop $0
FunctionEnd

Function ${PREFIX}InitMaintenanceGuard
  StrCpy $PreflightLog "$TEMP\NhacViecAnhHa-$PreflightOperation-last.log"
  ClearErrors
  FileOpen $0 "$PreflightLog" w
  ${IfNot} ${Errors}
    FileWriteUTF16LE /BOM $0 "NhacViecAnhHa ${APP_VERSION} $PreflightOperation preflight$\r$\n"
    FileClose $0
  ${EndIf}
  ; Keep this handle for the whole setup/uninstall process. Windows releases
  ; it on every exit path. Local\ scopes it to this Windows logon session.
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\NhacViecAnhHaMoi.Maintenance") p.r0 ?e'
  Pop $1
  StrCpy $MaintenanceMutex $0
  ${If} $0 = 0
  ${OrIf} $1 == 183
    StrCpy $PreflightCode 1618
    StrCpy $PreflightNativeCode $1
    StrCpy $PreflightPath "$INSTDIR"
    Call ${PREFIX}WritePreflightLog
    IfSilent maintenance_busy_quit
    MessageBox MB_OK|MB_ICONEXCLAMATION "Một bộ cài hoặc bộ gỡ Nhắc việc anh Hà đang chạy. Anh hãy hoàn tất cửa sổ đó rồi chạy lại."
    maintenance_busy_quit:
    SetErrorLevel 1618
    Quit
  ${EndIf}
FunctionEnd

Function ${PREFIX}CheckWritableFile
  Exch $0
  Push $1
  Push $2
  ; OPEN_EXISTING never truncates a file. Image sections are checked separately
  ; with Restart Manager before reaching this permission/sharing check.
  System::Call 'kernel32::CreateFileW(w r0, i 0x40010000, i 7, p 0, i 3, i 0x80, p 0) p.r1 ?e'
  Pop $2
  ${If} $1 = -1
    ${If} $2 != 2
    ${AndIf} $2 != 3
      StrCpy $PreflightPath $0
      StrCpy $PreflightNativeCode $2
      StrCpy $PreflightCode $2
      ${If} $PreflightCode = 0
        StrCpy $PreflightCode 1603
      ${EndIf}
    ${EndIf}
  ${Else}
    System::Call 'kernel32::CloseHandle(p r1)'
  ${EndIf}
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

Function ${PREFIX}CheckInternalDirectory
  Exch $0
  Push $1
  Push $2
  Push $3
  Push $4
  System::Call 'kernel32::GetFileAttributesW(w r0) i.r3 ?e'
  Pop $4
  ${If} $3 = -1
    ${If} $4 != 2
    ${AndIf} $4 != 3
      StrCpy $PreflightPath $0
      StrCpy $PreflightCode $4
      StrCpy $PreflightNativeCode $4
      ${If} $PreflightCode = 0
        StrCpy $PreflightCode 1603
      ${EndIf}
    ${EndIf}
    Goto directory_done
  ${EndIf}
  IntOp $4 $3 & 0x400
  ${If} $4 != 0
    ; Never follow a junction/symlink outside the application payload.
    StrCpy $PreflightPath $0
    StrCpy $PreflightCode 1603
    StrCpy $PreflightNativeCode 4390
    Goto directory_done
  ${EndIf}
  ; Check every payload directory, including permission to create new files.
  Push $0
  Call ${PREFIX}ProbeWritableDirectory
  ${If} $PreflightCode != 0
    Goto directory_done
  ${EndIf}
  ClearErrors
  FindFirst $1 $2 "$0\*"
  IfErrors directory_find_failed
  Goto directory_next
  directory_find_failed:
    System::Call 'kernel32::GetLastError() i.r4'
    ${If} $4 != 2
    ${AndIf} $4 != 18
      StrCpy $PreflightPath $0
      StrCpy $PreflightCode $4
      StrCpy $PreflightNativeCode $4
      ${If} $PreflightCode = 0
        StrCpy $PreflightCode 1603
      ${EndIf}
    ${EndIf}
    Goto directory_done
  directory_next:
    ${If} $2 == "."
    ${OrIf} $2 == ".."
      Goto directory_advance
    ${EndIf}
    System::Call 'kernel32::GetFileAttributesW(w "$0\$2") i.r3 ?e'
    Pop $4
    ${If} $3 = -1
      StrCpy $PreflightPath "$0\$2"
      StrCpy $PreflightCode $4
      StrCpy $PreflightNativeCode $4
      ${If} $PreflightCode = 0
        StrCpy $PreflightCode 1603
      ${EndIf}
      Goto directory_close
    ${EndIf}
    IntOp $4 $3 & 0x10
    ${If} $4 != 0
      Push "$0\$2"
      Call ${PREFIX}CheckInternalDirectory
    ${Else}
      Push "$0\$2"
      Call ${PREFIX}CheckWritableFile
    ${EndIf}
    ${If} $PreflightCode != 0
      Goto directory_close
    ${EndIf}
    directory_advance:
    ClearErrors
    FindNext $1 $2
    IfErrors directory_close directory_next
  directory_close:
    FindClose $1
  directory_done:
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

Function ${PREFIX}CheckRunningApplication
  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6
  Push $7
  Push $8
  Push $9
  StrCpy $0 "$INSTDIR\${APP_EXE}"
  StrCpy $8 1
  IfFileExists "$0" running_has_exe
  StrCpy $0 "$INSTDIR\_internal\_sqlite3.pyd"
  IfFileExists "$0" running_begin running_done
  running_has_exe:
  IfFileExists "$INSTDIR\_internal\_sqlite3.pyd" 0 running_begin
  StrCpy $8 2
  running_begin:
  ; Restart Manager reports processes using an image without terminating them.
  ; Checking the loaded EXE covers all previous versions, including minimized
  ; tray instances. Checking the SQLite image also covers independent holders.
  System::Call 'rstrtmgr::RmStartSession(*i .r1, i 0, w .r2) i.r3'
  ${If} $3 != 0
    StrCpy $PreflightCode 1603
    StrCpy $PreflightNativeCode $3
    StrCpy $PreflightPath $0
    Goto running_done
  ${EndIf}
  System::Call '*(&w${NSIS_MAX_STRLEN} r0) p.r4'
  StrCpy $9 "$INSTDIR\_internal\_sqlite3.pyd"
  System::Call '*(&w${NSIS_MAX_STRLEN} r9) p.r5'
  System::Call '*(p r4, p r5) p.r6'
  System::Call 'rstrtmgr::RmRegisterResources(i r1, i r8, p r6, i 0, p 0, i 0, p 0) i.r3'
  ${If} $3 == 0
    StrCpy $7 0
    StrCpy $8 0
    System::Call 'rstrtmgr::RmGetList(i r1, *i .r7, *i r8, p 0, *i .r9) i.r3'
    ${If} $7 > 0
      StrCpy $PreflightCode 32
      StrCpy $PreflightNativeCode 32
      StrCpy $PreflightPath $0
    ${ElseIf} $3 != 0
      StrCpy $PreflightCode 1603
      StrCpy $PreflightNativeCode $3
      StrCpy $PreflightPath $0
    ${EndIf}
  ${Else}
    StrCpy $PreflightCode 1603
    StrCpy $PreflightNativeCode $3
    StrCpy $PreflightPath $0
  ${EndIf}
  System::Free $6
  System::Free $5
  System::Free $4
  System::Call 'rstrtmgr::RmEndSession(i r1)'
  running_done:
  Pop $9
  Pop $8
  Pop $7
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

Function ${PREFIX}ProbeWritableDirectory
  Exch $0
  Push $1
  Push $2
  Push $3
  Push $4
  StrCpy $4 $0
  ClearErrors
  CreateDirectory "$4"
  ${If} ${Errors}
    StrCpy $PreflightPath $4
    StrCpy $PreflightCode 5
    StrCpy $PreflightNativeCode 5
    Goto probe_done
  ${EndIf}
  ; A unique CREATE_NEW temporary file, automatically removed on CloseHandle.
  ; Never open or truncate an existing file just to test directory permissions.
  System::Call 'kernel32::GetCurrentProcessId() i.r1'
  System::Call 'kernel32::GetTickCount() i.r2'
  StrCpy $0 "$4\.nhacviec-write-check-$1-$2.tmp"
  System::Call 'kernel32::CreateFileW(w r0, i 0x40010000, i 7, p 0, i 1, i 0x04000100, p 0) p.r1 ?e'
  Pop $3
  ${If} $1 = -1
    StrCpy $PreflightPath $4
    StrCpy $PreflightCode $3
    StrCpy $PreflightNativeCode $3
    ${If} $PreflightCode = 0
      StrCpy $PreflightCode 1603
    ${EndIf}
  ${Else}
    System::Call 'kernel32::CloseHandle(p r1)'
  ${EndIf}
  probe_done:
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

Function ${PREFIX}RequireWritableTarget
  preflight_retry:
  StrCpy $PreflightCode 0
  StrCpy $PreflightNativeCode 0
  StrCpy $PreflightPath "$INSTDIR"
  Call ${PREFIX}CheckRunningApplication
  ${If} $PreflightCode == 0
    Push "$INSTDIR\${APP_EXE}"
    Call ${PREFIX}CheckWritableFile
  ${EndIf}
  ${If} $PreflightCode == 0
    Push "$INSTDIR\_internal"
    Call ${PREFIX}CheckInternalDirectory
  ${EndIf}
  !if "${PREFIX}" == ""
    ; The uninstaller is itself running during removal, so test it only setup.
    ${If} $PreflightCode == 0
      Push "$INSTDIR\Uninstall.exe"
      Call ${PREFIX}CheckWritableFile
    ${EndIf}
  !endif
  ${If} $PreflightCode == 0
    Push "$INSTDIR"
    Call ${PREFIX}ProbeWritableDirectory
  ${EndIf}
  Call ${PREFIX}WritePreflightLog
  ${If} $PreflightCode == 0
    Return
  ${EndIf}
  IfSilent preflight_quit
  ${If} $PreflightCode == 32
  ${OrIf} $PreflightCode == 33
  ${OrIf} $PreflightCode == 1224
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Ứng dụng hoặc một tệp đang được sử dụng:$\r$\n$PreflightPath$\r$\n$\r$\nAnh chọn Thoát hẳn trong Nhắc việc anh Hà hoặc menu khay hệ thống, rồi nhấn Thử lại. Dấu X chỉ thu nhỏ ứng dụng.$\r$\n$\r$\nChưa thay đổi tệp ứng dụng hay dữ liệu. Chọn Hủy để dừng." IDRETRY preflight_retry
  ${ElseIf} $PreflightCode == 5
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Không ghi được vào tệp hoặc thư mục:$\r$\n$PreflightPath$\r$\n$\r$\nAnh kiểm tra quyền ghi và thuộc tính Chỉ đọc, hoặc chọn thư mục cài đặt anh có quyền sử dụng. Nhấn Thử lại sau khi xử lý.$\r$\n$\r$\nChưa thay đổi tệp ứng dụng hay dữ liệu. Chọn Hủy để dừng." IDRETRY preflight_retry
  ${Else}
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Chưa kiểm tra được điều kiện cài/gỡ tại:$\r$\n$PreflightPath$\r$\nMã Windows: $PreflightNativeCode$\r$\n$\r$\nAnh đóng ứng dụng, kiểm tra thư mục và thử lại. Chưa thay đổi tệp ứng dụng hay dữ liệu.$\r$\nNhật ký: $PreflightLog" IDRETRY preflight_retry
  ${EndIf}
  preflight_quit:
  SetErrorLevel $PreflightCode
  Quit
FunctionEnd

!macroend

!insertmacro DefineMaintenancePreflight ""
!insertmacro DefineMaintenancePreflight "un."

!endif
