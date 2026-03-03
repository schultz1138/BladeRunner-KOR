@echo off
chcp 65001 >nul

cd /d "%~dp0"
set "GAME_DIR=%cd%"

echo [STEP] 바탕화면 바로가기 생성
set "GAME_DIR_PS=%GAME_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop';" ^
 "$DesktopPath=[Environment]::GetFolderPath('Desktop');" ^
 "if([string]::IsNullOrWhiteSpace($DesktopPath)){throw '바탕화면 경로를 찾을 수 없습니다.'};" ^
 "$WshShell=New-Object -ComObject WScript.Shell;" ^
 "$Shortcut=$WshShell.CreateShortcut((Join-Path $DesktopPath 'Blade Runner Classic (KOR).lnk'));" ^
 "$GameDir=$env:GAME_DIR_PS;" ^
 "$TargetPath=(Join-Path $GameDir 'start.bat');" ^
 "if(-not (Test-Path $TargetPath)){throw '폴더 내에서 start.bat를 찾을 수 없습니다. 경로: ' + $TargetPath};" ^
 "$Shortcut.TargetPath=$TargetPath;" ^
 "$Shortcut.WorkingDirectory=$GameDir;" ^
 "$IconPath=(Join-Path $GameDir 'BladeRunner.ico');" ^
 "if(Test-Path $IconPath){$Shortcut.IconLocation=$IconPath};" ^
 "$Shortcut.Save()"

if errorlevel 1 (
    echo [ERROR] 바탕화면 바로가기 생성에 실패했습니다.
) else (
    echo [OK] 바탕화면에 바로가기를 생성했습니다. ("Blade Runner Classic (KOR)")
)
echo.
pause
exit /b 0
