@echo off
setlocal
if "%~1"=="" (
    echo Usage: apply_patch.bat [Target Source Directory]
    echo Example: apply_patch.bat ..\scummvm-2026.1.0_clean
    exit /b 1
)
set "TARGET=%~f1"
cd /d "%~dp0"

if not exist "%TARGET%" (
    echo [ERROR] Target directory not found: %TARGET%
    exit /b 1
)

echo Applying patch to: %TARGET%

if not exist "%TARGET%\engines\bladerunner\ui" mkdir "%TARGET%\engines\bladerunner\ui" >nul 2>&1
if not exist "%TARGET%\dists\msvc_br" mkdir "%TARGET%\dists\msvc_br" >nul 2>&1

echo [1/2] Copying runtime source files (18 files)...
for %%F in (
    "engines\bladerunner\bladerunner.cpp"
    "engines\bladerunner\bladerunner.h"
    "engines\bladerunner\dialogue_menu.cpp"
    "engines\bladerunner\subtitles.cpp"
    "engines\bladerunner\ui\end_credits.cpp"
    "engines\bladerunner\ui\esper.cpp"
    "engines\bladerunner\ui\kia.cpp"
    "engines\bladerunner\ui\kia_section_clues.cpp"
    "engines\bladerunner\ui\kia_section_crimes.cpp"
    "engines\bladerunner\ui\kia_section_diagnostic.cpp"
    "engines\bladerunner\ui\kia_section_pogo.cpp"
    "engines\bladerunner\ui\kia_section_save.cpp"
    "engines\bladerunner\ui\kia_section_settings.cpp"
    "engines\bladerunner\ui\kia_section_suspects.cpp"
    "engines\bladerunner\ui\scores.cpp"
    "engines\bladerunner\ui\ui_dropdown.cpp"
    "engines\bladerunner\ui\ui_image_picker.cpp"
    "engines\bladerunner\ui\ui_scroll_box.cpp"
) do (
    copy /y "%%~F" "%TARGET%\%%~F" >nul
    if errorlevel 1 goto :error
)

echo [2/2] Copying MSVC build config files...
for %%F in (
    "dists\msvc_br\bladerunner.vcxproj"
    "dists\msvc_br\bladerunner.vcxproj.filters"
    "dists\msvc_br\ScummVM_ASanarm64.props"
    "dists\msvc_br\ScummVM_ASanx64.props"
    "dists\msvc_br\ScummVM_ASanx86.props"
    "dists\msvc_br\ScummVM_Debugarm64.props"
    "dists\msvc_br\ScummVM_Debugx64.props"
    "dists\msvc_br\ScummVM_Debugx86.props"
    "dists\msvc_br\ScummVM_Globalarm64.props"
    "dists\msvc_br\ScummVM_Globalx64.props"
    "dists\msvc_br\ScummVM_Globalx86.props"
    "dists\msvc_br\ScummVM_LLVMarm64.props"
    "dists\msvc_br\ScummVM_LLVMx64.props"
    "dists\msvc_br\ScummVM_LLVMx86.props"
    "dists\msvc_br\ScummVM_Releasearm64.props"
    "dists\msvc_br\ScummVM_Releasex64.props"
    "dists\msvc_br\ScummVM_Releasex86.props"
    "dists\msvc_br\scummvm-detection.vcxproj"
    "dists\msvc_br\scummvm-detection.vcxproj.filters"
    "dists\msvc_br\scummvm.sln"
    "dists\msvc_br\scummvm.vcxproj"
    "dists\msvc_br\scummvm.vcxproj.filters"
    "dists\msvc_br\engines\detection_table.h"
    "dists\msvc_br\engines\plugins_table.h"
    "dists\scummvm_rc_engine_data.rh"
    "dists\scummvm_rc_engine_data_big.rh"
    "dists\scummvm_rc_engine_data_core.rh"
) do (
    copy /y "%%~F" "%TARGET%\%%~F" >nul
    if errorlevel 1 goto :error
)

echo [SUCCESS] Patch applied successfully.
exit /b 0

:error
echo [ERROR] Failed to apply patch.
exit /b 1
