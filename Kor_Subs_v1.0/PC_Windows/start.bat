@echo off

cd /d "%~dp0"

if not exist "Saved Games" (
    mkdir "Saved Games"
)

start "" "scummvm.exe" ^
    -c "scummvm.ini" ^
    --path="." ^
    --savepath=".\Saved Games" ^
    -n -f bladerunner


exit
