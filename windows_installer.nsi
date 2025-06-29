; NSIS Installer Config for OrDraft
; This script embeds installation files using explicit File commands.

; Basic installer settings
Name "OrDraft Installer"
OutFile "OrDraftInstaller.exe"
InstallDir "$PROGRAMFILES\OrDraft"
InstallDirRegKey HKLM "Software\OrDraft" "Install_Dir"

!include "MUI2.nsh"
!include "nsDialogs.nsh"         ; For custom pages
!include "LogicLib.nsh"          ; For using ${If}/${Else} constructs

Var MAIN_EXE
Var CREATE_SHORTCUT           ; Stores user choice for shortcut creation

; MUI Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
Page custom ShortcutPageCreate ShortcutPageLeave   ; Custom page for additional options
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; -------------------------------
; Installation Section
; -------------------------------
Section "Install" SEC01
    ; Remove any previous installation remnants
    Call RemoveOldVersion

    ; Ensure $INSTDIR is explicitly set to the default install directory.
    StrCpy $INSTDIR "$PROGRAMFILES\OrDraft"
    CreateDirectory "$INSTDIR"
    SetOutPath "$INSTDIR"
    
    ; Embed the main executable from PyInstaller output.
    File "dist\OrDraft.exe"
SectionEnd

; -------------------------------
; Custom Page: Shortcut Options
; -------------------------------
Function ShortcutPageCreate
    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ; Create an instructional label.
    ${NSD_CreateLabel} 10u 10u 300u 12u "Select additional actions to perform after installation:"
    Pop $0

    ; Create a checkbox for shortcut creation (default checked).
    ${NSD_CreateCheckBox} 10u 30u 250u 12u "Create Desktop and Start Menu Shortcuts"
    Pop $R1
    ${NSD_SetState} $R1 ${BST_CHECKED}

    nsDialogs::Show
FunctionEnd

Function ShortcutPageLeave
    ${NSD_GetState} $R1 $CREATE_SHORTCUT
FunctionEnd

; -------------------------------
; Remove Previous Installation
; -------------------------------
Function RemoveOldVersion
    DetailPrint "Checking for previous version..."

    ClearErrors
    RMDir /r "$INSTDIR"
    IfErrors 0 +3
        DetailPrint "Warning: Could not remove (or no) old installation directory at $INSTDIR."
    
    ClearErrors
    Delete "$SMPROGRAMS\OrDraft\OrDraft.lnk"
    IfErrors 0 +3
        DetailPrint "Warning: Could not delete Start Menu shortcut at $SMPROGRAMS\OrDraft\OrDraft.lnk."
    
    ClearErrors
    RMDir "$SMPROGRAMS\OrDraft"
    IfErrors 0 +3
        DetailPrint "Warning: Could not remove Start Menu folder at $SMPROGRAMS\OrDraft."
    
    ClearErrors
    Delete "$DESKTOP\OrDraft.lnk"
    IfErrors 0 +3
        DetailPrint "Warning: Could not delete Desktop shortcut at $DESKTOP\OrDraft.lnk."
    
    ClearErrors
FunctionEnd

; -------------------------------
; Post-Installation Actions
; -------------------------------
Function .onInstSuccess
    ; Verify the main executable exists in $INSTDIR.
    ClearErrors
    FindFirst $0 $1 "$INSTDIR\OrDraft.exe"
    IfErrors 0 +3
        MessageBox MB_OK "Error: No executable found in $INSTDIR."
        Abort
    StrCpy $MAIN_EXE $1
    FindClose $0

    ${If} $CREATE_SHORTCUT == ${BST_CHECKED}
        DetailPrint "Creating shortcuts..."
        CreateDirectory "$SMPROGRAMS\OrDraft"
        CreateShortCut "$SMPROGRAMS\OrDraft\OrDraft.lnk" "$INSTDIR\OrDraft.exe" "" "$INSTDIR\OrDraft.exe" 0
        CreateShortCut "$DESKTOP\OrDraft.lnk" "$INSTDIR\OrDraft.exe" "" "$INSTDIR\OrDraft.exe" 0
    ${Else}
        DetailPrint "Skipping shortcut creation as per user selection."
    ${EndIf}
FunctionEnd

; -------------------------------
; Uninstaller Section
; -------------------------------
Section "Uninstall"
    Delete "$INSTDIR\OrDraft.exe"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\OrDraft.lnk"
    Delete "$SMPROGRAMS\OrDraft\OrDraft.lnk"
    RMDir "$SMPROGRAMS\OrDraft"
    DeleteRegKey HKLM "Software\OrDraft"
    RMDir /r "$APPDATA\Ordraft"
SectionEnd
