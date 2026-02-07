@echo off
setlocal

rem Build minimal Blade Runner-only solution to avoid unrelated engines.
rem Usage:
rem   build_msbuild_br.bat [ScummVM source root]
rem Optional env:
rem   SCUMMVM_SRC_ROOT : source root override (if no first arg)
rem   SCUMMVM_LIBS     : prebuilt deps root (required by project)
rem   OUTDIR           : msbuild output dir (default: <repo>\build_br\)

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

if not "%~1"=="" (
  set "SRC_ROOT=%~f1"
) else if defined SCUMMVM_SRC_ROOT (
  set "SRC_ROOT=%SCUMMVM_SRC_ROOT%"
) else if exist "%REPO_ROOT%\ScummVM_BR_2026.1.0\dists\msvc_br\scummvm.sln" (
  set "SRC_ROOT=%REPO_ROOT%\ScummVM_BR_2026.1.0"
) else (
  set "SRC_ROOT=%REPO_ROOT%\ScummVM_2026.1.0"
)

if not exist "%SRC_ROOT%\dists\msvc_br\scummvm.sln" (
  echo [ERROR] ScummVM source not found: "%SRC_ROOT%"
  exit /b 1
)

if not defined SCUMMVM_LIBS set "SCUMMVM_LIBS=%REPO_ROOT%\ThirdParty\scummvm_libs"
if not exist "%SCUMMVM_LIBS%" (
  echo [ERROR] SCUMMVM_LIBS not found: "%SCUMMVM_LIBS%"
  echo         Set SCUMMVM_LIBS to your dependency folder and retry.
  exit /b 1
)

if not defined OUTDIR set "OUTDIR=%REPO_ROOT%\build_br"
if not exist "%OUTDIR%" md "%OUTDIR%"

for %%P in ("%SCUMMVM_LIBS%\include" "%SCUMMVM_LIBS%\lib" "%SCUMMVM_LIBS%\bin") do (
  if not exist "%%~fP" (
    echo [ERROR] Missing dependency subfolder: "%%~fP"
    echo         Expected SCUMMVM_LIBS with include/lib/bin layout.
    exit /b 1
  )
)

echo [INFO] Source root   : "%SRC_ROOT%"
echo [INFO] SCUMMVM_LIBS  : "%SCUMMVM_LIBS%"
echo [INFO] Output folder : "%OUTDIR%"

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
  echo [ERROR] vswhere.exe not found. Install Visual Studio or Build Tools.
  exit /b 1
)

set "VSINSTALL="
for /f "usebackq tokens=* delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
  set "VSINSTALL=%%I"
)
if not defined VSINSTALL (
  echo [ERROR] No Visual Studio installation with C++ x64 tools found.
  exit /b 1
)

call "%VSINSTALL%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 (
  echo [ERROR] Failed to initialize Visual C++ environment.
  exit /b 1
)

pushd "%SRC_ROOT%\dists\msvc_br"
msbuild scummvm.sln /p:Configuration=Release /p:Platform=x64 /v:m ^
  /p:WholeProgramOptimization=false /p:TrackFileAccess=false ^
  /p:OutDir="%OUTDIR%" ^
  /fl /flp:logfile=msbuild_br.log;verbosity=diag
set "RC=%errorlevel%"
popd

if "%RC%"=="0" (
  call :copy_runtime_dlls
  if errorlevel 1 set "RC=1"
)

echo MSBUILD EXIT %RC%
exit /b %RC%

:copy_runtime_dlls
echo [INFO] Copying runtime DLLs from "%SCUMMVM_LIBS%\bin" ...
for %%D in (
  brotlicommon.dll
  brotlidec.dll
  bz2.dll
  FLAC.dll
  freetype.dll
  fribidi-0.dll
  jpeg62.dll
  libcurl.dll
  libpng16.dll
  ogg.dll
  SDL2.dll
  SDL2_net.dll
  vorbis.dll
  vorbisfile.dll
  zlib1.dll
) do (
  if not exist "%SCUMMVM_LIBS%\bin\%%~D" (
    echo [ERROR] Missing runtime DLL: "%SCUMMVM_LIBS%\bin\%%~D"
    exit /b 1
  )
  copy /y "%SCUMMVM_LIBS%\bin\%%~D" "%OUTDIR%\%%~D" >nul
  if errorlevel 1 (
    echo [ERROR] Failed to copy: "%%~D"
    exit /b 1
  )
)

echo [INFO] Runtime DLL copy complete.
exit /b 0
