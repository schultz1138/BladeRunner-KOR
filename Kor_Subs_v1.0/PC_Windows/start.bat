@echo off

:: 현재 배치 파일이 있는 폴더를 작업 경로로 설정
cd /d "%~dp0"

:: 세이브 폴더가 없으면 생성
if not exist "Saved Games" (
    mkdir "Saved Games"
)

:: ScummVM 실행
start "" "scummvm.exe" ^
    -c "scummvm.ini" ^
    --path="." ^
    --savepath=".\Saved Games" ^
    -n -f bladerunner

exit