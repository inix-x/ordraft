; NSIS Installer Config for OrDraft OF (Without zip2exe)
; This script embeds installation files using explicit File commands.

# new: Basic installer settings
Name "OrDraft OF Installer"
OutFile "OrDraftInstaller.exe"
InstallDir "$PROGRAMFILES\OrDraft OF"
InstallDirRegKey HKLM "Software\OrDraft" "Install_Dir"

!include "MUI2.nsh"
!include "nsDialogs.nsh"         ; new: For custom pages
!include "LogicLib.nsh"          ; new: For using ${If}/${Else} constructs

Var MAIN_EXE
Var CREATE_SHORTCUT           ; new: Stores user choice for shortcut creation

# new: MUI pages (welcome, license, directory, custom options, install, finish)
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"   ; new: Ensure license.txt is available
!insertmacro MUI_PAGE_DIRECTORY
Page custom ShortcutPageCreate ShortcutPageLeave   ; new: Custom page for extra actions
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

# new: Section for installing files
Section "Install" SEC01
    ; new: Remove any previous installation remnants before installing the new version.
    Call RemoveOldVersion

    ; new: Create installation directory
    CreateDirectory "$INSTDIR\OrDraft-OF"

    ; new: Embed the main executable into the installer
    File "OrDraft-OF\OrDraft.exe"
    
    ; new: Embed all files in the Templates folder
    CreateDirectory "$INSTDIR\OrDraft-OF\Templates"
    File /r "OrDraft-OF\Templates\*.*"
SectionEnd

# new: Custom page for additional post-install actions
Function ShortcutPageCreate
    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ; new: Instruction label for extra actions
    ${NSD_CreateLabel} 10u 10u 300u 12u "Select additional actions to perform after installation:"
    Pop $0

    ; new: Checkbox for creating shortcuts (default checked)
    ${NSD_CreateCheckBox} 10u 30u 250u 12u "Create Desktop and Start Menu Shortcuts"
    Pop $R1
    ${NSD_SetState} $R1 ${BST_CHECKED}

    nsDialogs::Show
FunctionEnd

# new: Function to capture user selections from the custom page
Function ShortcutPageLeave
    ${NSD_GetState} $R1 $CREATE_SHORTCUT
FunctionEnd

# new: Function to remove previous installation remnants
Function RemoveOldVersion
    DetailPrint "Checking for previous version..."

    ClearErrors
    RMDir /r "$INSTDIR\OrDraft-OF"
    IfErrors 0 +3
        DetailPrint "Warning: Could not remove (or no) old installation directory at $INSTDIR\OrDraft-OF."
    
    ClearErrors
    Delete "$SMPROGRAMS\OrDraft\OrDraft OF.lnk"
    IfErrors 0 +3
        DetailPrint "Warning: Could not delete Start Menu shortcut at $SMPROGRAMS\OrDraft\OrDraft OF.lnk."
    
    ClearErrors
    RMDir "$SMPROGRAMS\OrDraft"
    IfErrors 0 +3
        DetailPrint "Warning: Could not remove Start Menu folder at $SMPROGRAMS\OrDraft."
    
    ClearErrors
    Delete "$DESKTOP\OrDraft OF.lnk"
    IfErrors 0 +3
        DetailPrint "Warning: Could not delete Desktop shortcut at $DESKTOP\OrDraft OF.lnk."
    
    ClearErrors
FunctionEnd

# new: Post-installation actions based on user choices from the custom page
Function .onInstSuccess
    ; new: Locate the main executable in $INSTDIR:
    ClearErrors
    FindFirst $0 $1 "$INSTDIR\OrDraft-OF\OrDraft.exe"
    IfErrors 0 +3
        MessageBox MB_OK "Error: No executable found in $INSTDIR."
        Abort
    StrCpy $MAIN_EXE $1
    FindClose $0

    ${If} $CREATE_SHORTCUT == ${BST_CHECKED}
        DetailPrint "Creating shortcuts..."
        CreateDirectory "$SMPROGRAMS\OrDraft"
        CreateShortCut "$SMPROGRAMS\OrDraft\OrDraft OF.lnk" "$INSTDIR\OrDraft-OF\OrDraft.exe" "" "$INSTDIR\OrDraft-OF\OrDraft.exe" 0
        CreateShortCut "$DESKTOP\OrDraft OF.lnk" "$INSTDIR\OrDraft-OF\OrDraft.exe" "" "$INSTDIR\OrDraft-OF\OrDraft.exe" 0
    ${Else}
        DetailPrint "Skipping shortcut creation as per user selection."
    ${EndIf}
FunctionEnd

# new: Uninstaller section for complete removal of the application
Section "Uninstall"
    Delete "$INSTDIR\OrDraft-OF\OrDraft.exe"
    RMDir /r "$INSTDIR\OrDraft-OF"
    Delete "$DESKTOP\OrDraft OF.lnk"
    Delete "$SMPROGRAMS\OrDraft\OrDraft OF.lnk"
    RMDir "$SMPROGRAMS\OrDraft"
    DeleteRegKey HKLM "Software\OrDraft"
    RMDir /r "$APPDATA\Ordraft"
SectionEnd
