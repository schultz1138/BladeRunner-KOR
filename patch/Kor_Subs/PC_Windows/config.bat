@echo off

cd /d "%~dp0"

if not exist "saves" (
    mkdir "saves"
)

start "" "scummvm-k.exe" ^
    -c "scummvm-k.ini" ^
    --path="." ^
    --savepath=".\saves"


exit
